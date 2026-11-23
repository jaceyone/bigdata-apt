# -*- coding: utf-8 -*-
"""图9：样本内 R² 与 10 折交叉验证 R² 的坡度图，以及 M2 的预测–观测一致性。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D

from _common import (CACHE_DIR, save_fig, top_legend, label_subplots_below,
                     register_data_inputs)

CVF = Path(CACHE_DIR) / "CV结果.csv"
PRED = Path(CACHE_DIR) / "绘图数据_预测.csv"
register_data_inputs(CVF, PRED)
cv = pd.read_csv(CVF, encoding="utf-8-sig")
pred = pd.read_csv(PRED, encoding="utf-8-sig")
colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]  # Nature/NPG 色板、全篇统一

SHORT = {"M0": "M0 均值基线", "M1": "M1 全模型", "M2": "M2 月份 FE（最优）",
         "M3": "M3 仅 X1", "M4": "M4 X1+线性月"}
MCOLOR = {"M0": "#8C8C8C", "M1": colors[1], "M2": colors[0], "M3": colors[2], "M4": colors[3]}

models = cv["模型"].tolist()
r2_in = cv["R²"].to_numpy(dtype=float)
r2_cv = cv["CV_R²均值"].to_numpy(dtype=float)
row = cv.loc[cv["模型"] == "M2"].iloc[0]


def place_panels(fig, axes, ncols, box, wspace=0.26, hspace=0.30):
    """按 L/R/B/T 直接摆面板：nature 的占位布局引擎不认 subplots_adjust。"""
    axes = np.asarray(axes, dtype=object).ravel()
    left, right, bottom, top = box
    nrows = len(axes) // ncols
    w = (right - left) / (ncols + (ncols - 1) * wspace)
    h = (top - bottom) / (nrows + (nrows - 1) * hspace)
    for k, ax in enumerate(axes):
        r, c = divmod(k, ncols)
        ax.set_position([left + c * w * (1 + wspace),
                         top - (r + 1) * h - r * h * hspace, w, h])


fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.8))
fig.set_layout_engine("none")   # 关掉紧凑布局：边距与图例位置按固定值摆
place_panels(fig, axes, 2, (0.075, 0.965, 0.105, 0.885), wspace=0.26)


def finish(ax, xlabel, ylabel):
    ax.set_xlabel(xlabel, fontsize=11, labelpad=5)
    ax.set_ylabel(ylabel, fontsize=11, labelpad=5)
    ax.grid(True, ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)


# (a) 坡度图：样本内 R² → 10 折 CV R²
ax = axes[0]
for i, m in enumerate(models):
    ax.plot([0, 1], [r2_in[i], r2_cv[i]], color=MCOLOR[m],
            lw=2.3 if m == "M2" else 1.5, zorder=5 if m == "M2" else 3,
            marker="o", ms=6.4 if m == "M2" else 5.2, mfc=MCOLOR[m],
            mec="white", mew=0.9)
ax.axhline(0, color="#333333", lw=0.9, zorder=2)


def label_column(x_text, ys, values, color_of, side, gap=0.0118):
    """数值成列排在两侧；重叠时上下错开，并用细引线指回各自的点。"""
    pos = np.array(ys, dtype=float)
    order = np.argsort(pos)
    for k in range(1, len(order)):
        prev, cur = order[k - 1], order[k]
        if pos[cur] - pos[prev] < gap:
            pos[cur] = pos[prev] + gap
    outer = x_text - 0.014 if side == "right" else x_text + 0.014
    inner = 1.03 if side == "right" else -0.03
    ha = "left" if side == "right" else "right"
    for i in range(len(ys)):
        if abs(pos[i] - ys[i]) > 1e-9:
            ax.plot([inner, outer], [ys[i], pos[i]], color=color_of[i],
                    lw=0.55, alpha=0.85, zorder=4)
        ax.text(x_text, pos[i], f"{values[i]:.3f}", ha=ha, va="center",
                fontsize=9.2, color=color_of[i], zorder=6,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))


col_in = [MCOLOR[m] for m in models]
label_column(-0.13, r2_in, r2_in, col_in, "left")
label_column(1.12, r2_cv, r2_cv, col_in, "right")

ax.set_xlim(-0.32, 1.44)
ax.set_ylim(-0.062, 0.242)
ax.set_xticks([0, 1])
ax.set_xticklabels(["样本内 R²", "10 折交叉验证 R²"], fontsize=10)
ax.set_yticks(np.arange(0.0, 0.21, 0.05))
ax.text(0.30, 0.226, f"M2 最优：CV R² = {row['CV_R²均值']:.3f}",
        ha="left", va="center", fontsize=9.4, color=colors[0])
ax.text(0.30, -0.026, f"M0：CV R² = {r2_cv[0]:.3f}",
        ha="left", va="top", fontsize=9.2, color="#666666")
finish(ax, "R² 的计算口径", "R²（log1p 曝光）")

# (b) 预测 – 观测 1:1
ax = axes[1]
obs = pred["观测值"].to_numpy(dtype=float)
prd = pred["交叉验证预测"].to_numpy(dtype=float)
rmse, mae, r2cv = float(row["CV_RMSE"]), float(row["CV_MAE"]), float(row["CV_R²均值"])
lo = float(min(obs.min(), prd.min()))
hi = float(max(obs.max(), prd.max()))
pad = 0.06 * (hi - lo)
lo, hi = lo - pad, hi + pad
ax.fill_between([lo, hi], [lo - rmse, hi - rmse], [lo + rmse, hi + rmse],
                color=colors[0], alpha=0.13, lw=0, zorder=1)
ax.plot([lo, hi], [lo, hi], color="#333333", lw=1.1, ls="--", zorder=2)
ax.scatter(prd, obs, s=9, color=colors[0], edgecolor="none", linewidths=0, alpha=0.55, zorder=3)
ax.set_xlim(lo, hi)
ax.set_ylim(lo, hi)
ax.set_aspect("equal", adjustable="box")
ax.text(0.035, 0.975, f"R² = {r2cv:.3f}\nRMSE = {rmse:.3f}\nMAE = {mae:.3f}",
        transform=ax.transAxes, ha="left", va="top", fontsize=9.6, linespacing=1.6)
ax.text(0.97, 0.04, "淡带 ±RMSE，虚线 1:1",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=9.0, color="#333333")
finish(ax, "交叉验证预测值（log1p 曝光）", "观测值（log1p 曝光）")

handles = [Line2D([], [], color=MCOLOR[m], lw=2.3 if m == "M2" else 1.5,
                  marker="o", ms=5.6, mfc=MCOLOR[m], mec="white", mew=0.9, label=SHORT[m])
           for m in models]
top_legend(fig, axes=[axes[0]], handles=handles, labels=[h.get_label() for h in handles],
           ncol=5, prop=FontProperties(size=9.5), frameon=True, borderpad=0.35,
           bbox_to_anchor=(0.5, 0.975))
# 本图已在下方手写 a/b 题注：占位标号让 nature 的 tidy 不要再自动加一遍
for _ax, _tag in zip(axes, "ab"):
    _ax.text(0, 0, f"({_tag})", visible=False)
label_subplots_below(fig, axes, [
    "a 样本内 R² → 10 折 CV R²",
    f"b M2 预测–观测 1:1（n={len(pred)}）",
], fontsize=10)
save_fig(fig, "图9_预测能力验证", chart_types=["line", "parity"],
         chart_style="modelviz", chart_color_scheme="modelviz")
