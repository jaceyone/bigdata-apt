# -*- coding: utf-8 -*-
"""问题四改版候选：拼一张例图核对表。"""
import os
from PIL import Image, ImageDraw, ImageFont

THUMB = r"E:\桌面\国赛论文改造\gallery-export（画廊选图）\recipe_gallery\thumb"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "画廊对照")
os.makedirs(OUT, exist_ok=True)
PICKS = ["advanced-22", "journal-148", "advanced-3", "advanced-4", "journal-16",
         "journal-17", "journal-119", "journal-38", "academic-12", "competition-21",
         "journal-72", "dotplot" ]

COLS, IW, IH, LH = 5, 380, 300, 26
try:
    FONT = ImageFont.load_default(size=18)
except Exception:
    FONT = ImageFont.load_default()

rows = (len(PICKS) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * IW, rows * (IH + LH)), (246, 246, 246))
for i, name in enumerate(PICKS):
    p = os.path.join(THUMB, name + ".webp")
    tile = Image.new("RGB", (IW, IH + LH), "white")
    if os.path.exists(p):
        im = Image.open(p).convert("RGB")
        im.thumbnail((IW - 8, IH - 8))
        tile.paste(im, ((IW - im.width) // 2, (IH - im.height) // 2))
    d = ImageDraw.Draw(tile)
    d.rectangle([0, 0, IW - 1, IH + LH - 1], outline=(180, 180, 180))
    d.rectangle([0, IH, IW - 1, IH + LH - 1], fill=(232, 232, 232))
    d.text((8, IH + 4), f"[{i+1}] {name}" + ("" if os.path.exists(p) else "  MISSING"), fill="black", font=FONT)
    sheet.paste(tile, ((i % COLS) * IW, (i // COLS) * (IH + LH)))

out = os.path.join(OUT, "problem4_candidates.png")
sheet.save(out)
print(out, sheet.size)
