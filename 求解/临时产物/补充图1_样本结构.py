# -*- coding: utf-8 -*-
"""补充图1：类型构成、主题分布与粉丝—曝光联合分布。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
from matplotlib.transforms import blended_transform_factory
from scipy.stats import gaussian_kde, pearsonr

DATA = ROOT / "清洗数据.csv"
OUT = Path(__file__).resolve().parent
df = pd.read_csv(DATA)
df["paid"] = df["X7"].astype(int)
colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]  # Nature/NPG 色板

fig = plt.figure(figsize=(12.8, 10.6))
fig.set_layout_engine("none")          # 版式由下方 gridspec 的边距显式给定
gs = fig.add_gridspec(2, 2, height_ratios=[0.92, 1.38],
                      left=0.082, right=0.972, top=0.925, bottom=0.098,
                      hspace=0.34, wspace=0.28)

# ── (a) 背靠背条形图：类型 × 付费 + 右侧付费占比列 ──
ax = fig.add_subplot(gs[0, 0])
order = ["Photo", "Status", "Link", "Video"]
ypos = np.arange(len(order))[::-1]
n0 = np.array([((df.X2c == g) & (df.paid == 0)).sum() for g in order])
n1 = np.array([((df.X2c == g) & (df.paid == 1)).sum() for g in order])
ax.barh(ypos, -n0, height=0.58, color=colors[0], edgecolor="black",
        linewidth=0.5, label="自然", zorder=2)
ax.barh(ypos, n1, height=0.58, color=colors[1], edgecolor="black",
        linewidth=0.5, label="付费", zorder=2)
ax.axvline(0, color="black", lw=0.9, zorder=3)
blend = blended_transform_factory(ax.transAxes, ax.transData)
for y, a, b in zip(ypos, n0, n1):
    off = 8 if max(a, b) >= 20 else 30  # 极小条形（Video）标签外移，避免贴住零轴
    ax.text(-a - off, y, f"{a}", ha="right", va="center", fontsize=8.5, color=colors[0])
    ax.text(b + off, y, f"{b}", ha="left", va="center", fontsize=8.5, color=colors[1])
    ax.text(0.985, y, f"{b / (a + b) * 100:.1f}%", transform=blend, ha="right",
            va="center", fontsize=8.5, color="#333333")
ax.text(0.985, 1.035, "付费占比", transform=ax.transAxes, ha="right", va="bottom",
        fontsize=8.3, color="#555555")
ax.set_xlim(-380, 272)
ax.set_xticks([-300, -200, -100, 0, 100, 200])
ax.set_xticklabels(["300", "200", "100", "0", "100", "200"])
ax.set_xticks([], minor=True)
ax.set_yticks(ypos)
ax.set_yticklabels(order, fontsize=9.5)
ax.set_ylim(-0.62, 3.62)
ax.set_xlabel("帖子数（左：自然，右：付费）", fontsize=10.5)
ax.set_ylabel("帖子类型", fontsize=10.5)
ax.legend(loc="lower left", bbox_to_anchor=(0.008, 0.02), frameon=True,
          edgecolor="#333333", fontsize=9.0)

# ── (b) 半分小提琴：主题 × 对数曝光 ──
ax = fig.add_subplot(gs[0, 1])
themes = [1, 2, 3]
tcolors = [colors[0], colors[3], colors[2]]
for i, th in enumerate(themes):
    y = df.loc[df.X3c == th, "logY"].values
    ys = np.linspace(y.min() - 0.08, y.max() + 0.08, 260)
    dens = gaussian_kde(y)(ys)
    dens = dens / dens.max() * 0.38
    ax.fill_betweenx(ys, i, i + dens, color=tcolors[i], alpha=0.62, lw=0, zorder=2)
    ax.fill_betweenx(ys, i, i - dens, color=tcolors[i], alpha=0.28, lw=0, zorder=2)
    ax.plot(i + dens, ys, color=tcolors[i], lw=0.9, zorder=3)
    ax.plot(i - dens, ys, color=tcolors[i], lw=0.9, zorder=3)
    bp = ax.boxplot([y], positions=[i], widths=0.11, patch_artist=True,
                    showfliers=False,
                    medianprops=dict(color="black", lw=1.2),
                    whiskerprops=dict(color="black", lw=0.8),
                    capprops=dict(color="black", lw=0.8),
                    boxprops=dict(edgecolor="black", lw=0.6, facecolor="white"),
                    flierprops=dict(marker=""))
    for group in bp.values():
        for artist in group:
            artist.set_zorder(6)
    ax.text(i, 5.98, f"n={len(y)}｜中位 {np.median(y):.2f}", ha="center", va="top",
            fontsize=8.3, color="#333333")
ax.set_xticks([0, 1, 2])
ax.set_xticklabels(["主题1", "主题2", "主题3"], fontsize=9.5)
ax.set_xlim(-0.62, 2.62)
ax.set_ylim(5.45, 14.45)
ax.set_xlabel("内容主题", fontsize=10.5)
ax.set_ylabel("对数曝光 $\\log(1+Y_1)$", fontsize=10.5)

# ── (c) 联合分布 + 95% 置信椭圆 + 边缘密度 ──
sub = gs[1, :].subgridspec(2, 2, width_ratios=[4.2, 1], height_ratios=[1, 4.2],
                           hspace=0.04, wspace=0.04)
axj = fig.add_subplot(sub[1, 0])
axt = fig.add_subplot(sub[0, 0], sharex=axj)
axr = fig.add_subplot(sub[1, 1], sharey=axj)


def add_ellipse(ax_, xv, yv, color, level=0.95):
    """95% 置信椭圆：np.cov 主轴 + 马氏距离的样本分位半径（只描边，不遮散点）。"""
    cov = np.cov(xv, yv)
    vals, vecs = np.linalg.eigh(cov)
    order_ = vals.argsort()[::-1]
    vals, vecs = vals[order_], vecs[:, order_]
    angle = np.degrees(np.arctan2(vecs[1, 0], vecs[0, 0]))
    dev = np.vstack([xv - xv.mean(), yv - yv.mean()])
    d2 = np.einsum("ij,ij->j", dev, np.linalg.solve(cov, dev))
    radius = np.sqrt(np.quantile(d2, level))  # 恰好圈住 95% 样本
    width, height = 2 * radius * np.sqrt(vals[0]), 2 * radius * np.sqrt(vals[1])
    ax_.add_patch(Ellipse((xv.mean(), yv.mean()), width, height, angle=angle,
                          facecolor="none", edgecolor=color,
                          lw=1.15, ls=(0, (5, 3)), zorder=4))


for flag, color, label in [(0, colors[0], "自然"), (1, colors[1], "付费")]:
    part = df[df.paid == flag]
    axj.scatter(part.logX1, part.logY, s=12, color=color, alpha=0.55,
                edgecolors="none", label=f"{label}（n={len(part)}）", zorder=2)
    add_ellipse(axj, part.logX1.values, part.logY.values, color)

r, p = pearsonr(df.logX1.values, df.logY.values)
axj.text(0.025, 0.972,
         f"Pearson r={r:.3f}\np={p:.3f}（n={len(df)}）",
         transform=axj.transAxes, ha="left", va="top", fontsize=9.2,
         linespacing=1.5, zorder=7,
         bbox=dict(boxstyle="round,pad=0.30", facecolor="white",
                   edgecolor="none", alpha=0.90))
axj.set_xlabel("粉丝规模对数 $\\log X_1$", fontsize=10.5)
axj.set_ylabel("对数曝光 $\\log(1+Y_1)$", fontsize=10.5)
axj.set_xlim(11.24, 11.99)
axj.set_ylim(6.05, 14.25)

handles, labels = axj.get_legend_handles_labels()
handles.append(Line2D([], [], color="#8C8C8C", ls="--", lw=1.2, label="95% 置信椭圆"))
axj.legend(handles=handles, labels=labels, loc="upper right", frameon=True,
           edgecolor="#333333", framealpha=0.96, fontsize=8.8, markerscale=1.7)

bins_x = np.linspace(df.logX1.min(), df.logX1.max(), 24)
bins_y = np.linspace(df.logY.min(), df.logY.max(), 26)
for flag, color in [(0, colors[0]), (1, colors[1])]:
    part = df[df.paid == flag]
    axt.hist(part.logX1, bins=bins_x, density=True, histtype="stepfilled",
             alpha=0.40, color=color, edgecolor="black", linewidth=0.35)
    axr.hist(part.logY, bins=bins_y, density=True, orientation="horizontal",
             histtype="stepfilled", alpha=0.40, color=color,
             edgecolor="black", linewidth=0.35)
for a_ in (axt, axr):                      # 边缘密度：留框线但不画刻度
    a_.tick_params(which="both", bottom=False, top=False, left=False, right=False,
                   labelbottom=False, labelleft=False)
axt.set_ylabel("密度", fontsize=9.2, labelpad=3)
axr.set_xlabel("密度", fontsize=9.2, labelpad=3)

ax.tick_params(axis="y", length=0)
ax.grid(True, ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)
axj.grid(True, ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)

# 子图标号（写成各坐标轴的文字，样式层才认这一格已经标过号）


def cap_below(ax_, text, x=None, gap=0.012):
    fig.canvas.draw()
    tight = ax_.get_tightbbox(fig.canvas.get_renderer()).transformed(
        fig.transFigure.inverted())
    pos = ax_.get_position()
    ax_.text((pos.x0 + pos.x1) / 2 if x is None else x, tight.y0 - gap, text,
             transform=fig.transFigure, ha="center", va="top", fontsize=10,
             fontweight="bold")


def tag_panel(ax_, tag):
    """写一个不可见的 (a) 标号：样式层据此认为该格已标号，不再自动补号。"""
    ax_.text(0.0, 1.02, f"({tag})", transform=ax_.transAxes, alpha=0.0)


ax_a, ax_b = fig.axes[0], fig.axes[1]
for a_, tag in ((ax_a, "a"), (ax_b, "b"), (axj, "c")):
    tag_panel(a_, tag)
cap_below(ax_a, "a 类型与付费构成")
cap_below(ax_b, "b 主题曝光分布")
jb, rb = axj.get_position(), axr.get_position()
cap_below(axj, "c 粉丝规模—曝光联合分布",
          x=(jb.x0 + rb.x1) / 2, gap=0.014)

fig.savefig(OUT / "补充图1_样本结构.png", dpi=400, bbox_inches="tight", facecolor="white")
print("saved", OUT / "补充图1_样本结构.png")
