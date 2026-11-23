# -*- coding: utf-8 -*-
"""图2：粉丝规模 log(X1) 与月份 X4 的单调共线关系（核心陷阱）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats as st

from _common import CACHE_DIR, save_fig, register_data_inputs

DATA = Path(CACHE_DIR) / "绘图数据_月份.csv"
register_data_inputs(DATA)
df = pd.read_csv(DATA, encoding="utf-8-sig")
colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]  # Nature/NPG 色板
BLUE, RED = colors[0], colors[1]

rng = np.random.default_rng(20261122)
jit = rng.uniform(-0.22, 0.22, len(df))

# ---- 统计量（全部由本 CSV 现算） --------------------------------------------------
px, py = df.X1.values, df.X4.values
pearson = float(np.corrcoef(px, py)[0, 1])
spearman = float(st.spearmanr(px, py).statistic)
grp = df.groupby("X4")["logX1"]
agg = grp.agg(["mean", "std", "count"])
sem = agg["std"] / np.sqrt(agg["count"])
tcrit = st.t.ppf(0.975, agg["count"] - 1)
ci = tcrit * sem
sse = float(((df.logX1 - grp.transform("mean")) ** 2).sum())
sst = float(((df.logX1 - df.logX1.mean()) ** 2).sum())
r2 = 1.0 - sse / sst
sd_within = np.sqrt(sse / len(df))

fig = plt.figure(figsize=(9.8, 7.8))
gs = fig.add_gridspec(2, 1, height_ratios=[3.5, 1.0], hspace=0.08,
                      left=0.095, right=0.975, top=0.975, bottom=0.105)
ax = fig.add_subplot(gs[0])
axb = fig.add_subplot(gs[1], sharex=ax)

# ---- 主面板：散点 + 月均值折线 + 95% 置信带 --------------------------------------
ax.scatter(df.X4 + jit, df.logX1, s=7, color=BLUE, alpha=0.40,
           edgecolors="none", label="单条帖子", zorder=2)
ax.fill_between(agg.index, agg["mean"] - ci, agg["mean"] + ci,
                color=RED, alpha=0.18, lw=0, zorder=3, label="月均值 95% 置信带")
ax.plot(agg.index, agg["mean"], color=RED, lw=1.6, marker="o", markersize=5.2,
        markeredgecolor="black", markeredgewidth=0.5, zorder=5, label="月均值")

# 圈注 |月内偏差| 最大的 3 个帖子（同一月份同一粉丝数只留一条，避免重叠）
cand = (df.assign(ad=df.within_dev.abs())
          .drop_duplicates(subset=["X4", "X1"])
          .nlargest(3, "ad"))
offsets = {0: (-108, 14), 1: (58, 34), 2: (46, 2)}
cand = cand.sort_values("within_dev", ascending=False)
for k, (idx, row) in enumerate(cand.iterrows()):
    pos = df.index.get_indexer([idx])[0]
    hx, hy = row.X4 + jit[pos], row.logX1
    ax.plot([hx], [hy], "o", ms=9.5, mfc="none", mec="#333333", mew=0.9, zorder=6)
    ax.annotate(f"{int(row.X4)}月 {row.within_dev:+,.0f}", xy=(hx, hy),
                xytext=offsets.get(k, (40, 20)), textcoords="offset points",
                fontsize=8.5, color="#333333", ha="center", va="center", zorder=7,
                arrowprops=dict(arrowstyle="-", lw=0.6, color="#777777",
                                shrinkA=2, shrinkB=5))

ax.set_ylabel("粉丝规模 log(X1)（自然对数）", fontsize=10.5)
ax.set_xticks(range(1, 13))
ax.set_xlim(0.35, 12.65)
ax.set_ylim(11.25, 11.93)
ax.set_yticks([11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9])
ax.tick_params(labelbottom=False)
ax.text(0.018, 0.952,
        f"Pearson r = {pearson:.3f}   Spearman ρ = {spearman:.3f}\n"
        f"log(X1) ~ 月份哑变量  R² = {r2:.3f}\n"
        f"月内 log(X1) 标准差 = {sd_within:.3f}（{sd_within:.1%}）",
        transform=ax.transAxes, va="top", ha="left", fontsize=9, linespacing=1.6,
        zorder=8, bbox=dict(boxstyle="round,pad=0.32", facecolor="white",
                            edgecolor="#D5D9DE", linewidth=0.6, alpha=0.94))
ax.legend(loc="lower right", fontsize=8.5, labelspacing=0.45,
          handlelength=2.0, borderaxespad=0.8, markerscale=1.4)

# ---- 下挂小条：月内偏差 -----------------------------------------------------------
axb.axhspan(-1800, 1800, color=RED, alpha=0.10, lw=0, zorder=1)
axb.axhline(0, color="black", lw=0.8, zorder=3)
for y in (-1800, 1800):
    axb.axhline(y, color=RED, lw=0.9, ls="--", zorder=3)
axb.scatter(df.X4 + jit, df.within_dev, s=7, color=BLUE, alpha=0.45,
            edgecolors="none", zorder=2)
axb.set_ylim(-6200, 7200)
axb.set_yticks([-6000, -4000, -2000, 0, 2000, 4000, 6000])
axb.set_yticklabels([f"{v:,}" for v in [-6000, -4000, -2000, 0, 2000, 4000, 6000]])
axb.set_ylabel("月内偏差", fontsize=10.5)
axb.set_xlabel("发帖月份 X4", fontsize=10.5)
axb.set_xticks(range(1, 13))
axb.text(12.55, 4500, "月内波动 ±1,800", ha="right", va="center",
         fontsize=8.5, color=RED)
axb.text(0.012, 0.94, "偏差 = X1 − 该月均值", transform=axb.transAxes,
         ha="left", va="top", fontsize=8.5, color="#777777")
axb.text(0.012, 0.06,
         f"中位 |偏差| = {df.within_dev.abs().median():,.0f} 次"
         f"（约占均值 {df.within_dev.abs().median() / df.X1.mean():.1%}）",
         transform=axb.transAxes, ha="left", va="bottom", fontsize=8.5,
         color="#333333")

for a in (ax, axb):
    a.grid(True, axis="y", ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)

# nature 存图收尾会给多面板自动补 (a)(b)；本图下挂条是主图的残差带，不是独立面板，
# 这里按「作者已排布」标记一次，避免自动编号把残差带错标成 (b)。
ax.text(0.0, 1.0, "(a)", transform=ax.transAxes, visible=False)

save_fig(fig, "图2_粉丝规模与月份共线", chart_types=["scatter", "line"],
         chart_style="modelviz", chart_color_scheme="modelviz")
