# -*- coding: utf-8 -*-
"""图14：变量字典与缺失检查（纯表格，nature 风格）。

与图6/图11/图16 同一套模板：Times + 宋体、字号 11 / 9.5 / 8.5 三档、线宽 0.8pt、
白底、表头浅灰 #EDF0F4 + 上下两条 0.8pt 细线；组间一条 0.8pt 线，行间不画线。
「类型」列用深蓝同色不同深度的小色标（100 / 70 / 45 / 25%），不是彩色胶囊、不圆角。

数据取自 问题一/结果/表1_变量字典.csv；派生变量 lnX1、lnY 的类别数与缺失数由
求解/清洗数据.csv 实算，无任何手填数字。图内只保留短标签，无说明性长句。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 套用 nature 风格（必须在 _common 之前）

# 本文档统一 400 dpi（nature_style 默认取 500，作为下限会覆盖脚本实参）
nature_style.ensure()._ACTIVE_PREFS["dpi"] = 400

import pandas as pd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import colors as mcolors  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

PROB = Path(__file__).resolve().parents[1]
OUT = PROB / "结果"
DICT_CSV = OUT / "表1_变量字典.csv"
CLEAN_CSV = ROOT / "清洗数据.csv"
for _p in (DICT_CSV, CLEAN_CSV):
    if not _p.is_file():
        raise FileNotFoundError(str(_p))
OUT.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ 数据
dic = pd.read_csv(DICT_CSV, encoding="utf-8-sig")
clean = pd.read_csv(CLEAN_CSV, encoding="utf-8-sig")

# 类型色标：深蓝 #3C5488 同色不同深度（连续 100% → 指示 25%），不用彩色
BLUE = "#3C5488"
PILL_ALPHA = {"连续": 1.00, "名义": 0.70, "循环": 0.45, "二元": 0.25}
KIND_TEXT = {"连续": "连续", "名义": "名义", "循环": "循环", "二元": "指示"}


def mix(c1, c2, t):
    a = mcolors.to_rgb(c1)
    b = mcolors.to_rgb(c2)
    return mcolors.to_hex([x + (y - x) * float(t) for x, y in zip(a, b)])


SWATCH = {k: mix(BLUE, "#FFFFFF", 1.0 - a) for k, a in PILL_ALPHA.items()}


def kind_of(text):
    text = str(text)
    if text.startswith("连续"):
        return "连续"
    if text.startswith("名义"):
        return "名义"
    if "周期" in text or "有序" in text:
        return "循环"
    if "二元" in text:
        return "二元"
    raise ValueError("未知数据类型：" + text)


rows = []
for _, r in dic.iterrows():
    var = str(r["变量"]).strip()
    is_out = var.startswith("Y")
    rows.append(dict(
        var=var,
        label=str(r["含义"]).strip(),
        kind=kind_of(r["数据类型"]),
        nunique=int(r["唯一值数"]),
        miss=int(r["缺失数"]),
        group="输出" if is_out else "输入",
        role1=("输出 " + var) if is_out else ("输入 " + var),
        role2="因变量" if str(r["因果角色"]).strip() == "结果" else "自变量",
    ))

# 派生变量（lnX1 / lnY）：计数全部来自清洗数据
DERIVED = [("lnX1", "粉丝规模对数（log X1）", "logX1", "自变量"),
           ("lnY", "曝光对数（log1p Y1）", "logY", "因变量")]
for var, label, column, role2 in DERIVED:
    rows.append(dict(var=var, label=label, kind="连续",
                     nunique=int(clean[column].nunique()),
                     miss=int(clean[column].isna().sum()),
                     group="派生", role1="派生", role2=role2))

assert rows[8]["nunique"] == rows[0]["nunique"], "lnX1 与 X1 取值数不一致"
assert rows[9]["nunique"] == rows[7]["nunique"], "lnY 与 Y1 取值数不一致"
assert rows[8]["miss"] == rows[9]["miss"] == 0, "派生量不应有缺失"

# ------------------------------------------------------------------ 版面（单位：英寸）
W, H = 9.20, 5.40
PITCH, BAND = 0.400, 0.360
TOPM, HEAD_H, GAP = 0.22, 0.36, 0.08

X0, X1 = 0.10, W - 0.10
BAR_X, BAR_W = 0.150, 0.030
X_VAR, X_MEAN = 0.240, 0.620
X_ROLE = 3.350
SW_X, SW = 4.640, 0.135
KIND_X = SW_X + SW + 0.115
X_CNT = 6.280
X_MISS = 6.920
X_NOTE = 7.100

FS_BIG, FS_MAIN, FS_SUB = 11.0, 9.5, 8.5
LW = 0.8

C_INK, C_SUB, C_FAINT = "#26282D", "#5A6068", "#8A9098"
C_HEAD_BG, C_HEAD_TX = "#EDF0F4", "#4F5661"
C_RULE_STRONG, C_RULE = "#9FA9B4", "#C9D2DC"
GROUP_BAR = {"输入": BLUE, "输出": "#8C8C8C", "派生": "#A9B8D4"}
GROUP_TX = "#4A5058"

fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect("equal")
ax.axis("off")


def T(x, y, s, size=FS_MAIN, color=C_INK, ha="left", va="center", weight="normal",
      family=None, zorder=5):
    kw = {"family": family} if family is not None else {}
    return ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
                   fontweight=weight, zorder=zorder, **kw)


def NUM(x, y, s, size=FS_MAIN, color=C_INK, weight="normal"):
    return T(x, y, s, size=size, color=color, ha="right",
             family="Times New Roman", weight=weight)


def swatch(x0, yc, color, size=SW):
    ax.add_patch(Rectangle((x0, yc - size / 2.0), size, size, facecolor=color,
                           edgecolor="none", zorder=3))


rows_top = H - TOPM - HEAD_H - GAP
head_y0 = rows_top + GAP

# ------------------------------------------------------------------ 表头
ax.add_patch(Rectangle((X0, head_y0), X1 - X0, HEAD_H, facecolor=C_HEAD_BG,
                       edgecolor="none", zorder=1))
ax.plot([X0, X1], [head_y0 + HEAD_H, head_y0 + HEAD_H], color=C_RULE_STRONG, lw=LW, zorder=2)
hy = head_y0 + HEAD_H / 2.0
T(X_VAR, hy, "变量", size=FS_MAIN, color=C_HEAD_TX)
T(X_ROLE, hy, "角色", size=FS_MAIN, color=C_HEAD_TX)
T(SW_X, hy, "类型", size=FS_MAIN, color=C_HEAD_TX)
T(X_CNT, hy, "类别数", size=FS_MAIN, color=C_HEAD_TX, ha="right")
T(X_MISS, hy, "缺失", size=FS_MAIN, color=C_HEAD_TX, ha="right")
ax.plot([X0, X1], [head_y0, head_y0], color=C_RULE_STRONG, lw=LW, zorder=2)

# ------------------------------------------------------------------ 逐行（行间不画线）
for i, r in enumerate(rows):
    y_top = rows_top - i * PITCH
    yc = y_top - BAND / 2.0

    T(X_VAR, yc, r["var"], size=FS_BIG, weight="bold")
    T(X_MEAN, yc, r["label"], size=FS_MAIN)
    T(X_ROLE, yc + 0.075, r["role1"], size=FS_SUB, color=C_SUB)
    T(X_ROLE, yc - 0.075, r["role2"], size=FS_SUB, color=C_FAINT)
    swatch(SW_X, yc, SWATCH[r["kind"]])
    T(KIND_X, yc, KIND_TEXT[r["kind"]], size=FS_MAIN)
    NUM(X_CNT, yc, f'{r["nunique"]}')

    if r["miss"] > 0:
        NUM(X_MISS, yc, f'{r["miss"]}', color="#E64B35", weight="bold")
        T(X_NOTE, yc, "条 → 众数填补", size=FS_SUB, color=C_SUB)
    else:
        NUM(X_MISS, yc, f'{r["miss"]}', color=C_SUB)

# ------------------------------------------------------------------ 分组色条与组间细线
groups = []
for i, r in enumerate(rows):
    if not groups or groups[-1][0] != r["group"]:
        groups.append([r["group"], i, i])
    else:
        groups[-1][2] = i

for gname, i0, i1 in groups:
    y_hi = rows_top - i0 * PITCH
    y_lo = rows_top - i1 * PITCH - BAND
    ax.add_patch(Rectangle((BAR_X, y_lo), BAR_W, y_hi - y_lo,
                           facecolor=GROUP_BAR[gname], edgecolor="none", zorder=3))
    label = T(0.080, (y_hi + y_lo) / 2.0, gname, size=FS_SUB, color=GROUP_TX,
              ha="center", va="center")
    label.set_rotation(90)
    if i0 > 0:
        ax.plot([X0, X1], [y_hi + (PITCH - BAND) / 2.0] * 2, color=C_RULE,
                lw=LW, zorder=2)

rows_bottom = rows_top - (len(rows) - 1) * PITCH - BAND

# ------------------------------------------------------------------ 图例（短标签）
LEG_Y = rows_bottom - 0.40
legend = [("连续", "连续 · X1 Y1"),
          ("名义", "名义 · X2 X3"),
          ("循环", "循环 · X4–X6"),
          ("二元", "指示 · X7")]
for k, (key, text) in enumerate(legend):
    lx = 0.16 + k * 1.86
    swatch(lx, LEG_Y, SWATCH[key])
    T(lx + 0.26, LEG_Y, text, size=FS_MAIN, color=C_SUB)
T(8.30, LEG_Y, "红字 = 有缺失", size=FS_MAIN, color=C_SUB)

png = OUT / "图14_变量字典与缺失.png"
fig.savefig(png, dpi=400, bbox_inches="tight", pad_inches=0.05, facecolor="white")
plt.close(fig)
print("已保存:", png)
