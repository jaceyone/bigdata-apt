# -*- coding: utf-8 -*-
"""图16：六种设定 × 七个主效应的系数稳健性矩阵（nature 风格）。

数据：问题四/临时产物/稳健性系数矩阵.csv（问题四/代码/表17_稳健性系数矩阵.py 生成，
      付费系数与 表16 逐位对账）。
版式：行 = 7 个主效应（付费 / 类型 / 主题 / 时段，左侧竖排分组色条 + 组间白线）；
      列 = 6 种设定（底部两行折行标签）；格内 = 系数（3 位）+ 显著星号；
      颜色 = 行内归一化系数（红正 / 浅绿负 / 白≈0）；顶部水平色标；
      右侧一列「全设定方向一致？」。
画布按 plot_style 的 6.3 英寸（16cm 版心）档；图下不留说明性长句。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401,E402  —— 必须在 _common 之前导入，接管全局 nature 样式
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from _common import CACHE_DIR, register_data_inputs, save_fig  # noqa: E402

DATA = Path(CACHE_DIR) / "稳健性系数矩阵.csv"
register_data_inputs(DATA)
d = pd.read_csv(DATA, encoding="utf-8-sig")

SPECS = ["M1 全模型", "M2 月份固定效应", "M3 仅logX1", "M4 logX1+线性月份",
         "Huber 稳健回归", "Gamma GLM（log 链接）"]
COLS = ["M1\n全模型", "M2 月份\n固定效应", "M3\n仅 logX1",
        "M4 logX1\n+线性月份", "Huber\n稳健回归", "Gamma GLM\n(log 链接)"]
# 分组色条：颜色刻意避开红/绿（红绿只表示系数正负），只承担"结构"信息
GROUPS = [("付费", ["付费"], "#3C5488"),
          ("类型", ["类型：Video", "类型：Status", "类型：Link"], "#8491B4"),
          ("主题", ["主题 2", "主题 3"], "#8C6BB1"),
          ("时段", ["时段：凌晨"], "#A8A8A8")]
ROWS = [r for _, members, _ in GROUPS for r in members]
NROW, NCOL = len(ROWS), len(SPECS)

piv = d.pivot(index="参数", columns="设定", values="系数").loc[ROWS, SPECS]
piv_star = d.pivot(index="参数", columns="设定", values="显著性").loc[ROWS, SPECS]
V = piv.values.astype(float)
rowmax = np.nanmax(np.abs(V), axis=1, keepdims=True)
rowmax[rowmax == 0] = 1.0
Z = np.nan_to_num(V / rowmax, nan=0.0)          # 行内归一化：每行除以该行 |系数| 最大值

# ── 画布：6.3×4.3 英寸（16cm 版心档），位置按英寸折算成 figure 分数 ──
FIG_W, FIG_H = 6.3, 4.3
X_L, X_W = 1.30 / FIG_W, 4.06 / FIG_W            # 矩阵
Y_B, Y_H = 0.115, 0.745
BAR_X, BAR_W = 0.15 / FIG_W, 0.13 / FIG_W        # 左侧分组色条
PANEL_X, PANEL_W = 5.42 / FIG_W, 0.73 / FIG_W    # 右侧方向一致列
TOP = Y_B + Y_H
ROW_H = Y_H / NROW

CMAP = LinearSegmentedColormap.from_list(
    "robust_red_green", [(0.0, "#00A087"), (0.5, "#FFFFFF"), (1.0, "#E64B35")], N=512)
NORM = Normalize(vmin=-1, vmax=1)

fig = plt.figure(figsize=(FIG_W, FIG_H))
ax = fig.add_axes([X_L, Y_B, X_W, Y_H])
ax.set_xlim(0, NCOL)
ax.set_ylim(NROW, 0)


def cell_rgb(z, star):
    """单元格填色：颜色重量必须与证据强度同向。
    ns     → 与白色按 0.45:0.55 混合（叠 55% 白），明显淡于显著格；
    ***    → 在行内归一化色上再深 8%，最强证据最重；
    ** / * → 保持原饱和。
    """
    base = np.array(CMAP(NORM(z))[:3], dtype=float)
    if star in ("", "ns"):
        return base * 0.45 + 0.55
    if star == "***":
        return np.clip(1.0 - (1.0 - base) * 1.08, 0.0, 1.0)
    return base


# 逐格铺色（白细格线 0.8）+ 格内系数 3 位与星号
for i in range(NROW):
    for j in range(NCOL):
        v = V[i, j]
        if not np.isfinite(v):
            continue
        star = "" if pd.isna(piv_star.values[i, j]) else str(piv_star.values[i, j])
        rgb = cell_rgb(Z[i, j], star)
        ax.add_patch(Rectangle((j, i), 1, 1, facecolor=tuple(rgb), edgecolor="white",
                               linewidth=0.8, zorder=2))
        lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        ink = "white" if lum < 0.55 else "#1A1A1A"
        ax.text(j + 0.5, i + 0.5, f"{v:.3f}" + (" ns" if star == "ns" else star),
                ha="center", va="center", fontsize=9.0, color=ink, zorder=5)

# 组间白线（比格线粗，切分组）
y = 0
for k, (_, members, _) in enumerate(GROUPS):
    y += len(members)
    if k < len(GROUPS) - 1:
        ax.axhline(y, color="white", lw=2.6, zorder=4)

for side in ("top", "right", "left", "bottom"):   # 外框一律不加粗边
    ax.spines[side].set_visible(False)
ax.set_yticks(np.arange(NROW) + 0.5)
ax.set_yticklabels(ROWS, fontsize=9.2, color="#1A1A1A")
ax.set_xticks(np.arange(NCOL) + 0.5)
ax.set_xticklabels(COLS, fontsize=9.0, linespacing=1.4, color="#1A1A1A")
ax.tick_params(axis="y", length=0, pad=7)
ax.tick_params(axis="x", length=0, pad=6)
ax.grid(False)
for lbl in ax.get_xticklabels():
    if lbl.get_text().startswith("M2"):         # 最终模型
        lbl.set_fontweight("bold")
        lbl.set_color("#3C5488")
    elif lbl.get_text().startswith("Gamma"):    # 非 OLS 对照
        lbl.set_color("#5A5F66")

# 非 OLS 列：稍浅的虚线描边
ax.add_patch(Rectangle((NCOL - 1, 0), 1, NROW, fill=False, edgecolor="#B3BAC1",
                       linewidth=1.1, linestyle=(0, (2.8, 2.0)), zorder=6, clip_on=False))


def fig_x(x_in):
    """英寸 → figure 分数，便于把辅助图元钉在与矩阵行严格对齐的位置。"""
    return x_in / FIG_W


def fig_y(y_in_from_bottom):
    return y_in_from_bottom / FIG_H


BOT_IN = Y_B * FIG_H
ROW_IN = ROW_H * FIG_H


def row_center(i):
    """第 i 行的竖直中心（figure 分数，行序自上而下）。"""
    return fig_y(BOT_IN + (NROW - i - 0.5) * ROW_IN)


# ── 左侧竖排分组色条（figure 级图元，与矩阵行严格对齐）──
y0 = 0
for name, members, color in GROUPS:
    h = len(members)
    bottom = fig_y(BOT_IN + (NROW - y0 - h) * ROW_IN)      # 该组最底一行的下沿
    hh = h * ROW_H
    fig.add_artist(Rectangle((BAR_X, bottom), BAR_W, hh, transform=fig.transFigure,
                             facecolor=color, edgecolor="none", zorder=2))
    fig.text(BAR_X - 0.0090, bottom + hh / 2, name, rotation=90,
             ha="center", va="center", fontsize=9.0, color="#1A1A1A")
    y0 += h

# ── 右侧：全设定方向一致？（✓ 用折线画，绕开字体缺字形）──
x_mid = PANEL_X + PANEL_W / 2


consistent = []
for i in range(NROW):
    vals = V[i, np.isfinite(V[i])]
    ok = bool(np.all(vals > 0) or np.all(vals < 0))
    consistent.append(ok)
    yc = row_center(i)
    if ok:
        pts = [(-0.032, 0.019), (-0.008, -0.005), (0.046, 0.049)]
    else:
        pts = [(-0.034, 0.000), (0.034, 0.000)]
    for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
        fig.add_artist(Line2D([fig_x(x_mid * FIG_W + xa), fig_x(x_mid * FIG_W + xb)],
                              [yc + fig_y(ya), yc + fig_y(yb)],
                              transform=fig.transFigure, color="#1A1A1A" if ok else "#A6A6A6",
                              lw=1.5 if ok else 1.3, solid_capstyle="round", zorder=3))

fig.add_artist(Line2D([PANEL_X - 0.011, PANEL_X - 0.011], [Y_B, TOP],
                      transform=fig.transFigure, color="#E0E0E0", lw=0.8, zorder=1))
fig.text(x_mid, TOP + 0.012, "全设定方向\n一致？", ha="center", va="bottom",
         fontsize=9.0, color="#1A1A1A", linespacing=1.45)

# ── 顶部水平色标 ──
cax = fig.add_axes([X_L, 0.932, 0.250, 0.017])
cax.set_label("<colorbar>")          # 收尾体检据此把色标轴排除在"子图面板"之外
cb = fig.colorbar(ScalarMappable(norm=NORM, cmap=CMAP), cax=cax, orientation="horizontal")
cb.set_ticks([-1, -0.5, 0, 0.5, 1])
cb.set_ticklabels(["-1", "-0.5", "0", "0.5", "1"])
cb.ax.tick_params(direction="out", length=2.4, width=0.6, pad=2.4, labelsize=9.0,
                  colors="#1A1A1A")
cb.outline.set_linewidth(0.5)
cb.outline.set_edgecolor("#5A5F66")
for s in ("top", "bottom", "left", "right"):
    cb.ax.spines[s].set_linewidth(0.5)
    cb.ax.spines[s].set_color("#5A5F66")
fig.text(X_L, 0.958, "行内归一化系数", ha="left", va="bottom",
         fontsize=9.4, color="#1A1A1A")
fig.text(X_L + 0.272, 0.910, "ns 已淡化", ha="left", va="center",
         fontsize=9.0, color="#5A5F66")

save_fig(fig, "图16_系数稳健性矩阵", chart_types=["heatmap"],
         chart_style="nature", chart_color_scheme="nature")

print("行内归一化（行=主效应，列=设定）：")
print(pd.DataFrame(np.round(Z, 3), index=ROWS, columns=SPECS).to_string())
print("\n全设定方向一致：", dict(zip(ROWS, consistent)))
