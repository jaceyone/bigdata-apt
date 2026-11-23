# -*- coding: utf-8 -*-
"""图0 示例：数据理解流程（参照 gallery figure_gallery/data-preprocessing 版式）。

结构：上游数据圆柱 → 四张带小插图的处理卡片 → 下游输出圆柱。
数据全部来自 求解\清洗数据.csv（真数据），不编数。
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
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse, Rectangle

d = pd.read_csv(ROOT / "清洗数据.csv", encoding="utf-8-sig")

DEEP, RED, GREEN, CYAN = "#3C5488", "#E64B35", "#00A087", "#4DBBD5"
SLATE, INK, SUB = "#4A6A8A", "#1F2329", "#5A6068"
CARD_EC, CARD_FC = "#C9D2DC", "#F7F8FA"
MIST = "#DCE3EA"

fig = plt.figure(figsize=(11.0, 7.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")


def box(x, y, w, h, fc, ec, lw=1.0, r=1.2, z=2):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                       linewidth=lw, facecolor=fc, edgecolor=ec, zorder=z)
    ax.add_patch(p)
    return p


def cylinder(cx, cy, w, h, top, sub):
    """数据圆柱：上下椭圆 + 矩形，写两行字。"""
    rx, ry = w / 2, h * 0.13
    ax.add_patch(Rectangle((cx - rx, cy - ry), w, 2 * ry, facecolor="#EFF2F5",
                           edgecolor="#8C99A6", linewidth=1.0, zorder=2))
    ax.add_patch(Rectangle((cx - rx, cy - ry), w, 2 * ry, facecolor="#EFF2F5",
                           edgecolor="none", zorder=2))
    ax.add_patch(Ellipse((cx, cy + ry), w, 2 * ry, facecolor="#EFF2F5",
                         edgecolor="#8C99A6", linewidth=1.0, zorder=3))
    ax.add_patch(Ellipse((cx, cy - ry), w, 2 * ry, facecolor="#E7EBEF",
                         edgecolor="#8C99A6", linewidth=1.0, zorder=1))
    ax.text(cx, cy, top, ha="center", va="center", fontsize=11.5, color=INK, zorder=4)


def arrow(p0, p1, rad=0.0, color="#7A8797", lw=1.1, ls="-"):
    a = FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=11,
                        connectionstyle=f"arc3,rad={rad}", linewidth=lw,
                        color=color, linestyle=ls, shrinkA=2, shrinkB=2, zorder=5)
    ax.add_patch(a)


def card(x, y, w, h, title, body, tag):
    box(x, y, w, h, CARD_FC, CARD_EC, lw=1.0, r=1.4, z=2)
    ax.text(x + 1.6, y + h - 3.4, title, ha="left", va="center", fontsize=11, color=INK, zorder=6)
    ax.text(x + 1.6, y + h - 8.2, body, ha="left", va="center", fontsize=8.4,
            color=SUB, linespacing=1.6, zorder=6)
    ax.text(x + w - 1.6, y + h - 3.4, tag, ha="right", va="center", fontsize=8.2,
            color="#96A1AC", zorder=6)


# ---------------- 上游：原始数据 ----------------
cylinder(50, 90.0, 34, 11.0, "原始数据：500 条帖子 × 8 个字段（X1–X7、Y1）", "")
arrow((50, 84.2), (50, 79.0))

# 分流横线
ax.plot([11.5, 88.5], [77.2, 77.2], color="#7A8797", lw=1.1, zorder=4)
for xc in (11.5, 36.0, 64.0, 88.5):
    arrow((xc, 77.2), (xc, 70.6))

# ---------------- 四张卡片 ----------------
CW, CH, CY = 22.0, 26.5, 39.5
xs = [0.5, 26.0, 51.5, 77.0]

card(xs[0], CY, CW, CH, "识别变量类型", "连续 2 · 名义 2\n循环 3 · 指示 1", "表1")
card(xs[1], CY, CW, CH, "判定数据结构", "一行 = 一条帖子\n截面 + 伪时间", "2.1.2")
card(xs[2], CY, CW, CH, "刻画分布特征", "Y₁ 偏度 8.33\n峰度 93.05（重尾）", "表2")
card(xs[3], CY, CW, CH, "量化共线证据", "r=0.941 · ρ=0.996\nVIF=143.0", "表3")

# 卡片内小插图：类型胶囊
axins = ax.inset_axes([xs[0] / 100 + 0.018, 0.428, CW / 100 - 0.055, 0.105], transform=ax.transAxes)
axins.axis("off")
axins.set_xlim(0, 10)
axins.set_ylim(0, 4)
for i, (lab, col) in enumerate([("连续", GREEN), ("名义", RED), ("循环", "#8E7BC8"), ("指示", "#E0A050")]):
    xx = 0.15 + (i % 4) * 2.45
    axins.add_patch(FancyBboxPatch((xx, 1.4), 2.1, 1.5, boxstyle="round,pad=0,rounding_size=0.7",
                                   facecolor=col, edgecolor="none", alpha=0.85))
    axins.text(xx + 1.05, 2.15, lab, ha="center", va="center", fontsize=7.2, color="white")

# 小插图：X1 随月份（伪时间）
ax2 = ax.inset_axes([xs[1] / 100 + 0.018, 0.428, CW / 100 - 0.055, 0.105], transform=ax.transAxes)
mm = d.groupby("X4")["X1"].mean()
ax2.plot(mm.index, mm.values / 1e4, color=SLATE, lw=1.4, marker="o", ms=2.6)
ax2.set_xticks([1, 12])
ax2.set_yticks([])
ax2.tick_params(labelsize=6.5, length=1.8, width=0.6)
ax2.set_xlabel("月份", fontsize=7, labelpad=1.2)
ax2.grid(axis="y", ls="--", lw=0.4, color="#DDDDDD")

# 小插图：Y1 直方（重尾）
ax3 = ax.inset_axes([xs[2] / 100 + 0.018, 0.428, CW / 100 - 0.055, 0.105], transform=ax.transAxes)
ax3.hist(d["Y1"], bins=np.logspace(np.log10(500), np.log10(1.2e6), 22),
         color=SLATE, edgecolor="white", linewidth=0.4)
ax3.set_xscale("log")
ax3.set_yticks([])
ax3.tick_params(labelsize=6.5, length=1.8, width=0.6)
ax3.set_xlabel("曝光（对数）", fontsize=7, labelpad=1.2)

# 小插图：X1–X4 散点
ax4 = ax.inset_axes([xs[3] / 100 + 0.018, 0.428, CW / 100 - 0.055, 0.105], transform=ax.transAxes)
rng = np.random.default_rng(20261122)
ax4.scatter(d["X4"] + rng.uniform(-0.22, 0.22, len(d)), d["X1"] / 1e4,
            s=1.6, color=RED, alpha=0.55, linewidths=0)
ax4.set_xticks([1, 12])
ax4.set_yticks([])
ax4.tick_params(labelsize=6.5, length=1.8, width=0.6)
ax4.set_xlabel("月份", fontsize=7, labelpad=1.2)
ax4.grid(axis="y", ls="--", lw=0.4, color="#DDDDDD")

# ---------------- 下游：输出 ----------------
for xc in (11.5, 36.0, 64.0, 88.5):
    arrow((xc, CY - 0.4), (xc, 27.0))
ax.plot([11.5, 88.5], [25.2, 25.2], color="#7A8797", lw=1.1, zorder=4)
arrow((50, 25.2), (50, 18.6))

cylinder(50, 12.0, 44, 11.5, "理解结论：变量角色 · 截面/时序结构 · 共线证据", "")

fig.savefig(Path(__file__).resolve().parent / "图0_数据理解流程_示例.png",
            dpi=400, bbox_inches="tight", facecolor="white")
print("saved")
