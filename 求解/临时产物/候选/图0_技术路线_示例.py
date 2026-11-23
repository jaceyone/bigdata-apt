# -*- coding: utf-8 -*-
"""图0 示例：研究内容 × 技术路线 × 方法与工具（参照 figure_gallery/proposal-content-route）。

三栏结构：左=研究内容（四问），中=技术路线（纵向串联），右=方法与工具（含小图）。
所有数字取自项目既有结果（表2/表3/表6/表10/表13），不编数。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

d = pd.read_csv(ROOT / "清洗数据.csv", encoding="utf-8-sig")
rng = np.random.default_rng(20261122)

INK, SUB, LINE = "#1F2329", "#5A6068", "#8C99A6"
DEEP, RED, GREEN, CYAN = "#3C5488", "#E64B35", "#00A087", "#4DBBD5"
CARD_FC, CARD_EC = "#F7F8FA", "#C9D2DC"
HEAD_FC = "#EDF0F4"
ACCENT = "#2E5C8A"

YMIN = 13.0
fig = plt.figure(figsize=(11.6, 6.0))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(YMIN, 100)
ax.axis("off")


def box(x, y, w, h, fc=CARD_FC, ec=CARD_EC, lw=0.9, r=1.0, z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                linewidth=lw, facecolor=fc, edgecolor=ec, zorder=z))


def arrow(p0, p1, color=LINE, lw=0.9):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=9,
                                 linewidth=lw, color=color, shrinkA=0, shrinkB=1, zorder=5))


def elbow(x0, y0, x1, y1, color=LINE, lw=0.9):
    """先水平后垂直再水平的三段折线，末端带箭头。"""
    xm = (x0 + x1) / 2
    ax.plot([x0, xm], [y0, y0], color=color, lw=lw, zorder=4, solid_capstyle="butt")
    ax.plot([xm, xm], [y0, y1], color=color, lw=lw, zorder=4, solid_capstyle="butt")
    arrow((xm, y1), (x1, y1), color=color, lw=lw)


# ---------------- 顶部目标横幅 ----------------
box(2, 90.5, 96, 8.0, fc=HEAD_FC, ec="#B9C4D0", lw=1.0, r=1.2, z=1)
ax.text(50, 96.2, "研究目标：量化品牌主页 500 条帖子曝光（Y₁）的影响因素，并给出付费投放与内容策略",
        ha="center", va="center", fontsize=11.2, color=INK, zorder=6)
ax.text(50, 92.4, "数据：Facebook 化妆品品牌主页帖级截面数据（X1–X7 输入，Y1 输出）",
        ha="center", va="center", fontsize=8.6, color=SUB, zorder=6)

# 栏目标题
for x, t in ((13.5, "研究内容"), (45.5, "技术路线"), (76.5, "方法与工具")):
    ax.text(x, 86.6, t, ha="center", va="center", fontsize=11.0, color=INK, zorder=6)
ax.plot([2, 98], [84.4, 84.4], color="#D3DAE2", lw=0.9, zorder=3)

# ---------------- 左：研究内容 ----------------
contents = [
    (68.0, "内容一：数据理解", "粒度 · 结构 · 变量因果角色"),
    (52.0, "内容二：清洗与编码", "缺失 1 条 · 独热 · log1p"),
    (36.0, "内容三：回归与预测", "OLS+HC3 · 共线/残差/CV 诊断"),
    (20.0, "内容四：效应解释", "付费 · 视频 · 主题 · 稳健性"),
]
for y, t1, t2 in contents:
    box(2, y, 23.5, 12.5)
    ax.text(13.7, y + 8.1, t1, ha="center", va="center", fontsize=10.0, color=INK, zorder=6)
    ax.text(13.7, y + 3.9, t2, ha="center", va="center", fontsize=8.0, color=SUB, zorder=6)

# ---------------- 中：技术路线（5 步纵向） ----------------
steps = [
    (71.0, "读取原始数据：识别变量类型与粒度", "500 行 × 8 列 · 一行 = 一条帖子"),
    (58.0, "刻画结构与分布：截面 + 伪时间", "偏度 8.33 → 0.73（log1p）"),
    (45.0, "缺失填补 · 独热编码 · 对数变换", "X7 众数填补 · X2/X3 哑变量"),
    (32.0, "OLS + HC3：共线、残差与交叉验证", "VIF 143.0→3.23 · R²=0.207 · CV 0.101"),
    (19.0, "效应测算与稳健性检验", "付费 +40.1% · Video ×4.90"),
]
for y, t1, t2 in steps:
    box(30.5, y, 31.0, 11.0, fc="#FFFFFF", ec="#9FB0C2", lw=1.0)
    ax.text(46.0, y + 7.1, t1, ha="center", va="center", fontsize=9.4, color=INK, zorder=6)
    ax.text(46.0, y + 3.3, t2, ha="center", va="center", fontsize=8.0, color=SUB, zorder=6)

for i in range(len(steps) - 1):
    y_top = steps[i][0]
    y_bot = steps[i + 1][0] + 11.0
    arrow((46.0, y_top), (46.0, y_bot + 0.4))

# 左→中：内容框折线接到对应步骤
for cy, si in ((68.0, 0), (52.0, 1), (36.0, 3), (20.0, 4)):
    elbow(25.6, cy + 6.2, 30.3, steps[si][0] + 5.5)

# 内容三 同时覆盖诊断与主模型：补一条到第 3 步
elbow(25.6, 42.0, 30.3, steps[2][0] + 5.5)

# ---------------- 右：方法与工具 ----------------
methods = [
    ("描述统计 · 分位与偏度", "hist"),
    ("Spearman 相关 · 月内 SD", "scatter"),
    ("众数填补 · 独热 · log1p", "bars"),
    ("VIF · BP/JB/Cook · 10 折 CV", "matrix"),
    ("Duan smearing · 参数模拟 CI", "ci"),
]
ax.plot([63.0, 63.0], [16.0, 83.0], color="#D3DAE2", lw=0.9, ls=(0, (3, 3)), zorder=3)

ICON_X, ICON_W, ICON_H = 0.800, 0.130, 0.082
for i, (t1, icon) in enumerate(methods):
    cy = steps[i][0] + 5.5                      # 与中列步骤同高
    ax.text(64.2, cy + 1.4, t1, ha="left", va="center", fontsize=8.6, color=SUB, zorder=6)
    y0 = (cy - YMIN) / (100 - YMIN) - ICON_H / 2
    axins = ax.inset_axes([ICON_X, y0, ICON_W, ICON_H], transform=ax.transAxes)
    if icon == "hist":
        axins.hist(np.log1p(d["Y1"]), bins=14, color=DEEP, edgecolor="white", linewidth=0.35)
    elif icon == "scatter":
        axins.scatter(d["X4"] + rng.uniform(-0.25, 0.25, len(d)), d["X1"] / 1e4,
                      s=1.2, color=RED, alpha=0.45, linewidths=0)
    elif icon == "bars":
        axins.bar([0, 1, 2], [4, 3, 3], color=[DEEP, GREEN, CYAN], width=0.62,
                  edgecolor="white", linewidth=0.4)
        axins.set_xticks([0, 1, 2])
        axins.set_xticklabels(["类型", "主题", "时段"])
        axins.tick_params(axis="x", labelsize=5.8, length=0, pad=1.0)
        axins.set_yticks([])
    elif icon == "matrix":
        axins.imshow([[143.0, 124.9, 1.9, 1.8], [3.2, 1.9, 1.8, 1.5]], cmap="Reds",
                     aspect="auto", vmin=0, vmax=150)
        axins.set_xticks([]); axins.set_yticks([])
    else:
        axins.errorbar([0, 1, 2], [40.1, 47.1, 37.4], yerr=[[33, 31, 24], [37, 40, 30]],
                       fmt="o", ms=3.0, color=RED, ecolor="#D9A79C", elinewidth=0.9, capsize=1.4)
        axins.set_xticks([]); axins.set_yticks([]); axins.tick_params(length=1.4, width=0.5)
fig.savefig(Path(__file__).resolve().parent / "图0_技术路线_示例.png",
            dpi=400, bbox_inches="tight", facecolor="white")
print("saved")
