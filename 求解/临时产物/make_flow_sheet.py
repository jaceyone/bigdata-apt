# -*- coding: utf-8 -*-
"""流程图候选：从 figure_gallery 取 blue 变体拼对照表。"""
import os
from PIL import Image, ImageDraw, ImageFont

GAL = r"E:\桌面\国赛论文改造\gallery-export（画廊选图）\figure_gallery"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "画廊对照")
os.makedirs(OUT, exist_ok=True)

PICKS = [
    "data-preprocessing", "data-pipeline", "ml-workflow", "roadmap-phases",
    "thesis-chapter-flow", "proposal-content-route", "problem-restatement", "standard-flowchart",
]
COLS, IW, IH, LH = 4, 470, 330, 26
try:
    FONT = ImageFont.load_default(size=16)
except Exception:
    FONT = ImageFont.load_default()

rows = (len(PICKS) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * IW, rows * (IH + LH)), (246, 246, 246))
for i, name in enumerate(PICKS):
    p = os.path.join(GAL, name, "blue.png")
    tile = Image.new("RGB", (IW, IH + LH), "white")
    d = ImageDraw.Draw(tile)
    if os.path.exists(p):
        im = Image.open(p).convert("RGB")
        im.thumbnail((IW - 10, IH - 10))
        tile.paste(im, ((IW - im.width) // 2, (IH - im.height) // 2))
        lab = f"[{i+1}] {name}"
    else:
        lab = f"[{i+1}] {name}  MISSING"
    d.rectangle([0, 0, IW - 1, IH + LH - 1], outline=(180, 180, 180))
    d.rectangle([0, IH, IW - 1, IH + LH - 1], fill=(232, 232, 232))
    d.text((8, IH + 4), lab, fill="black", font=FONT)
    sheet.paste(tile, ((i % COLS) * IW, (i // COLS) * (IH + LH)))

out = os.path.join(OUT, "flow_candidates.png")
sheet.save(out)
print(out, sheet.size)
