# -*- coding: utf-8 -*-
"""补充图2：发帖量、付费占比与曝光的时间结构（nature 版式）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import t as tdist

DATA = ROOT / "清洗数据.csv"
OUT = Path(__file__).resolve().parent
df = pd.read_csv(DATA)
colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]  # Nature/NPG 色板


def groom(ax, axis="y"):
    """单向浅灰虚线网格。"""
    ax.grid(True, axis=axis, ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)


fig = plt.figure(figsize=(12.4, 9.6))
fig.set_layout_engine("none")          # 版式由下方 gridspec 的边距显式给定
_gs = fig.add_gridspec(2, 2, left=0.072, right=0.938, top=0.918, bottom=0.105,
                       hspace=0.52, wspace=0.34)
axes = np.array([[fig.add_subplot(_gs[r, c]) for c in range(2)] for r in range(2)])

# ── (a) 逐月发帖量与付费占比 ──
ax = axes[0, 0]
m = df.groupby("month_c").agg(n=("Y1", "size"), paid=("X7", "sum"))
m["share"] = m.paid / m.n
bars = ax.bar(m.index, m.n, width=0.64, color=colors[0], alpha=0.62,
              edgecolor="#2F4A75", linewidth=0.5, label="月度帖子数", zorder=3)
for x, n in zip(m.index, m.n):
    ax.text(x, n + 1.4, f"{int(n)}", ha="center", va="bottom",
            fontsize=8.4, color="#3A3A3A", zorder=5)
ax.set_xlabel("月份", fontsize=10.5)
ax.set_ylabel("帖子数", fontsize=10.5)
ax.set_xticks(range(1, 13))
ax.set_ylim(0, 74)
ax.set_xlim(0.35, 12.65)

ax2 = ax_a2 = ax.twinx()
line, = ax2.plot(m.index, m.share * 100, color=colors[1], marker="o", ms=4.6,
                 lw=1.5, label="月度付费占比（右轴）",
                 markeredgecolor="white", markeredgewidth=0.8, zorder=6)
overall = ax2.axhline(df.X7.mean() * 100, color=colors[2], ls=(0, (5, 2.2)),
                      lw=1.1, label="整体付费占比 27.8%", zorder=4)
ax2.set_ylabel("付费占比（%）", fontsize=10.5)
ax2.set_ylim(0, 68)
ax2.spines["left"].set_visible(False)
ax2.spines["top"].set_visible(False)
ax2.patch.set_visible(False)
ax2.grid(False)
ax2.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)
ax2.tick_params(axis="y", which="both", left=False, right=True, labelright=True)
ax.text(0.02, 0.945, f"最高 4 月 {m.share.max() * 100:.1f}%\n最低 1 月 {m.share.min() * 100:.1f}%",
        transform=ax.transAxes, ha="left", va="top", fontsize=9.2,
        color="#444444", linespacing=1.5)
groom(ax, "y")

# ── (b) 逐月平均对数曝光与 95% 置信带 ──
ax = axes[0, 1]
g = df.groupby("month_c").logY.agg(["mean", "std", "count"])
se = g["std"] / np.sqrt(g["count"])
crit = tdist.ppf(0.975, g["count"] - 1)
lo, hi = g["mean"] - crit * se, g["mean"] + crit * se
ax.fill_between(g.index, lo, hi, color=colors[0], alpha=0.18, linewidth=0)
ax.plot(g.index, g["mean"], color=colors[0], marker="o", ms=5.0, lw=1.6,
        markeredgecolor="white", markeredgewidth=0.8, zorder=4)
ax.axhline(df.logY.mean(), color="#8C8C8C", ls=(0, (5, 2.2)), lw=1.0, zorder=2)
ax.text(1.012, (df.logY.mean() - 8.15) / (10.90 - 8.15),
        f"全样本 {df.logY.mean():.2f}", transform=ax.transAxes, ha="left",
        va="center", fontsize=8.8, color="#666666", clip_on=False)
ax.annotate("2 月 10.13（最高）", xy=(2.1, 10.24), xytext=(3.35, 10.62),
            ha="left", va="center", fontsize=9.2, color="#2B2B2B",
            arrowprops=dict(arrowstyle="-", lw=0.7, color="#666666",
                            shrinkA=2, shrinkB=3))
ax.annotate("10 月 8.83（最低）", xy=(10, 8.80), xytext=(9.6, 8.28),
            ha="center", va="bottom", fontsize=9.2, color="#2B2B2B",
            arrowprops=dict(arrowstyle="-", lw=0.7, color="#666666",
                            shrinkA=2, shrinkB=3))
ax.set_xlabel("月份", fontsize=10.5)
ax.set_ylabel("平均对数曝光", fontsize=10.5)
ax.set_xticks(range(1, 13))
ax.set_xlim(0.35, 12.65)
ax.set_ylim(8.15, 10.90)
groom(ax, "y")

# ── (c) 星期均值与 95% 置信区间 ──
ax = axes[1, 0]
w = df.groupby("weekday_c").logY.agg(["mean", "std", "count"])
se = w["std"] / np.sqrt(w["count"])
crit = tdist.ppf(0.975, w["count"] - 1)
ax.axhline(df.logY.mean(), color="#8C8C8C", ls=(0, (5, 2.2)), lw=1.0, zorder=1)
ax.errorbar(w.index, w["mean"], yerr=crit * se, fmt="o-", color=colors[2],
            ms=5.4, lw=1.5, capsize=3.2, elinewidth=1.0,
            markeredgecolor="white", markeredgewidth=0.8, zorder=4)
ax.text(4, 10.045, "周四 9.74（最高）", ha="center", va="bottom",
        fontsize=9.2, color="#2B2B2B")
ax.text(7.35, 8.715, "周日 9.06（最低）", ha="right", va="top",
        fontsize=9.2, color="#2B2B2B")
ax.set_xlabel("星期", fontsize=10.5)
ax.set_ylabel("平均对数曝光", fontsize=10.5)
ax.set_xticks(range(1, 8))
ax.set_xticklabels([f"周{'一二三四五六日'[i-1]}\n({int(n)})"
                    for i, n in zip(w.index, w["count"])])
ax.set_xlim(0.6, 7.4)
ax.set_ylim(8.55, 10.20)
groom(ax, "y")

# ── (d) 合并时段后的均值与 95% 置信区间 ──
ax = axes[1, 1]
bands = ["凌晨", "上午", "下午晚间"]
h = df.groupby("hour_band").logY.agg(["mean", "std", "count"]).reindex(bands)
se = h["std"] / np.sqrt(h["count"])
crit = tdist.ppf(0.975, h["count"] - 1)
ax.axhline(df.logY.mean(), color="#8C8C8C", ls=(0, (5, 2.2)), lw=1.0, zorder=1)
ax.errorbar(range(3), h["mean"], yerr=crit * se, fmt="o", color=colors[3],
            ms=6.4, capsize=4.0, elinewidth=1.1, markeredgecolor="white",
            markeredgewidth=0.8, zorder=4)
for x, (mu, n) in enumerate(zip(h["mean"], h["count"])):
    ax.text(x, mu + 0.055, f"{mu:.2f}", ha="center", va="bottom",
            fontsize=9.4, color="#2B2B2B")
ax.set_xticks(range(3))
ax.set_xticklabels([f"{b}\n({int(n)})" for b, n in zip(bands, h["count"])])
ax.set_xlabel("时段（合并后）", fontsize=10.5)
ax.set_ylabel("平均对数曝光", fontsize=10.5)
ax.set_xlim(-0.5, 2.5)
ax.set_ylim(9.10, 9.80)
groom(ax, "y")

# ── 顶部单行图例（带框） ──
handles, labels, seen = [], [], set()
for a_ in (axes[0, 0], ax_a2):
    hs, ls = a_.get_legend_handles_labels()
    for hdl, lab in zip(hs, ls):
        if lab and lab not in seen:
            handles.append(hdl)
            labels.append(lab)
            seen.add(lab)
leg = fig.legend(handles=handles, labels=labels, loc="upper center",
                 bbox_to_anchor=(0.505, 0.992), ncol=3, frameon=True,
                 edgecolor="#333333", framealpha=1.0, fontsize=9.6,
                 handlelength=1.9, columnspacing=2.4, handletextpad=0.7,
                 borderaxespad=0.0)
for handle in getattr(leg, "legend_handles", []):
    if isinstance(handle, plt.Rectangle):
        handle.set_alpha(0.62)


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


for (r, c), tag in {(0, 0): "a", (0, 1): "b", (1, 0): "c", (1, 1): "d"}.items():
    tag_panel(axes[r, c], tag)

cap_below(axes[0, 0], "a 月度发帖量与付费占比")
cap_below(axes[0, 1], "b 月度平均曝光")
cap_below(axes[1, 0], "c 星期平均曝光")
cap_below(axes[1, 1], "d 三时段平均曝光")

fig.savefig(OUT / "补充图2_时间结构.png", dpi=400, bbox_inches="tight", facecolor="white")
print("saved", OUT / "补充图2_时间结构.png")
