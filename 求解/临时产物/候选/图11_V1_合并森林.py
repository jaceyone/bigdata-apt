# -*- coding: utf-8 -*-
"""图11 候选 V1：三组合并森林（单面板横向 + 右侧三列数值），nature 风格。

只读 问题四/临时产物/调整预测.csv；输出 PNG 到本脚本所在目录，不触碰 问题四/结果/ 正式文件。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # 求解/
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import NullLocator

HERE = Path(__file__).resolve().parent
DATA = ROOT / "问题四" / "临时产物" / "调整预测.csv"

colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]      # Nature/NPG（与 nature 同源）
DEEP, RED, CYAN, SLATE = colors[0], colors[1], colors[3], colors[5]
STEEL, MIST = "#5E7C96", "#8CA6BC"                          # 冷青灰阶（主题组）
INK, SUB, FAINT = "#1F2329", "#4A5058", "#8A8F99"
GRID, BAND, SEP = "#E7E9EE", "#F6F7FA", "#E2E6ED"
DARK_R, DARK_B = "#B8402D", "#3E6382"
EDGE = plt.rcParams["axes.edgecolor"]
ELW = plt.rcParams["axes.linewidth"]

d = pd.read_csv(DATA, encoding="utf-8-sig")


def rec(panel, group):
    row = d[(d["面板"] == panel) & (d["组"] == group)].iloc[0]
    return dict(v=float(row["值"]), lo=float(row["CI下限"]), hi=float(row["CI上限"]),
                n=int(row["样本量"]))


# 组名, [(水平名, 取数面板, 颜色, 是否基准水平)]
SPEC = [
    ("付费", [("自然", "a 付费", DEEP, True), ("付费", "a 付费", RED, False)]),
    ("内容类型", [("Photo", "b 内容类型", DEEP, True), ("Status", "b 内容类型", CYAN, False),
                  ("Link", "b 内容类型", SLATE, False), ("Video", "b 内容类型", RED, False)]),
    ("内容主题", [("主题1", "c 内容主题", DEEP, True), ("主题2", "c 内容主题", STEEL, False),
                  ("主题3", "c 内容主题", MIST, False)]),
]

rows, group_spans = [], []
for gname, items in SPEC:
    first = len(rows)
    for name, panel, color, base in items:
        rows.append(dict(group=gname, name=name, color=color, base=base, **rec(panel, name)))
    group_spans.append((gname, first, len(rows) - 1))

BASE = float(rows[0]["v"])                     # 自然 / Photo / 主题1 共用同一基准预测值
n = len(rows)
p_int = float(d[(d["面板"] == "d 交互描述") & (d["系列"] == "交互p值")]["值"].iloc[0])

FIG_W, FIG_H = 8.7, 6.9
AX = [0.195, 0.150, 0.395, 0.700]
YT, YB = -0.62, n - 0.5                        # 仅行区在框内，表头浮在框上方
HEAD_Y = -0.95
BAND_X0, C1, C2, C3 = 0.0, 1.040, 1.288, 1.536
BAND_X1 = AX[0] + AX[2] * (C3 + 0.258)

fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor="white")
ax = fig.add_axes(AX)
ax.set_ylim(YB, YT)
ax.set_xscale("log")
ax.set_facecolor("none")                       # 让行底纹透过绘图区

P = ax.get_position()


def fy(y):
    """数据 y -> 图幅纵向比例（自下向上）。"""
    return P.y0 + (YB - y) / (YB - YT) * P.height


# ---------------- 行底纹 + 组间分隔带（整图层，随 bbox 精确裁边）----------------
for gname, i0, i1 in group_spans:
    for i in range(i0, i1 + 1):                             # 组内隔行浅底（基准行必上底）
        if (i - i0) % 2 == 0:
            y0, y1 = fy(i + 0.5), fy(i - 0.5)
            fig.add_artist(Rectangle((BAND_X0, y0), BAND_X1 - BAND_X0, y1 - y0,
                                     transform=fig.transFigure, facecolor=BAND,
                                     edgecolor="none", zorder=-20))

for k in range(1, len(group_spans)):
    yb = group_spans[k][1] - 0.5                            # 组间分界
    y0, y1 = fy(yb + 0.17), fy(yb - 0.17)
    fig.add_artist(Rectangle((BAND_X0, y0), BAND_X1 - BAND_X0, y1 - y0,
                             transform=fig.transFigure, facecolor=SEP,
                             edgecolor="none", zorder=-19))

# 表头横线 / 底部通栏横线（与 nature 边框同色同宽，接成一条表线）/ 组名竖栏线
for yy in (YT, YB):
    fig.add_artist(Line2D([BAND_X0, BAND_X1], [fy(yy)] * 2, transform=fig.transFigure,
                          color=EDGE, lw=ELW, solid_capstyle="butt", zorder=-15))
fig.add_artist(Line2D([0.040] * 2, [fy(-0.5), fy(n - 0.5)], transform=fig.transFigure,
                      color="#D3D9E1", lw=0.75, solid_capstyle="butt", zorder=-15))

# ---------------- 基准竖虚线（贯穿全部行）----------------
ax.vlines(BASE, -0.5, n - 0.5, color="#98A0AB", lw=0.85, ls=(0, (2.8, 2.4)), zorder=1)

# ---------------- 点 + 95% CI ----------------
for i, r in enumerate(rows):
    ax.errorbar(r["v"], i, xerr=[[r["v"] - r["lo"]], [r["hi"] - r["v"]]], fmt="none",
                ecolor=r["color"], elinewidth=0.95, capsize=2.8, capthick=0.9, zorder=3)
    ax.plot([r["v"]], [i], ls="none", marker="s" if r["base"] else "o", ms=6.3,
            mfc="white" if r["base"] else r["color"],
            mec=r["color"] if r["base"] else "#2F343B",
            mew=1.05 if r["base"] else 0.5, zorder=4)

# ---------------- 文字：行名 / n / 三列数值 ----------------
yt = ax.get_yaxis_transform()
for i, r in enumerate(rows):
    ax.text(-0.360, i, r["name"], transform=yt, ha="left", va="center",
            fontsize=9.8, color=INK if not r["base"] else "#2B3038")
    ax.text(-0.045, i, f"n={r['n']}", transform=yt, ha="right", va="center",
            fontsize=8.2, color=FAINT)

    ratio = r["v"] / BASE
    pct = ratio - 1.0
    if r["base"]:
        rel, rel_c = "—（基准）", FAINT
    elif abs(pct) < 1.0:
        rel, rel_c = f"{pct:+.1%}", DARK_R if pct > 0 else DARK_B
    else:
        rel, rel_c = f"×{ratio:.2f}", DARK_R if pct > 0 else DARK_B

    ax.text(C1, i, f"{r['v'] / 1e4:.2f} 万", transform=yt, ha="left", va="center",
            fontsize=9.0, color=SUB if r["base"] else INK)
    ax.text(C2, i, rel, transform=yt, ha="left", va="center", fontsize=8.9, color=rel_c)
    ax.text(C3, i, f"{r['lo'] / 1e4:.2f}–{r['hi'] / 1e4:.2f} 万", transform=yt,
            ha="left", va="center", fontsize=8.6, color=SUB)

# ---------------- 表头（框上方）----------------
for x, txt, ha, fs, col in [(-0.360, "变量水平", "left", 9.0, INK),
                            (-0.045, "样本量", "right", 8.6, SUB),
                            (C1, "调整预测", "left", 9.0, INK),
                            (C2, "相对基准", "left", 9.0, INK),
                            (C3, "95% CI", "left", 9.0, INK)]:
    ax.text(x, HEAD_Y, txt, transform=yt, ha=ha, va="center", fontsize=fs, color=col)

# ---------------- 组名（竖排）----------------
for gname, i0, i1 in group_spans:
    fig.text(0.0200, fy((i0 + i1) / 2), gname, rotation=90, ha="center", va="center",
             fontsize=9.0, color=DEEP)

# ---------------- 图内要点（不留图下注释）----------------
diff = rows[1]["v"] - rows[0]["v"]
ax.text(9.4e4, 1.0, f"差值 +{diff:,.0f} 次", ha="left", va="center", fontsize=8.8,
        color=DARK_R, zorder=6)
ax.text(0.972, 0.962, f"交互 p = {p_int:.3f}（不显著）", transform=ax.transAxes,
        ha="right", va="top", fontsize=8.6, color="#2B3038", zorder=8,
        bbox=dict(boxstyle="round,pad=0.36", fc="white", ec="#C7CEDA", lw=0.6))

# ---------------- 图例 ----------------
handles = [
    Line2D([], [], ls="none", marker="s", ms=6.0, mfc="white", mec=DEEP, mew=1.05,
           label="基准水平（自然 / Photo / 主题1）"),
    Line2D([], [], ls="none", marker="o", ms=6.0, mfc=RED, mec="#2F343B", mew=0.5,
           label="付费 / Video 提升水平"),
    Line2D([], [], ls="none", marker="o", ms=6.0, mfc=CYAN, mec="#2F343B", mew=0.5,
           label="其余水平"),
    Line2D([], [], color="#98A0AB", lw=0.9, ls=(0, (2.8, 2.4)), label="基准预测 4.02 万"),
]
fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(BAND_X0 + 0.002, 0.962),
           ncol=4, frameon=False, fontsize=8.6, handlelength=1.7, handletextpad=0.5,
           columnspacing=1.5, borderaxespad=0.0)

# ---------------- 坐标轴 ----------------
ax.set_xlim(1.42e4, 5.30e5)
ax.set_xticks([2e4, 3e4, 5e4, 1e5, 2e5, 5e5])
ax.set_xticklabels(["2", "3", "5", "10", "20", "50"])
ax.xaxis.set_minor_locator(NullLocator())
ax.set_yticks([])
ax.set_xlabel("调整预测曝光（万次，对数刻度）", labelpad=5, color=INK)
ax.tick_params(axis="x", which="minor", bottom=False, top=False)
ax.tick_params(axis="x", which="major", pad=5)
ax.set_axisbelow(True)
ax.xaxis.grid(True, color=GRID, lw=0.65)
ax.yaxis.grid(False)

fig.savefig(HERE / "图11_V1_合并森林.png", dpi=400, bbox_inches="tight", facecolor="white")
print("saved:", HERE / "图11_V1_合并森林.png")
