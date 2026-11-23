# -*- coding: utf-8 -*-
"""图17：付费效应分组异质性森林图。

左列分组名（竖排）+ 组内缩进子样本名；中列点 + 95%CI（x = 付费系数）；
右侧 系数 (95%CI) / N / p 三列数值；三档底纹分隔四个分组块；
有组内 P 的分组在组右侧画竖向括线。样式走项目 nature 风格（nature_style）。

数据先由本脚本生成：问题四/临时产物/子样本异质性.csv
口径：logY ~ 付费 + 类型 + 主题 + 月份哑变量 + 星期哑变量 + 时段组（= 最终模型 M2，
不含 logX1），OLS + HC3 稳健标准误；子样本内不含变异的类别自然退化。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nature_style  # noqa: F401  # 全篇 Nature 风格样式，须在 import _common 之前

# 样式库预置 500 dpi 与 constrained layout；本图统一 400 dpi、固定坐标轴盒
import plot_style as _ps  # noqa: E402
_ps.apply(dpi=400, prefs={"dpi": 400})
_ps._ACTIVE_PREFS["dpi"] = 400          # savefig 保护层按此值决定最终 dpi
_ps._ACTIVE_PREFS["_explicit"] = ["dpi"]

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.font_manager import FontProperties
from matplotlib.transforms import blended_transform_factory
from scipy import stats
import statsmodels.api as sm

from _common import CACHE_DIR, save_fig, shared_path, top_legend

CACHE_DIR = Path(CACHE_DIR)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(shared_path("清洗数据.csv"), encoding="utf-8-sig")
C_MAIN = "#3C5488"       # 深蓝：显著
C_LOW = "#8491B4"        # 灰蓝：n < 30 仅参考
C_INK = "#1A1A1A"

# ══════════════════════════════════════════════════════════════
# 1. 子样本回归
# ══════════════════════════════════════════════════════════════
BLOCK_ORDER = ["类型", "主题", "月份", "星期", "时段"]
DROP_ORDER = ["时段", "星期", "月份", "主题", "类型"]   # 控制变量先退化，核心解释变量最后


def block_of(col):
    if col in ("const", "付费"):
        return None
    return col.split("_")[0]


def full_design(d):
    """与问题四主程序 build_design(x1=False, month='dummy') 完全一致的 M2 口径。"""
    X = pd.DataFrame(index=d.index)
    X["const"] = 1.0
    for lev in ["Status", "Link", "Video"]:
        X[f"类型_{lev}"] = (d["X2"] == lev).astype(float)
    for lev in [2, 3]:
        X[f"主题_{lev}"] = (d["X3"] == lev).astype(float)
    for m in range(2, 13):
        X[f"月份_{m}"] = (d["X4"] == m).astype(float)
    for w in range(2, 8):
        X[f"星期_{w}"] = (d["X5"] == w).astype(float)
    X["时段_凌晨"] = (d["hour_band"] == "凌晨").astype(float)
    X["时段_下午晚间"] = (d["hour_band"] == "下午晚间").astype(float)
    X["付费"] = d["X7"].astype(float)
    return X


def prune_rank(X, cols):
    """按 const → 付费 → 其余 的优先序保留线性无关列。"""
    keep, rank = [], 0
    priority = [c for c in ["const", "付费"] if c in cols] + \
               [c for c in cols if c not in ("const", "付费")]
    for c in priority:
        r = np.linalg.matrix_rank(X[keep + [c]].values)
        if r > rank:
            keep.append(c)
            rank = r
    return ["const"] + [c for c in keep if c != "const"]


def usable_cols(X):
    """剔除子样本内无变异、或仅 1 条观测的类别哑变量（该点杠杆=1，HC3 会发散）。"""
    keep = []
    n = len(X)
    for c in X.columns:
        v = X[c].values
        if c == "const":
            keep.append(c)
            continue
        s = int(round(float(v.sum())))
        if np.ptp(v) == 0:                 # 该水平在子样本内不存在 / 恒为常数
            continue
        if min(s, n - s) < 2:              # 单观测哑变量 → 该观测被精确拟合
            continue
        keep.append(c)
    return keep


def fit_subsample(d, label, own_block=None):
    X_all = full_design(d)
    n = len(d)
    raw = list(X_all.columns)
    cols = usable_cols(X_all)
    if "付费" not in cols:
        raise ValueError(f"{label}：付费在子样本内无变异")
    dropped_levels = [c for c in raw
                      if c not in cols and c != "const" and block_of(c) != own_block]
    cols = prune_rank(X_all, cols)
    dropped_blocks = []

    # df 不足时按 时段→星期→月份→主题→类型 整块退化，保证 HC3 稳定
    while (n - len(cols)) < 10:
        target = next((b for b in DROP_ORDER
                       if b not in dropped_blocks and any(block_of(c) == b for c in cols)), None)
        if target is None:
            break
        cols = [c for c in cols if block_of(c) != target]
        dropped_blocks.append(target)
        cols = prune_rank(X_all, cols)

    y = d["logY"].astype(float)
    res = sm.OLS(y, X_all[cols]).fit(cov_type="HC3")
    b, se, dfr = float(res.params["付费"]), float(res.bse["付费"]), int(res.df_resid)
    if not np.isfinite(se) or se <= 0:            # 极端小样本兜底：仅保留常数与付费
        cols = ["const", "付费"]
        res = sm.OLS(y, X_all[cols]).fit(cov_type="HC3")
        b, se, dfr = float(res.params["付费"]), float(res.bse["付费"]), int(res.df_resid)
        dropped_blocks = ["类型", "主题", "月份", "星期", "时段"]
    tc = stats.t.ppf(0.975, dfr)
    p = float(2 * stats.t.sf(abs(b / se), dfr))
    kept = [name for name in BLOCK_ORDER if any(block_of(c) == name for c in cols)]
    return dict(label=label, N=n, b=b, se=se, lo=b - tc * se, hi=b + tc * se, p=p,
                df=dfr, k=len(cols), kept=kept, dropped=dropped_blocks,
                n_levels=len(dropped_levels))


SUBSETS = [
    ("全样本", [("全样本", df)], None),
    ("帖子类型", [(t, df[df["X2"] == t]) for t in ["Photo", "Status", "Link", "Video"]], "类型"),
    ("内容主题", [(f"主题 {k}", df[df["X3"] == k]) for k in [1, 2, 3]], "主题"),
    ("发布时段", [(t, df[df["hour_band"] == t]) for t in ["凌晨", "上午", "下午晚间"]], "时段"),
]

fits, order = {}, []
for group, subs, own in SUBSETS:
    for name, d in subs:
        r = fit_subsample(d, name, own_block=own)
        r["group"] = group
        fits[name] = r
        order.append((group, name))


def group_wald(names):
    """组内付费系数是否相同：χ² Wald。子样本互斥 ⇒ cov(b_i−b_j)=SE_i²+SE_j²。"""
    b = np.array([fits[n]["b"] for n in names], dtype=float)
    se = np.array([fits[n]["se"] for n in names], dtype=float)
    k = len(names)
    if k < 2 or not np.all(np.isfinite(se)) or np.any(se <= 0):
        return np.nan
    D = np.zeros((k - 1, k))
    for i in range(k - 1):
        D[i, i] = 1.0
        D[i, -1] = -1.0
    Db = D @ b
    S = D @ np.diag(se ** 2) @ D.T
    try:
        W = float(Db @ np.linalg.inv(S) @ Db)
    except np.linalg.LinAlgError:
        return np.nan
    if not np.isfinite(W) or W < 0:
        return np.nan
    return float(stats.chi2.sf(W, k - 1))


GROUP_P, GROUP_P_SUB, GROUP_DF = {}, {}, {}

# 口径一（主）：在全样本 M2 上加「付费 × 组哑变量」交互，HC3 协方差下的联合 Wald（F）
# —— 与问题四主程序图11 的「付费×类型 交互 p」同一口径，避免同一篇论文里两个 P 打架。
INTER_COLS = {"帖子类型": ["类型_Status", "类型_Link", "类型_Video"],
              "内容主题": ["主题_2", "主题_3"],
              "发布时段": ["时段_凌晨", "时段_下午晚间"]}
X_pool = full_design(df)
y_pool = df["logY"].astype(float)
for group, cols_inter in INTER_COLS.items():
    Xi = X_pool.copy()
    for c in cols_inter:
        Xi[f"付费x{c}"] = Xi["付费"] * Xi[c]
    mi = sm.OLS(y_pool, Xi).fit(cov_type="HC3")
    R = np.zeros((len(cols_inter), Xi.shape[1]))
    for i, c in enumerate(cols_inter):
        R[i, Xi.columns.get_loc(f"付费x{c}")] = 1.0
    ft = mi.f_test(R)
    GROUP_P[group] = float(ft.pvalue)
    GROUP_DF[group] = (len(cols_inter), int(mi.df_resid))

# 口径二（对照）：互斥子样本的系数 Q 检验
for group, subs, _ in SUBSETS:
    GROUP_P_SUB[group] = (group_wald([n for n, _ in subs])
                          if group != "全样本" else np.nan)

# ---- CSV
rows = []
for group, subs, _ in SUBSETS:
    first = True
    for name, _ in subs:
        f = fits[name]
        if name == "全样本":
            note = "与最终模型 M2 同规格（含月份哑变量、不含 logX1），对照 表16 的 0.3374"
        else:
            parts = []
            if group == "帖子类型":
                parts.append("类型哑变量整体退化")
            elif group == "内容主题":
                parts.append("主题哑变量整体退化")
            else:
                parts.append("时段哑变量整体退化（基线为子样本内剩余时段）")
            if f["n_levels"]:
                parts.append(f"另有 {f['n_levels']} 个类别哑变量在子样本内无变异或仅 1 条观测（该点杠杆=1，HC3 不可用），并入基线")
            if f["dropped"]:
                parts.append("df<10，" + "/".join(f["dropped"]) + " 整块退化")
            parts.append(f"df={f['df']}，k={f['k']}")
            if f["N"] < 30:
                parts.append(f"n={f['N']}，仅参考")
                if name == "Video":
                    parts.append("该宽 CI 使「类型」组内 P 检验功效极低")
            note = "；".join(parts)
        if first and name != "全样本":
            d1, d2 = GROUP_DF[group]
            note += ("；组内 P 为全样本 M2 加「付费×组哑变量」交互的 HC3 联合 Wald（F，df1=%d, df2=%d），"
                     "与图11 的交互 P 同口径；对照口径（互斥子样本系数 Q 检验）p=%.3f" % (d1, d2, GROUP_P_SUB[group]))
        first = False
        gp = GROUP_P.get(group, np.nan)
        rows.append([group, name, f["N"], round(f["b"], 4), round(f["se"], 4),
                     round(f["lo"], 4), round(f["hi"], 4), round(f["p"], 4),
                     ("" if not np.isfinite(gp) else round(gp, 4)),
                     note])

tab = pd.DataFrame(rows, columns=["分组", "子样本", "N", "付费系数", "标准误",
                                  "CI下限", "CI上限", "p值", "组内P", "备注"])
CSV_PATH = CACHE_DIR / "子样本异质性.csv"
tab.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

print("=" * 100)
print(tab[["分组", "子样本", "N", "付费系数", "标准误", "CI下限", "CI上限", "p值", "组内P"]].to_string(index=False))
print("=" * 100)
print("全样本付费系数 = %.4f（表16 M2 = 0.3374，差 %.4f）"
      % (fits["全样本"]["b"], abs(fits["全样本"]["b"] - 0.3374)))
for name in ["Link", "Video"]:
    print(f"{name}: N={fits[name]['N']} b={fits[name]['b']:+.3f} se={fits[name]['se']:.3f} "
          f"CI=[{fits[name]['lo']:+.3f},{fits[name]['hi']:+.3f}] p={fits[name]['p']:.3f} "
          f"k={fits[name]['k']} df={fits[name]['df']} kept={fits[name]['kept']}")
for g in ["帖子类型", "内容主题", "发布时段"]:
    print(f"组内 P（{g}，联合 Wald F df={GROUP_DF[g]}）= {GROUP_P[g]:.4f}"
          f" ｜ 对照：子样本 Q 检验 p={GROUP_P_SUB[g]:.4f}")

# ══════════════════════════════════════════════════════════════
# 2. 图（Nature 风格：四边框、刻度向内、横向淡网格；图下方不留说明性长句）
# ══════════════════════════════════════════════════════════════
LBL = {"全样本": "全样本", "Photo": "Photo", "Status": "Status", "Link": "Link",
       "Video": "Video", "主题 1": "主题1", "主题 2": "主题2", "主题 3": "主题3",
       "凌晨": "凌晨", "上午": "上午", "下午晚间": "下午晚间"}
GROUP_ORDER = ["全样本", "帖子类型", "内容主题", "发布时段"]
# 三档底纹：全样本浅蓝高亮，三个分组维度轮换三档中性色
GROUP_FACE = {"全样本": ("#E3E9F3", 0.90), "帖子类型": ("#FFFFFF", 0.0),
              "内容主题": ("#F1F3F6", 1.0), "发布时段": ("#E5E8ED", 1.0)}

n_row = len(order)
ypos = np.arange(n_row)[::-1]
y_of = {name: y for (_, name), y in zip(order, ypos)}
row_of_group = {g: [n for gg, n in order if gg == g] for g in GROUP_ORDER}

B_BASE = fits["全样本"]["b"]
LO_BASE, HI_BASE = fits["全样本"]["lo"], fits["全样本"]["hi"]

fig = plt.figure(figsize=(9.7, 6.6), layout=None)
fig.set_layout_engine("none")
L, B = 0.098, 0.128
AXW_IN, AXH_IN = 3.90, 5.00
W_, H_ = AXW_IN / 9.7, AXH_IN / 6.6
T = B + H_
ax = fig.add_axes([L, B, W_, H_])
AXW = AXW_IN


def extra(inch):                      # 右侧各列：英寸 → axes 坐标
    return 1.0 + inch / AXW


xt = blended_transform_factory(ax.transAxes, ax.transData)
x_group = -0.75 / AXW                # 左侧竖排组名（轴左外 0.75 in）
x_brace = extra(0.13)
x_brace_lab = extra(0.245)
x_ci = extra(1.18)
x_n = extra(2.46)
x_p = extra(2.86)
x_note = extra(3.54)

# ---- 三档底纹 + 分组分隔线
for g in GROUP_ORDER:
    ys = [y_of[n] for n in row_of_group[g]]
    face, alpha = GROUP_FACE[g]
    ax.axhspan(min(ys) - 0.5, max(ys) + 0.5, facecolor=face, alpha=alpha,
               edgecolor="none", linewidth=0, zorder=0)
    ax.axhline(min(ys) - 0.5, color="#C9D0D9", lw=0.7, zorder=1.2)

# ---- 表头分隔线
ax.plot([0.0, x_note - 0.06], [n_row - 0.50, n_row - 0.50], transform=xt,
        color="#C9CED6", lw=0.7, clip_on=False, zorder=1.4)

# ---- 0 参考线与全样本 95%CI 浅色竖带
ax.axvspan(LO_BASE, HI_BASE, facecolor="#4DBBD5", alpha=0.16, edgecolor="none",
           linewidth=0, zorder=0.4)
ax.vlines(B_BASE, -0.55, n_row - 0.50, color="#4DBBD5", lw=1.1, zorder=1.6)
ax.vlines(0, -0.55, n_row - 0.50, color="#333333", lw=1.0, ls=(0, (4, 3)), zorder=1.8)

# ---- 逐行：点 + 95%CI + 右侧三列数值
for group, name in order:
    f = fits[name]
    y = y_of[name]
    small = f["N"] < 30
    col = C_LOW if small else C_MAIN
    p = f["p"]
    if small:
        marker, mfc, mec, mew = "s", ("white" if p >= 0.05 else col), col, 0.95
    elif p < 0.01:
        marker, mfc, mec, mew = "s", col, C_INK, 0.5
    elif p < 0.05:
        marker, mfc, mec, mew = "o", col, C_INK, 0.5
    else:
        marker, mfc, mec, mew = "s", "white", col, 0.95
    ax.errorbar(f["b"], y, xerr=[[f["b"] - f["lo"]], [f["hi"] - f["b"]]], fmt=marker,
                mfc=mfc, mec=mec, mew=mew, color=col, ecolor=col, elinewidth=1.15,
                capsize=3.2, capthick=0.9, markersize=6.8, zorder=3)
    ax.text(x_ci, y, f"{f['b']:.2f} ({f['lo']:.2f}, {f['hi']:.2f})", transform=xt,
            ha="left", va="center", fontsize=9.0, color="#222222")
    ax.text(x_n, y, f"{f['N']}", transform=xt, ha="left", va="center",
            fontsize=9.0, color="#222222")
    ax.text(x_p, y, "p<0.001" if p < 1e-3 else f"p={p:.3f}", transform=xt,
            ha="left", va="center", fontsize=9.0,
            color=col if p < 0.05 else "#6E6E6E")
    if small:
        ax.text(x_note, y, f"n={f['N']}，仅参考", transform=xt, ha="left",
                va="center", fontsize=9.0, color=C_LOW)

# ---- 列标题
for x, txt in [(x_ci, "系数 (95%CI)"), (x_n, "N"), (x_p, "p")]:
    ax.text(x, n_row - 0.42, txt, transform=xt, ha="left", va="bottom",
            fontsize=9.0, color="#4A4A4A")

# ---- 组内 P 竖向括线（组内行区右侧）
for g in ["帖子类型", "内容主题", "发布时段"]:
    gp = GROUP_P[g]
    if not np.isfinite(gp):
        continue
    ys = [y_of[n] for n in row_of_group[g]]
    y0, y1 = min(ys) - 0.33, max(ys) + 0.33
    hook = 0.026
    # 三段两点短线拼括线：点数 <3 不会被存图收尾的 dress_bare_lines 补上 marker
    ax.plot([x_brace, x_brace], [y0, y1], transform=xt, color="#59616D", lw=1.1,
            clip_on=False, zorder=2.2, solid_capstyle="butt")
    ax.plot([x_brace, x_brace + hook], [y1, y1], transform=xt, color="#59616D",
            lw=1.1, clip_on=False, zorder=2.2, solid_capstyle="butt")
    ax.plot([x_brace, x_brace + hook], [y0, y0], transform=xt, color="#59616D",
            lw=1.1, clip_on=False, zorder=2.2, solid_capstyle="butt")
    ax.text(x_brace_lab, (y0 + y1) / 2.0, f"组内 P={gp:.3f}", transform=xt,
            ha="left", va="center", fontsize=9.0, color="#3A3A3A")

# ---- 左侧竖排组名
for g in GROUP_ORDER:
    ys = [y_of[n] for n in row_of_group[g]]
    ax.text(x_group, (min(ys) + max(ys)) / 2.0, g, transform=xt, rotation=90,
            ha="center", va="center", fontsize=9.2, color="#333333",
            fontweight="bold")

# ---- 坐标轴
ax.set_yticks(ypos)
ax.set_yticklabels([LBL[name] for _, name in order], fontsize=9.5)
ax.set_ylim(-0.55, n_row - 0.04)
xlo = min([fits[n]["lo"] for _, n in order] + [0.0]) - 0.18
xhi = max([fits[n]["hi"] for _, n in order] + [0.0]) + 0.15
ax.set_xlim(xlo, xhi)
ticks = np.arange(np.ceil(xlo * 2) / 2, np.floor(xhi * 2) / 2 + 0.01, 0.5)
ax.set_xticks(ticks)
ax.set_xticklabels([("0" if abs(t) < 1e-9 else f"{t:g}") for t in ticks], fontsize=9.5)
ax.set_xlabel("付费系数 β（log1p 曝光；M2 同规格 · HC3 稳健 SE）", fontsize=10.0, labelpad=4)
ax.tick_params(axis="x", direction="in", length=4, width=0.8)
ax.tick_params(axis="x", which="minor", length=0, bottom=False, top=False)
ax.tick_params(axis="y", which="both", length=0, pad=6)
ax.set_axisbelow(True)

handles = [
    Line2D([], [], marker="s", ls="none", mfc=C_MAIN, mec=C_INK, mew=0.5, ms=6.4,
           label="p<0.01 实心方块"),
    Line2D([], [], marker="o", ls="none", mfc=C_MAIN, mec=C_INK, mew=0.5, ms=6.4,
           label="0.01≤p<0.05 实心圆"),
    Line2D([], [], marker="s", ls="none", mfc="white", mec=C_MAIN, mew=0.95, ms=6.4,
           label="p≥0.05 空心方块"),
    Line2D([], [], marker="s", ls="none", mfc="white", mec=C_LOW, mew=0.95, ms=6.4,
           label="n<30 仅参考"),
    Line2D([], [], color="#555555", lw=1.1, label="95% CI"),
    Patch(facecolor="#4DBBD5", alpha=0.3, edgecolor="none", label="全样本 95%CI 带"),
]
top_legend(fig, [ax], fontsize=9.0, handles=handles,
           labels=[h.get_label() for h in handles], ncol=3, auto_expand=False,
           frameon=True, edgecolor="0.82", framealpha=1.0,
           columnspacing=1.0, handletextpad=0.5, labelspacing=0.45,
           prop=FontProperties(family=plt.rcParams["font.family"], size=9.0),
           subplot_top=T)

save_fig(fig, "图17_付费效应异质性森林", chart_types=["forest"],
         chart_style="nature", chart_color_scheme="nature")
print("CSV:", CSV_PATH)
