# -*- coding: utf-8 -*-
"""图11 候选 V2：配对哑铃（a 相对基准偏移 + b 付费×类型交互），nature 风格。

只读 问题四/临时产物/调整预测.csv；输出正式图到 问题四/结果/图11_调整预测效应.png（含可编辑 SVG）。
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
from matplotlib.ticker import NullLocator

HERE = Path(__file__).resolve().parent
DATA = ROOT / "问题四" / "临时产物" / "调整预测.csv"

colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]      # Nature/NPG（与 nature 同源）
DEEP, RED, CYAN, SLATE = colors[0], colors[1], colors[3], colors[5]
STEEL, MIST = "#5E7C96", "#8CA6BC"
INK, SUB, FAINT = "#1F2329", "#4A5058", "#8A8F99"
GRID = "#E7E9EE"
DARK_R, DARK_B = "#B8402D", "#3E6382"
CI_GRAY = "#C9D0DA"

d = pd.read_csv(DATA, encoding="utf-8-sig")


def rec(panel, group):
    row = d[(d["面板"] == panel) & (d["组"] == group)].iloc[0]
    return dict(v=float(row["值"]), lo=float(row["CI下限"]), hi=float(row["CI上限"]),
                n=int(row["样本量"]))


# 面板 a：组名, 基准水平名, [(水平名, 取数面板, 颜色)]（组内按估计值降序）
GROUPS = [
    ("付费", "自然", [("付费", "a 付费", RED)]),
    ("内容类型", "Photo", [("Video", "b 内容类型", RED), ("Status", "b 内容类型", CYAN),
                          ("Link", "b 内容类型", SLATE)]),
    ("内容主题", "主题1", [("主题3", "c 内容主题", MIST), ("主题2", "c 内容主题", STEEL)]),
]

rows, tags = [], []
for gname, base_name, items in GROUPS:
    panel = {"付费": "a 付费", "内容类型": "b 内容类型", "内容主题": "c 内容主题"}[gname]
    first = len(rows)
    for name, rpanel, color in items:
        rows.append(dict(group=gname, base_name=base_name, name=name, color=color,
                         **rec(rpanel, name)))
    tags.append((gname, base_name, first, len(rows) - 1))
BASE = float(rec("a 付费", "自然")["v"])                 # 三组共用同一基准预测值
N_BASE = int(rec("a 付费", "自然")["n"])
n = len(rows)

# 面板 d
dd = d[d["面板"] == "d 交互描述"]
p_int = float(dd[dd["系列"] == "交互p值"]["值"].iloc[0])
dd = dd[dd["系列"] != "交互p值"]
TYPE_ORDER = ["Photo", "Status", "Link", "Video"]
TYPE_COLOR = {"Photo": DEEP, "Status": CYAN, "Link": SLATE, "Video": RED}
TYPE_DY = {"Photo": -12, "Status": 10, "Link": 13, "Video": 10}
inter = {}
for lev in TYPE_ORDER:
    s = dd[dd["系列"] == lev].set_index("组")
    inter[lev] = (float(s.loc["自然", "值"]), int(s.loc["自然", "样本量"]),
                  float(s.loc["付费", "值"]), int(s.loc["付费", "样本量"]))

FIG_W, FIG_H = 10.4, 5.5
AX1 = [0.195, 0.190, 0.330, 0.665]
AX2 = [0.630, 0.190, 0.290, 0.665]
XLO, XHI = 1.42e4, 5.40e5

fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor="white")

# ==================== (a) 配对哑铃 ====================
ax = fig.add_axes(AX1)
ax.set_xscale("log")
ax.set_ylim(n - 0.5, -0.95)
yt = ax.get_yaxis_transform()

for i, r in enumerate(rows):
    # 95% CI（浅灰粗线段，垫底）
    ax.plot([r["lo"], r["hi"]], [i, i], color=CI_GRAY, lw=2.3, solid_capstyle="round",
            zorder=1, alpha=0.95)
    up = r["v"] >= BASE
    ac = DARK_R if up else DARK_B
    ax.annotate("", xy=(r["v"], i), xytext=(BASE, i), zorder=3,
                arrowprops=dict(arrowstyle="-|>", color=ac, lw=1.0,
                                shrinkA=4.2, shrinkB=4.2, mutation_scale=9))
    # 基准端（蓝空心）
    ax.plot([BASE], [i], ls="none", marker="o", ms=6.9, mfc="white", mec=DEEP, mew=1.15, zorder=5)
    # 该水平估计（红实心）
    ax.plot([r["v"]], [i], ls="none", marker="o", ms=7.2, mfc=RED, mec="#2F343B",
            mew=0.45, zorder=6)
    # 差值（连线上方）
    mid = float(np.sqrt(BASE * r["v"]))
    pct = r["v"] / BASE - 1.0
    lab = f"{pct:+.1%}" if abs(pct) < 1.0 else f"×{r['v'] / BASE:.2f}"
    ax.text(mid, i - 0.28, lab, ha="center", va="center", fontsize=8.9, color=ac, zorder=7)
    # 端点数值（行线下方，避开 CI 与差值）
    ax.text(r["v"], i + 0.21, f"{r['v'] / 1e4:.2f} 万",
            ha="left" if up else "right", va="center", fontsize=8.2, color=SUB, zorder=7)
    # Video 的 CI 数值（四类最宽、n=7，点名标出）
    if r["name"] == "Video":
        ax.text(r["hi"], i + 0.42, f"CI {r['lo'] / 1e4:.2f}–{r['hi'] / 1e4:.2f} 万",
                ha="right", va="center", fontsize=7.2, color="#7C8695", zorder=7)
    # 行名 + n
    ax.text(-0.345, i, r["name"], transform=yt, ha="left", va="center", fontsize=9.6, color=INK)
    ax.text(-0.045, i, f"n={r['n']}", transform=yt, ha="right", va="center",
            fontsize=8.0, color=FAINT)

# 分组标签
for gname, base_name, i0, i1 in tags:
    ax.text(-0.345, i0 - 0.52, f"{gname}  基准 {base_name}", transform=yt, ha="left",
            va="center", fontsize=7.4, color=SUB)

# 基准竖线
ax.vlines(BASE, -0.55, n - 0.5, color="#94A0AD", lw=0.85, ls=(0, (2.8, 2.4)), zorder=2)
ax.text(BASE, -0.62, "基准 4.02 万", ha="center", va="center", fontsize=7.8, color=DEEP,
        bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none"), zorder=8)

ax.set_xlim(XLO, XHI)
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
ax.text(0.012, 0.978, "(a)", transform=ax.transAxes, ha="left", va="top",
        fontsize=10.5, fontweight="bold", color=INK, zorder=9)

h1 = [Line2D([], [], ls="none", marker="o", ms=6.6, mfc="white", mec=DEEP, mew=1.15,
             label="基准水平估计"),
      Line2D([], [], ls="none", marker="o", ms=6.8, mfc=RED, mec="#2F343B", mew=0.45,
             label="该水平估计"),
      Line2D([], [], color=CI_GRAY, lw=2.3, label="95% CI"),
      Line2D([], [], color=DARK_R, lw=1.0, marker=">", ms=4.0, label="提升（红）/ 下降（蓝）")]
ax.legend(handles=h1, loc="lower left", bbox_to_anchor=(-0.005, 1.005), ncol=4,
          frameon=False, fontsize=8.2, handlelength=1.5, handletextpad=0.45,
          columnspacing=1.1, borderaxespad=0.0)

# ==================== (b) 付费×类型交互 ====================
ax2 = fig.add_axes(AX2)
ax2.set_yscale("log")
ax2.set_ylim(6.6e3, 7.6e4)
ax2.set_xlim(-0.30, 1.34)

for lev in TYPE_ORDER:
    v0, n0, v1, n1 = inter[lev]
    c = TYPE_COLOR[lev]
    ax2.plot([0, 1], [v0, v1], color=c, lw=2.2, solid_capstyle="round", zorder=3)
    ax2.scatter([0, 1], [v0, v1], s=330, color=c, alpha=0.26, edgecolor="none", zorder=2)
    ax2.scatter([0, 1], [v0, v1], s=22, color=c, alpha=0.95, edgecolor="none", zorder=4)
    dy = TYPE_DY[lev]
    ax2.annotate(f"{v0 / 1e4:.2f}", xy=(0, v0), xytext=(-8, dy * 0.55),
                 textcoords="offset points", ha="right", va="center",
                 fontsize=8.4, color=SUB)
    ax2.annotate(f"{v1 / 1e4:.2f} 万", xy=(1, v1), xytext=(9, dy),
                 textcoords="offset points", ha="left", va="center",
                 fontsize=8.6, color=c)

ax2.set_xticks([0, 1])
ax2.set_xticklabels(["自然", "付费"])
ax2.set_yticks([8e3, 1e4, 1.5e4, 2e4, 3e4, 4e4, 6e4])
ax2.set_yticklabels(["0.8", "1.0", "1.5", "2.0", "3.0", "4.0", "6.0"])
ax2.yaxis.set_minor_locator(NullLocator())
ax2.set_ylabel("观测中位数曝光（万次，对数刻度）", labelpad=5, color=INK)
ax2.set_xlabel("付费标记", labelpad=5, color=INK)
ax2.tick_params(axis="both", which="major", pad=5)
ax2.set_axisbelow(True)
ax2.yaxis.grid(True, color=GRID, lw=0.65)
ax2.xaxis.grid(False)
ax2.text(0.012, 0.978, "(b)", transform=ax2.transAxes, ha="left", va="top",
         fontsize=10.5, fontweight="bold", color=INK, zorder=9)
ax2.text(0.982, 0.968, f"交互 p = {p_int:.3f}", transform=ax2.transAxes,
         ha="right", va="top", fontsize=8.8, color="#2B3038",
         bbox=dict(boxstyle="round,pad=0.36", fc="white", ec="#C7CEDA", lw=0.6))

h2 = [Line2D([], [], color=TYPE_COLOR[t], lw=2.2, marker="o", ms=5.0,
             label=f"{t}（{inter[t][1]}/{inter[t][3]}）") for t in TYPE_ORDER]
ax2.legend(handles=h2, loc="lower left", bbox_to_anchor=(-0.005, 1.005), ncol=4,
           frameon=False, fontsize=8.2, handlelength=1.9, handletextpad=0.45,
           columnspacing=1.1, borderaxespad=0.0, labelspacing=0.45)

# ==================== 面板题注（一句话）====================
diff = rows[0]["v"] - BASE
fig.text(AX1[0] + AX1[2] / 2, 0.070, "各水平相对基准的调整预测",
         ha="center", va="bottom", fontsize=9.4, color=INK)
fig.text(AX2[0] + AX2[2] / 2, 0.070, "付费 × 类型的观测中位数",
         ha="center", va="bottom", fontsize=9.4, color=INK)

import _common
OUT_PNG = HERE.parent / "结果" / "图11_调整预测效应.png"
OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT_PNG, dpi=400, bbox_inches="tight", facecolor="white")
_common.save_fig(fig, "图11_调整预测效应", dpi=400)
print("saved:", OUT_PNG)
