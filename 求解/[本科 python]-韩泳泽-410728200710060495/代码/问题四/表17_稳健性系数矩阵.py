# -*- coding: utf-8 -*-
"""表17：六种设定 × 七个主效应的系数稳健性矩阵（图16 的数据底座）。

口径完全照抄 问题四/代码/主程序.py 第 218 行起的"六种设定稳健性"：
  M1 全模型        : logY ~ logX1 + 类型 + 主题 + 月份哑变量 + 星期哑变量 + 时段 + 付费   (OLS, HC3)
  M2 月份固定效应  : M1 去掉 logX1（最终模型，列与 主模型.pkl 完全一致）                   (OLS, HC3)
  M3 仅logX1      : 保留 logX1、去掉月份哑变量                                          (OLS, HC3)
  M4 logX1+线性月份: 月份改线性项 X4                                                     (OLS, HC3)
  Huber 稳健回归   : M2 设计 + RLM(HuberT)；statsmodels 的 RLM 没有 HC3，用其 HC 家族
                     的 H1 稳健协方差（= 主程序缺省口径，与表16 逐位对齐）               (RLM, H1)
  Gamma GLM       : M2 设计 + Gamma(log 链接)，HC3

七个主效应：付费 / 类型：Video / 类型：Status / 类型：Link / 主题 2 / 主题 3 / 时段：凌晨。
p 值：OLS(H3) 与 RLM 用 t / 正态双侧，Gamma GLM 用正态双侧（statsmodels 缺省）。
数据：求解/清洗数据.csv（500 条，X7 无缺失：自然 361 / 付费 139，与主程序同一样本）。
输出：问题四/临时产物/稳健性系数矩阵.csv（不覆盖任何已有 CSV/图）。
"""
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import statsmodels.api as sm

df = pd.read_csv(ROOT / "清洗数据.csv", encoding="utf-8-sig")
with open(ROOT / "问题三" / "临时产物" / "主模型.pkl", "rb") as f:
    M = pickle.load(f)
cols = M["columns"]
y = df["logY"].astype(float)


def build_design(d, x1=True, month="dummy"):
    """与主程序 build_design 逐字一致，保证六种设定的设计矩阵同源。"""
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


Xm1 = build_design(df, True, "dummy")
Xm2 = build_design(df, False, "dummy")[cols]
Xm3 = build_design(df, True, "none")
Xm4 = build_design(df, True, "linear")

SPECS = ["M1 全模型", "M2 月份固定效应", "M3 仅logX1", "M4 logX1+线性月份",
         "Huber 稳健回归", "Gamma GLM（log 链接）"]
# 表中参数名（展示用） → 设计矩阵列名
EFFECTS = [("付费", "付费"),
           ("类型：Video", "类型_Video"),
           ("类型：Status", "类型_Status"),
           ("类型：Link", "类型_Link"),
           ("主题 2", "主题_2"),
           ("主题 3", "主题_3"),
           ("时段：凌晨", "时段_凌晨")]

fits = {}
for label, X in [("M1 全模型", Xm1), ("M2 月份固定效应", Xm2),
                 ("M3 仅logX1", Xm3), ("M4 logX1+线性月份", Xm4)]:
    fits[label] = sm.OLS(y, X).fit(cov_type="HC3")
fits["Huber 稳健回归"] = sm.RLM(y, Xm2).fit()          # 缺省 HuberT + H1 稳健协方差
fits["Gamma GLM（log 链接）"] = sm.GLM(
    df["Y1"].astype(float), Xm2,
    family=sm.families.Gamma(link=sm.families.links.Log())).fit(cov_type="HC3")


def stars(p):
    if not np.isfinite(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


rows = []
for label in SPECS:
    r = fits[label]
    for disp, col in EFFECTS:
        if col not in r.params.index:       # 该设定缺此参数时留空，不编造
            rows.append([label, disp, np.nan, np.nan, np.nan, ""])
            continue
        b = float(r.params[col])
        se = float(r.bse[col])
        p = float(r.pvalues[col])
        rows.append([label, disp, b, se, p, stars(p)])
tab = pd.DataFrame(rows, columns=["设定", "参数", "系数", "标准误", "p值", "显著性"])

# 数值列四位小数（与 表11/表16 同口径）；p 值四位，显著性另列承载量级
for c in ["系数", "标准误", "p值"]:
    tab[c] = tab[c].astype(float).round(4)

out = ROOT / "问题四" / "临时产物" / "稳健性系数矩阵.csv"
out.parent.mkdir(parents=True, exist_ok=True)
tab.to_csv(out, index=False, encoding="utf-8-sig")

# ---------- 自检：与 表16 的付费系数逐位对账 ----------
ref = pd.read_csv(ROOT / "问题四" / "结果" / "表16_效应稳健性对比.csv", encoding="utf-8-sig")
ref = ref.set_index("设定")["付费系数"]
paid = tab[tab["参数"] == "付费"].set_index("设定")["系数"]
diff = (paid - ref).abs()
print("付费系数（本表 / 表16）：")
for s in SPECS:
    print(f"  {s:22s} {paid[s]: .4f}  /{ref[s]: .4f}   |Δ|={diff[s]:.5f}")
assert float(diff.max()) < 0.005, "与表16 对不上，设计口径有误"
assert len(tab) == 42 and list(tab["设定"].unique()) == SPECS
print(f"\n已保存: {out}")
print(f"样本 n={len(df)}（自然 {(df.X7 == 0).sum()} / 付费 {(df.X7 == 1).sum()}）；"
      f"缺参数留空 {int(tab['系数'].isna().sum())} 处")
print(tab.to_string(index=False))
