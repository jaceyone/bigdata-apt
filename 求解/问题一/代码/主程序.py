# -*- coding: utf-8 -*-
"""问题一：数据理解（题面 2.1）
读取原始 CSV，完成单位/粒度、截面结构、因果角色与核心共线问题的量化。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from _common import (BASE_DIR, CACHE_DIR, OUT_DIR, resolve_input, save_csv,
                     record_checks)

RESULT_DIR = Path(OUT_DIR)
CACHE_DIR = Path(CACHE_DIR)
RESULT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ---------- 1. 读取原始数据（只读原件） ----------
src = resolve_input("source-1ce2d1eb-371f-41f2-9c0f-1e1ec8d6f73a")
df = pd.read_csv(src, encoding="utf-8-sig")
df.columns = [c.strip() for c in df.columns]
df["row_id"] = np.arange(1, len(df) + 1)
raw = df.copy()

# ---------- 2. 基础检查 ----------
n_rows, n_cols = raw.shape
missing = raw[["X1", "X2", "X3", "X4", "X5", "X6", "X7", "Y1"]].isna().sum()
dups = int(raw.duplicated(subset=["X1", "X2", "X3", "X4", "X5", "X6", "X7", "Y1"]).sum())

# ---------- 3. 变量字典 ----------
var_dict = pd.DataFrame([
    ["X1", "粉丝规模（主页粉丝数）", "连续", "状态/规模", "81,370–139,441", raw.X1.nunique(), int(missing["X1"])],
    ["X2", "帖子类型（载体形式）", "名义", "发帖决策", "Photo/Status/Link/Video", raw.X2.nunique(), int(missing["X2"])],
    ["X3", "内容类别（内容主题）", "名义", "发帖决策", "1/2/3", raw.X3.nunique(), int(missing["X3"])],
    ["X4", "发帖月份", "有序/周期", "发帖决策（时机）", "1–12", raw.X4.nunique(), int(missing["X4"])],
    ["X5", "发帖星期", "有序/周期", "发帖决策（时机）", "1–7", raw.X5.nunique(), int(missing["X5"])],
    ["X6", "发帖时段（小时）", "有序/周期", "发帖决策（时机）", "0–23（样本 1–23）", raw.X6.nunique(), int(missing["X6"])],
    ["X7", "是否付费推广", "二元", "发帖决策", "0/1", raw.X7.nunique(dropna=True), int(missing["X7"])],
    ["Y1", "曝光总次数（Lifetime Post Total Reach）", "连续（计数）", "结果", "570–1,110,282", raw.Y1.nunique(), int(missing["Y1"])],
], columns=["变量", "含义", "数据类型", "因果角色", "取值范围/类别", "唯一值数", "缺失数"])
save_csv(var_dict, "表1_变量字典.csv")

# ---------- 4. 描述性统计 ----------
df["logY"] = np.log1p(df.Y1)
df["logX1"] = np.log(df.X1)
num_cols = ["X1", "X3", "X4", "X5", "X6", "X7", "Y1", "logY", "logX1"]
desc = pd.DataFrame({
    "变量": num_cols,
    "样本量": [int(df[c].notna().sum()) for c in num_cols],
    "均值": [df[c].mean() for c in num_cols],
    "标准差": [df[c].std() for c in num_cols],
    "最小值": [df[c].min() for c in num_cols],
    "P25": [df[c].quantile(.25) for c in num_cols],
    "中位数": [df[c].median() for c in num_cols],
    "P75": [df[c].quantile(.75) for c in num_cols],
    "最大值": [df[c].max() for c in num_cols],
    "偏度": [stats.skew(df[c].dropna()) for c in num_cols],
    "峰度": [stats.kurtosis(df[c].dropna()) for c in num_cols],
})
save_csv(desc.round(4), "表2_描述性统计.csv")

# ---------- 5. 共线与分布指标 ----------
month_fit = smf.ols("logX1 ~ C(X4)", data=df).fit()
within_resid = month_fit.resid
total_sd = df.logX1.std(ddof=1)
within_sd = np.sqrt(np.mean(within_resid ** 2))
corr_pearson = df.X1.corr(df.X4)
corr_spearman = df.X1.corr(df.X4, method="spearman")
unique_per_month = df.groupby("X4").X1.nunique()

metrics = pd.DataFrame([
    ["样本量", n_rows, "500 条帖子"],
    ["变量数", 8, "7 个输入 + 1 个输出"],
    ["完全重复行", dups, "按 8 个原始变量判定"],
    ["X7 缺失数", int(missing["X7"]), "仅第 499 行缺失，占 0.2%"],
    ["Y1 偏度（原始）", stats.skew(df.Y1), "右偏严重，需 log1p"],
    ["Y1 峰度（原始）", stats.kurtosis(df.Y1), "超额峰度"],
    ["Y1 最大值/中位数", df.Y1.max() / df.Y1.median(), "极端重尾"],
    ["log1p(Y1) 偏度", stats.skew(df.logY), "变换后接近对称"],
    ["log1p(Y1) 峰度", stats.kurtosis(df.logY), "变换后峰度显著下降"],
    ["log(X1) 偏度", stats.skew(df.logX1), "左偏（粉丝数持续增长）"],
    ["Pearson r(X1, X4)", corr_pearson, "粉丝规模与月份的线性相关"],
    ["Spearman ρ(X1, X4)", corr_spearman, "单调相关接近 1"],
    ["R²(logX1 ~ 月份哑变量)", month_fit.rsquared, "99.2% 的粉丝规模变异在月间"],
    ["log(X1) 总标准差", total_sd, "跨全部帖子"],
    ["log(X1) 月内标准差", within_sd, "仅 1.3%，月内几乎不变"],
    ["月内方差占比", within_sd ** 2 / total_sd ** 2, "1 - R²"],
    ["X1 唯一值数", df.X1.nunique(), "90 个不同取值，重复多"],
    ["月内 X1 唯一值中位数", unique_per_month.median(), "每月仅约 6–7 个不同粉丝数"],
    ["X1 最大值/最小值", df.X1.max() / df.X1.min(), "量级跨度有限"],
], columns=["指标", "数值", "说明"])
save_csv(metrics.round(6), "表3_共线与分布指标.csv")

# ---------- 6. 相关系数矩阵 ----------
corr_vars = ["logY", "logX1", "X3", "X4", "X5", "X6", "X7"]
corr = df[corr_vars].corr(method="spearman")
corr.index = ["logY", "logX1", "X3", "X4", "X5", "X6", "X7"]
corr.to_csv(RESULT_DIR / "相关系数.csv", encoding="utf-8-sig")

# ---------- 7. 绘图数据 ----------
plot_dist = df[["row_id", "Y1", "logY", "X2", "X3", "X7"]].copy()
plot_dist.to_csv(CACHE_DIR / "绘图数据_分布.csv", index=False, encoding="utf-8-sig")

plot_month = df[["row_id", "X1", "X4", "logX1"]].copy()
plot_month["month_mean"] = plot_month.groupby("X4").X1.transform("mean")
plot_month["within_dev"] = plot_month.X1 - plot_month.month_mean
plot_month.to_csv(CACHE_DIR / "绘图数据_月份.csv", index=False, encoding="utf-8-sig")

# 供后文复用的原始数据副本（不改原件）
raw.to_csv(CACHE_DIR / "原始数据副本.csv", index=False, encoding="utf-8-sig")

# ---------- 8. 关键数值输出 ----------
print("数据形状:", raw.shape)
print("缺失:", missing.to_dict())
print("Y1 偏度/峰度: %.2f / %.2f -> log1p: %.2f / %.2f" % (
    stats.skew(df.Y1), stats.kurtosis(df.Y1), stats.skew(df.logY), stats.kurtosis(df.logY)))
print("X1-X4 Pearson %.3f Spearman %.3f; logX1~month R2 %.4f" % (
    corr_pearson, corr_spearman, month_fit.rsquared))
print("logX1 总SD %.4f 月内SD %.4f 月内占比 %.4f" % (
    total_sd, within_sd, within_sd ** 2 / total_sd ** 2))
print("X2 分布:", raw.X2.value_counts().to_dict())
print("X7 分布:", raw.X7.value_counts(dropna=False).to_dict())
print("结果目录:", RESULT_DIR)

# ---------- 9. 实际计算检查 ----------
record_checks({
    "样本量为500且8列": (n_rows == 500 and n_cols >= 8),
    "无完全重复行": (dups == 0),
    "X7仅1个缺失": (int(missing["X7"]) == 1),
    "X1范围在文档区间": (raw.X1.min() >= 81370 and raw.X1.max() <= 139441),
    "Y1范围在文档区间": (raw.Y1.min() >= 570 and raw.Y1.max() <= 1110282),
    "X2为四类": (set(raw.X2.unique()) == {"Photo", "Status", "Link", "Video"}),
    "X3取值1到3": (set(raw.X3.unique()) == {1, 2, 3}),
    "X1与月份强共线": (corr_spearman > 0.99 and month_fit.rsquared > 0.99),
    "log变换降低偏度": (stats.skew(df.logY) < stats.skew(df.Y1)),
})
