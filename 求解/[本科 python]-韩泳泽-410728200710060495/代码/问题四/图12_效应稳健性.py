# -*- coding: utf-8 -*-
"""图12：付费提升与 Video/Photo 倍数在六种设定下的稳健性（定稿版·双列横条 95%CI）。

版式：单面板；左轴一列设定名（两行折行，只写一次），右侧并排
     · 付费提升%（线性轴，红 #E64B35），点 + 95%CI 横条 + 基准 40.1% 竖线 + ±10% 淡带
     · Video 倍数（对数轴，深蓝 #3C5488），点 + 95%CI 横条 + 基准 ×4.90 竖线
M2 整行淡黄底高亮（最终模型）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator, NullFormatter

from _common import (CACHE_DIR, save_fig, register_data_inputs)

DATA = Path(CACHE_DIR) / "稳健性系数.csv"
register_data_inputs(DATA)
df = pd.read_csv(DATA, encoding="utf-8-sig")

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
C_BAND, C_M2 = "#4DBBD5", "#FFF2B8"
n = len(SPECS)
i_m2 = SPECS.index("M2 月份固定效应")
ypos = np.arange(n)[::-1].astype(float)

fig = plt.figure(figsize=(12.8, 5.4))
fig.set_layout_engine("none")          # 版式由下方 gridspec 的边距显式给定
gs = fig.add_gridspec(1, 3, width_ratios=[0.52, 1.0, 1.0], wspace=0.075,
                      left=0.028, right=0.988, top=0.860, bottom=0.215)
ax_n = fig.add_subplot(gs[0, 0])
ax_p = fig.add_subplot(gs[0, 1])
ax_v = fig.add_subplot(gs[0, 2])

# ── 左：设定名（两行、行距压紧）+ M2 整行淡黄高亮 ──
for ax in (ax_n, ax_p, ax_v):
    ax.set_ylim(-0.66, n - 0.34)
    ax.axhspan(ypos[i_m2] - 0.46, ypos[i_m2] + 0.46, facecolor=C_M2,
               alpha=0.65, edgecolor="none", zorder=0)
ax_n.set_xlim(0, 1)
ax_n.axis("off")
for i, (y, name) in enumerate(zip(ypos, NAMES)):
    ax_n.text(0.0, y, name, ha="left", va="center", fontsize=10.5,
              color="#111111" if i == i_m2 else "#242424",
              fontweight="bold" if i == i_m2 else "normal", linespacing=1.10)
ax_n.text(0.0, 1.035, "a 估计设定", transform=ax_n.transAxes, ha="left", va="bottom",
          fontsize=10.5, color="#333333", fontweight="bold")

# ── 左列：付费提升 %（线性轴） ──
ax_p.set_xlim(-5, 110)
ax_p.xaxis.set_major_locator(FixedLocator([0, 20, 40, 60, 80, 100]))
ax_p.axhspan(BASE_PCT * 0.9, BASE_PCT * 1.1, facecolor=C_BAND, alpha=0.16,
             edgecolor="none", zorder=0.4)
ax_p.axvline(BASE_PCT, color="#1A1A1A", ls=(0, (5, 2.6)), lw=1.05, zorder=1.2)
for i, y in enumerate(ypos):
    est, lo, hi = (float(pct.iloc[i]["估计"]), float(pct.iloc[i]["下限"]),
                   float(pct.iloc[i]["上限"]))
    ax_p.barh(y, hi - lo, left=lo, height=0.46, color=C_PCT, alpha=0.45,
              edgecolor="none", zorder=2)
    ax_p.plot([est], [y], marker="o", ls="none", ms=8.4 if i == i_m2 else 8.0,
              mfc=C_PCT, mec="white", mew=0.8, zorder=4)
    ax_p.annotate(f"{est:.1f}%", (hi, y), xytext=(6, 0), textcoords="offset points",
                  ha="left", va="center", fontsize=9.0, color=C_PCT_D,
                  fontweight="bold" if i == i_m2 else "normal", zorder=5)
ax_p.text(0.0, 1.035, "b 付费提升（%）", transform=ax_p.transAxes,
          ha="left", va="bottom", fontsize=11.0, color=C_PCT, fontweight="bold")
ax_p.set_xlabel("付费带来的曝光提升（%）", labelpad=4)

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
    ax_v.barh(y, hi - lo, left=lo, height=0.46, color=C_VID, alpha=0.45,
              edgecolor="none", zorder=2)
    ax_v.plot([est], [y], marker="o", ls="none", ms=8.4 if i == i_m2 else 8.0,
              mfc=C_VID, mec="white", mew=0.8, zorder=4)
    ax_v.annotate(f"×{est:.2f}", (hi, y), xytext=(6, 0), textcoords="offset points",
                  ha="left", va="center", fontsize=9.0, color=C_VID_D,
                  fontweight="bold" if i == i_m2 else "normal", zorder=5)
ax_v.text(0.0, 1.035, "c Video/Photo 倍数", transform=ax_v.transAxes,
          ha="left", va="bottom", fontsize=11.0, color=C_VID, fontweight="bold")
ax_v.set_xlabel("Video 相对 Photo 的曝光倍数", labelpad=4)

for ax in (ax_p, ax_v):
    ax.yaxis.set_visible(False)
    ax.grid(True, axis="x", ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)

for ax_, tag in ((ax_n, "a"), (ax_p, "b"), (ax_v, "c")):
    # 不可见标号占位：样式层据此不再自动补 (a)(b)(c)
    ax_.text(0.5, 0.5, f"({tag})", transform=ax_.transAxes, alpha=0.0)

# ── 图例（4 项） ──
handles = [
    Line2D([], [], marker="o", ls="none", mfc=C_PCT, mec="white", mew=0.8,
           ms=7.6, label="付费提升"),
    Line2D([], [], marker="o", ls="none", mfc=C_VID, mec="white", mew=0.8,
           ms=7.6, label="Video 倍数"),
    Patch(facecolor=C_PCT, alpha=0.45, edgecolor="none", label="95% CI"),
    Patch(facecolor=C_M2, alpha=0.90, edgecolor="none", label="最终模型 M2"),
]
fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.028, 0.040),
           ncol=4, frameon=True, edgecolor="#333333", framealpha=1.0,
           fontsize=9.6, handlelength=1.8, columnspacing=2.0,
           handletextpad=0.65, borderaxespad=0.0)

save_fig(fig, "图12_效应稳健性", chart_types=["forest"],
         chart_style="modelviz", chart_color_scheme="modelviz")
print(f"付费用范围 {pct['估计'].min():.2f}–{pct['估计'].max():.2f}; "
      f"Video 范围 {vid['估计'].min():.2f}–{vid['估计'].max():.2f}")
