# -*- coding: utf-8 -*-
"""问题四：模型预测与解释（题面 2.4）
付费的额外曝光、Video 与 Photo 的差异、X3 的显著性与两两差异、六种设定稳健性。
"""
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from _common import (CACHE_DIR, OUT_DIR, save_csv, shared_path, record_checks)

CACHE_DIR = Path(CACHE_DIR)
OUT_DIR = Path(OUT_DIR)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(shared_path("清洗数据.csv"), encoding="utf-8-sig")
with open(ROOT / "问题三" / "临时产物" / "主模型.pkl", "rb") as f:
    M = pickle.load(f)

cols = M["columns"]
params = M["params"]
cov = M["cov"]
smear = M["smearing"]
df_resid = M["df_resid"]
y = df["logY"].astype(float)

MONTH_COLS = [f"月份_{m}" for m in range(2, 13)]


def build_design(d, x1=True, month="dummy"):
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


X2 = build_design(df, x1=False, month="dummy")[cols]
assert list(X2.columns) == list(cols)

rng = np.random.default_rng(20261122)
NDRAW = 1000
draws = rng.multivariate_normal(params.values, cov.values, size=NDRAW)

X1_MED = float(df["X1"].median())
BASE = {"logX1": X1_MED, "X2": "Photo", "X3": 1, "X4": 7, "X5": 4,
        "hour_band": "上午", "X7": 0}


def profile(**kw):
    r = dict(BASE)
    r.update(kw)
    return pd.DataFrame([r])


def exposure(rows):
    """Duan smearing 还原：E[Y] = exp(eta) * E[exp(resid)] - 1。"""
    Xs = build_design(rows, x1=False, month="dummy")[cols]
    eta = Xs.values @ params.values
    eta_d = Xs.values @ draws.T
    point = np.exp(eta) * smear - 1
    sim = np.exp(eta_d) * smear - 1
    lo, hi = np.percentile(sim, [2.5, 97.5], axis=1)
    return point, lo, hi, sim


def ci_t(b, se):
    tc = stats.t.ppf(0.975, df_resid)
    return b - tc * se, b + tc * se


# ---------- 1. 付费效应 ----------
b_paid = float(params["付费"])
se_paid = float(M["bse"]["付费"])
p_paid = float(2 * stats.t.sf(abs(b_paid / se_paid), df_resid))
ci_paid = ci_t(b_paid, se_paid)
paid_pct = np.expm1(b_paid)
paid_pct_ci = np.expm1(ci_paid)

p0, p0lo, p0hi, sim0 = exposure(profile(X7=0))
p1, p1lo, p1hi, sim1 = exposure(profile(X7=1))
diff_sim = sim1[0] - sim0[0]
ratio_sim = sim1[0] / sim0[0]
rep_diff = float(p1[0] - p0[0])
rep_ratio = float(p1[0] / p0[0])

# 全样本 ATE
Xa = X2.copy()
Xa["付费"] = 1.0
Xb = X2.copy()
Xb["付费"] = 0.0
ea = np.exp(Xa.values @ params.values) * smear - 1
eb = np.exp(Xb.values @ params.values) * smear - 1
ea_d = np.exp(Xa.values @ draws.T) * smear - 1
eb_d = np.exp(Xb.values @ draws.T) * smear - 1
ate_diff_d = ea_d.mean(axis=0) - eb_d.mean(axis=0)
ate_ratio_d = ea_d.mean(axis=0) / eb_d.mean(axis=0)
ate_diff = float(ea.mean() - eb.mean())
ate_ratio = float(ea.mean() / eb.mean())

raw_paid = df.loc[df.X7 == 1, "Y1"]
raw_nat = df.loc[df.X7 == 0, "Y1"]

tab13 = pd.DataFrame([
    ["M2 付费系数 β", b_paid, ci_paid[0], ci_paid[1], "log1p 尺度，HC3 稳健标准误"],
    ["exp(β)−1（%）", paid_pct * 100, paid_pct_ci[0] * 100, paid_pct_ci[1] * 100,
     "几何均值提升；等价于中位数近似提升"],
    ["代表性画像：自然帖子预测曝光", p0[0], p0lo[0], p0hi[0],
     f"Photo、主题1、7月、周四、上午、X1={X1_MED:,.0f}；Duan 还原"],
    ["代表性画像：付费帖子预测曝光", p1[0], p1lo[0], p1hi[0], "同上，X7=1"],
    ["代表性画像：差值（次）", rep_diff, np.percentile(diff_sim, 2.5), np.percentile(diff_sim, 97.5),
     "付费−自然；参数模拟 95%CI"],
    ["代表性画像：倍数", rep_ratio, np.percentile(ratio_sim, 2.5), np.percentile(ratio_sim, 97.5),
     "付费/自然；参数模拟 95%CI"],
    ["全样本 ATE：差值（次）", ate_diff, np.percentile(ate_diff_d, 2.5), np.percentile(ate_diff_d, 97.5),
     "500 条帖子逐条反事实，取样本平均"],
    ["全样本 ATE：倍数", ate_ratio, np.percentile(ate_ratio_d, 2.5), np.percentile(ate_ratio_d, 97.5),
     "全样本反事实均值之比"],
    ["原始数据：付费组中位曝光", float(raw_paid.median()), np.nan, np.nan, f"n={len(raw_paid)}，未调整"],
    ["原始数据：自然组中位曝光", float(raw_nat.median()), np.nan, np.nan, f"n={len(raw_nat)}，未调整"],
    ["原始数据：中位数比", float(raw_paid.median() / raw_nat.median()), np.nan, np.nan, "未调整，仅作描述"],
    ["原始数据：均值比", float(raw_paid.mean() / raw_nat.mean()), np.nan, np.nan, "未调整，受极端值影响"],
], columns=["指标", "估计值", "95%CI下限", "95%CI上限", "说明"])
tab13[["估计值", "95%CI下限", "95%CI上限"]] = tab13[["估计值", "95%CI下限", "95%CI上限"]].round(4)
save_csv(tab13, "表13_付费效应测算.csv")

# ---------- 2. 内容类型效应 ----------
type_rows = []
type_pred = {}
for lev in ["Photo", "Status", "Link", "Video"]:
    pt, lo, hi, _ = exposure(profile(X2=lev))
    type_pred[lev] = (float(pt[0]), float(lo[0]), float(hi[0]), int((df.X2 == lev).sum()))

# 反事实：全样本改为某类型，其余不变
def ate_by_type(lev):
    Xt = X2.copy()
    for l in ["Status", "Link", "Video"]:
        Xt[f"类型_{l}"] = 1.0 if l == lev else 0.0
    et = np.exp(Xt.values @ params.values) * smear - 1
    return float(et.mean()), et


for lev in ["Video", "Status", "Link"]:
    b = float(params[f"类型_{lev}"])
    se = float(M["bse"][f"类型_{lev}"])
    p = float(2 * stats.t.sf(abs(b / se), df_resid))
    lo, hi = ci_t(b, se)
    ate_t, _ = ate_by_type(lev)
    ate_p, _ = ate_by_type("Photo")
    type_rows.append([f"{lev} vs Photo", b, se, p, np.exp(b), np.exp(lo), np.exp(hi),
                      type_pred[lev][0], type_pred["Photo"][0], ate_t / ate_p,
                      f"n={type_pred[lev][3]}" + ("；样本极少，CI 较宽" if lev == "Video" else "")])
tab14 = pd.DataFrame(type_rows, columns=[
    "对比", "系数", "HC3标准误", "p值", "倍数", "倍数CI下限", "倍数CI上限",
    "代表性画像处理组曝光", "代表性画像对照组曝光", "全样本ATE倍数", "说明"])
tab14[["系数", "HC3标准误", "p值", "倍数", "倍数CI下限", "倍数CI上限",
       "代表性画像处理组曝光", "代表性画像对照组曝光", "全样本ATE倍数"]] = \
    tab14[["系数", "HC3标准误", "p值", "倍数", "倍数CI下限", "倍数CI上限",
           "代表性画像处理组曝光", "代表性画像对照组曝光", "全样本ATE倍数"]].round(4)
save_csv(tab14, "表14_内容类型效应与两两对比.csv")

# ---------- 3. X3 主题效应 ----------
idx3 = [list(params.index).index("主题_2"), list(params.index).index("主题_3")]
b3 = params.values[idx3]
V3 = cov.values[np.ix_(idx3, idx3)]
W = float(b3 @ np.linalg.inv(V3) @ b3)
p_joint = float(stats.chi2.sf(W, 2))

b2, b3v = float(params["主题_2"]), float(params["主题_3"])
se2, se3 = float(M["bse"]["主题_2"]), float(M["bse"]["主题_3"])
p2 = float(2 * stats.t.sf(abs(b2 / se2), df_resid))
p3 = float(2 * stats.t.sf(abs(b3v / se3), df_resid))
ci2, ci3 = ci_t(b2, se2), ci_t(b3v, se3)

bd = b2 - b3v
sed = float(np.sqrt(V3[0, 0] + V3[1, 1] - 2 * V3[0, 1]))
pdiff = float(2 * stats.norm.sf(abs(bd / sed)))
z = stats.norm.ppf(0.975)

rows15 = [
    ["联合检验（Wald）", "主题2=主题3=0", W, np.nan, p_joint, np.nan, np.nan, np.nan,
     "H0：两哑变量系数同时为0；df=2"],
    ["主题2 vs 主题1", "差异", b2, se2, p2, np.exp(b2), np.exp(ci2[0]), np.exp(ci2[1]),
     "HC3 t 检验"],
    ["主题3 vs 主题1", "差异", b3v, se3, p3, np.exp(b3v), np.exp(ci3[0]), np.exp(ci3[1]),
     "HC3 t 检验"],
    ["主题2 vs 主题3", "差异", bd, sed, pdiff, np.exp(bd), np.exp(bd - z * sed), np.exp(bd + z * sed),
     "Wald z 检验，两系数协方差来自 HC3"],
]
tab15 = pd.DataFrame(rows15, columns=[
    "项目", "对比", "系数或统计量", "标准误", "p值", "倍数", "倍数CI下限", "倍数CI上限", "说明"])
tab15[["系数或统计量", "标准误", "p值", "倍数", "倍数CI下限", "倍数CI上限"]] = \
    tab15[["系数或统计量", "标准误", "p值", "倍数", "倍数CI下限", "倍数CI上限"]].round(4)
save_csv(tab15, "表15_内容主题X3效应与两两对比.csv")

# ---------- 4. 六种设定稳健性 ----------
Xm1 = build_design(df, True, "dummy")
Xm2 = build_design(df, False, "dummy")[cols]
Xm3 = build_design(df, True, "none")
Xm4 = build_design(df, True, "linear")


def joint_x3(b, V, names):
    ii = [list(names).index("主题_2"), list(names).index("主题_3")]
    bb = np.asarray(b)[ii]
    VV = np.asarray(V)[np.ix_(ii, ii)]
    w = float(bb @ np.linalg.inv(VV) @ bb)
    return w, float(stats.chi2.sf(w, 2))


specs = []
for label, X in [("M1 全模型", Xm1), ("M2 月份固定效应", Xm2),
                 ("M3 仅logX1", Xm3), ("M4 logX1+线性月份", Xm4)]:
    r = sm.OLS(y, X).fit(cov_type="HC3")
    names = list(X.columns)
    w, pj = joint_x3(r.params.values, r.cov_params().values, names)
    specs.append([label, r.params["付费"], r.bse["付费"], r.pvalues["付费"],
                  r.params["类型_Video"], r.bse["类型_Video"], r.pvalues["类型_Video"], pj])

hub = sm.RLM(y, Xm2).fit()
w_h, p_h = joint_x3(hub.params.values, hub.cov_params().values, list(Xm2.columns))
specs.append(["Huber 稳健回归", hub.params["付费"], hub.bse["付费"], hub.pvalues["付费"],
              hub.params["类型_Video"], hub.bse["类型_Video"], hub.pvalues["类型_Video"], p_h])

gam = sm.GLM(df["Y1"].astype(float), Xm2,
             family=sm.families.Gamma(link=sm.families.links.Log())).fit(cov_type="HC3")
w_g, p_g = joint_x3(gam.params.values, gam.cov_params().values, list(Xm2.columns))
specs.append(["Gamma GLM（log 链接）", gam.params["付费"], gam.bse["付费"], gam.pvalues["付费"],
              gam.params["类型_Video"], gam.bse["类型_Video"], gam.pvalues["类型_Video"], p_g])

rob = pd.DataFrame(specs, columns=[
    "设定", "付费系数", "付费标准误", "付费p值", "Video系数", "Video标准误", "Video p值", "X3联合p值"])
rob["付费提升%"] = np.expm1(rob["付费系数"]) * 100
rob["付费提升CI下限"] = np.expm1(rob["付费系数"] - z * rob["付费标准误"]) * 100
rob["付费提升CI上限"] = np.expm1(rob["付费系数"] + z * rob["付费标准误"]) * 100
rob["Video倍数"] = np.exp(rob["Video系数"])
rob["Video倍数CI下限"] = np.exp(rob["Video系数"] - z * rob["Video标准误"])
rob["Video倍数CI上限"] = np.exp(rob["Video系数"] + z * rob["Video标准误"])
rob = rob[["设定", "付费系数", "付费标准误", "付费p值", "付费提升%", "付费提升CI下限", "付费提升CI上限",
           "Video系数", "Video标准误", "Video p值", "Video倍数", "Video倍数CI下限", "Video倍数CI上限",
           "X3联合p值"]]
rob = rob.round(4)
save_csv(rob, "表16_效应稳健性对比.csv")

# ---------- 5. 调整预测与交互 ----------
pred_rows = []
for lev in [0, 1]:
    pt, lo, hi, _ = exposure(profile(X7=lev))
    pred_rows.append(["a 付费", "自然" if lev == 0 else "付费", "付费", pt[0], lo[0], hi[0], int((df.X7 == lev).sum())])
for lev in ["Photo", "Status", "Link", "Video"]:
    pt, lo, hi, _ = exposure(profile(X2=lev))
    pred_rows.append(["b 内容类型", lev, lev, pt[0], lo[0], hi[0], type_pred[lev][3]])
for lev in [1, 2, 3]:
    pt, lo, hi, _ = exposure(profile(X3=lev))
    pred_rows.append(["c 内容主题", f"主题{lev}", f"主题{lev}", pt[0], lo[0], hi[0], int((df.X3 == lev).sum())])

# 交互：付费×类型（仅用于检验效应是否以主效应为主）
Xi = Xm2.copy()
for lev in ["Status", "Link", "Video"]:
    Xi[f"付费x{lev}"] = Xi["付费"] * Xi[f"类型_{lev}"]
mi = sm.OLS(y, Xi).fit(cov_type="HC3")
int_cols = ["付费xStatus", "付费xLink", "付费xVideo"]
R = np.zeros((3, Xi.shape[1]))
for i, c in enumerate(int_cols):
    R[i, Xi.columns.get_loc(c)] = 1
wt = mi.f_test(R)
p_int = float(wt.pvalue)

cell = df.groupby(["X2", "X7"])["Y1"].agg(["median", "count"]).reset_index()
for _, r in cell.iterrows():
    pred_rows.append(["d 交互描述", "自然" if r["X7"] == 0 else "付费", r["X2"],
                      float(r["median"]), np.nan, np.nan, int(r["count"])])
pred_df = pd.DataFrame(pred_rows, columns=["面板", "组", "系列", "值", "CI下限", "CI上限", "样本量"])
pred_df = pd.concat([pred_df, pd.DataFrame([["d 交互描述", "检验", "交互p值", p_int, np.nan, np.nan, np.nan]],
                                           columns=pred_df.columns)], ignore_index=True)
pred_df[["值", "CI下限", "CI上限"]] = pred_df[["值", "CI下限", "CI上限"]].round(2)
pred_df.to_csv(CACHE_DIR / "调整预测.csv", index=False, encoding="utf-8-sig")

# 稳健性绘图数据
rob_rows = []
for _, r in rob.iterrows():
    rob_rows.append([r["设定"], "付费提升%", r["付费提升%"], r["付费提升CI下限"], r["付费提升CI上限"]])
    rob_rows.append([r["设定"], "Video倍数", r["Video倍数"], r["Video倍数CI下限"], r["Video倍数CI上限"]])
pd.DataFrame(rob_rows, columns=["设定", "效应", "估计", "下限", "上限"]).to_csv(
    CACHE_DIR / "稳健性系数.csv", index=False, encoding="utf-8-sig")

# 效应测算汇总（供正文引用）
eff_rows = [
    ["付费", "样本平均ATE倍数", ate_ratio, np.percentile(ate_ratio_d, 2.5), np.percentile(ate_ratio_d, 97.5)],
    ["付费", "样本平均ATE差值", ate_diff, np.percentile(ate_diff_d, 2.5), np.percentile(ate_diff_d, 97.5)],
    ["Video vs Photo", "调整预测倍数", type_pred["Video"][0] / type_pred["Photo"][0], np.nan, np.nan],
    ["主题2 vs 1", "倍数", np.exp(b2), np.exp(ci2[0]), np.exp(ci2[1])],
    ["主题3 vs 1", "倍数", np.exp(b3v), np.exp(ci3[0]), np.exp(ci3[1])],
    ["主题2 vs 3", "倍数", np.exp(bd), np.exp(bd - z * sed), np.exp(bd + z * sed)],
    ["交互检验", "付费×类型 p 值", p_int, np.nan, np.nan],
    ["主题联合检验", "Wald p 值", p_joint, np.nan, np.nan],
]
pd.DataFrame(eff_rows, columns=["对象", "指标", "估计", "下限", "上限"]).round(4).to_csv(
    CACHE_DIR / "效应测算.csv", index=False, encoding="utf-8-sig")

# ---------- 输出 ----------
print("代表性画像 X1 中位数:", X1_MED)
print("付费: β=%.4f, p=%.4f, exp(β)-1=%.1f%%, 95%%CI=[%.1f%%, %.1f%%]" % (
    b_paid, p_paid, paid_pct * 100, paid_pct_ci[0] * 100, paid_pct_ci[1] * 100))
print("代表性曝光: 自然 %.0f, 付费 %.0f, 差 %.0f, 倍数 %.2f" % (p0[0], p1[0], rep_diff, rep_ratio))
print("全样本 ATE: 差 %.0f, 倍数 %.3f, CI=[%.3f, %.3f]" % (
    ate_diff, ate_ratio, np.percentile(ate_ratio_d, 2.5), np.percentile(ate_ratio_d, 97.5)))
print("Video: β=%.4f, 倍数=%.3f, CI=[%.2f, %.2f], p=%.4f, n=%d" % (
    params["类型_Video"], np.exp(params["类型_Video"]),
    np.exp(ci_t(params["类型_Video"], M["bse"]["类型_Video"])[0]),
    np.exp(ci_t(params["类型_Video"], M["bse"]["类型_Video"])[1]),
    2 * stats.t.sf(abs(params["类型_Video"] / M["bse"]["类型_Video"]), df_resid), type_pred["Video"][3]))
print("X3 联合 Wald=%.3f, p=%.4f; 2 vs 3: %.3f (p=%.4f)" % (W, p_joint, bd, pdiff))
print("交互检验 p=%.3f" % p_int)
print("稳健性设定数:", len(rob), "付费提升范围 %.1f–%.1f%%, Video倍数范围 %.2f–%.2f" % (
    rob["付费提升%"].min(), rob["付费提升%"].max(), rob["Video倍数"].min(), rob["Video倍数"].max()))
print("已保存 表13–16 与绘图数据")

record_checks({
    "样本量500": len(df) == 500,
    "设计矩阵列与主模型一致": list(X2.columns) == list(M["train_X"].columns),
    "付费系数为正且显著": b_paid > 0 and p_paid < 0.05,
    "Video系数显著": 2 * stats.t.sf(abs(params["类型_Video"] / M["bse"]["类型_Video"]), df_resid) < 0.05,
    "X3联合检验显著": p_joint < 0.05,
    "ATE倍数大于1": ate_ratio > 1,
    "六种设定方向一致": bool((rob["付费提升%"] > 0).all() and (rob["Video倍数"] > 1).all()),
    "所有预测曝光为正": bool((pred_df.loc[pred_df["面板"] != "d 交互描述", "值"] > 0).all()),
    "模拟CI有限": bool(np.isfinite(np.percentile(ate_ratio_d, [2.5, 97.5])).all()),
})
