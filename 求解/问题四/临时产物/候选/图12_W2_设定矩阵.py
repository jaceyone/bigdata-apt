# -*- coding: utf-8 -*-
"""图12 候选 W2：设定矩阵（上：付费/Video 两行点+CI；下：组件开关矩阵 + 相对基准变化列）。

只读 问题四/临时产物/稳健性系数.csv，输出 PNG 到同目录，不触碰 问题四/结果/。
组件构成按设定名与 问题四/代码/主程序.py 的 build_design 参数推断。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE
for _anc in HERE.parents:
    if (_anc / "_common.py").is_file():
        ROOT = _anc
        break
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import NullFormatter

from _common import CACHE_DIR, get_plot_style

DATA = Path(CACHE_DIR) / "稳健性系数.csv"
df = pd.read_csv(DATA, encoding="utf-8-sig")
_style = get_plot_style("modelviz")

SPECS = ["M1 全模型", "M2 月份固定效应", "M3 仅logX1", "M4 logX1+线性月份",
         "Huber 稳健回归", "Gamma GLM（log 链接）"]
COLS = ["M1\n全模型", "M2 月份\n固定效应", "M3\n仅 logX1", "M4\n线性月份",
        "Huber\n稳健回归", "Gamma\nlog 链接"]
ROWS = ["logX1", "月份固定效应", "星期固定效应", "主题（X3）", "类型（X2）",
        "稳健估计", "Gamma 链接"]
# 1=启用, 0=未启用, 9=不适用（M4 的月份以线性项进入，不是固定效应）
ON = np.array([
    [1, 0, 1, 1, 0, 0],
    [1, 1, 0, 9, 1, 1],
    [1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 1],
])

pct = df[df["效应"] == "付费提升%"].set_index("设定").loc[SPECS]
vid = df[df["效应"] == "Video倍数"].set_index("设定").loc[SPECS]
BASE_PCT = float(pct.loc["M2 月份固定效应", "估计"])
BASE_VID = float(vid.loc["M2 月份固定效应", "估计"])
d_pct = (pct["估计"].values / BASE_PCT - 1) * 100
d_vid = (vid["估计"].values / BASE_VID - 1) * 100

C_PCT, C_PCT_D = "#E64B35", "#9E2E1C"
C_VID, C_VID_D = "#3C5488", "#22395A"
C_BAND, C_M2 = "#4DBBD5", "#FFF2B8"
C_ON, C_OFF, C_NA = "#3C5488", "#9AA7BA", "#D2D2D2"
i_m2 = SPECS.index("M2 月份固定效应")

nrow, ncol = ON.shape
xpos = np.arange(len(SPECS), dtype=float)
ygrid = np.arange(nrow)[::-1].astype(float)

fig = plt.figure(figsize=(11.8, 7.9))
gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.0, 1.52],
                      width_ratios=[1.0, 0.40], hspace=0.42, wspace=0.02,
                      left=0.112, right=0.985, top=0.884, bottom=0.208)
ax_p = fig.add_subplot(gs[0, 0])
ax_v = fig.add_subplot(gs[1, 0], sharex=ax_p)
ax_m = fig.add_subplot(gs[2, 0], sharex=ax_p)
ax_c = fig.add_subplot(gs[2, 1], sharex=ax_p)

for ax in (ax_p, ax_v, ax_m):
    ax.axvspan(i_m2 - 0.47, i_m2 + 0.47, facecolor=C_M2, alpha=0.55,
               edgecolor="none", zorder=0)


def draw_effect(ax, sub, base, color, dark, fmt):
    ax.axhspan(base * 0.9, base * 1.1, facecolor=C_BAND, alpha=0.16,
               edgecolor="none", zorder=0.4)
    ax.axhline(base, color="#1A1A1A", ls=(0, (5, 2.6)), lw=1.0, zorder=1.2)
    for i, x in enumerate(xpos):
        est = float(sub.iloc[i]["估计"])
        lo, hi = float(sub.iloc[i]["下限"]), float(sub.iloc[i]["上限"])
        ax.errorbar(x, est, yerr=[[est - lo], [hi - est]], fmt="o", color=color,
                    ecolor=color, elinewidth=1.15, capsize=3.2, capthick=0.9,
                    markersize=7.0 if i == i_m2 else 6.0,
                    markeredgecolor=dark, markeredgewidth=0.85, zorder=4)
        ax.annotate(fmt(est), (x, est), xytext=(7, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=8.3, color=dark, zorder=6,
                    fontweight="bold" if i == i_m2 else "normal",
                    bbox=dict(boxstyle="round,pad=0.12", facecolor="white",
                              edgecolor="none", alpha=0.80))


draw_effect(ax_p, pct, BASE_PCT, C_PCT, C_PCT_D, lambda v: f"{v:.1f}%")
ax_p.set_ylim(4, 100)
ax_p.set_yticks([20, 40, 60, 80, 100])
ax_p.set_ylabel("付费提升（%）", fontsize=9.4, labelpad=3)
ax_p.set_title("a　付费提升（%）· 点＝估计，竖线＝95% CI", loc="left", pad=8,
               fontsize=9.8, color=C_PCT, fontweight="bold")

draw_effect(ax_v, vid, BASE_VID, C_VID, C_VID_D, lambda v: f"×{v:.2f}")
ax_v.set_yscale("log")
ax_v.set_ylim(1.45, 15.5)
ax_v.set_yticks([2, 3, 4, 5, 7, 10])
ax_v.set_yticklabels(["2", "3", "4", "5", "7", "10"])
ax_v.yaxis.set_minor_formatter(NullFormatter())
ax_v.set_yticks([], minor=True)
ax_v.set_ylabel("Video/Photo 倍数\n（对数轴）", fontsize=9.4, labelpad=3)
ax_v.set_title("b　Video 相对 Photo 的曝光倍数 · 基准 ×4.90", loc="left", pad=8,
               fontsize=9.8, color=C_VID, fontweight="bold")

for ax in (ax_p, ax_v):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#4A4A4A")
    ax.spines["bottom"].set_color("#4A4A4A")
    ax.spines["bottom"].set_linewidth(0.8)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#ECECEC", lw=0.6, zorder=0.8)
    ax.xaxis.grid(True, color="#F3F3F3", lw=0.6, zorder=0.9)
    ax.tick_params(axis="y", labelsize=8.4, direction="out", length=3, width=0.7)
    ax.tick_params(axis="x", labelbottom=False, length=0)
    ax.set_xlim(-0.55, len(SPECS) - 0.45)

# ── c：设定开关矩阵 ──
for j, x in enumerate(xpos):
    for i, y in enumerate(ygrid):
        v = ON[i, j]
        if v == 9:
            ax_m.plot([x], [y], marker="o", ls="none", ms=4.6,
                      mfc=C_NA, mec=C_NA, mew=0, zorder=3)
        elif v == 1:
            ax_m.plot([x], [y], marker="o", ls="none", ms=8.2,
                      mfc=C_ON, mec="#1E3252", mew=0.9, zorder=4)
        else:
            ax_m.plot([x], [y], marker="o", ls="none", ms=7.6,
                      mfc="white", mec=C_OFF, mew=1.1, zorder=4)
for k in range(nrow + 1):
    ax_m.axhline(k - 0.5, color="#E4E4E4", lw=0.7, zorder=1)
ax_m.set_ylim(nrow - 0.5, -0.5)
ax_m.set_yticks(ygrid)
ax_m.set_yticklabels(ROWS, fontsize=8.4, color="#2B2B2B")
ax_m.set_xticks(xpos)
ax_m.set_xticklabels(COLS, fontsize=8.3, linespacing=1.35, color="#2B2B2B")
ax_m.set_xlim(-0.55, len(SPECS) - 0.45)
for side in ("top", "right", "left"):
    ax_m.spines[side].set_visible(False)
ax_m.spines["bottom"].set_color("#4A4A4A")
ax_m.spines["bottom"].set_linewidth(0.8)
ax_m.tick_params(axis="y", length=0)
ax_m.tick_params(axis="x", length=3, width=0.7, direction="out", pad=5)
ax_m.set_title("c　模型组件构成（实心＝启用，空心＝未启用，浅灰＝不适用）",
               loc="left", pad=8, fontsize=9.8, color="#1A1A1A", fontweight="bold")
for lbl in ax_m.get_xticklabels():
    if lbl.get_text().startswith("M2"):
        lbl.set_fontweight("bold")
        lbl.set_color("#8A6D12")

# ── 右侧：相对基准变化 ──
ax_c.set_ylim(nrow - 0.5, -0.5)
ax_c.set_yticks([])
for side in ("top", "right", "left", "bottom"):
    ax_c.spines[side].set_visible(False)
ax_c.tick_params(axis="x", length=0, labelbottom=False)
ax_c.set_title("相对基准变化\n付费 / Video", fontsize=8.0, color="#333333",
               pad=8, loc="center", linespacing=1.35)
y_mid = (nrow - 1) / 2
for i, x in enumerate(xpos):
    tsp = "—" if i == i_m2 else f"{d_pct[i]:+.1f}%"
    tsv = "—" if i == i_m2 else f"{d_vid[i]:+.1f}%"
    ax_c.text(x, y_mid - 0.42, tsp, ha="center", va="center", fontsize=7.3,
              color="#8A6D12" if i == i_m2 else C_PCT_D, fontweight="bold")
    ax_c.text(x, y_mid + 0.44, tsv, ha="center", va="center", fontsize=7.3,
              color="#8A6D12" if i == i_m2 else C_VID_D)

# ── 图例 + 注 ──
handles = [
    Line2D([], [], marker="o", ls="none", mfc="#4A4A4A", mec="#1A1A1A", mew=0.9,
           ms=5.8, label="估计 + 95% CI"),
    Line2D([], [], color="#1A1A1A", ls=(0, (5, 2.6)), lw=1.0, label="M2 基准"),
    Patch(facecolor=C_BAND, alpha=0.32, edgecolor="none", label="基准 ±10% 带"),
    Line2D([], [], marker="o", ls="none", mfc=C_ON, mec="#1E3252", mew=0.9,
           ms=7.0, label="启用"),
    Line2D([], [], marker="o", ls="none", mfc="white", mec=C_OFF, mew=1.1,
           ms=6.6, label="未启用"),
    Line2D([], [], marker="o", ls="none", mfc=C_NA, mec=C_NA, mew=0, ms=4.2,
           label="不适用"),
    Patch(facecolor=C_M2, alpha=0.9, edgecolor="none", label="最终模型 M2"),
]
fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.112, 0.098),
           ncol=7, frameon=False, fontsize=8.0, handlelength=1.5,
           columnspacing=1.2, handletextpad=0.55, borderaxespad=0.0)
fig.text(0.112, 0.050,
         "注：点＝估计值，竖线＝95% CI（HC3）；灰虚线＝M2 基准（付费 "
         f"{BASE_PCT:.1f}%、Video ×{BASE_VID:.2f}），淡青带＝付费基准 ±10%"
         f"（{BASE_PCT * 0.9:.1f}–{BASE_PCT * 1.1:.1f}%）。",
         fontsize=7.1, color="#5C5C5C", va="bottom")
fig.text(0.112, 0.014,
         "组件构成按设定名与建模代码推断（M2 剔除 logX1；M4 的月份以线性项进入，"
         "故不计入“月份固定效应”）；右列 Δ＝（估计÷M2−1）×100%。",
         fontsize=7.1, color="#5C5C5C", va="bottom")

out = HERE / "图12_W2_设定矩阵.png"
fig.savefig(out, dpi=400, bbox_inches="tight", facecolor="white")
print("saved:", out)
print("Δ付费:", np.round(d_pct, 2), " ΔVideo:", np.round(d_vid, 2))
