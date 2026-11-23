# -*- coding: utf-8 -*-
"""图10：七组变量的 Shapley R² 贡献与总方差构成（横向双联：条形 + 瀑布）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Patch

from _common import (CACHE_DIR, save_fig, top_legend, label_subplots_below,
                     register_data_inputs)

DATA = Path(CACHE_DIR) / "Shapley.csv"
register_data_inputs(DATA)
d = pd.read_csv(DATA, encoding="utf-8-sig")
colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]  # Nature/NPG 色板

DECISION = {"发帖类型 X2", "内容主题 X3", "星期 X5", "时段 X6", "付费 X7"}
C_DEC, C_SCALE, C_UNEXP = colors[0], colors[1], "#BFBFBF"

groups = d[~d["变量组"].str.contains("合计|未解释")].copy()
explained = float(d.loc[d["变量组"].str.contains("合计"), "占总方差"].sum())
unexplained = float(d.loc[d["变量组"].str.contains("未解释"), "占总方差"].iloc[0])


def place_panels(fig, axes, ncols, box, wspace=0.22, hspace=0.30, width_ratios=None):
    """按 L/R/B/T 直接摆面板：nature 的占位布局引擎不认 subplots_adjust。"""
    axes = np.asarray(axes, dtype=object).ravel()
    left, right, bottom, top = box
    nrows = len(axes) // ncols
    ratios = np.asarray(width_ratios or [1.0] * ncols, dtype=float)
    w_avg = (right - left) / (ncols + (ncols - 1) * wspace)
    widths = w_avg * ratios / ratios.mean()
    gap = w_avg * wspace
    h = (top - bottom) / (nrows + (nrows - 1) * hspace)
    for k, ax in enumerate(axes):
        r, c = divmod(k, ncols)
        x0 = left + widths[:c].sum() + c * gap
        ax.set_position([x0, top - (r + 1) * h - r * h * hspace, widths[c], h])


fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.8),
                         gridspec_kw={"width_ratios": [1.0, 1.05]})
fig.set_layout_engine("none")   # 关掉紧凑布局：边距与斜排刻度按固定值摆
place_panels(fig, axes, 2, (0.075, 0.965, 0.175, 0.885), wspace=0.22,
             width_ratios=[1.0, 1.05])

# ---------------- (a) 七个变量组的 Shapley R²（降序横向条形） ----------------
ax = axes[0]
ga = groups.sort_values("Shapley_R²", ascending=True).reset_index(drop=True)
ypos = np.arange(len(ga))
bcol = [C_DEC if g in DECISION else C_SCALE for g in ga["变量组"]]
ax.barh(ypos, ga["Shapley_R²"], height=0.58, color=bcol,
        edgecolor="black", linewidth=0.6, zorder=3)
xmax = float(ga["Shapley_R²"].max())
for y, r, share in zip(ypos, ga["Shapley_R²"], ga["占已解释方差"]):
    ax.text(r + xmax * 0.024, y, f"{r:.4f}（{share * 100:.1f}%）",
            va="center", ha="left", fontsize=9.2)
ax.set_yticks(ypos)
ax.set_yticklabels(ga["变量组"], fontsize=10)
ax.set_xlim(0, xmax * 1.46)
ax.set_ylim(-0.62, len(ga) - 0.38)
ax.set_xlabel("Shapley R² 贡献（log1p 曝光方差）", fontsize=11, labelpad=5)
ax.xaxis.set_major_locator(plt.MaxNLocator(5))
ax.grid(False)
ax.grid(True, axis="x", ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)

# ---------------- (b) 瀑布：逐组累加到已解释 20.7% ----------------
ax = axes[1]
gb = groups.sort_values("Shapley_R²", ascending=False).reset_index(drop=True)
vals = gb["占总方差"].to_numpy(dtype=float) * 100.0
cums = np.cumsum(vals)
expl_pct = explained * 100.0
unexp_pct = unexplained * 100.0
n = len(vals)

for i, (v, c) in enumerate(zip(vals, cums)):
    col = C_DEC if gb.loc[i, "变量组"] in DECISION else C_SCALE
    ax.bar(i, v, bottom=c - v, width=0.62, color=col,
           edgecolor="black", linewidth=0.6, zorder=3)
    ax.text(i, c + 1.1, f"{c:.1f}", ha="center", va="bottom", fontsize=9.0)
    if i < n - 1:
        ax.plot([i + 0.31, i + 1 - 0.31], [c, c], color="#8C8C8C", lw=0.7,
                ls=(0, (3, 2)), zorder=2)

# 末段：未解释方差
ax.bar(n, unexp_pct, bottom=expl_pct, width=0.62, color=C_UNEXP,
       edgecolor="black", linewidth=0.6, zorder=3)
ax.plot([n - 1 + 0.31, n - 0.31], [cums[-1], cums[-1]], color="#8C8C8C",
        lw=0.7, ls=(0, (3, 2)), zorder=2)
ax.text(n, 100.0 + 1.1, "100.0", ha="center", va="bottom", fontsize=9.2)
ax.text(n, expl_pct + unexp_pct / 2.0, f"未解释 {unexp_pct:.1f}%", rotation=90,
        ha="center", va="center", fontsize=9.0)

# 已解释水平的贯穿虚线
ax.axhline(expl_pct, color="#A6A6A6", lw=0.8, ls=(0, (5, 2.5)), zorder=1)
ax.text(-0.12, expl_pct + 1.4, f"已解释 {expl_pct:.1f}%", ha="left", va="bottom",
        fontsize=9.0, color="#555555")

ax.set_xticks(np.arange(n + 1))
ax.set_xticklabels(list(gb["变量组"]) + ["未解释方差"], fontsize=9.0,
                   rotation=30, ha="right", rotation_mode="anchor")
ax.set_xlim(-0.62, n + 0.62)
ax.set_ylim(0, 106)
ax.set_yticks([0, 20, 40, 60, 80, 100])
ax.set_xlabel("变量组（按 Shapley R² 降序累加）", fontsize=11, labelpad=5)
ax.set_ylabel("占总方差比例（%）", fontsize=11, labelpad=5)
ax.grid(False)
ax.grid(True, axis="y", ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)

handles = [Patch(facecolor=C_DEC, edgecolor="black", linewidth=0.6, label="发帖决策（5 组）"),
           Patch(facecolor=C_SCALE, edgecolor="black", linewidth=0.6, label="账号规模与时间（2 组）"),
           Patch(facecolor=C_UNEXP, edgecolor="black", linewidth=0.6, label="未解释方差")]
top_legend(fig, axes=[axes[0]], handles=handles,
           labels=[h.get_label() for h in handles], ncol=3,
           prop=FontProperties(size=9.5), frameon=True, borderpad=0.35,
           bbox_to_anchor=(0.5, 0.965))
# 本图已在下方手写 a/b 题注：占位标号让 nature 的 tidy 不要再自动加一遍
for _ax, _tag in zip(axes, "ab"):
    _ax.text(0, 0, f"({_tag})", visible=False)
caps = label_subplots_below(fig, axes, [
    "a 七组变量的 Shapley R²",
    "b 逐组累加至已解释 20.7%",
], fontsize=10)
# 两个面板题注对齐到同一行（b 的旋转刻度把它压得更低）
cap_y = min(c.get_position()[1] for c in caps)
for cap in caps:
    cap.set_y(cap_y)
save_fig(fig, "图10_方差贡献Shapley", chart_types=["bar", "waterfall"],
         chart_style="modelviz", chart_color_scheme="modelviz")
