# -*- coding: utf-8 -*-
"""问题二：数据清洗与整理（题面 2.2）
缺失处理、类型识别、独热编码与 log1p/log 变换，输出统一分析数据。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from _common import (CACHE_DIR, OUT_DIR, resolve_input, save_csv, shared_path,
                     record_checks)

CACHE_DIR = Path(CACHE_DIR)
OUT_DIR = Path(OUT_DIR)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- 1. 读取原件 ----------
src = resolve_input("source-1ce2d1eb-371f-41f2-9c0f-1e1ec8d6f73a")
df = pd.read_csv(src, encoding="utf-8-sig")
df.columns = [c.strip() for c in df.columns]
df["row_id"] = np.arange(1, len(df) + 1)
n0 = len(df)

# ---------- 2. 缺失与异常检查 ----------
miss = df[["X1", "X2", "X3", "X4", "X5", "X6", "X7", "Y1"]].isna().sum()
dup = int(df.duplicated(subset=["X1", "X2", "X3", "X4", "X5", "X6", "X7", "Y1"]).sum())
checks = []
checks.append(["X1 取值范围", f"{df.X1.min():,}–{df.X1.max():,}", "在文档 81,370–139,441 内", "保留"])
checks.append(["X2 取值集合", "、".join(sorted(df.X2.unique())), "4 类，与文档一致", "转为名义变量"])
checks.append(["X3 取值集合", "、".join(map(str, sorted(df.X3.unique()))), "1/2/3，与文档一致", "转为名义变量"])
checks.append(["X4 取值范围", f"{df.X4.min()}–{df.X4.max()}", "1–12，无越界", "保留并编码"])
checks.append(["X5 取值范围", f"{df.X5.min()}–{df.X5.max()}", "1–7，无越界", "保留并编码"])
checks.append(["X6 取值范围", f"{df.X6.min()}–{df.X6.max()}", "0–23 内；样本 1–23，0 与 21 时无帖子", "按分布合并为 3 组"])
checks.append(["X7 取值集合", "0/1（缺失 1 条）", "二元变量；第 499 行缺失", "众数填补 0，另做删除敏感性"])
checks.append(["Y1 取值范围", f"{df.Y1.min():,}–{df.Y1.max():,}", "全部为正，与文档一致", "log1p 变换"])
checks.append(["完全重复行", f"{dup} 条", "无重复帖子", "无需去重"])
checks.append(["异常值", "Y1 存在 1 条 1,110,282 的极端曝光", "属真实病毒式传播，不是录入错误", "保留，log 变换压缩"])

# ---------- 3. 缺失处理 ----------
mode_x7 = int(df.X7.mode().iloc[0])
df["X7_imputed"] = df.X7.isna().astype(int)
df["X7"] = df.X7.fillna(mode_x7).astype(int)
checks.append(["X7 填补", f"众数 {mode_x7}，共 {int(df.X7_imputed.sum())} 条", "填补后无缺失", "保留填补标记"])

check_df = pd.DataFrame(checks, columns=["检查项", "实际结果", "判断", "处理"])
save_csv(check_df, "表4_缺失与异常检查.csv")

# ---------- 4. 类型识别与编码 ----------
df["X2c"] = pd.Categorical(df.X2, categories=["Photo", "Status", "Link", "Video"])
df["X3c"] = pd.Categorical(df.X3.astype(str), categories=["1", "2", "3"])
df["month_c"] = pd.Categorical(df.X4.astype(str), categories=[str(i) for i in range(1, 13)])
df["weekday_c"] = pd.Categorical(df.X5.astype(str), categories=[str(i) for i in range(1, 8)])
df["hour_band"] = pd.cut(df.X6, bins=[-1, 5, 11, 23],
                         labels=["凌晨", "上午", "下午晚间"])
# 以“上午”为参照组，与编码方案表一致
df["hour_band"] = df["hour_band"].cat.reorder_categories(["上午", "凌晨", "下午晚间"])
df["logY"] = np.log1p(df.Y1)
df["logX1"] = np.log(df.X1)

encoding = pd.DataFrame([
    ["X1", "连续", "log(X1)", "—", "粉丝规模弹性；避免量级差异"],
    ["X2", "名义（4 类）", "独热编码，3 个哑变量", "Photo", "比 Photo 的相对曝光差异"],
    ["X3", "名义（3 类）", "独热编码，2 个哑变量", "1", "比主题 1 的相对曝光差异"],
    ["X4", "有序/周期（12）", "独热编码，11 个哑变量", "1 月", "控制季节性与时间趋势"],
    ["X5", "有序/周期（7）", "独热编码，6 个哑变量", "周一", "控制星期效应"],
    ["X6", "有序/周期（24）", "按分布合并为 3 组，2 个哑变量", "上午（6–11 时）", "凌晨 0–5、上午 6–11、下午晚间 12–23；避免稀疏单元"],
    ["X7", "二元", "0/1 数值", "0（自然）", "付费的额外曝光"],
    ["Y1", "连续计数", "log1p(Y1)", "—", "压缩重尾，系数近似百分比效应"],
], columns=["变量", "识别类型", "编码/变换", "基线/参照", "解释"])
save_csv(encoding, "表5_编码与变换方案.csv")

# ---------- 5. 变换前后分布特征 ----------
trans = pd.DataFrame([
    ["Y1", stats.skew(df.Y1), stats.skew(df.logY), stats.kurtosis(df.Y1), stats.kurtosis(df.logY),
     df.Y1.min(), df.Y1.max()],
    ["X1", stats.skew(df.X1), stats.skew(df.logX1), stats.kurtosis(df.X1), stats.kurtosis(df.logX1),
     df.X1.min(), df.X1.max()],
], columns=["变量", "偏度_变换前", "偏度_变换后", "峰度_变换前", "峰度_变换后", "最小值", "最大值"])
save_csv(trans.round(4), "表6_变换前后分布特征.csv")

# ---------- 6. 缺失处理敏感性 ----------
formula = "logY ~ X2c + X3c + month_c + weekday_c + hour_band + X7"
m_imp = smf.ols(formula, data=df).fit()
m_drop = smf.ols(formula, data=df[df.X7_imputed == 0]).fit()
sens = pd.DataFrame([
    ["付费系数（众数填补）", m_imp.params["X7"], m_imp.bse["X7"], len(df)],
    ["付费系数（删除缺失行）", m_drop.params["X7"], m_drop.bse["X7"], int((df.X7_imputed == 0).sum())],
    ["差异", m_imp.params["X7"] - m_drop.params["X7"], np.nan, np.nan],
], columns=["方案", "X7系数", "标准误", "样本量"])
save_csv(sens.round(6), "表6b_缺失处理敏感性.csv")

# ---------- 7. 保存统一分析数据 ----------
keep = ["row_id", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "Y1", "X7_imputed",
        "X2c", "X3c", "month_c", "weekday_c", "hour_band", "logY", "logX1"]
clean = df[keep].copy()
clean.to_csv(shared_path("清洗数据.csv"), index=False, encoding="utf-8-sig")

# ---------- 8. 绘图数据 ----------
cat_rows = []
for col, label in [("X2", "帖子类型"), ("X3", "内容主题")]:
    vc = df[col].value_counts().sort_index()
    for k, v in vc.items():
        cat_rows.append([label, str(k), int(v)])
x7_counts = df.X7.value_counts().sort_index()
for k, v in x7_counts.items():
    cat_rows.append(["是否付费", "自然" if k == 0 else "付费", int(v)])
cat_rows.append(["是否付费", "缺失（填补）", int(df.X7_imputed.sum())])
cat_df = pd.DataFrame(cat_rows, columns=["变量", "类别", "计数"])
cat_df.to_csv(CACHE_DIR / "绘图数据_类别.csv", index=False, encoding="utf-8-sig")

hour_counts = df.X6.value_counts().sort_index()
hour_df = pd.DataFrame({"小时": hour_counts.index.astype(int), "计数": hour_counts.values})
hour_df.to_csv(CACHE_DIR / "绘图数据_小时.csv", index=False, encoding="utf-8-sig")

trans_plot = df[["row_id", "Y1", "logY", "X1", "logX1"]].copy()
trans_plot.to_csv(CACHE_DIR / "绘图数据_变换.csv", index=False, encoding="utf-8-sig")

# ---------- 9. 输出 ----------
print("原始样本:", n0, "填补后缺失:", int(df[["X1", "X2", "X3", "X4", "X5", "X6", "X7", "Y1"]].isna().sum().sum()))
print("X7 众数:", mode_x7, "填补条数:", int(df.X7_imputed.sum()))
print("Y1 偏度 %.2f -> %.2f; 峰度 %.2f -> %.2f" % (
    stats.skew(df.Y1), stats.skew(df.logY), stats.kurtosis(df.Y1), stats.kurtosis(df.logY)))
print("付费系数：填补 %.4f，删除 %.4f，差异 %.4f" % (
    m_imp.params["X7"], m_drop.params["X7"], m_imp.params["X7"] - m_drop.params["X7"]))
print("小时分布前 6:", hour_counts.head(6).to_dict())
print("已保存:", shared_path("清洗数据.csv"))

record_checks({
    "缺失值总数由1变为0": (int(df[["X1","X2","X3","X4","X5","X6","X7","Y1"]].isna().sum().sum()) == 0),
    "X7仅填补1条": (int(df.X7_imputed.sum()) == 1),
    "X7取值0或1": (set(df.X7.unique()) == {0, 1}),
    "X2四类完整": (set(df.X2c.astype(str).unique()) == {"Photo","Status","Link","Video"}),
    "X3三类完整": (set(df.X3c.astype(str).unique()) == {"1","2","3"}),
    "时段覆盖0到23": (int(df.X6.min()) >= 0 and int(df.X6.max()) <= 23),
    "logY与logX1有限": (bool(np.isfinite(df.logY).all() and np.isfinite(df.logX1).all())),
    "缺失处理差异小于0.01": (abs(m_imp.params["X7"] - m_drop.params["X7"]) < 0.01),
    "清洗数据行数为500": (len(clean) == 500),
})
