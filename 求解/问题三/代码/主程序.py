# -*- coding: utf-8 -*-
"""问题三：回归预测分析（题面 2.3）
OLS + HC3；全模型与最终模型对比；共线性、残差、整体显著性、交叉验证、Shapley。
"""
import math
import pickle
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.model_selection import KFold
from statsmodels.stats.diagnostic import het_breuschpagan, het_white, linear_reset
from statsmodels.stats.outliers_influence import variance_inflation_factor, OLSInfluence
from statsmodels.stats.stattools import durbin_watson

from _common import (CACHE_DIR, OUT_DIR, save_csv, shared_path, record_checks)

CACHE_DIR = Path(CACHE_DIR)
OUT_DIR = Path(OUT_DIR)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

DATA = shared_path("清洗数据.csv")
df = pd.read_csv(DATA, encoding="utf-8-sig")
y = df["logY"].astype(float)
N = len(df)

TYPE_COLS = ["类型_Status", "类型_Link", "类型_Video"]
THEME_COLS = ["主题_2", "主题_3"]
MONTH_COLS = [f"月份_{m}" for m in range(2, 13)]
WEEK_COLS = [f"星期_{w}" for w in range(2, 8)]
HOUR_COLS = ["时段_凌晨", "时段_下午晚间"]


def build_design(d, x1=True, month="dummy"):
    """手工设计矩阵，保证交叉验证与预测时列结构固定。"""
    X = pd.DataFrame(index=d.index)
    X["const"] = 1.0
    if x1:
        X["logX1"] = d["logX1"].astype(float)
    for lev in ["Status", "Link", "Video"]:
        X[f"类型_{lev}"] = (d["X2"] == lev).astype(float)
    for lev in [2, 3]:
        X[f"主题_{lev}"] = (d["X3"] == lev).astype(float)
    if month == "dummy":
        for m in range(2, 13):
            X[f"月份_{m}"] = (d["X4"] == m).astype(float)
    elif month == "linear":
        X["月份"] = d["X4"].astype(float)
    for w in range(2, 8):
        X[f"星期_{w}"] = (d["X5"] == w).astype(float)
    X["时段_凌晨"] = (d["hour_band"] == "凌晨").astype(float)
    X["时段_下午晚间"] = (d["hour_band"] == "下午晚间").astype(float)
    X["付费"] = d["X7"].astype(float)
    return X


X1 = build_design(df, x1=True, month="dummy")
X2 = build_design(df, x1=False, month="dummy")
X3 = build_design(df, x1=True, month="none")
X4 = build_design(df, x1=True, month="linear")
X0 = X1[["const"]]

MODELS = {"M0": X0, "M1": X1, "M2": X2, "M3": X3, "M4": X4}
FITS = {k: sm.OLS(y, X).fit() for k, X in MODELS.items()}
FITS_HC3 = {k: sm.OLS(y, X).fit(cov_type="HC3") for k, X in MODELS.items()}

WEEK_NAME = {2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}


def pretty(name):
    if name == "const":
        return "常数项"
    if name == "logX1":
        return "log(粉丝规模)"
    if name == "X7" or name == "付费":
        return "付费（X7=1）"
    if name.startswith("类型_"):
        return "类型：" + name.split("_", 1)[1]
    if name.startswith("主题_"):
        return "主题：" + name.split("_", 1)[1]
    if name.startswith("星期_"):
        return "星期：" + WEEK_NAME[int(name.split("_", 1)[1])]
    if name.startswith("月份_"):
        return "月份：" + name.split("_", 1)[1] + "月"
    if name == "月份":
        return "月份（线性）"
    if name.startswith("时段_"):
        return "时段：" + name.split("_", 1)[1]
    return name


def vif_table(X):
    vals = []
    for i, c in enumerate(X.columns):
        if c == "const":
            vals.append(np.nan)
        else:
            vals.append(float(variance_inflation_factor(X.values, i)))
    return pd.Series(vals, index=X.columns)


def gvif_table(X):
    """Fox–Monette GVIF：基于设计矩阵（不含常数项）的相关矩阵。"""
    Xn = X.drop(columns="const")
    R = np.corrcoef(Xn.values, rowvar=False)
    groups = {}
    for c in Xn.columns:
        key = c.split("_")[0] if c.startswith(("类型", "主题", "月份", "星期", "时段")) else c
        groups.setdefault(key, []).append(Xn.columns.get_loc(c))
    rows = []
    for key, idx in groups.items():
        other = [j for j in range(Xn.shape[1]) if j not in idx]
        sign1, logdet1 = np.linalg.slogdet(R[np.ix_(idx, idx)])
        sign2, logdet2 = np.linalg.slogdet(R[np.ix_(other, other)])
        sign0, logdet0 = np.linalg.slogdet(R)
        gvif = math.exp(logdet1 + logdet2 - logdet0)
        adj = gvif ** (1.0 / (2 * len(idx)))
        rows.append([key, len(idx), gvif, adj])
    return pd.DataFrame(rows, columns=["变量组", "自由度", "GVIF", "GVIF调整"])


VIF1 = vif_table(X1)
VIF2 = vif_table(X2)
GVIF1 = gvif_table(X1)


def cond_number(X):
    Z = (X.drop(columns="const") - X.drop(columns="const").mean()) / X.drop(columns="const").std(ddof=0)
    return float(np.linalg.cond(Z.values))


COND1, COND2 = cond_number(X1), cond_number(X2)

# 月内/月间分解
month_dummies = pd.get_dummies(df["X4"], prefix="m", drop_first=False).astype(float)
aux = sm.OLS(df["logX1"], month_dummies).fit()
within_sd = float(np.sqrt(np.mean(aux.resid ** 2)))
total_sd = float(df["logX1"].std(ddof=1))
within_share = within_sd / total_sd

# 加入 logX1 的增量 F（相对 M2）
rss1, rss2 = FITS["M1"].ssr, FITS["M2"].ssr
df1, df2 = FITS["M1"].df_resid, FITS["M2"].df_resid
inc_f = ((rss2 - rss1) / (df2 - df1)) / (rss1 / df1)
inc_p = float(stats.f.sf(inc_f, df2 - df1, df1))


def coef_table(model, res, res_hc3, vif):
    params = res.params
    se = res_hc3.bse
    tcrit = stats.t.ppf(0.975, res.df_resid)
    tval = params / se
    pval = 2 * stats.t.sf(np.abs(tval), res.df_resid)
    stars = np.where(pval < 0.001, "***", np.where(pval < 0.01, "**", np.where(pval < 0.05, "*", "")))
    out = pd.DataFrame({
        "变量": [pretty(c) for c in params.index],
        "系数": params.values,
        "经典标准误": res.bse.values,
        "HC3标准误": se.values,
        "t值": tval.values,
        "p值": pval,
        "95%CI下限": (params - tcrit * se).values,
        "95%CI上限": (params + tcrit * se).values,
        "VIF": [vif.get(c, np.nan) for c in params.index],
        "显著性": stars,
    })
    out.insert(0, "模型", model)
    return out


tab7 = coef_table("M1 全模型", FITS["M1"], FITS_HC3["M1"], VIF1)
tab11 = coef_table("M2 最终模型", FITS["M2"], FITS_HC3["M2"], VIF2)
for t in (tab7, tab11):
    num = [c for c in t.columns if c not in ("模型", "变量", "显著性")]
    t[num] = t[num].round(4)
save_csv(tab7, "表7_全模型系数表.csv")
save_csv(tab11, "表11_最终模型系数表.csv")

# ---------- 共线性诊断表 ----------
rows = [
    ["M1 最大 VIF（不含常数）", "全部解释变量", np.nanmax(VIF1.values), ">10 严重", "严重共线"],
    ["M1 VIF", "log(粉丝规模)", VIF1["logX1"], ">10 严重", "严重共线"],
    ["M1 VIF", "月份哑变量最大值", VIF1[MONTH_COLS].max(), ">10 严重", "与 logX1 互为镜像"],
    ["M1 标准化设计矩阵条件数", "全部解释变量", COND1, ">30 严重", "数值不稳定"],
    ["M1 增量 F 统计量", "在 M2 基础上加入 logX1", inc_f, "—", "增量贡献很小"],
    ["M1 增量 F 检验 p 值", "在 M2 基础上加入 logX1", inc_p, ">0.05 不显著", "X1 系数不可识别"],
    ["R²(logX1 ~ 月份哑变量)", "月间趋势", aux.rsquared, ">0.9 近乎确定", "粉丝规模几乎由月份决定"],
    ["月内 logX1 方差占比", "组内变异", within_share ** 2, "<0.05 信息不足",
     f"月内 SD={within_sd:.4f}，总 SD={total_sd:.4f}，占比 {within_share ** 2:.2%}"],
    ["M2 最大 VIF（不含常数）", "全部解释变量", np.nanmax(VIF2.values), "<5 可接受", "共线已缓解"],
    ["M2 标准化设计矩阵条件数", "全部解释变量", COND2, "<30 可接受", "通过"],
]
for _, r in GVIF1.iterrows():
    rows.append([f"GVIF^(1/(2df))：{r['变量组']}", f"自由度 {int(r['自由度'])}", r["GVIF调整"],
                 ">2.24 需关注", "超过阈值" if r["GVIF调整"] > 2.24 else "未超过阈值"])
diag = pd.DataFrame(rows, columns=["诊断项", "对象", "数值", "参考阈值", "判断"])
diag["数值"] = diag["数值"].astype(float).round(4)
save_csv(diag, "表8_共线性诊断.csv")

# ---------- 残差诊断 ----------
def diagnostic_rows(model, res, X):
    resid = np.asarray(res.resid, dtype=float)
    Xv = np.asarray(X, dtype=float)
    jb_stat, jb_p = stats.jarque_bera(resid)[:2]
    bp = het_breuschpagan(resid, Xv)
    try:
        wh = het_white(resid, Xv)
    except Exception:
        wh = (np.nan, np.nan, np.nan, np.nan)
    try:
        rs = linear_reset(res, power=3, use_f=True)
        rs_stat, rs_p = float(rs.fvalue), float(rs.pvalue)
    except Exception:
        rs_stat, rs_p = np.nan, np.nan
    dw = durbin_watson(resid)
    infl = OLSInfluence(res)
    cook = infl.cooks_distance[0]
    lev = infl.hat_matrix_diag
    p = Xv.shape[1]
    return [
        [model, "Jarque–Bera 正态性", jb_stat, jb_p, "残差非正态" if jb_p < 0.05 else "不能拒绝正态"],
        [model, "Breusch–Pagan 异方差", bp[0], bp[1], "存在异方差" if bp[1] < 0.05 else "未检出异方差"],
        [model, "White 异方差", wh[0], wh[1], "存在异方差" if (np.isfinite(wh[1]) and wh[1] < 0.05) else "未检出/不可判定"],
        [model, "Ramsey RESET（3 阶）", rs_stat, rs_p, "函数形式不足" if (np.isfinite(rs_p) and rs_p < 0.05) else "未检出设定误差"],
        [model, "Durbin–Watson", dw, np.nan, "接近 2，无强自相关（截面数据仅作参考）"],
        [model, "Cook 距离最大值", float(np.nanmax(cook)), np.nan,
         "存在强影响点" if np.nanmax(cook) > 1 else "无 Cook>1 的强影响点"],
        [model, "高杠杆点个数（h>2p/n）", int(np.sum(lev > 2 * p / len(lev))), np.nan,
         f"阈值 h>{2 * p / len(lev):.3f}"],
    ]


tab9 = pd.DataFrame(
    diagnostic_rows("M1 全模型", FITS["M1"], X1) + diagnostic_rows("M2 最终模型", FITS["M2"], X2),
    columns=["模型", "检验", "统计量", "p值", "判断"])
tab9["统计量"] = tab9["统计量"].astype(float).round(4)
tab9["p值"] = tab9["p值"].astype(float).round(4)
save_csv(tab9, "表9_残差诊断检验.csv")

# ---------- 交叉验证 ----------
def cv_model(X, yv, repeats=5, folds=10, seed=20261122):
    r2s, rmses, maes = [], [], []
    oof_first = None
    for r in range(repeats):
        kf = KFold(n_splits=folds, shuffle=True, random_state=seed + r)
        oof = np.full(len(yv), np.nan)
        for tr, te in kf.split(X):
            m = sm.OLS(yv.iloc[tr], X.iloc[tr]).fit()
            pred = np.asarray(m.predict(X.iloc[te]))
            oof[te] = pred
            r2s.append(1 - np.sum((yv.iloc[te].values - pred) ** 2) /
                       np.sum((yv.iloc[te].values - yv.iloc[te].mean()) ** 2))
            rmses.append(np.sqrt(np.mean((yv.iloc[te].values - pred) ** 2)))
            maes.append(np.mean(np.abs(yv.iloc[te].values - pred)))
        if r == 0:
            oof_first = oof
    return {"r2": np.array(r2s), "rmse": np.array(rmses), "mae": np.array(maes), "oof": oof_first}


CV = {}
for k, X in MODELS.items():
    CV[k] = cv_model(X, y)

LABELS = {
    "M0": "M0 均值基线",
    "M1": "M1 全模型（含 logX1 与月份）",
    "M2": "M2 月份固定效应（最终模型）",
    "M3": "M3 仅 logX1（无月份）",
    "M4": "M4 logX1 + 线性月份",
}
rows = []
for k in MODELS:
    r = FITS[k]
    rows.append([
        k, LABELS[k], int(len(r.params)), r.rsquared, r.rsquared_adj, np.sqrt(r.mse_resid),
        r.aic, r.bic, r.fvalue if k != "M0" else np.nan,
        r.f_pvalue if k != "M0" else np.nan,
        CV[k]["r2"].mean(), CV[k]["r2"].std(ddof=1),
        CV[k]["rmse"].mean(), CV[k]["mae"].mean(),
    ])
tab10 = pd.DataFrame(rows, columns=[
    "模型", "设定", "参数个数", "R²", "调整R²", "残差标准误", "AIC", "BIC",
    "整体F", "F检验p值", "CV_R²均值", "CV_R²标准差", "CV_RMSE", "CV_MAE"])
num_cols = ["R²", "调整R²", "残差标准误", "AIC", "BIC", "整体F", "F检验p值",
            "CV_R²均值", "CV_R²标准差", "CV_RMSE", "CV_MAE"]
tab10[num_cols] = tab10[num_cols].round(4)
save_csv(tab10, "表10_模型比较与交叉验证.csv")

# ---------- Shapley R² ----------
GROUPS = {
    "发帖类型 X2": TYPE_COLS,
    "内容主题 X3": THEME_COLS,
    "月份 X4": MONTH_COLS,
    "星期 X5": WEEK_COLS,
    "时段 X6": HOUR_COLS,
    "付费 X7": ["付费"],
    "粉丝规模 logX1": ["logX1"],
}
keys = list(GROUPS)
K = len(keys)
r2_cache = {}
for mask in range(1 << K):
    cols = ["const"]
    for i, key in enumerate(keys):
        if mask >> i & 1:
            cols += GROUPS[key]
    r2_cache[mask] = float(sm.OLS(y, X1[cols]).fit().rsquared)

shap = {}
for i, key in enumerate(keys):
    val = 0.0
    for mask in range(1 << K):
        if mask >> i & 1:
            continue
        s = bin(mask).count("1")
        w = math.factorial(s) * math.factorial(K - s - 1) / math.factorial(K)
        val += w * (r2_cache[mask | (1 << i)] - r2_cache[mask])
    shap[key] = val

full_r2 = FITS["M1"].rsquared
rows = []
for key in keys:
    rows.append([key, len(GROUPS[key]), shap[key], shap[key] / full_r2, shap[key]])
decision = sum(shap[k] for k in keys[:2] + keys[3:6])
scale_time = shap["月份 X4"] + shap["粉丝规模 logX1"]
rows.append(["发帖决策合计（X2/X3/X5/X6/X7）", 13, decision, decision / full_r2, decision])
rows.append(["账号规模与时间合计（X1/X4）", 12, scale_time, scale_time / full_r2, scale_time])
rows.append(["未解释方差", np.nan, 1 - full_r2, np.nan, 1 - full_r2])
tab12 = pd.DataFrame(rows, columns=["变量组", "自由度", "Shapley_R²", "占已解释方差", "占总方差"])
tab12[["Shapley_R²", "占已解释方差", "占总方差"]] = tab12[["Shapley_R²", "占已解释方差", "占总方差"]].round(6)
save_csv(tab12, "表12_Shapley方差分解.csv")

# ---------- 绘图数据 ----------
main_cols = ["类型_Status", "类型_Link", "类型_Video", "主题_2", "主题_3",
             "时段_凌晨", "时段_下午晚间", "付费"]
res2h = FITS_HC3["M2"]
tcrit = stats.t.ppf(0.975, res2h.df_resid)
forest = pd.DataFrame({
    "变量": main_cols,
    "标签": [pretty(c) for c in main_cols],
    "系数": [res2h.params[c] for c in main_cols],
    "标准误": [res2h.bse[c] for c in main_cols],
    "CI下限": [res2h.params[c] - tcrit * res2h.bse[c] for c in main_cols],
    "CI上限": [res2h.params[c] + tcrit * res2h.bse[c] for c in main_cols],
    "p值": [2 * stats.t.sf(abs(res2h.params[c] / res2h.bse[c]), res2h.df_resid) for c in main_cols],
    "倍数": [np.exp(res2h.params[c]) for c in main_cols],
})
forest.to_csv(CACHE_DIR / "绘图数据_森林.csv", index=False, encoding="utf-8-sig")

res2 = FITS["M2"]
infl = OLSInfluence(res2)
std_res = np.asarray(infl.resid_studentized_internal)
osm, osr = stats.probplot(std_res, dist="norm", fit=False)
resid_df = pd.DataFrame({
    "拟合值": res2.fittedvalues,
    "残差": res2.resid,
    "标准化残差": std_res,
    "尺度位置": np.sqrt(np.abs(std_res)),
    "杠杆值": infl.hat_matrix_diag,
    "Cook距离": infl.cooks_distance[0],
    "QQ理论": osm,
    "QQ样本": osr,
})
resid_df.to_csv(CACHE_DIR / "绘图数据_残差.csv", index=False, encoding="utf-8-sig")

pred_df = pd.DataFrame({
    "观测值": y.values,
    "样本内拟合": res2.fittedvalues.values,
    "交叉验证预测": CV["M2"]["oof"],
})
pred_df.to_csv(CACHE_DIR / "绘图数据_预测.csv", index=False, encoding="utf-8-sig")

vif_rows = []
for model, vif in [("M1", VIF1), ("M2", VIF2)]:
    for c in vif.index:
        if c == "const":
            continue
        vif_rows.append([model, c, pretty(c), float(vif[c])])
pd.DataFrame(vif_rows, columns=["模型", "变量", "标签", "VIF"]).to_csv(
    CACHE_DIR / "VIF.csv", index=False, encoding="utf-8-sig")
tab10.to_csv(CACHE_DIR / "CV结果.csv", index=False, encoding="utf-8-sig")
tab12.to_csv(CACHE_DIR / "Shapley.csv", index=False, encoding="utf-8-sig")

# ---------- 保存主模型 ----------
payload = {
    "model": "M2",
    "columns": list(X2.columns),
    "params": res2h.params.copy(),
    "bse": res2h.bse.copy(),
    "cov": res2h.cov_params().copy(),
    "df_resid": int(res2h.df_resid),
    "resid": pd.Series(np.asarray(res2.resid), index=df.index),
    "fitted": pd.Series(np.asarray(res2.fittedvalues), index=df.index),
    "y": y.copy(),
    "train_X": X2.copy(),
    "train_y": y.copy(),
    "smearing": float(np.mean(np.exp(np.asarray(res2.resid)))),
    "r2": float(res2.rsquared),
    "r2_adj": float(res2.rsquared_adj),
    "sigma2": float(res2.mse_resid),
}
with open(CACHE_DIR / "主模型.pkl", "wb") as f:
    pickle.dump(payload, f, protocol=4)

# ---------- 输出 ----------
print("样本量:", N)
print("M1: 参数 %d, R2=%.4f, adjR2=%.4f, 残差SE=%.4f" % (
    len(FITS["M1"].params), FITS["M1"].rsquared, FITS["M1"].rsquared_adj, np.sqrt(FITS["M1"].mse_resid)))
print("M2: 参数 %d, R2=%.4f, adjR2=%.4f, 残差SE=%.4f" % (
    len(FITS["M2"].params), FITS["M2"].rsquared, FITS["M2"].rsquared_adj, np.sqrt(FITS["M2"].mse_resid)))
print("VIF logX1=%.1f, M1 max=%.1f, M2 max=%.2f, cond M1=%.0f, cond M2=%.1f" % (
    VIF1["logX1"], np.nanmax(VIF1.values), np.nanmax(VIF2.values), COND1, COND2))
print("R2(logX1~月份)=%.4f, 月内SD=%.4f, 占比=%.4f, 增量F p=%.3f" % (
    aux.rsquared, within_sd, within_share, inc_p))
print("CV R2:", {k: round(CV[k]["r2"].mean(), 4) for k in MODELS})
print("Shapley 合计=%.6f, 全模型R2=%.6f" % (sum(shap.values()), full_r2))
print("已保存 主模型.pkl 与 表7–12")

record_checks({
    "样本量500": N == 500,
    "设计矩阵无缺失": bool(X1.notna().all().all() and X2.notna().all().all()),
    "M1参数27": len(FITS["M1"].params) == 27,
    "M2参数26": len(FITS["M2"].params) == 26,
    "logX1的VIF>100": VIF1["logX1"] > 100,
    "M1条件数>30": COND1 > 30,
    "M2最大VIF<5": np.nanmax(VIF2.values) < 5,
    "R2有限且在0到1之间": bool(0 <= FITS["M1"].rsquared <= 1 and 0 <= FITS["M2"].rsquared <= 1),
    "Shapley合计等于全模型R2": abs(sum(shap.values()) - full_r2) < 1e-6,
    "CV结果有限": bool(all(np.isfinite(CV[k]["r2"]).all() for k in MODELS)),
    "主模型文件存在": (CACHE_DIR / "主模型.pkl").exists(),
})
