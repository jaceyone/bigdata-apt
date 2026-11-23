# -*- coding: utf-8 -*-
"""图5：变换前后分布。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from matplotlib.ticker import FuncFormatter, MaxNLocator, LogLocator

from _common import (CACHE_DIR, save_fig, label_subplots_below,
                     register_data_inputs)

DATA = Path(CACHE_DIR) / "绘图数据_变换.csv"
TAB = Path(CACHE_DIR).parents[0] / "结果" / "表6_变换前后分布特征.csv"
register_data_inputs(DATA, TAB)
df = pd.read_csv(DATA, encoding="utf-8-sig")
tab = pd.read_csv(TAB, encoding="utf-8-sig").set_index("变量")
colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]  # Nature/NPG 色板

y = df["Y1"].values.astype(float)
ly = df["logY"].values.astype(float)
n = len(y)

sk_y = float(tab.loc["Y1", "偏度_变换前"])
ku_y = float(tab.loc["Y1", "峰度_变换前"])
sk_l = float(tab.loc["Y1", "偏度_变换后"])
ku_l = float(tab.loc["Y1", "峰度_变换后"])
y_max = float(tab.loc["Y1", "最大值"])
assert abs(y.max() - y_max) < 1
jb_l = stats.jarque_bera(ly)
assert jb_l.pvalue < 1e-3

fig, axes = plt.subplots(2, 2, figsize=(11.6, 9.0))
fig.subplots_adjust(left=0.085, right=0.975, top=0.945, bottom=0.095,
                    hspace=0.40, wspace=0.26)


def lightgrid(ax, axis="y"):
    """nature 已接管四边框/刻度/次刻度；这里只补一条轻量网格（Q–Q 面板不要网格）。"""
    if axis is None:
        ax.grid(False)
    else:
        ax.grid(True, axis=axis, ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)


wan = FuncFormatter(lambda v, p: (f"{v / 1e4:.0f}万" if v >= 1e4 else f"{v:.0f}"))

# ---------------------------------------------------------------- (a) 原始 Y1
ax = axes[0, 0]
bins = np.linspace(y.min(), y.max(), 39)          # 38 箱，等值宽
counts, edges, _ = ax.hist(y, bins=bins, color=colors[0], edgecolor="black",
                           linewidth=0.4, zorder=3)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_ylim(0.62, 1400)
ax.set_xlim(y.min() * 0.8, y.max() * 1.6)
ax.set_xlabel("曝光总次数 $Y_1$（次，对数刻度）", fontsize=10.5)
ax.set_ylabel("帖子数（条，对数刻度）", fontsize=10.5)
ax.xaxis.set_major_formatter(wan)
ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0,), numticks=10))
ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=10))
first_share = counts[0] / n * 100
# 同一批数据换成旧口径（30 箱等值宽）的首箱，供正文引用
c30, e30 = np.histogram(y, bins=np.linspace(y.min(), y.max(), 31))
share30 = c30[0] / n * 100
ax.text(0.975, 0.975,
        f"偏度 {sk_y:.2f}，峰度 {ku_y:.2f}\n最大 {y_max / 1e4:.1f} 万次\n"
        f"首箱 ≤{edges[1] / 1e4:.1f} 万：{int(counts[0])} 条，{first_share:.1f}%\n"
        f"30 箱 ≤{e30[1] / 1e4:.1f} 万：{int(c30[0])} 条，{share30:.1f}%",
        transform=ax.transAxes, fontsize=7.9, ha="right", va="top", linespacing=1.55,
        color="#333333")
lightgrid(ax)

# ---------------------------------------------------------------- (b) log1p(Y1)
ax = axes[0, 1]
dens, _ = np.histogram(ly, bins=28, density=True)
ax.hist(ly, bins=28, density=True, color=colors[2], edgecolor="black",
        linewidth=0.4, zorder=3)
xs = np.linspace(ly.min() - 0.3, ly.max() + 0.3, 400)
ax.plot(xs, stats.norm.pdf(xs, ly.mean(), ly.std(ddof=1)), color="#333333",
        lw=1.0, ls=(0, (5, 2)), zorder=4)
ax.set_xlabel("$\\log(1+Y_1)$", fontsize=10.5)
ax.set_ylabel("密度", fontsize=10.5)
ax.set_ylim(0, dens.max() * 1.30)
ax.set_xlim(5.8, 14.6)
ax.xaxis.set_major_locator(MaxNLocator(5))
ax.yaxis.set_major_locator(MaxNLocator(5))
ax.text(0.035, 0.955,
        f"偏度 {sk_l:.2f}（原 {sk_y:.2f}）\n峰度 {ku_l:.2f}（原 {ku_y:.2f}）\n"
        f"JB p<0.001",
        transform=ax.transAxes, fontsize=8.5, ha="left", va="top", linespacing=1.6,
        color="#333333")
ax.text(0.975, 0.42, "虚线：正态密度", transform=ax.transAxes,
        fontsize=8.5, ha="right", va="top", color="#555555")
lightgrid(ax)

# ---------------------------------------------------------------- (c) 原始 Q–Q
ax = axes[1, 0]
(osm, osr), (slope, intercept, _) = stats.probplot(y, dist="norm")
ax.scatter(osm, osr, s=10, color=colors[0], edgecolor="none", alpha=0.55, zorder=3)
lx = np.linspace(osm.min(), osm.max(), 300)
lyy = slope * lx + intercept
keep = lyy > 0
ax.plot(lx[keep], lyy[keep], color="black", lw=1.0, ls=(0, (5, 2)), zorder=4)
ax.set_yscale("log")
ax.set_ylim(400, 3.2e6)
ax.set_xlim(osm.min() - 0.3, osm.max() + 0.3)
ax.set_xlabel("理论分位数（标准正态）", fontsize=10.5)
ax.set_ylabel("样本分位数（次，对数刻度）", fontsize=10.5)
ax.yaxis.set_major_formatter(wan)
ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0,), numticks=10))
ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=10))
ax.xaxis.set_major_locator(MaxNLocator(5))
ax.text(0.97, 0.07, "上尾上翘\n参考线：正态拟合", transform=ax.transAxes,
        fontsize=8.5, ha="right", va="bottom", linespacing=1.6, color="#333333")
lightgrid(ax, axis=None)

# ---------------------------------------------------------------- (d) 变换后 Q–Q
ax = axes[1, 1]
(osm2, osr2), (slope2, intercept2, _) = stats.probplot(ly, dist="norm")
ax.scatter(osm2, osr2, s=10, color=colors[2], edgecolor="none", alpha=0.55, zorder=3)
ax.plot(osm2, slope2 * np.asarray(osm2) + intercept2, color="black", lw=1.0,
        ls=(0, (5, 2)), zorder=4)
ax.set_xlabel("理论分位数（标准正态）", fontsize=10.5)
ax.set_ylabel("样本分位数（$\\log(1+Y_1)$ 尺度）", fontsize=10.5)
ax.set_xlim(osm2.min() - 0.3, osm2.max() + 0.3)
ax.set_ylim(ly.min() - 0.6, ly.max() + 0.6)
ax.xaxis.set_major_locator(MaxNLocator(5))
ax.yaxis.set_major_locator(MaxNLocator(5))
ax.text(0.97, 0.07, "主体贴合参考线\nJB p<0.001",
        transform=ax.transAxes, fontsize=8.5, ha="right", va="bottom",
        linespacing=1.6, color="#333333")
lightgrid(ax, axis=None)

label_subplots_below(fig, axes, [
    "a 原始曝光分布（38 箱）",
    "b 对数变换后",
    "c 原始 Q–Q（对数纵轴）",
    "d 变换后 Q–Q",
], fontsize=9.5)
# nature 存图收尾会给多面板自动补 (a)(b)(c)(d)；本图已用下方题注标号，标记为已排布。
axes[0, 0].text(0.0, 1.0, "(a)", transform=axes[0, 0].transAxes, visible=False)

save_fig(fig, "图5_变换前后分布", chart_types=["histogram", "qq"],
         chart_style="modelviz", chart_color_scheme="modelviz")
