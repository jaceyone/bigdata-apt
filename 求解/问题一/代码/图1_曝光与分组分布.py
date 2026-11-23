# -*- coding: utf-8 -*-
"""图1：曝光总次数 Y1 的重尾分布，以及付费/类型/主题三组差异（雨云图）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

from _common import (CACHE_DIR, save_fig, label_subplots_below,
                     register_data_inputs)

DATA = Path(CACHE_DIR) / "绘图数据_分布.csv"
register_data_inputs(DATA)
raw = pd.read_csv(DATA, encoding="utf-8-sig")          # 全部 500 条帖子
df = raw.dropna(subset=["X7"]).copy()                  # 分组统计用 X7 已知的 499 条
df["paid"] = df["X7"].astype(int).map({0: "自然", 1: "付费"})
colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]  # Nature/NPG 色板
GRAY = "#8C8C8C"
XT = (1e3, 1e4, 1e5, 1e6)
XT_LABEL = [f"{v:,.0f}" for v in XT]


def lightgrid(ax):
    """nature 已接管边框/刻度；这里只补一条轻量横网格。"""
    ax.grid(True, axis="y", ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)


def rain(ax, values, xc, color, rng, label, half=0.08, viol=0.52):
    """单组雨云：左侧抖动散点 + 窄箱线 + 右侧半小提琴；中位数标在小提琴右缘。"""
    v = np.asarray(values, dtype=float)
    ax.scatter(xc - 0.16 + rng.uniform(-0.13, 0.13, len(v)), v,
               s=6, color=color, alpha=0.45, edgecolors="none", zorder=3)
    bp = ax.boxplot([v], positions=[xc], widths=2 * half, patch_artist=True,
                    medianprops=dict(color="black", lw=1.15),
                    whiskerprops=dict(color="black", lw=0.8),
                    capprops=dict(color="black", lw=0.8, gapcolor="none"),
                    flierprops=dict(marker="", linestyle="none"),
                    zorder=4)
    for box in bp["boxes"]:
        box.set_facecolor(color)
        box.set_alpha(0.72)
        box.set_edgecolor("black")
        box.set_linewidth(0.55)
    med = float(np.median(v))
    x_right = xc + half + 0.03
    if len(v) >= 15:
        lg = np.log10(v)
        kde = gaussian_kde(lg, bw_method=0.35)
        grid = np.linspace(lg.min() - 0.015, lg.max() + 0.015, 260)
        dens = kde(grid)
        dens = dens / dens.max() * viol
        ax.fill_betweenx(10 ** grid, x_right, x_right + dens,
                         facecolor=color, alpha=0.38, edgecolor=color,
                         lw=0.7, zorder=2)
        width_at_med = float(np.interp(np.log10(med), grid, dens))
        ax.text(x_right + width_at_med + 0.035, med, f"{med:,.0f}",
                ha="left", va="center", fontsize=8.5, color="#333333", zorder=6)
    else:
        # n 太小不成密度：只保留散点，中位数照标，参考性写在刻度标签里
        ax.text(x_right + 0.04, med, f"{med:,.0f}", ha="left", va="center",
                fontsize=8.5, color=GRAY, zorder=6)
    return med


fig, axes = plt.subplots(2, 2, figsize=(11.2, 8.6))

# ---- (a) Y1 原始分布：对数横轴 + 均值/中位数竖线 ---------------------------------
ax = axes[0, 0]
y_all = raw["Y1"].to_numpy(dtype=float)
avg, med = y_all.mean(), float(np.median(y_all))
skew = float(((y_all - avg) ** 3).mean() / ((y_all - avg) ** 2).mean() ** 1.5)
bins = np.logspace(np.log10(500), np.log10(1.2e6), 38)
ax.hist(y_all, bins=bins, color=colors[0], alpha=0.86, edgecolor="black",
        linewidth=0.45, zorder=2)
ax.set_xscale("log")
ax.set_xlim(480, 1.32e6)
ax.set_ylim(0, 88)
ax.set_xticks(XT)
ax.set_xticklabels(XT_LABEL)
ax.axvline(avg, color=colors[2], lw=1.5, ls="--", label="均值", zorder=5)
ax.axvline(med, color=colors[1], lw=1.5, ls="-.", label="中位数", zorder=5)
ax.set_xlabel("曝光总次数（对数刻度）", fontsize=10.5)
ax.set_ylabel("帖子数", fontsize=10.5)
ax.text(0.032, 0.962,
        f"均值 {avg:,.0f}\n中位数 {med:,.0f}\n偏度 {skew:.2f}",
        transform=ax.transAxes, va="top", ha="left", fontsize=9,
        linespacing=1.6, zorder=7)
ax.legend(loc="upper right", fontsize=8.5,
          handlelength=1.8, borderaxespad=0.6)
lightgrid(ax)

# ---- (b) 付费 / 自然 -----------------------------------------------------------
ax = axes[0, 1]
rng = np.random.default_rng(20261122)
med_b = rain(ax, df.loc[df.paid == "自然", "Y1"].values, 0, colors[0], rng, "自然")
med_b2 = rain(ax, df.loc[df.paid == "付费", "Y1"].values, 1.7, colors[1], rng, "付费")
ax.set_yscale("log")
ax.set_yticks(XT)
ax.set_yticklabels(XT_LABEL)
ax.set_ylim(430, 1.55e6)
ax.set_xlim(-0.85, 2.72)
ax.set_xticks([0, 1.7])
ax.set_xticklabels([f"自然\nn={int((df.paid == '自然').sum())}",
                    f"付费\nn={int((df.paid == '付费').sum())}"], fontsize=9.5)
ax.set_ylabel("曝光总次数（对数刻度）", fontsize=10.5)
ax.text(0.5, 0.965, f"中位数提升 {med_b2 / med_b - 1:+.1%}",
        transform=ax.transAxes, ha="center", va="top", fontsize=9,
        color=colors[1], zorder=7)
lightgrid(ax)

# ---- (c) 四种帖子类型：Video 仅 7 条，只画散点 ----------------------------------
ax = axes[1, 0]
order = ["Photo", "Status", "Link", "Video"]
palette = [colors[0], colors[2], colors[3], GRAY]
for i, (name, col) in enumerate(zip(order, palette)):
    vals = df.loc[df.X2 == name, "Y1"].values
    rain(ax, vals, i * 1.7, col, rng, name)
ax.set_yscale("log")
ax.set_yticks(XT)
ax.set_yticklabels(XT_LABEL)
ax.set_ylim(430, 1.55e6)
ax.set_xlim(-0.85, 3 * 1.7 + 1.35)
ax.set_xticks([i * 1.7 for i in range(4)])
ax.set_xticklabels([f"Photo\nn={(df.X2 == 'Photo').sum()}",
                    f"Status\nn={(df.X2 == 'Status').sum()}",
                    f"Link\nn={(df.X2 == 'Link').sum()}",
                    f"Video\nn=7"], fontsize=9.5)
ax.set_ylabel("曝光总次数（对数刻度）", fontsize=10.5)
lightgrid(ax)

# ---- (d) 三类内容主题 ------------------------------------------------------------
ax = axes[1, 1]
theme_pal = [colors[0], colors[2], colors[3]]
for i, (g, col) in enumerate(zip([1, 2, 3], theme_pal)):
    rain(ax, df.loc[df.X3 == g, "Y1"].values, i * 1.7, col, rng, f"主题{g}")
ax.set_yscale("log")
ax.set_yticks(XT)
ax.set_yticklabels(XT_LABEL)
ax.set_ylim(430, 1.55e6)
ax.set_xlim(-0.85, 2 * 1.7 + 1.35)
ax.set_xticks([0, 1.7, 3.4])
ax.set_xticklabels([f"主题{g}\nn={int((df.X3 == g).sum())}" for g in [1, 2, 3]], fontsize=9.5)
ax.set_ylabel("曝光总次数（对数刻度）", fontsize=10.5)
lightgrid(ax)

fig.subplots_adjust(hspace=0.42, wspace=0.30)
# nature 存图收尾会给多面板自动补 (a)(b)(c)(d)；本图已用下方 a/b/c/d 题注标号，
# 这里按「作者已排布」标记一次，避免角落再出现一套重复编号。
axes[0, 0].text(0.0, 1.0, "(a)", transform=axes[0, 0].transAxes, visible=False)
label_subplots_below(fig, axes, [
    "a 曝光总次数分布（n=500）",
    "b 自然与付费",
    "c 四种帖子类型",
    "d 三类内容主题",
], fontsize=9.5)
save_fig(fig, "图1_曝光与分组分布", chart_types=["boxplot", "histogram"],
         chart_style="modelviz", chart_color_scheme="modelviz")
