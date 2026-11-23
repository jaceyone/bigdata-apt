# -*- coding: utf-8 -*-
"""图4：类别结构与缺失。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter

from _common import (CACHE_DIR, save_fig, label_subplots_below,
                     register_data_inputs)

CAT = Path(CACHE_DIR) / "绘图数据_类别.csv"
HOUR = Path(CACHE_DIR) / "绘图数据_小时.csv"
CLEAN = Path(CACHE_DIR).parents[1] / "清洗数据.csv"
register_data_inputs(CAT, HOUR, CLEAN)

cat = pd.read_csv(CAT, encoding="utf-8-sig")
hour = pd.read_csv(HOUR, encoding="utf-8-sig")
clean = pd.read_csv(CLEAN, encoding="utf-8-sig")
colors = ["#3C5488", "#E64B35", "#00A087", "#4DBBD5",
          "#F39B7F", "#8491B4", "#91D1C2", "#B09C85"]  # Nature/NPG 色板
GREY = "#8C8C8C"


def cnt(var, key):
    """从类别表取一个计数。"""
    return int(cat.loc[(cat["变量"] == var) & (cat["类别"] == key), "计数"].iloc[0])


N = int(cat.loc[cat["变量"] == "帖子类型", "计数"].sum())
n_nat_total = cnt("是否付费", "自然")
n_paid_total = cnt("是否付费", "付费")
n_fill = cnt("是否付费", "缺失（填补）")
overall_paid = n_paid_total / N * 100

# 类型 × 付费 交叉计数：类别表里没有，用 清洗数据.csv 现场算（X2c × 付费标记）。
# 该 CSV 中 X7 是众数填补后的 0/1 付费标记（361 自然 / 139 付费），X7_imputed 是
# 第 500 行的填补标记（仅 1 个 1），与 表4 的“众数 0 填补、保留填补标记”一致。
paid = clean["X7"].astype(int)
assert paid.sum() == n_paid_total and int((1 - paid).sum()) == n_nat_total
assert int(clean["X7_imputed"].sum()) == n_fill

typ = ["Photo", "Status", "Link", "Video"]
n_typ = np.array([cnt("帖子类型", k) for k in typ])
n_nat = np.array([int(((clean["X2c"] == k) & (paid == 0)).sum()) for k in typ])
n_paid = np.array([int(((clean["X2c"] == k) & (paid == 1)).sum()) for k in typ])
share = np.where(n_nat + n_paid > 0, n_paid / np.maximum(n_nat + n_paid, 1) * 100, 0.0)
assert (n_nat + n_paid).tolist() == n_typ.tolist()

fig = plt.figure(figsize=(11.8, 9.1))
# 本图 (a) 带窄条列、各格轴标签不对称，交给自动布局会各行算各的高度（(b) 下留白、上下排不齐），
# 故按脚本里显式给的 margins/hspace 出图，两排顶/底边严格对齐。
fig.set_layout_engine("none")
gs = fig.add_gridspec(2, 2, left=0.105, right=0.975, top=0.915, bottom=0.085,
                      hspace=0.44, wspace=0.30)


def lightgrid(ax, axis="y"):
    """nature 已接管四边框/刻度/次刻度；这里只补一条轻量网格。"""
    ax.grid(True, axis=axis, ls="--", lw=0.6, color="#DDDDDD", alpha=0.9)


# ---------------------------------------------------------------- (a) 类型×付费
# 背靠背横向条形：左=自然、右=付费（同一行、同一尺度对齐），右挂“付费占比 %”列
sub = gs[0, 0].subgridspec(1, 2, width_ratios=[2.95, 1.0], wspace=0.10)
axa = fig.add_subplot(sub[0, 0])
axs = fig.add_subplot(sub[0, 1], sharey=axa)

ypos = np.arange(len(typ))
BH = 0.56
axa.barh(ypos, -n_nat, height=BH, color=colors[0], label="自然帖")
axa.barh(ypos, n_paid, height=BH, color=colors[1], label="付费帖")
for y, v in zip(ypos, n_nat):
    axa.text(-v - 10, y, str(v), ha="right", va="center", fontsize=8.5, color="#333333")
for y, v in zip(ypos, n_paid):
    axa.text(v + 10, y, str(v), ha="left", va="center", fontsize=8.5, color="#333333")

axa.set_ylim(len(typ) - 0.45, -1.10)
axa.set_xlim(-430, 345)
axa.set_yticks(ypos)
axa.set_yticklabels([f"{k}（n={v}）" for k, v in zip(typ, n_typ)], fontsize=9.5)
axa.set_xticks([-400, -300, -200, -100, 0, 100, 200, 300])
axa.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{abs(v):.0f}"))
axa.set_xlabel("帖子数（条）", fontsize=10.5)
axa.axvline(0, color="#333333", lw=0.9, zorder=1)
axa.text(-190, -0.62, "自然帖", ha="center", va="bottom", fontsize=9, color=colors[0])
axa.text(175, -0.62, "付费帖", ha="center", va="bottom", fontsize=9, color=colors[1])
lightgrid(axa, axis="x")

axs.barh(ypos, share, height=0.36, color=colors[1])
axs.axvline(overall_paid, color=GREY, lw=0.9, ls=(0, (4, 3)), zorder=0.6)
axs.text(overall_paid + 5.0, -0.86, f"整体 {overall_paid:.1f}%", fontsize=9,
         color="#666666", ha="left", va="center")
for y, v in zip(ypos, share):
    axs.text(v + 3.0, y, f"{v:.1f}%", ha="left", va="center", fontsize=8.5, color="#333333")
axs.set_xlim(0, 100)
axs.set_xticks([0, 25, 50, 75, 100])
# 列头写在窄条上方（此处不写轴标签，避免与列头重复）
axs.text(0.5, 1.035, "付费占比 %", transform=axs.transAxes, ha="center", va="bottom",
         fontsize=9, color="#333333")
axs.tick_params(axis="y", left=False, labelleft=False)
lightgrid(axs, axis="x")

# ---------------------------------------------------------------- (b) 内容主题
axb = fig.add_subplot(gs[0, 1])
th = ["1", "2", "3"]
v3 = np.array([cnt("内容主题", k) for k in th])
axb.bar(np.arange(3), v3, width=0.52, color=[colors[0], colors[5], colors[3]])
for i, v in enumerate(v3):
    axb.text(i, v + 6, f"{v}\n（{v / N * 100:.1f}%）", ha="center", va="bottom",
             fontsize=9, linespacing=1.35, color="#333333")
axb.set_xticks(np.arange(3))
axb.set_xticklabels([f"主题 {k}" for k in th], fontsize=9.5)
axb.set_ylim(0, 305)
axb.set_xlim(-0.62, 2.62)
axb.set_ylabel("帖子数（条）", fontsize=10.5)
axb.yaxis.set_major_locator(MaxNLocator(4, integer=True))
lightgrid(axb)

# ---------------------------------------------------------------- (c) 付费与缺失
axc = fig.add_subplot(gs[1, 0])
lab_p = ["自然", "付费", "缺失"]
v_p = [n_nat_total, n_paid_total, n_fill]
cols_p = [colors[0], colors[1], GREY]
bars = axc.bar(np.arange(3), v_p, width=0.52, color=cols_p)
bars[2].set_hatch("////")
bars[2].set_edgecolor("#5A5A5A")
for i, v in enumerate(v_p):
    if i == 2:
        axc.text(1.95, 8, f"{v}（{v / N * 100:.1f}%）", ha="left", va="bottom",
                 fontsize=9, color="#333333")
    else:
        axc.text(i, v + 8, f"{v}\n（{v / N * 100:.1f}%）", ha="center", va="bottom",
                 fontsize=9, linespacing=1.35, color="#333333")
axc.annotate("缺失 1 条，众数填补", xy=(1.72, 6), xytext=(1.30, 70),
             fontsize=8.5, ha="left", va="center", linespacing=1.5, color="#333333",
             arrowprops=dict(arrowstyle="-|>", mutation_scale=7, color="#555555",
                             lw=0.8, shrinkA=3, shrinkB=2))
axc.set_xticks(np.arange(3))
axc.set_xticklabels(lab_p, fontsize=9.5)
axc.set_ylim(0, 445)
axc.set_xlim(-0.62, 2.62)
axc.set_ylabel("帖子数（条）", fontsize=10.5)
axc.yaxis.set_major_locator(MaxNLocator(4, integer=True))
axc.text(0.97, 0.95, f"付费占 {overall_paid:.1f}%", transform=axc.transAxes,
         fontsize=8.5, ha="right", va="top", color="#444444")
lightgrid(axc)

# ---------------------------------------------------------------- (d) 发布小时
axd = fig.add_subplot(gs[1, 1])
hrs = hour["小时"].values.astype(int)
cts = hour["计数"].values.astype(int)
peak = {3, 10}
bands = [(-0.5, 5.5, "凌晨 0–5"), (5.5, 11.5, "上午 6–11"), (11.5, 23.5, "下午晚间 12–23")]
for i, (lo, hi, _) in enumerate(bands):
    axd.axvspan(lo, hi, color="#F2F2F2" if i % 2 == 0 else "#FAFAFA", zorder=0, lw=0)
axd.bar(hrs, cts, width=0.62,
        color=[colors[1] if h in peak else colors[0] for h in hrs])
for h, c in zip(hrs, cts):
    if h in peak:
        axd.text(h, c + 3, str(c), ha="center", va="bottom", fontsize=9,
                 fontweight="bold", color=colors[1])
axd.set_xlim(-0.5, 23.5)
axd.set_ylim(0, 138)
axd.set_xticks([0, 4, 8, 12, 16, 20, 23])
axd.set_xlabel("发布小时（时）", fontsize=10.5)
axd.set_ylabel("帖子数（条）", fontsize=10.5)
axd.yaxis.set_major_locator(MaxNLocator(4, integer=True))
for i, (lo, hi, name) in enumerate(bands):
    axd.text((lo + hi) / 2.0, 128, name, ha="center", va="bottom", fontsize=8.5,
             color="#666666")
axd.text(0.975, 0.40, "峰值 3 时 105 条、10 时 78 条", transform=axd.transAxes,
         fontsize=8.5, ha="right", va="top", color="#333333")
lightgrid(axd)

# ---------------------------------------------------------------- 子图题注
texts = label_subplots_below(fig, [axa, axb, axc, axd], [
    "a 帖子类型 × 付费",
    "b 内容主题",
    "c 付费标记与缺失",
    "d 发布小时（3/10 时双峰）",
], fontsize=9.5)
pa, ps = axa.get_position(), axs.get_position()
texts[0].set_x((pa.x0 + ps.x1) / 2.0)
# 同排两格的轴标签高度不同，把题注拉到同一基线，免得 a/b、c/d 一高一低
for row in (texts[:2], texts[2:]):
    y_cap = min(t.get_position()[1] for t in row)
    for t in row:
        t.set_position((t.get_position()[0], y_cap))
# nature 存图收尾会给多面板自动补 (a)(b)(c)…；本图已用下方 a/b/c/d 题注标号，
# 且付费占比列不是独立面板，标记为已排布以免编号错位。
axa.text(0.0, 1.0, "(a)", transform=axa.transAxes, visible=False)

save_fig(fig, "图4_类别结构与缺失", chart_types=["bar"],
         chart_style="modelviz", chart_color_scheme="modelviz")
