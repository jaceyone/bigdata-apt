# -*- coding: utf-8 -*-
"""图15：模型绩效评分表（表格式热力 + 单标尺图例，nature 风格）。

视觉语言与图6/图11/图16 对齐：Times + 宋体、字号 9.5 / 8.5 两档、线宽 0.6–0.9、
只用 NPG 深蓝 #3C5488 的单一「差→优」明度梯度（浅灰 #F2F4F7 → 深蓝 #3C5488），
组底条与标尺轨道用与图16 一致的浅灰，不再出现棕/粉/淡绿彩色底。

行＝5 个模型，按 CV_R² 均值降序；七列指标全部列内归一为「越优越深」
（↑ 类越大越深，↓ 类越小越深），列内最优值加黑色描边。
数值全部取自 问题三/结果/表10_模型比较与交叉验证.csv。
得分口径：CV R² 均值 − 0.1 × CV R² 标准差（折间波动已并入得分列）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格（必须在 _common 之前）

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import colors as mcolors  # noqa: E402
from matplotlib.patches import Rectangle, FancyBboxPatch  # noqa: E402

# 本文档统一 400 dpi（nature_style 默认取 500，作为下限会覆盖脚本实参）
nature_style.ensure()._ACTIVE_PREFS["dpi"] = 400

PROB = Path(__file__).resolve().parents[1]
OUT = PROB / "结果"
CSV = OUT / "表10_模型比较与交叉验证.csv"
if not CSV.is_file():
    raise FileNotFoundError(str(CSV))
OUT.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ 数据
tab = pd.read_csv(CSV, encoding="utf-8-sig")
tab["名称"] = tab["设定"].str.replace(r"^M\d\s*", "", regex=True).str.strip()
tab["得分"] = tab["CV_R²均值"] - 0.1 * tab["CV_R²标准差"]
tab = tab.sort_values(["CV_R²均值", "CV_RMSE"], ascending=[False, True]).reset_index(drop=True)

# 列定义：(表头, 副标, 字段, 方向(1=越大越优 / -1=越小越优))
COLS = [
    ("RMSE", "残差标准误", "残差标准误", -1),
    ("MAE", "CV_MAE", "CV_MAE", -1),
    ("R²", "全样本", "R²", 1),
    ("调整R²", "全样本", "调整R²", 1),
    ("CV R²", "均值", "CV_R²均值", 1),
    ("CV RMSE", "折间", "CV_RMSE", -1),
    ("得分", "均值−0.1×波动", "得分", 1),
]

# 全表单一明度梯度（NPG #3C5488 ← 浅灰 #F2F4F7），不混搭色相
BLUE = "#3C5488"
RAMP_LO, RAMP_HI = "#F2F4F7", BLUE

FS_BIG, FS_MAIN, FS_SUB = 11.0, 9.5, 8.5

C_INK, C_SUB, C_FAINT = "#26282D", "#5A6068", "#8A9098"
C_GROUP_BG, C_GROUP_TX = "#E4E9EF", "#4F5661"
C_HEAD_BG, C_HEAD_TX = "#EDF0F4", "#4F5661"
C_RULE, C_ROW_RULE = "#C9D2DC", "#D5DBE3"
C_FRAME = "#9FA9B4"
C_BEST_BADGE, C_BEST_TX = BLUE, "white"
C_BADGE_BG, C_BADGE_TX = "#EDF0F4", "#5A6068"


def mix(c1, c2, t):
    a = np.array(mcolors.to_rgb(c1))
    b = np.array(mcolors.to_rgb(c2))
    return mcolors.to_hex(a + (b - a) * float(np.clip(t, 0, 1)))


def ink_on(bg):
    r, g, b = mcolors.to_rgb(bg)
    return "white" if (0.299 * r + 0.587 * g + 0.114 * b) < 0.58 else "#1E2025"


# ------------------------------------------------------------------ 版面（英寸）
W, H = 9.60, 4.45
TOPM, GBAR_H, HEAD_H, GAP = 0.15, 0.24, 0.36, 0.05
PITCH, CELL_H = 0.520, 0.420

BADGE_X0, BADGE_X1 = 0.10, 0.54
X_ID, X_NAME = 0.64, 0.98
COL_X = [(2.66, 3.40), (3.47, 4.21), (4.34, 5.08), (5.15, 5.89),
         (6.02, 6.76), (6.83, 7.57), (7.70, 8.44)]
NOTE_X0, NOTE_X1 = 8.58, 9.50
GROUP_BARS = [(2.60, 4.27), (4.28, 5.95), (5.96, 7.63), (7.64, 8.50)]
GROUP_NAMES = ["精度", "拟合优度", "交叉验证", "综合"]

gbar_y0 = H - TOPM - GBAR_H
head_y0 = gbar_y0 - HEAD_H
rows_top = head_y0 - GAP

fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect("equal")
ax.axis("off")


def T(x, y, s, size=FS_MAIN, color=C_INK, ha="left", va="center", weight="normal",
      family=None, zorder=6):
    kw = {"family": family} if family is not None else {}
    return ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
                   fontweight=weight, zorder=zorder, **kw)


def NUM(x, y, s, size=FS_MAIN, color=C_INK, weight="normal"):
    return T(x, y, s, size=size, color=color, ha="right",
             family="Times New Roman", weight=weight)


# ------------------------------------------------------------------ 组名底条（浅灰，与图16 一致）
for k, ((gx0, gx1), gname) in enumerate(zip(GROUP_BARS, GROUP_NAMES)):
    ax.add_patch(Rectangle((gx0, gbar_y0), gx1 - gx0 - (0.03 if k < 3 else 0.0), GBAR_H,
                           facecolor=C_GROUP_BG, edgecolor="none", zorder=1))
    T((gx0 + gx1) / 2.0 - (0.015 if k < 3 else 0.0), gbar_y0 + GBAR_H / 2.0, gname,
      size=FS_BIG, color=C_GROUP_TX, ha="center")

# ------------------------------------------------------------------ 表头
ax.add_patch(Rectangle((BADGE_X0, head_y0), NOTE_X1 - BADGE_X0, HEAD_H,
                       facecolor=C_HEAD_BG, edgecolor="none", zorder=1))
ax.plot([BADGE_X0, NOTE_X1], [head_y0 + HEAD_H, head_y0 + HEAD_H],
        color=C_FRAME, lw=0.8, zorder=2)
hy = head_y0 + HEAD_H / 2.0
T((BADGE_X0 + BADGE_X1) / 2.0, hy, "名次", size=FS_MAIN, color=C_HEAD_TX, ha="center")
T(X_ID, hy, "模型", size=FS_MAIN, color=C_HEAD_TX)
for (cx0, cx1), (main, sub, _f, direction) in zip(COL_X, COLS):
    arrow = "↑" if direction > 0 else "↓"
    T(cx1 - 0.06, hy + 0.078, f"{main} {arrow}", size=FS_MAIN, color=C_HEAD_TX, ha="right")
    T(cx1 - 0.06, hy - 0.088, sub, size=FS_SUB, color=C_FAINT, ha="right")
T(NOTE_X0, hy, "缺失/备注", size=FS_MAIN, color=C_HEAD_TX)
ax.plot([BADGE_X0, NOTE_X1], [head_y0, head_y0], color=C_FRAME, lw=0.8, zorder=2)
# 整表外框：一条 0.8pt #9FA9B4 细线（与图16 外框同一档），四周留 0.06 英寸内边
_FP = 0.06
ax.add_patch(Rectangle((BADGE_X0 - _FP, rows_top - len(tab) * PITCH - _FP),
                       NOTE_X1 - BADGE_X0 + 2 * _FP,
                       (gbar_y0 + GBAR_H) - (rows_top - len(tab) * PITCH) + 2 * _FP,
                       fill=False, edgecolor=C_FRAME, lw=0.8, zorder=5))

# ------------------------------------------------------------------ 列内归一（统一为「越优越深」）与列内最优
values = {col[2]: tab[col[2]].to_numpy(dtype=float) for col in COLS}
best = {}
for _main, _sub, field, direction in COLS:
    vals = values[field]
    best[field] = float(vals.min() if direction < 0 else vals.max())

# ------------------------------------------------------------------ 逐行
NOTE_TEXT = {"M0": "", "M1": "参数 27", "M2": "最终模型", "M3": "无月份", "M4": "线性月份"}

for i, row in tab.iterrows():
    y_top = rows_top - i * PITCH
    y_bot = y_top - PITCH
    yc = y_top - PITCH / 2.0

    badge = "最优" if i == 0 else str(i + 1)
    bg = C_BEST_BADGE if i == 0 else C_BADGE_BG
    ax.add_patch(Rectangle((BADGE_X0, yc - 0.125), BADGE_X1 - BADGE_X0, 0.250,
                           linewidth=0, facecolor=bg, edgecolor="none", zorder=2))
    T((BADGE_X0 + BADGE_X1) / 2.0, yc, badge,
      size=FS_SUB, color=C_BEST_TX if i == 0 else C_BADGE_TX,
      ha="center", weight="bold" if i == 0 else "normal")

    T(X_ID, yc, row["模型"], size=FS_BIG, weight="bold")
    T(X_NAME, yc, row["名称"], size=FS_SUB, color=C_SUB)

    for (cx0, cx1), (main, sub, field, direction) in zip(COL_X, COLS):
        vals = values[field]
        lo, hi = float(vals.min()), float(vals.max())
        v = float(row[field])
        norm = 0.5 if hi == lo else (v - lo) / (hi - lo)
        # 统一「越优越深」：↑ 类直接取归一值，↓ 类翻转到 1-归一值
        t = norm if direction > 0 else 1.0 - norm
        fill = mix(RAMP_LO, RAMP_HI, t)
        ax.add_patch(Rectangle((cx0, yc - CELL_H / 2.0), cx1 - cx0, CELL_H,
                               facecolor=fill, edgecolor="none", zorder=2))
        NUM(cx1 - 0.07, yc, f"{v:.4f}", color=ink_on(fill))
        if abs(v - best[field]) < 5e-9:
            ax.add_patch(Rectangle((cx0, yc - CELL_H / 2.0), cx1 - cx0, CELL_H,
                                   fill=False, edgecolor="#111111", lw=0.9, zorder=4))

    mid = row["模型"]
    if NOTE_TEXT.get(mid):
        T(NOTE_X0 + 0.05, yc, NOTE_TEXT[mid], size=FS_SUB, color=C_SUB)
    else:
        T((NOTE_X0 + NOTE_X1) / 2.0, yc, "—", size=FS_MAIN, color=C_FAINT,
          ha="center", family="Times New Roman")

    if i < len(tab) - 1:
        ax.plot([BADGE_X0, NOTE_X1], [y_bot, y_bot], color=C_ROW_RULE, lw=0.8, zorder=1)

rows_bottom = rows_top - len(tab) * PITCH
ax.plot([BADGE_X0, NOTE_X1], [rows_bottom, rows_bottom], color=C_RULE, lw=0.8, zorder=1)

# ------------------------------------------------------------------ 单一明度标尺图例
LEG_X0 = 0.10
LEG_TITLE_Y = rows_bottom - 0.30
LEG_BAR_Y = rows_bottom - 0.50
LEG_SUB_Y = rows_bottom - 0.655
T(LEG_X0, LEG_TITLE_Y, "列内归一：越优越深", size=FS_MAIN, color=C_SUB)
n_seg = 200
for s in range(n_seg):
    ax.add_patch(Rectangle((LEG_X0 + 2.60 * s / n_seg, LEG_BAR_Y), 2.60 / n_seg + 0.002,
                           0.140, linewidth=0,
                           facecolor=mix(RAMP_LO, RAMP_HI, s / (n_seg - 1)),
                           edgecolor="none", zorder=3))
ax.add_patch(Rectangle((LEG_X0, LEG_BAR_Y), 2.60, 0.140, fill=False,
                       edgecolor=C_RULE, lw=0.8, zorder=4))
T(LEG_X0, LEG_SUB_Y, "差", size=FS_SUB, color=C_FAINT, ha="left")
T(LEG_X0 + 2.60, LEG_SUB_Y, "优", size=FS_SUB, color=C_FAINT, ha="right")
T(LEG_X0 + 3.05, LEG_TITLE_Y - 0.02, "黑框 = 该列列内最优；↑ 越大越优　↓ 越小越优",
  size=FS_SUB, color=C_FAINT)

ax.set_xlim(0, W)
ax.set_ylim(0, H)

png = OUT / "图15_模型绩效评分表.png"
fig.savefig(png, dpi=400, bbox_inches="tight", pad_inches=0.05, facecolor="white")
plt.close(fig)
print("已保存:", png)
