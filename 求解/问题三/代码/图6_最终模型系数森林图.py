# -*- coding: utf-8 -*-
"""图6：M2 最终模型主效应系数森林图（四组森林 + 右侧 ×倍数 / β(95%CI) / p 数值列）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.transforms import blended_transform_factory

from _common import (CACHE_DIR, save_fig, top_legend, label_subplots_below,
                     register_data_inputs)

DATA = Path(CACHE_DIR) / "绘图数据_森林.csv"
register_data_inputs(DATA)
d = pd.read_csv(DATA, encoding="utf-8-sig")
colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]  # Nature/NPG 色板

# (数据标签, 行标签, 组名)：组内保持原结论顺序
ORDER = [("付费（X7=1）", "X7 = 1", "付费"),
         ("类型：Status", "Status", "类型"),
         ("类型：Video", "Video", "类型"),
         ("类型：Link", "Link", "类型"),
         ("主题：2", "主题 2", "主题"),
         ("主题：3", "主题 3", "主题"),
         ("时段：凌晨", "凌晨", "时段"),
         ("时段：下午晚间", "下午晚间", "时段")]
src = d.set_index("标签")
rows = [(src.loc[key], short, group) for key, short, group in ORDER]
n = len(rows)
ypos = np.arange(n)[::-1]


def f_p(p):
    return "p<0.001" if p < 1e-3 else f"p={p:.3f}"


fig, ax = plt.subplots(figsize=(11.4, 6.9))
fig.set_layout_engine("none")   # 关掉紧凑布局：右侧数值列靠固定边距排版
L, R, B, T = 0.155, 0.715, 0.115, 0.895
ax.set_position([L, B, R - L, T - B])   # nature 的占位引擎不认 subplots_adjust，直接给位置
axw = fig.get_size_inches()[0] * (R - L)
x_mult = 1.03                       # ×倍数列
x_ci = x_mult + 0.66 / axw          # β (95%CI) 列
x_p = x_ci + 1.42 / axw             # p 列
xt = blended_transform_factory(ax.transAxes, ax.transData)

# ---- 四组底纹（隔组浅灰）与分隔线
groups = []
for name in ["付费", "类型", "主题", "时段"]:
    ys = [y for y, (_, _, g) in zip(ypos, rows) if g == name]
    groups.append((name, ys))
for index, (name, ys) in enumerate(groups):
    if index % 2 == 1:
        ax.axhspan(min(ys) - 0.5, max(ys) + 0.5, facecolor="#F3F5F8",
                   edgecolor="none", linewidth=0, zorder=0)
    ax.axhline(min(ys) - 0.5, color="#CDD3DB", lw=0.8, zorder=1.5)

# ---- 表头分隔线（画到坐标轴外）
ax.plot([0.0, x_p + 0.13], [n - 0.52, n - 0.52], transform=xt,
        color="#C9CED6", lw=0.8, clip_on=False, zorder=1.5)

# ---- 0 参考线（止于表头分隔线）
ax.vlines(0, -0.62, n - 0.52, color="#333333", lw=1.0, ls=(0, (4, 3)), zorder=2)
# ---- 轻量竖向网格（不穿表头）
ax.grid(False)
ax.grid(True, axis="x", ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)
ax.axhspan(n - 0.50, n + 0.10, facecolor="white", edgecolor="none", lw=0, zorder=0.9)

# ---- 逐行：点 + 95%CI + 三列数值
for y, (row, short, group) in zip(ypos, rows):
    beta, lo, hi, p = row["系数"], row["CI下限"], row["CI上限"], row["p值"]
    sig = p < 0.05
    col = colors[0] if (sig and beta > 0) else colors[1] if sig else "#8C8C8C"
    ax.errorbar(beta, y, xerr=[[beta - lo], [hi - beta]], fmt="o", color=col,
                ecolor=col, elinewidth=1.25, capsize=3.4, capthick=0.9,
                markersize=7.4, markeredgecolor="black", markeredgewidth=0.55,
                zorder=3)
    ax.text(x_mult, y, f"×{row['倍数']:.2f}", transform=xt, ha="left",
            va="center", fontsize=9.6, color="#222222")
    ax.text(x_ci, y, f"{beta:.2f} ({lo:.2f}, {hi:.2f})", transform=xt,
            ha="left", va="center", fontsize=9.4, color="#222222")
    ax.text(x_p, y, f_p(p), transform=xt, ha="left", va="center", fontsize=9.4,
            color=col if sig else "#6E6E6E")

# ---- 列标题
for x, txt in [(x_mult, "×倍数"), (x_ci, "β (95%CI)"), (x_p, "p")]:
    ax.text(x, n - 0.45, txt, transform=xt, ha="left", va="bottom",
            fontsize=9.6, color="#4A4A4A")

# ---- 左侧竖排组名
for name, ys in groups:
    ax.text(-0.205, (min(ys) + max(ys)) / 2.0, name, transform=xt, rotation=90,
            ha="center", va="center", fontsize=10.0, color="#3A3A3A",
            fontweight="bold")

# ---- 坐标轴
ax.set_yticks(ypos)
ax.set_yticklabels([short for _, short, _ in rows], fontsize=10)
ax.set_xlim(-0.85, 2.55)
ax.set_ylim(-0.62, n - 0.02)
ax.set_xticks([0, 0.5, 1.0, 1.5, 2.0])
ax.set_xticklabels(["0", "0.5", "1.0", "1.5", "2.0"], fontsize=10)
ax.set_xlabel("系数 β（log1p 曝光尺度）", fontsize=11, labelpad=6)
ax.tick_params(axis="y", which="both", length=0, pad=7)

handles = [Line2D([], [], marker="o", ls="none", mfc=colors[0], mec="black",
                  mew=0.5, ms=7.2, label="显著为正"),
           Line2D([], [], marker="o", ls="none", mfc=colors[1], mec="black",
                  mew=0.5, ms=7.2, label="显著为负"),
           Line2D([], [], marker="o", ls="none", mfc="#8C8C8C", mec="black",
                  mew=0.5, ms=7.2, label="不显著"),
           Line2D([], [], color="#555555", lw=1.3, label="95% CI")]
top_legend(fig, [ax], handles=handles,
           labels=[h.get_label() for h in handles], ncol=4, auto_expand=False,
           prop=FontProperties(size=9.5), frameon=True,
           borderpad=0.35, bbox_to_anchor=(0.5, 0.985), subplot_top=T)

label_subplots_below(fig, [ax], ["最终模型 M2 的主效应"], fontsize=10)

save_fig(fig, "图6_最终模型系数森林图", chart_types=["forest"],
         chart_style="modelviz", chart_color_scheme="modelviz")
