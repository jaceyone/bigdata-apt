# -*- coding: utf-8 -*-
"""图7：共线性诊断单面板哑铃图（M1 全模型 → M2 最终模型，对数 VIF 轴 + 5/10 阈值）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FixedFormatter
from matplotlib.transforms import blended_transform_factory

from _common import (CACHE_DIR, save_fig, label_subplots_below, register_data_inputs)

DATA = Path(CACHE_DIR) / "VIF.csv"
register_data_inputs(DATA)
d = pd.read_csv(DATA, encoding="utf-8-sig")
colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]  # Nature/NPG 色板

NAME = {"logX1": "粉丝规模 logX1", "类型": "帖子类型 X2", "主题": "内容主题 X3",
        "月份": "月份 X4", "星期": "星期 X5", "时段": "时段 X6", "付费": "付费 X7"}
C_M1, C_M2 = colors[1], colors[0]           # M1 红，M2 深蓝
C_T5, C_T10 = colors[4], colors[1]          # 阈值 5 橙虚，10 红虚


def term_of(v):
    """把哑变量名归回变量组（月份_10 → 月份）。"""
    if v == "logX1":
        return "logX1"
    if v.startswith(("类型_", "主题_", "月份_", "星期_", "时段_")):
        return v.split("_")[0]
    return "付费"


d["变量组"] = d["变量"].map(term_of)
agg = d.groupby(["模型", "变量组"], as_index=False)["VIF"].max()   # 哑变量组取组内最大 VIF
piv = agg.pivot(index="变量组", columns="模型", values="VIF").sort_values("M1", ascending=False)
order = list(piv.index)
m1 = piv["M1"].to_numpy(dtype=float)
m2 = piv["M2"].to_numpy(dtype=float)
n = len(order)
ypos = np.arange(n)[::-1]

m2_max = float(np.nanmax(m2))
m1_x4 = float(piv.loc["月份", "M1"])
m2_x4 = float(piv.loc["月份", "M2"])


def fmt(v, ref):
    """大数一位小数（143.0→3.2），小数两位；同一行看同一精度。"""
    return f"{v:.1f}" if max(v, ref) >= 20 else f"{v:.2f}"


def right_label(a, b):
    if not np.isfinite(b):
        return f"{fmt(a, a)} → 已剔除"
    drop = (1.0 - b / a) * 100.0
    text = f"{fmt(a, a)} → {fmt(b, a)}"
    return text + (f"（↓{drop:.0f}%）" if drop >= 1 else "")


XLO, XHI = 0.9, 300.0

fig, ax = plt.subplots(figsize=(10.4, 6.4))
fig.set_layout_engine("none")   # 关掉紧凑布局：右侧数值列靠固定边距排版
L, R, B, T = 0.200, 0.700, 0.135, 0.868
ax.set_position([L, B, R - L, T - B])   # nature 的占位引擎不认 subplots_adjust，直接给位置
xt = blended_transform_factory(ax.transAxes, ax.transData)
X_TEXT = 1.045          # 数值列起点：离右边框留出空隙，别和边框撞车

# ---- 三档底纹：<5 可接受 / 5–10 临界 / >10 严重
for lo, hi, face in [(XLO, 5, "#F1F8F4"), (5, 10, "#FDF3E6"), (10, XHI, "#FBEDEA")]:
    ax.axvspan(lo, hi, facecolor=face, edgecolor="none", linewidth=0, zorder=0)

# ---- 行参考网格（轻量）
ax.grid(False)
ax.grid(True, axis="y", ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)

# ---- 阈值线（5 橙虚、10 红虚），止于顶部标注带之下
ax.vlines([5], -0.72, n + 0.24, color=C_T5, lw=1.2, ls=(0, (5, 3)), zorder=2)
ax.vlines([10], -0.72, n + 0.24, color=C_T10, lw=1.2, ls=(0, (5, 3)), zorder=2)

# ---- 分区文字（顶部标注带，空白行内）
for x, txt, col in [(np.sqrt(XLO * 5), "可接受 <5", "#1B7F63"),
                    (np.sqrt(5 * 10), "临界", "#C0801F"),
                    (np.sqrt(10 * XHI), "严重 >10", "#C0392B")]:
    ax.text(x, n + 0.42, txt, ha="center", va="center", fontsize=9.2, color=col)

# ---- 哑铃：M1 大红点 — 灰箭头 → M2 蓝点，右侧标数值与降幅
for i, (y, a, b) in enumerate(zip(ypos, m1, m2)):
    if np.isfinite(b):
        ax.annotate("", xy=(b, y), xytext=(a, y), zorder=3,
                    arrowprops=dict(arrowstyle="-|>", color="#8C8C8C", lw=1.15,
                                    mutation_scale=9, shrinkA=6.0, shrinkB=6.0))
    ax.scatter([a], [y], s=150, color=C_M1, edgecolor="white", linewidth=1.0, zorder=4)
    if np.isfinite(b):
        ax.scatter([b], [y], s=46, color=C_M2, edgecolor="white", linewidth=1.0, zorder=5)
    is_key = order[i] == "月份"
    ax.text(X_TEXT, y, right_label(a, b), transform=xt, ha="left", va="center",
            fontsize=9.6, color="#222222",
            fontweight="bold" if is_key else "normal")

# 右侧列标题
ax.text(X_TEXT, n + 0.42, "M1 → M2（降幅）", transform=xt, ha="left", va="center",
        fontsize=9.2, color="#4A4A4A")

# ---- 坐标轴：对数 VIF
ax.set_xscale("log")
ax.set_xlim(XLO, XHI)
ax.set_ylim(-0.72, n + 0.66)
ax.xaxis.set_major_locator(FixedLocator([1, 2, 5, 10, 20, 50, 100, 300]))
ax.xaxis.set_major_formatter(FixedFormatter(["1", "2", "5", "10", "20", "50", "100", "300"]))
ax.tick_params(axis="x", which="major", labelsize=10)
ax.tick_params(axis="y", which="both", length=0, pad=7, labelsize=10)
ax.set_yticks(ypos)
ax.set_yticklabels([NAME[k] for k in order])
ax.set_xlabel("VIF（方差膨胀因子，对数刻度）", fontsize=11, labelpad=6)

leg = [Line2D([], [], marker="o", ls="none", mfc=C_M1, mec="white", mew=1.0,
              ms=8.5, label="M1 全模型"),
       Line2D([], [], marker="o", ls="none", mfc=C_M2, mec="white", mew=1.0,
              ms=6.0, label="M2 最终模型"),
       Line2D([], [], color=C_T5, lw=1.2, ls=(0, (5, 3)), label="VIF=5"),
       Line2D([], [], color=C_T10, lw=1.2, ls=(0, (5, 3)), label="VIF=10")]
ax.legend(handles=leg, loc="lower left", bbox_to_anchor=(0.0, 1.022), ncol=4,
          fontsize=9.5, handletextpad=0.45, columnspacing=1.5,
          borderaxespad=0.1, borderpad=0.35)

label_subplots_below(fig, [ax], ["M1 → M2 的 VIF 变化"], fontsize=10)

save_fig(fig, "图7_共线性诊断", chart_types=["bar"],
         chart_style="modelviz", chart_color_scheme="modelviz")
