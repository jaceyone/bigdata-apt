# -*- coding: utf-8 -*-
"""图8：M2 最终模型的残差诊断四联图（残差–拟合 / 正态 Q–Q / 尺度–位置 / Cook 距离）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _common import (CACHE_DIR, save_fig, label_subplots_below, register_data_inputs)

DATA = Path(CACHE_DIR) / "绘图数据_残差.csv"
TEST = Path(ROOT) / "问题三" / "结果" / "表9_残差诊断检验.csv"
register_data_inputs(DATA, TEST)
d = pd.read_csv(DATA, encoding="utf-8-sig")
test = pd.read_csv(TEST, encoding="utf-8-sig")
colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]  # Nature/NPG 色板、全篇统一


def test_value(model, key):
    """表9 中取指定模型、指定检验的（统计量, p 值）。"""
    row = test[(test["模型"] == model) & (test["检验"].str.contains(key, regex=False))]
    if row.empty:
        raise KeyError(f"表9 缺少检验：{model} / {key}")
    row = row.iloc[0]
    return float(row["统计量"]), float(row["p值"])


def p_text(p):
    """表9 的 p 值：小于 0.00005 才写成 p<0.001，其余给 4 位小数（BP 需显示 0.0005）。"""
    return "p<0.001" if p < 5e-5 else f"p={p:.4f}"


def place_panels(fig, axes, ncols, box, wspace=0.20, hspace=0.30):
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


BP_CHI2, BP_P = test_value("M2 最终模型", "Breusch")
JB_STAT, JB_P = test_value("M2 最终模型", "Jarque")

fit = d["拟合值"].to_numpy(dtype=float)
res = d["残差"].to_numpy(dtype=float)
sres = d["标准化残差"].to_numpy(dtype=float)
scal = d["尺度位置"].to_numpy(dtype=float)
cook = d["Cook距离"].to_numpy(dtype=float)
n = int(len(d))
thr = 4.0 / n                       # 4/n 影响点阈值
sigma = float(res.std())
n_beyond = int((cook > thr).sum())
top = np.argsort(cook)[::-1][:3]    # Cook 最大的 3 个观测
obs_id = np.arange(1, n + 1)

fig, axes = plt.subplots(2, 2, figsize=(12.2, 9.4))
fig.set_layout_engine("none")   # 关掉紧凑布局：边距与行距按固定值摆
place_panels(fig, axes, 2, (0.075, 0.965, 0.095, 0.965), wspace=0.20, hspace=0.30)
pt = dict(s=13, color=colors[0], edgecolor="#222222", linewidth=0.25, alpha=0.5, zorder=3)


def finish(ax, xlabel, ylabel):
    ax.set_xlabel(xlabel, fontsize=11, labelpad=4)
    ax.set_ylabel(ylabel, fontsize=11, labelpad=4)
    ax.grid(True, ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)


# (a) 残差 – 拟合值：0 线 + ±2σ 淡带
ax = axes[0, 0]
ax.axhspan(-2 * sigma, 2 * sigma, color=colors[3], alpha=0.15, lw=0, zorder=1)
ax.scatter(fit, res, **pt)
ax.axhline(0, color="#333333", lw=0.9, ls="--", zorder=4)
ax.set_ylim(-3.3, 5.0)
ax.text(0.975, 0.965, f"BP={BP_CHI2:.1f}，{p_text(BP_P)}\nσ={sigma:.2f}",
        transform=ax.transAxes, ha="right", va="top", fontsize=9.4, linespacing=1.5)
finish(ax, "拟合值（log1p 曝光）", "残差")

# (b) 正态 Q–Q（QQ理论/QQ样本为独立排序的分位数列，序号取标准化残差最大值所在行）
ax = axes[0, 1]
lo, hi = -3.5, 4.6
ax.plot([lo, hi], [lo, hi], color="#333333", lw=1.0, ls="--", zorder=2)
ax.scatter(d["QQ理论"], d["QQ样本"], s=10, color=colors[0], edgecolor="black",
           linewidth=0.2, alpha=0.55, zorder=3)
ax.set_xlim(lo, hi - 1.2)
ax.set_ylim(lo, hi)
jj = int(np.argmax(sres))
ax.annotate(f"{sres[jj]:.2f}（#{jj + 1}）",
            xy=(d["QQ理论"].iloc[-1], d["QQ样本"].iloc[-1]),
            xytext=(-9, 0), textcoords="offset points",
            ha="right", va="center", fontsize=9.0, color="#333333")
ax.text(0.03, 0.965, f"JB={JB_STAT:.1f}，{p_text(JB_P)}",
        transform=ax.transAxes, ha="left", va="top", fontsize=9.4, linespacing=1.5)
finish(ax, "理论分位数（标准正态）", "标准化残差")

# (c) 尺度 – 位置：√|标准化残差| 随拟合值上升
ax = axes[1, 0]
ax.scatter(fit, scal, **pt)
mu_scale = float(scal.mean())
ax.axhline(mu_scale, color="#333333", lw=0.9, ls="--", zorder=2)
bins = pd.qcut(pd.Series(fit), 5, labels=False, duplicates="drop")
bx = pd.Series(fit).groupby(bins).mean().to_numpy()
by = pd.Series(scal).groupby(bins).mean().to_numpy()
ax.plot(bx, by, color=colors[1], lw=1.5, marker="o", ms=4.6, mec="white", mew=0.7, zorder=5)
ax.set_ylim(0, 2.42)
ax.text(0.975, 0.965, "Spearman ρ=0.14",
        transform=ax.transAxes, ha="right", va="top", fontsize=9.4, linespacing=1.5)
finish(ax, "拟合值（log1p 曝光）", "√|标准化残差|")

# (d) Cook 距离 – 观测序号
ax = axes[1, 1]
ax.vlines(obs_id, 0, cook, color="#BFBFBF", lw=0.55, alpha=0.85, zorder=2)
ax.scatter(obs_id, cook, s=8, color=colors[0], edgecolor="none", alpha=0.75, zorder=3)
ax.axhline(thr, color=colors[1], lw=1.0, ls="--", zorder=4)
ax.scatter(obs_id[top], cook[top], s=54, color=colors[1], edgecolor="#222222",
           linewidth=0.5, zorder=6)
for rank, k in enumerate(top):
    xk, yk = float(obs_id[k]), float(cook[k])
    right_side = xk > 0.6 * n
    ax.annotate(f"{int(obs_id[k])}｜{yk:.4f}",
                xy=(xk, yk), xytext=(-10 if right_side else 10, 9), textcoords="offset points",
                ha="right" if right_side else "left", va="bottom", fontsize=9.0,
                color=colors[1], fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=colors[1], lw=0.55,
                                shrinkA=2, shrinkB=3))
ax.set_xlim(-8, n + 10)
ax.set_ylim(-0.0012, 0.0505)
ax.text(0.03, 0.97, f"Cook > 4/n 共 {n_beyond} 个（n={n}）\n4/n = {thr:.4f}",
        transform=ax.transAxes, ha="left", va="top", fontsize=9.4, linespacing=1.5)
finish(ax, "观测序号", "Cook 距离")

# 本图已在下方手写 a–d 题注：占位标号让 nature 的 tidy 不要再自动加一遍
for _ax, _tag in zip(axes.ravel(), "abcd"):
    _ax.text(0, 0, f"({_tag})", visible=False)

label_subplots_below(fig, axes, [
    "a 残差与拟合值",
    "b 标准化残差 Q–Q",
    "c 尺度–位置",
    "d Cook 距离",
], fontsize=10)
save_fig(fig, "图8_残差诊断", chart_types=["residual", "qq", "scatter"],
         chart_style="modelviz", chart_color_scheme="modelviz")
