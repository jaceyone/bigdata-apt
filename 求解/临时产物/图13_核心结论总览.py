# -*- coding: utf-8 -*-
"""图13：核心结论总览——2×2 子面板（nature 四边细框 + 内向刻度），数字取自结果表。

与图6/图11/图16 同一套模板：Times + 宋体、字号 11 / 9.5 / 8.5 三档、线宽 0.8–1.0pt、
白底细框、只用 NPG 深蓝 #3C5488 与红 #E64B35（余为中性灰）。
每个子面板 = 一块 matplotlib 坐标系（四边细框 + 内向刻度），面板头部（(a) 标号、
标题、大数字、两行结论）用 ax.text 写在面板左上、框线之外；没有圆角卡片、没有浅灰底块。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import nature_style  # noqa: F401  # 套用 nature 风格

# 本文档统一 400 dpi（nature_style 默认取 500，作为下限会覆盖脚本实参）
nature_style.ensure()._ACTIVE_PREFS["dpi"] = 400

import pandas as pd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
SOLVE = HERE.parent

BLUE = "#3C5488"
RED = "#E64B35"
INK = "#26282D"
SUB = "#5A6068"
FAINT = "#9FA9B4"
HAIR = "#C9D2DC"
BLOCK = "#E8EBEF"

FS_BIG, FS_MAIN, FS_SUB = 11.0, 9.5, 8.5
LW = 0.8

plt.rcParams["axes.unicode_minus"] = False

paid = pd.read_csv(SOLVE / "问题四" / "结果" / "表13_付费效应测算.csv", encoding="utf-8-sig")
type_df = pd.read_csv(SOLVE / "问题四" / "结果" / "表14_内容类型效应与两两对比.csv", encoding="utf-8-sig")
shap = pd.read_csv(SOLVE / "问题三" / "结果" / "表12_Shapley方差分解.csv", encoding="utf-8-sig")
model = pd.read_csv(SOLVE / "问题三" / "结果" / "表10_模型比较与交叉验证.csv", encoding="utf-8-sig")
vif = pd.read_csv(SOLVE / "问题三" / "结果" / "表8_共线性诊断.csv", encoding="utf-8-sig")


def row_of(frame, column, key):
    hit = frame[frame[column].astype(str).str.contains(key, regex=False)]
    if hit.empty:
        raise KeyError(key)
    return hit.iloc[0]


# 付费效应（表13）
pct = row_of(paid, "指标", "exp(β)")
nat = row_of(paid, "指标", "自然帖子预测曝光")
pro = row_of(paid, "指标", "付费帖子预测曝光")
diff = row_of(paid, "指标", "差值（次）")
paid_pct = float(pct["估计值"])            # 40.1325
paid_lo, paid_hi = float(pct["95%CI下限"]), float(pct["95%CI上限"])
nat_est, nat_lo, nat_hi = float(nat["估计值"]), float(nat["95%CI下限"]), float(nat["95%CI上限"])
pro_est, pro_lo, pro_hi = float(pro["估计值"]), float(pro["95%CI下限"]), float(pro["95%CI上限"])
paid_diff = float(diff["估计值"])           # 16142.2328

# 类型效应（表14）
video = row_of(type_df, "对比", "Video vs Photo")
status = row_of(type_df, "对比", "Status vs Photo")
link = row_of(type_df, "对比", "Link vs Photo")
video_mul, video_lo, video_hi = (float(video["倍数"]), float(video["倍数CI下限"]),
                                 float(video["倍数CI上限"]))
status_mul = float(status["倍数"])
link_mul = float(link["倍数"])

# 解释力（表10 R² / 表12 未解释份额）
r2 = float(row_of(model, "设定", "M2")["R²"])                 # 0.2068
unexplained = float(row_of(shap, "变量组", "未解释方差")["占总方差"])  # 0.793081
explained = 1 - unexplained

# 共线性（表8）
vif_m1 = float(row_of(vif, "诊断项", "M1 最大 VIF")["数值"])   # 142.9938
vif_m2 = float(row_of(vif, "诊断项", "M2 最大 VIF")["数值"])   # 3.2320

# ------------------------------------------------------------------ 画布与 2×2 子图网格
W, H = 9.60, 7.90
LM, RM, BM = 0.80, 0.18, 0.62       # 页边（英寸）
HEAD_H, GAPY, TOPM = 1.15, 1.75, 0.10   # 面板头高 / 行间距 / 顶边

fig = plt.figure(figsize=(W, H), facecolor="white")
fig.set_layout_engine("none")      # 面板头与微图按绝对坐标定位，别让约束布局重排
GAPX = 0.86
AX_H = (H - TOPM - HEAD_H - GAPY - BM) / 2.0
gs = fig.add_gridspec(
    2, 2,
    left=LM / W, right=1 - RM / W,
    top=1 - (TOPM + HEAD_H) / H, bottom=BM / H,
    wspace=GAPX / ((W - LM - RM - GAPX) / 2.0),
    hspace=GAPY / AX_H,
)
AX = {(0, 0): fig.add_subplot(gs[0, 0]), (0, 1): fig.add_subplot(gs[0, 1]),
      (1, 0): fig.add_subplot(gs[1, 0]), (1, 1): fig.add_subplot(gs[1, 1])}


def panel(ax):
    """nature 四边细框 + 向内刻度（与图6/图11/图16 同款）。"""
    ax.set_facecolor("none")
    for side in ("left", "bottom", "top", "right"):
        ax.spines[side].set_visible(True)
        ax.spines[side].set_color("#3A3F47")
        ax.spines[side].set_linewidth(LW)
    ax.tick_params(which="both", direction="in", top=True, right=True,
                   width=LW, length=3.0, color="#3A3F47", labelsize=FS_SUB, pad=2.5)
    ax.grid(False)
    return ax


def head(ax, tag, title, value_parts, text):
    """面板头部（左上，框线之外）：(a) 标号 + 标题、大数字、两行结论。"""
    h_in = ax.get_position().height * fig.get_figheight()
    w_in = ax.get_position().width * fig.get_figwidth()
    ax.text(0.0, 1 + 1.00 / h_in, tag, transform=ax.transAxes, ha="left", va="top",
            fontsize=FS_MAIN, fontweight="bold", color=INK)
    ax.text(0.056, 1 + 1.00 / h_in, title, transform=ax.transAxes, ha="left", va="top",
            fontsize=FS_MAIN, color=SUB)
    x = 0.0
    for s, color, family in value_parts:
        t = ax.text(x, 1 + 0.66 / h_in, s, transform=ax.transAxes, ha="left", va="top",
                    fontsize=FS_BIG, fontweight="bold", color=color, family=family)
        bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
        x += bb.width / (fig.dpi * w_in) + 0.012
    ax.text(0.0, 1 + 0.42 / h_in, text, transform=ax.transAxes, ha="left", va="top",
            fontsize=FS_MAIN, color=SUB, linespacing=1.55)


fig.canvas.draw()

# ── (a) 付费投放：两根柱 + 95% CI ──
ax = panel(AX[(0, 0)])
head(ax, "(a)", "付费投放的净效应",
     [(f"+{paid_pct:.1f}%", BLUE, "Times New Roman")],
     f"代表性画像上，付费帖子比自然帖子多 {paid_diff:,.0f} 次曝光；\n"
     f"95% 区间 {paid_lo:.1f}%–{paid_hi:.1f}%，方向稳定为正。")
vals = [nat_est, pro_est]
err = [[nat_est - nat_lo, pro_est - pro_lo], [nat_hi - nat_est, pro_hi - pro_est]]
ymax = max(nat_hi, pro_hi)
ax.bar([0, 1], vals, width=0.42, color=[HAIR, BLUE], edgecolor="none", zorder=3)
ax.errorbar([0, 1], vals, yerr=err, fmt="none", ecolor="#5A6068",
            elinewidth=LW, capsize=3.0, capthick=LW, zorder=4)
for x, v, hi in zip([0, 1], vals, [nat_hi, pro_hi]):
    ax.text(x, hi + 0.05 * ymax, f"{v/10000:.2f}万", ha="center", va="bottom",
            fontsize=FS_SUB, color=SUB)
ax.set_xticks([0, 1])
ax.set_xticklabels(["自然帖子", "付费帖子"], fontsize=FS_MAIN)
ax.set_xlim(-0.62, 1.62)
ax.set_ylim(0, ymax * 1.16)
ax.set_yticks([])
ax.set_ylabel("调整预测曝光（次）", fontsize=FS_MAIN, labelpad=5)

# ── (b) 内容类型：Video / Status / Link 相对 Photo 的倍数 ──
ax = panel(AX[(0, 1)])
head(ax, "(b)", "视频的曝光倍数",
     [(f"×{video_mul:.2f}", BLUE, "Times New Roman")],
     f"Video 相对 Photo 的曝光倍数为 {video_mul:.2f}，"
     f"区间 {video_lo:.2f}–{video_hi:.2f}；\n"
     f"样本仅 7 条，方向明确但幅度不确定。")
rows = [("Link", link_mul, float(link["倍数CI下限"]),
         float(link["倍数CI上限"]), BLUE),
        ("Status", status_mul, float(status["倍数CI下限"]),
         float(status["倍数CI上限"]), BLUE),
        ("Video", video_mul, video_lo, video_hi, RED)]
ax.axvline(1, color=FAINT, ls=(0, (4, 2.4)), lw=LW, zorder=1)
for y, (name, est, lo, hi, col) in enumerate(rows):
    ax.errorbar(est, y, xerr=[[est - lo], [hi - est]], fmt="o", color=col,
                ecolor=col, elinewidth=LW, capsize=2.6, capthick=LW,
                markersize=4.6, markeredgecolor="white", markeredgewidth=0.7,
                zorder=4)
    ax.text(hi * 1.10, y, f"×{est:.2f}", va="center", ha="left",
            fontsize=FS_SUB, color=col)
ax.set_yticks(range(3))
ax.set_yticklabels([r[0] for r in rows])
ax.set_xscale("log")
ax.set_xlim(0.55, 26)
ax.set_ylim(-0.55, 2.55)
ax.set_xticks([1, 2, 5, 10])
ax.set_xticklabels(["1", "2", "5", "10"])
ax.set_xlabel("相对 Photo 的曝光倍数（对数刻度）", fontsize=FS_MAIN, labelpad=5)

# ── (c) 解释力：100% 水平堆叠条 ──
ax = panel(AX[(1, 0)])
head(ax, "(c)", "模型解释力有限",
     [(f"R² = {r2:.3f}", BLUE, "Times New Roman")],
     f"类型、主题、月份、星期、时段与付费合计解释 {explained*100:.1f}%，\n"
     f"仍有 {unexplained*100:.1f}% 的方差未被解释，个体差异占主导。")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.barh(0.50, explained, left=0.0, height=0.62, color=BLUE,
        edgecolor="white", linewidth=LW, zorder=3)
ax.barh(0.50, unexplained, left=explained, height=0.62, color=BLOCK,
        edgecolor="white", linewidth=LW, zorder=3)
ax.text(explained / 2, 0.50, f"{explained*100:.1f}%", ha="center", va="center",
        fontsize=FS_SUB, fontweight="bold", color="white", zorder=4)
ax.text(explained + unexplained / 2, 0.50, f"未解释 {unexplained*100:.1f}%",
        ha="center", va="center", fontsize=FS_SUB, color=SUB, zorder=4)
ax.set_yticks([])
ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_xticklabels(["0", "25", "50", "75", "100%"])
ax.set_xlabel("方差占比（%）", fontsize=FS_MAIN, labelpad=5)

# ── (d) 共线性：哑铃（对数 VIF） ──
ax = panel(AX[(1, 1)])
head(ax, "(d)", "共线性诊断",
     [("143.0", RED, "Times New Roman"),
      ("→", SUB, None),
      (f"{vif_m2:.2f}", BLUE, "Times New Roman")],
     f"全模型 M1 的最大 VIF 为 {vif_m1:.1f}，剔除 log X1 后降至 {vif_m2:.2f}；\n"
     f"低于阈值 5，共线解除、系数可识别。")
ax.axvline(5, color=FAINT, ls=(0, (4, 2.4)), lw=LW, zorder=1)
ax.axvline(10, color=RED, ls=(0, (4, 2.4)), lw=LW, zorder=1)
ax.plot([vif_m2, vif_m1], [0, 1], color=HAIR, lw=1.0, zorder=2,
        solid_capstyle="round")
ax.scatter([vif_m1], [1], s=46, color=RED, edgecolors="white", linewidths=0.7, zorder=4)
ax.scatter([vif_m2], [0], s=46, color=BLUE, edgecolors="white", linewidths=0.7, zorder=4)
ax.text(vif_m1 / 1.24, 1.16, f"{vif_m1:.1f}", ha="center", va="bottom",
        fontsize=FS_SUB, color=SUB)
ax.text(vif_m2 * 1.24, -0.16, f"{vif_m2:.2f}", ha="center", va="top",
        fontsize=FS_SUB, color=SUB)
ax.text(5, 1.44, "阈值 5", ha="center", va="top", fontsize=FS_SUB, color=SUB,
        bbox=dict(facecolor="white", edgecolor="none", pad=1.2))
ax.text(11, 1.44, "阈值 10", ha="left", va="top", fontsize=FS_SUB, color=RED,
        bbox=dict(facecolor="white", edgecolor="none", pad=1.2))
ax.set_yticks([0, 1])
ax.set_yticklabels(["M2 最终", "M1 全模型"])
ax.set_xscale("log")
ax.set_xlim(2, 320)
ax.set_ylim(-0.55, 1.55)
ax.set_xticks([3, 5, 10, 30, 100])
ax.set_xticklabels(["3", "5", "10", "30", "100"])
ax.set_xlabel("最大方差膨胀因子 VIF（对数刻度）", fontsize=FS_MAIN, labelpad=5)

out = HERE / "图13_核心结论总览.png"
fig.savefig(out, dpi=400, bbox_inches="tight", facecolor="white")
print(out)
