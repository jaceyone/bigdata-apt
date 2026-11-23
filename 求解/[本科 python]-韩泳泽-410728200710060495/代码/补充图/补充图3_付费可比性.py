# -*- coding: utf-8 -*-
"""补充图3：付费组与自然组的可比性核查（nature 版式）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from scipy.stats import gaussian_kde

DATA = ROOT / "清洗数据.csv"
OUT = Path(__file__).resolve().parent
df = pd.read_csv(DATA)
df["paid"] = df["X7"].astype(int)
colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]  # Nature/NPG 色板


def groom(ax, axis="y"):
    """单向浅灰虚线网格。"""
    ax.grid(True, axis=axis, ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)


def half_violin(ax, values, center, side, color, grid, width=0.40):
    """在 center 处只画一侧的密度曲线（半分小提琴），返回归一化半宽。"""
    dens = gaussian_kde(values)(grid)
    half = dens / dens.max() * width
    ax.fill_betweenx(grid, center, center + side * half, facecolor=color,
                     alpha=0.38, edgecolor="none", zorder=2)
    ax.plot(center + side * half, grid, color=color, lw=0.9, zorder=2.1)
    return half


fig = plt.figure(figsize=(12.6, 9.7))
fig.set_layout_engine("none")          # 版式由下方 gridspec 的边距显式给定
_gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], width_ratios=[1, 1],
                       left=0.085, right=0.868, top=0.945, bottom=0.115,
                       hspace=0.30, wspace=0.60)
axes = np.array([[fig.add_subplot(_gs[r, c]) for c in range(2)] for r in range(2)])
rng = np.random.default_rng(20261122)

# ── (a) 粉丝规模对数：半分小提琴 + 箱线 + 散点 + SMD ──
ax = axes[0, 0]
groups = [df.loc[df.paid == 0, "logX1"].values, df.loc[df.paid == 1, "logX1"].values]
grid = np.linspace(11.13, 12.02, 400)
half = [half_violin(ax, groups[0], 0.0, -1, colors[0], grid),
        half_violin(ax, groups[1], 1.0, +1, colors[1], grid)]
for (center, vals, color, side), hw in zip(
        [(0.0, groups[0], colors[0], 1), (1.0, groups[1], colors[1], -1)], half):
    local = np.interp(vals, grid, hw)
    ax.scatter(center + side * rng.uniform(0.08, 0.92, len(vals)) * local,
               vals, s=2.1, color=color, alpha=0.22, edgecolors="none", zorder=3)
bp = ax.boxplot(groups, positions=[0, 1], widths=0.11, patch_artist=True,
                showfliers=True, medianprops=dict(color="black", lw=1.1, zorder=6),
                whiskerprops=dict(color="black", lw=0.7, zorder=6),
                capprops=dict(color="black", lw=0.7, zorder=6),
                flierprops=dict(marker="o", ms=2.2, mfc="none", mec="#555555",
                                mew=0.5, alpha=0.6, zorder=6),
                boxprops=dict(facecolor="white", edgecolor="black", lw=0.6,
                              zorder=5))
a, b = groups
smd = (a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
ax.text(0.035, 0.955, f"SMD={abs(smd):.3f}", transform=ax.transAxes,
        ha="left", va="top", fontsize=9.2, color="#222222",
        bbox=dict(boxstyle="round,pad=0.28", facecolor="#F4F6F9",
                  edgecolor="#DCE1E8", linewidth=0.7))
ax.set_xticks([0, 1])
ax.set_xticklabels([f"自然\n(n={len(a)})", f"付费\n(n={len(b)})"])
ax.set_xlim(-0.78, 1.78)
ax.set_ylim(11.10, 12.05)          # 上下各留余量，密度峰不贴框
ax.set_ylabel("粉丝规模对数 $\\log X_1$", fontsize=10.5)
ax.set_xlabel("帖子分组", fontsize=10.5)
groom(ax, "y")

# ── (b) 逐月付费占比与 Wilson 95% 区间 ──
ax = axes[0, 1]
m = df.groupby("month_c").agg(n=("Y1", "size"), k=("paid", "sum"))
m["p"] = m.k / m.n
z = 1.959963984540054
den = 1 + z * z / m.n
centre = (m.p + z * z / (2 * m.n)) / den
half_ci = z * np.sqrt(m.p * (1 - m.p) / m.n + z * z / (4 * m.n ** 2)) / den
lo, hi = centre - half_ci, centre + half_ci
bars = ax.bar(m.index, m.p * 100, width=0.64, color=colors[1], alpha=0.68,
              edgecolor="#8C2B20", linewidth=0.5, label="各月付费占比", zorder=3)
ax.errorbar(m.index, m.p * 100, yerr=[(m.p - lo) * 100, (hi - m.p) * 100],
            fmt="none", ecolor="#333333", elinewidth=0.9, capsize=3.0,
            capthick=0.8, zorder=4)
for x, val, top in zip(m.index, m.p * 100, hi * 100):
    ax.text(x, top + 1.6, f"{val:.1f}", ha="center", va="bottom",
            fontsize=7.8, color="#333333", zorder=5)
overall = ax.axhline(df.paid.mean() * 100, color=colors[2], ls=(0, (5, 2.2)),
                     lw=1.1, zorder=5)
ax.text(1.015, df.paid.mean() * 100 / 64, f"整体 {df.paid.mean()*100:.1f}%",
        transform=ax.transAxes, ha="left", va="center", fontsize=8.8,
        color="#00695C", clip_on=False, zorder=6)
ax.set_xlabel("月份", fontsize=10.5)
ax.set_ylabel("付费占比（%）", fontsize=10.5)
ax.set_xticks(range(1, 13))
ax.set_xlim(0.35, 12.65)
ax.set_ylim(0, 64)
groom(ax, "y")

# ── (c) 类型构成：100% 水平堆叠条 ──
ax = axes[1, 0]
order = ["Photo", "Status", "Link", "Video"]
ct = pd.crosstab(df.X2c, df.paid).reindex(order).fillna(0)
share = ct.div(ct.sum(axis=0), axis=1).T
seg_colors = [colors[0], colors[1], colors[3], colors[4]]
txt_colors = ["white", "white", "black", "black"]
rows = [("付费", 1), ("自然", 0)]
for label, y in rows:
    key = 1 if label == "付费" else 0
    left = 0.0
    for j, tp in enumerate(order):
        w = share.loc[key, tp]
        ax.barh(y, w, left=left, height=0.46, color=seg_colors[j],
                edgecolor="white", linewidth=1.0, zorder=3)
        if w >= 0.06:
            ax.text(left + w / 2, y, f"{w*100:.1f}%", ha="center", va="center",
                    fontsize=8.4 if w >= 0.2 else 7.2,
                    color=txt_colors[j], zorder=4)
        left += w
    ax.text(0.985, y + 0.34,
            f"Link {share.loc[key, 'Link']*100:.1f}% · Video {share.loc[key, 'Video']*100:.1f}%",
            ha="right", va="center", fontsize=7.8, color="#444444", zorder=4)
handles = [Patch(facecolor=seg_colors[j], edgecolor="white", label=order[j])
           for j in range(4)]
ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.035, 0.5),
          frameon=True, edgecolor="#333333", fontsize=8.6, handlelength=1.1,
          handleheight=0.9, labelspacing=0.85, borderaxespad=0.0)
ax.set_yticks([1, 0])
ax.set_yticklabels([f"付费\n(n={int(ct[1].sum())})",
                    f"自然\n(n={int(ct[0].sum())})"])
ax.set_xlim(0, 1.0)
ax.set_ylim(-0.55, 1.55)
ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_xticklabels(["0", "25", "50", "75", "100%"])
ax.set_xlabel("类型构成（组内占比）", fontsize=10.5)
groom(ax, "x")

# ── (d) 主题构成：100% 水平堆叠条 ──
ax = axes[1, 1]
order3 = [1, 2, 3]
labels3 = ["主题 1", "主题 2", "主题 3"]
ct = pd.crosstab(df.X3c, df.paid).reindex(order3).fillna(0)
share = ct.div(ct.sum(axis=0), axis=1).T
seg_colors = [colors[0], colors[2], colors[3]]
txt_colors = ["white", "white", "black"]
for label, y in rows:
    left = 0.0
    for j, th in enumerate(order3):
        w = share.loc[1 if label == "付费" else 0, th]
        ax.barh(y, w, left=left, height=0.46, color=seg_colors[j],
                edgecolor="white", linewidth=1.0, zorder=3)
        if w >= 0.06:
            ax.text(left + w / 2, y, f"{w*100:.1f}%", ha="center", va="center",
                    fontsize=8.0, color=txt_colors[j], zorder=4)
        left += w
handles = [Patch(facecolor=seg_colors[j], edgecolor="white", label=labels3[j])
           for j in range(3)]
ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.035, 0.5),
          frameon=True, edgecolor="#333333", fontsize=8.6, handlelength=1.1,
          handleheight=0.9, labelspacing=0.85, borderaxespad=0.0)
ax.set_yticks([1, 0])
ax.set_yticklabels([f"付费\n(n={int(ct[1].sum())})", f"自然\n(n={int(ct[0].sum())})"])
ax.set_xlim(0, 1.0)
ax.set_ylim(-0.55, 1.55)
ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_xticklabels(["0", "25", "50", "75", "100%"])
ax.set_xlabel("主题构成（组内占比）", fontsize=10.5)
groom(ax, "x")


def cap_below(ax_, text, gap=0.012):
    """题注挂在该坐标轴正下方；写成该轴的文字，样式层才认这一格已经标过号。"""
    fig.canvas.draw()
    tight = ax_.get_tightbbox(fig.canvas.get_renderer()).transformed(
        fig.transFigure.inverted())
    pos = ax_.get_position()
    ax_.text((pos.x0 + pos.x1) / 2.0, tight.y0 - gap, text, transform=fig.transFigure,
             ha="center", va="top", fontsize=10, fontweight="bold")


def tag_panel(ax_, tag):
    """写一个不可见的 (a) 标号：样式层据此认为该格已标号，不再自动补号。"""
    ax_.text(0.0, 1.02, f"({tag})", transform=ax_.transAxes, alpha=0.0)


for (r, c), tag in {**{(0, 0): "a", (0, 1): "b"}, **{(1, 0): "c", (1, 1): "d"}}.items():
    tag_panel(axes[r, c], tag)

cap_below(axes[0, 0], "a 粉丝规模分布")
cap_below(axes[0, 1], "b 逐月付费占比")
cap_below(axes[1, 0], "c 类型构成")
cap_below(axes[1, 1], "d 主题构成")

# 同一行的两格题注对齐到同一条基线
fig.canvas.draw()
for i in range(2):
    caps = [t for t in axes[i, 0].texts + axes[i, 1].texts if t.get_fontweight() == "bold"]
    if len(caps) == 2:
        y = min(c.get_position()[1] for c in caps)
        for c in caps:
            c.set_position((c.get_position()[0], y))

fig.savefig(OUT / "补充图3_付费可比性.png", dpi=400, bbox_inches="tight", facecolor="white")
print("saved", OUT / "补充图3_付费可比性.png")
