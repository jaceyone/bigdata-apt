# -*- coding: utf-8 -*-
"""图0 示例（第二版）：任务分组流程图。

配色照用户给的样例：深蓝标题条 + 浅蓝实心框 + 白底细边框 + 灰蓝虚线任务框 + 黑色细箭头。
内容为本文的技术路线（数据理解 → 清洗编码 → 回归诊断 → 效应解释），数字取自既有结果。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ---- 样例取色 ----
NAVY = "#2C5A85"      # 任务标题条
NAVY_T = "#24506F"
BLUE_FILL = "#A9C8E8"  # 浅蓝实心框
BLUE_EDGE = "#6B9AC4"
WHITE = "#FFFFFF"
BOX_EDGE = "#9FA9B4"   # 白框细边
DASH = "#93A7B8"       # 虚线任务框
INK = "#23303B"

plt.rcParams["font.family"] = ["Times New Roman", "SimSun", "STSong"]
plt.rcParams["axes.unicode_minus"] = False

fig = plt.figure(figsize=(12.8, 6.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 160)
ax.set_ylim(0, 80)
ax.axis("off")


def rect(x, y, w, h, fc, ec, lw=0.9, ls="-", z=2, r=0.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                facecolor=fc, edgecolor=ec, linewidth=lw,
                                linestyle=ls, zorder=z))


def txt(x, y, s, size=9.0, color=INK, weight="normal", ha="center", va="center", z=6):
    ax.text(x, y, s, ha=ha, va=va, fontsize=size, color=color, fontweight=weight, zorder=z)


def box(x, y, w, h, s, light=False, size=9.0):
    if light:
        rect(x, y, w, h, BLUE_FILL, BLUE_EDGE, lw=1.0)
        txt(x + w / 2, y + h / 2, s, size=size)
    else:
        rect(x, y, w, h, WHITE, BOX_EDGE, lw=1.0)
        txt(x + w / 2, y + h / 2, s, size=size)


def head(x, y, w, s):
    rect(x, y, w, 4.2, NAVY, NAVY, lw=0, r=0.5, z=3)
    txt(x + w / 2, y + 2.1, s, size=9.6, color="white", weight="bold", z=7)


def arrow(p0, p1, lw=1.0, color="#2B333B"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=10,
                                 linewidth=lw, color=color, shrinkA=0, shrinkB=0, zorder=5))


# ================= 左侧：数据来源 =================
box(3, 57, 15, 9, "给定数据", light=True)
box(3, 31, 15, 9, "帖级截面样本", light=True)
txt(10.5, 33.6, "", size=8)
arrow((10.5, 56.6), (10.5, 40.6))
txt(10.5, 35.2, "500 条 × 8 列", size=8.0, color="#3A4A58")
arrow((18.6, 35.5), (25.2, 35.5))

# ================= 任务 1 =================
rect(25, 8, 41, 68, "none", DASH, lw=1.0, ls=(0, (4, 3)), z=1)
head(31, 70, 28, "任务 1  数据理解")
box(35, 57, 22, 7, "读取原始数据 · 识别类型")
box(33, 45, 11.5, 7, "连续 2", light=False)
box(46.5, 45, 11.5, 7, "名义 2", light=False)
box(33, 36.5, 11.5, 7, "循环 3", light=False)
box(46.5, 36.5, 11.5, 7, "指示 1", light=False)
box(35, 24, 22, 7, "判定粒度与结构：一行 = 一条帖子")
box(35, 12.5, 22, 7, "输出变量字典与角色", light=True)
arrow((46, 56.6), (46, 52.6))
arrow((39.2, 52.0), (39.2, 45.5) if False else (39.2, 44.2))
arrow((52.8, 52.0), (52.8, 44.2))
arrow((39.2, 44.2), (39.2, 36.9))
arrow((39.2, 36.1), (39.2, 31.4))
arrow((52.8, 36.1), (52.8, 31.4))
arrow((46, 23.6), (46, 20.0))

# 侧支：因果角色 → 与主链并列
box(58.5, 45, 6.5, 18, "", light=False)
ax.text(61.75, 54, "因果角色\n划分", ha="center", va="center", fontsize=8.6, zorder=6)
arrow((57.0, 60.5), (58.3, 58.0))

# ================= 任务 2 =================
rect(69, 22, 33, 54, "none", DASH, lw=1.0, ls=(0, (4, 3)), z=1)
head(73, 70, 25, "任务 2  清洗与编码")
box(76, 57, 19, 7, "缺失检查：仅 1 条")
box(76, 45, 19, 7, "众数填补 · 独热编码")
box(72.5, 34, 11, 7, "X7 → 0", light=False)
box(84.5, 34, 11, 7, "X2/X3 哑变量", light=False)
box(76, 23.5, 19, 7, "log1p：偏度 0.73", light=True)
arrow((85.5, 56.6), (85.5, 52.6))
arrow((78, 52.0), (78, 41.4))
arrow((93, 52.0), (93, 41.4))
arrow((85.5, 33.6), (85.5, 31.0))

# ================= 任务 3 / 4 =================
rect(105, 40, 35, 36, "none", DASH, lw=1.0, ls=(0, (4, 3)), z=1)
head(109, 70, 27, "任务 3  回归与诊断")
box(112, 57, 21, 7, "OLS + HC3 稳健标准误")
box(108, 44, 14, 7, "共线 / 残差检验", light=False)
box(123, 44, 14, 7, "10 折交叉验证", light=False)
arrow((122.5, 56.6), (122.5, 51.4))

rect(105, 8, 35, 30, "none", DASH, lw=1.0, ls=(0, (4, 3)), z=1)
head(109, 33, 27, "任务 4  效应解释与检验")
box(112, 21, 21, 7, "付费 +40.1% · 视频 ×4.90")
box(108, 10.5, 14, 7, "主题 3 近零", light=False)
box(123, 10.5, 14, 7, "六设定稳健", light=False)

# 任务间串行箭头
arrow((66.2, 35.5), (68.8, 35.5))
arrow((102.2, 49.0), (104.8, 49.0))

# ================= 右侧：目标 =================
box(144, 39, 14, 10, "结论与\n行动建议", light=True)
arrow((140.2, 49.0), (143.8, 44.5))
arrow((140.2, 22.0), (143.8, 40.0))

fig.savefig(Path(__file__).resolve().parent / "图0_技术路线_示例2.png",
            dpi=400, bbox_inches="tight", facecolor="white")
print("saved")
