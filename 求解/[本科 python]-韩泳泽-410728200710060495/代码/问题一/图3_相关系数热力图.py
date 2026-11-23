# -*- coding: utf-8 -*-
"""图3：变量 Spearman 相关矩阵（下三角气泡）与各变量对 log(曝光) 的相关方向。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.cm import ScalarMappable

from _common import (CACHE_DIR, save_fig, get_correlation_scale,
                     register_data_inputs)

DATA = Path(CACHE_DIR).parent / "结果" / "相关系数.csv"
register_data_inputs(DATA)
corr = pd.read_csv(DATA, index_col=0, encoding="utf-8-sig")
colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]  # Nature/NPG 色板
BLUE, RED = colors[0], colors[1]
GRID = dict(color="#E5E5E5", lw=0.6)

NAMES = {"logY": "log(曝光)", "logX1": "log(粉丝规模)", "X3": "主题",
         "X4": "月份", "X5": "星期", "X6": "时段", "X7": "付费"}
order = ["logY", "logX1", "X3", "X4", "X5", "X6", "X7"]
mat = corr.loc[order, order].to_numpy(dtype=float)
labels = [NAMES[k] for k in order]
n = len(order)

cmap, norm = get_correlation_scale("modelviz")
norm = TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=1.0)

fig = plt.figure(figsize=(11.4, 6.5))
gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 0.36], wspace=0.07,
                      left=0.135, right=0.972, top=0.935, bottom=0.235)
ax = fig.add_subplot(gs[0])
axb = fig.add_subplot(gs[1], sharey=ax)

# ---- 左：下三角气泡矩阵 ----------------------------------------------------------
ax.set_xlim(-0.55, n - 1 + 0.55)
ax.set_ylim(n - 1 + 0.55, -0.55)          # 第 0 行在顶部
for k in np.arange(-0.5, n, 1.0):
    ax.axhline(k, color=GRID["color"], lw=GRID["lw"], zorder=0)
    ax.axvline(k, color=GRID["color"], lw=GRID["lw"], zorder=0)

def fmt(r, diag=False):
    """对角写 1.00；近似完全共线的格子保留 3 位，避免与对角线混成两个 1.00。"""
    if diag:
        return "1.00"
    if abs(r) >= 0.99:
        return f"{r:.3f}"
    if abs(r) < 0.01:
        return f"{r:.3f}"
    return f"{r:.2f}"


for i in range(n):
    for j in range(i + 1):
        r = mat[i, j]
        size = 40 + 1500 * abs(r)
        ax.scatter([j], [i], s=size, color=cmap(norm(r)), edgecolors="white",
                   linewidths=0.7, zorder=3)
        txt_col = "white" if abs(r) >= 0.5 else "#222222"
        ax.text(j, i, fmt(r, diag=(i == j)), ha="center", va="center", fontsize=8.2,
                color=txt_col, fontweight="bold" if abs(r) >= 0.5 else "normal",
                zorder=4)

# 共线核心：log(粉丝规模) × 月份 的格子加细黑描边，避免被对角线 1.00 的大球淹没
i_core, j_core = order.index("X4"), order.index("logX1")
r_core = mat[i_core, j_core]
ax.scatter([j_core], [i_core], s=1.30 * (40 + 1500 * abs(r_core)),
           facecolors="none", edgecolors="black", linewidths=0.9, zorder=5)

ax.set_xticks(range(n))
ax.set_xticklabels(labels, rotation=45, ha="right", rotation_mode="anchor", fontsize=9.5)
ax.set_yticks(range(n))
ax.set_yticklabels(labels, fontsize=9.5)
ax.grid(False)          # 矩阵的格子线由上面的 axhline/axvline 画，关掉刻度网格免重影
ax.text(0.975, 0.982, "气泡面积 ∝ |r|\n黑圈：共线核心",
        transform=ax.transAxes, ha="right", va="top", fontsize=8.5, color="#666666")

sm = ScalarMappable(norm=norm, cmap=cmap)
sm.set_array([])
# 交给约束布局排：挂在下三角矩阵下方，自动给 45° 刻度标签让位（固定 fig.add_axes 会压字）
cbar = fig.colorbar(sm, ax=ax, location="bottom", orientation="horizontal",
                    fraction=0.045, pad=0.04, aspect=40, shrink=0.96)
cbar.set_label("Spearman 相关系数", fontsize=9.5)
cbar.ax.tick_params(labelsize=8.5)
cbar.outline.set_linewidth(0.5)

# ---- 右：与 log(曝光) 的相关系数条形 --------------------------------------------
ylines = np.arange(1, n)
vals = mat[1:n, 0]
axb.barh(ylines, vals, height=0.56,
         color=[BLUE if v >= 0 else RED for v in vals],
         alpha=0.88, edgecolor="black", linewidth=0.45, zorder=3)
axb.axvline(0, color="black", lw=0.9, zorder=4)
for y, v in zip(ylines, vals):
    lab = f"{v:+.3f}" if abs(v) < 0.01 else f"{v:+.2f}"
    axb.text(v + (0.008 if v >= 0 else -0.008), y, lab,
             ha="left" if v >= 0 else "right", va="center", fontsize=8.5,
             color="#222222", zorder=5)
axb.set_xlim(-0.245, 0.245)
axb.set_ylim(n - 1 + 0.55, -0.55)
axb.set_xticks([-0.2, -0.1, 0.0, 0.1, 0.2])
axb.set_xticklabels(["-0.2", "-0.1", "0", "0.1", "0.2"])
axb.set_xlabel("与 log(曝光) 的相关系数", fontsize=9.5)
# sharey 下 set_yticks([]) 会连左格的刻度标签一起清掉，改为只隐藏本格的刻度线
axb.tick_params(axis="y", left=False, labelleft=False)
axb.grid(True, axis="x", ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)

# nature 存图收尾会给多面板自动补 (a)(b)；本图左右两格靠图注指认，标记为已排布。
ax.text(0.0, 1.0, "(a)", transform=ax.transAxes, visible=False)

save_fig(fig, "图3_相关系数热力图", chart_types=["heatmap"],
         chart_style="modelviz", chart_color_scheme="modelviz")
