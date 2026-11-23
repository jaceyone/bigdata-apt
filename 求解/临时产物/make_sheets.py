# -*- coding: utf-8 -*-
"""按 index.json 生成画廊候选缩略图对照表（4 列，标注 组名/变体号）。"""
import json, os
from PIL import Image, ImageDraw, ImageFont

GAL = r"E:\桌面\国赛论文改造\gallery-export（画廊选图）\recipe_gallery"
THUMB = os.path.join(GAL, "thumb")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "画廊对照")
os.makedirs(OUT, exist_ok=True)

idx = json.load(open(os.path.join(GAL, "index.json"), encoding="utf-8"))
MAP = {g["id"]: g for g in idx["groups"]}

SHEETS = {
    "S1_分布": [("raincloud", 3), ("box", 3), ("violin", 3), ("ridgeline", 2), ("beeswarm", 2)],
    "S2_构成与大小": [("bar", 4), ("stacked_bar", 3), ("back_to_back", 2), ("diverging_bar", 1),
                 ("lollipop", 1), ("dumbbell", 1), ("area", 1), ("donut", 1), ("waterfall", 2)],
    "S3_关系": [("scatter", 4), ("corr", 4), ("joint_density", 3), ("pairplot", 2), ("bubble", 1), ("dotplot", 2)],
    "S4_模型A": [("forest", 4), ("dot_ci", 1), ("importance", 1), ("coef_stability", 1), ("ablation", 1),
                 ("marginal", 1), ("prediction", 3), ("residual", 2), ("sensitivity", 2)],
    "S5_时间与检验": [("pareto_front", 2), ("calibration", 1), ("heatmap", 2), ("spacetime", 2), ("calendar", 1),
                  ("line", 3), ("smooth_curve", 1), ("dual_axis", 1), ("dual_axis_bar", 2)],
}

COLS, IW, IH, LH, PAD = 4, 380, 250, 24, 6
try:
    FONT = ImageFont.load_default(size=13)
except Exception:
    FONT = ImageFont.load_default()


def label_of(v):
    parts = v.split("#")
    return f"{parts[0].strip()}-{parts[1].strip()}"


def cell(path, label, missing=False):
    tile = Image.new("RGB", (IW, IH + LH), "white")
    if not missing:
        im = Image.open(path).convert("RGB")
        im.thumbnail((IW - 2 * PAD, IH - 2 * PAD))
        tile.paste(im, ((IW - im.width) // 2, (IH - im.height) // 2))
    d = ImageDraw.Draw(tile)
    d.rectangle([0, 0, IW - 1, IH + LH - 1], outline=(190, 190, 190))
    d.rectangle([0, IH, IW - 1, IH + LH - 1], fill=(236, 236, 236))
    d.text((6, IH + 4), label + ("  MISSING" if missing else ""), fill="black", font=FONT)
    return tile


summary = []
for name, specs in SHEETS.items():
    items = []
    for gid, cap in specs:
        g = MAP[gid]
        for v in g["variants"][:cap]:
            items.append((gid, v))
    rows = (len(items) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * IW, rows * (IH + LH)), (248, 248, 248))
    for i, (gid, v) in enumerate(items):
        p = os.path.join(THUMB, label_of(v) + ".webp")
        miss = not os.path.exists(p)
        sheet.paste(cell(p, label_of(v), miss), ((i % COLS) * IW, (i // COLS) * (IH + LH)))
        if miss:
            summary.append(p)
    out = os.path.join(OUT, name + ".png")
    sheet.save(out)
    print("OK", name, sheet.size)
print("MISSING:", summary)
