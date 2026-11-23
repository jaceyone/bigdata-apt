# -*- coding: utf-8 -*-
"""推荐替换候选：拼两张核对表（5 列）。"""
import os
from PIL import Image, ImageDraw, ImageFont

THUMB = r"E:\桌面\国赛论文改造\gallery-export（画廊选图）\recipe_gallery\thumb"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "画廊对照")
os.makedirs(OUT, exist_ok=True)

PICKS = [
    "basic-7", "journal-13", "competition-26", "basic-4", "journal-89",
    "basic-5", "competition-12", "journal-45", "advanced-20", "competition-8",
    "journal-6", "advanced-13", "journal-78", "advanced-2", "journal-22",
    "empirical-8", "competition-4", "academic-1", "advanced-7", "advanced-6",
    "empirical-9", "empirical-19", "advanced-21", "journal-11", "competition-25",
    "journal-63", "basic-3", "journal-50", "basic-2",
]

COLS, IW, IH, LH, PAD = 5, 380, 290, 26, 4
try:
    FONT = ImageFont.load_default(size=18)
except Exception:
    FONT = ImageFont.load_default()

for si in range(2):
    chunk = PICKS[si * 15:(si + 1) * 15]
    rows = (len(chunk) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * IW, rows * (IH + LH)), (246, 246, 246))
    for i, name in enumerate(chunk):
        tile = Image.new("RGB", (IW, IH + LH), "white")
        p = os.path.join(THUMB, name + ".webp")
        im = Image.open(p).convert("RGB")
        im.thumbnail((IW - 2 * PAD, IH - 2 * PAD))
        tile.paste(im, ((IW - im.width) // 2, (IH - im.height) // 2))
        d = ImageDraw.Draw(tile)
        d.rectangle([0, 0, IW - 1, IH + LH - 1], outline=(180, 180, 180))
        d.rectangle([0, IH, IW - 1, IH + LH - 1], fill=(232, 232, 232))
        tag = ["", "A", "B", "C", "D", "E"][i % 5] if False else ""
        d.text((8, IH + 4), f"[{si * 15 + i + 1}] {name}", fill="black", font=FONT)
        sheet.paste(tile, ((i % COLS) * IW, (i // COLS) * (IH + LH)))
    out = os.path.join(OUT, f"pick{si + 1}.png")
    sheet.save(out)
    print(out, sheet.size)
