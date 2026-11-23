# -*- coding: utf-8 -*-
"""图12 候选 W1：双列横条 95%CI（单面板：左设定名｜付费列｜Video 列）。

只读 问题四/临时产物/稳健性系数.csv，输出到同目录 PNG，不触碰 问题四/结果/。
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
from matplotlib.ticker import FixedLocator, NullFormatter

from _common import CACHE_DIR, get_plot_style

DATA = Path(CACHE_DIR) / "稳健性系数.csv"
df = pd.read_csv(DATA, encoding="utf-8-sig")
_style = get_plot_style("modelviz")

SPECS = ["M1 全模型", "M2 月份固定效应", "M3 仅logX1", "M4 logX1+线性月份",
         "Huber 稳健回归", "Gamma GLM（log 链接）"]
NAMES = ["M1\n全模型", "M2\n月份固定效应", "M3\n仅 logX1", "M4\nlogX1+线性月份",
         "Huber\n稳健回归", "Gamma GLM\n（log 链接）"]

pct = df[df["效应"] == "付费提升%"].set_index("设定").loc[SPECS]
vid = df[df["效应"] == "Video倍数"].set_index("设定").loc[SPECS]
BASE_PCT = float(pct.loc["M2 月份固定效应", "估计"])
BASE_VID = float(vid.loc["M2 月份固定效应", "估计"])

C_PCT, C_PCT_D = "#E64B35", "#9E2E1C"   # 付费：NPG 红
C_VID, C_VID_D = "#3C5488", "#22395A"   # Video：NPG 深蓝
C_BAND, C_M2 = "#4DBBD5", "#FFEFA8"
n = len(SPECS)
i_m2 = SPECS.index("M2 月份固定效应")
ypos = np.arange(n)[::-1].astype(float)

fig = plt.figure(figsize=(11.4, 5.3))
gs = fig.add_gridspec(1, 3, width_ratios=[0.44, 1.0, 1.0], wspace=0.07,
                      left=0.045, right=0.988, top=0.845, bottom=0.252)
ax_n = fig.add_subplot(gs[0, 0])
ax_p = fig.add_subplot(gs[0, 1])
ax_v = fig.add_subplot(gs[0, 2])

# ── 左：设定名（只写一次，两行折行）+ M2 整行淡黄高亮 ──
for ax in (ax_n, ax_p, ax_v):
    ax.set_ylim(-0.70, n - 0.30)
    ax.axhspan(ypos[i_m2] - 0.46, ypos[i_m2] + 0.46, facecolor=C_M2,
               alpha=0.60, edgecolor="none", zorder=0)
ax_n.set_xlim(0, 1)
ax_n.axis("off")
for i, (y, name) in enumerate(zip(ypos, NAMES)):
    ax_n.text(0.0, y, name, ha="left", va="center", fontsize=9.0,
              color="#111111" if i == i_m2 else "#242424",
              fontweight="bold" if i == i_m2 else "normal", linespacing=1.42)
ax_n.text(0.0, n - 0.30, "", ha="left", va="bottom")
ax_n.set_title("估计设定", fontsize=9.4, color="#333333", pad=12,
               loc="left", fontweight="bold")

# ── 左列：付费提升 %（线性轴） ──
ax_p.set_xlim(-5, 110)
ax_p.xaxis.set_major_locator(FixedLocator([0, 20, 40, 60, 80, 100]))
ax_p.axhspan(BASE_PCT * 0.9, BASE_PCT * 1.1, facecolor=C_BAND, alpha=0.16,
             edgecolor="none", zorder=0.4)
ax_p.axvline(BASE_PCT, color="#1A1A1A", ls=(0, (5, 2.6)), lw=1.05, zorder=1.2)
for i, y in enumerate(ypos):
    est, lo, hi = (float(pct.iloc[i]["估计"]), float(pct.iloc[i]["下限"]),
                   float(pct.iloc[i]["上限"]))
    ax_p.barh(y, hi - lo, left=lo, height=0.42, color=C_PCT, alpha=0.30,
              edgecolor="none", zorder=2)
    ax_p.plot([est], [y], marker="o", ls="none", ms=6.8 if i == i_m2 else 5.9,
              mfc=C_PCT, mec=C_PCT_D, mew=0.85, zorder=4)
    ax_p.annotate(f"{est:.1f}%", (hi, y), xytext=(6, 0), textcoords="offset points",
                  ha="left", va="center", fontsize=8.4, color=C_PCT_D,
                  fontweight="bold" if i == i_m2 else "normal", zorder=5)
ax_p.set_title("付费提升（%，线性轴）", fontsize=11.2, color=C_PCT,
               fontweight="bold", pad=11, loc="left")
ax_p.set_xlabel("付费带来的曝光提升（%）", fontsize=9.4, labelpad=3)

# ── 右列：Video 倍数（对数轴） ──
ax_v.set_xscale("log")
ax_v.set_xlim(1.40, 15.0)
ax_v.set_xticks([2, 3, 4, 5, 7, 10])
ax_v.set_xticklabels(["2", "3", "4", "5", "7", "10"])
ax_v.set_xticks([], minor=True)
ax_v.xaxis.set_minor_formatter(NullFormatter())
ax_v.axvline(BASE_VID, color="#1A1A1A", ls=(0, (5, 2.6)), lw=1.05, zorder=1.2)
for i, y in enumerate(ypos):
    est, lo, hi = (float(vid.iloc[i]["估计"]), float(vid.iloc[i]["下限"]),
                   float(vid.iloc[i]["上限"]))
    ax_v.barh(y, hi - lo, left=lo, height=0.42, color=C_VID, alpha=0.30,
              edgecolor="none", zorder=2)
    ax_v.plot([est], [y], marker="o", ls="none", ms=6.8 if i == i_m2 else 5.9,
              mfc=C_VID, mec=C_VID_D, mew=0.85, zorder=4)
    ax_v.annotate(f"×{est:.2f}", (hi, y), xytext=(6, 0), textcoords="offset points",
                  ha="left", va="center", fontsize=8.4, color=C_VID_D,
                  fontweight="bold" if i == i_m2 else "normal", zorder=5)
ax_v.set_title("Video/Photo 倍数（对数轴）", fontsize=11.2, color=C_VID,
               fontweight="bold", pad=11, loc="left")
ax_v.set_xlabel("Video 相对 Photo 的曝光倍数", fontsize=9.4, labelpad=3)

for ax in (ax_p, ax_v):
    ax.yaxis.set_visible(False)
    for side in ("left", "top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#4A4A4A")
    ax.spines["bottom"].set_linewidth(0.8)
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, color="#E8E8E8", lw=0.65, zorder=0.8)
    ax.tick_params(axis="x", labelsize=8.6, direction="out", length=3.2,
                   width=0.7, colors="#333333")

# ── 图例 + 注 ──
handles = [
    Line2D([], [], marker="o", ls="none", mfc=C_PCT, mec=C_PCT_D, mew=0.85,
           ms=6.4, label="付费提升"),
    Line2D([], [], marker="o", ls="none", mfc=C_VID, mec=C_VID_D, mew=0.85,
           ms=6.4, label="Video 倍数"),
    Patch(facecolor=C_PCT, alpha=0.30, edgecolor="none", label="95% CI 横条"),
    Line2D([], [], color="#1A1A1A", ls=(0, (5, 2.6)), lw=1.05, label="M2 基准"),
    Patch(facecolor=C_BAND, alpha=0.32, edgecolor="none", label="付费 ±10% 带"),
    Patch(facecolor=C_M2, alpha=0.85, edgecolor="none", label="最终模型 M2"),
]
fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.045, 0.118),
           ncol=6, frameon=False, fontsize=8.4, handlelength=1.7,
           columnspacing=1.5, handletextpad=0.6, borderaxespad=0.0)
fig.text(0.045, 0.030,
         "注：6 种设定为同一份真实系数（稳健性系数.csv，只读）；横条＝95% CI（HC3），"
         "条末端数值＝点估计。付费列线性轴、Video 列对数轴；基准取最终模型 M2"
         f"（{BASE_PCT:.1f}%），淡青带为其 ±10%（{BASE_PCT * 0.9:.1f}–{BASE_PCT * 1.1:.1f}%）。",
         fontsize=7.3, color="#5C5C5C", va="bottom")

out = HERE / "图12_W1_双列横条CI.png"
fig.savefig(out, dpi=400, bbox_inches="tight", facecolor="white")
print("saved:", out)
print(f"付费用范围 {pct['估计'].min():.2f}–{pct['估计'].max():.2f}; "
      f"Video 范围 {vid['估计'].min():.2f}–{vid['估计'].max():.2f}")
