# -*- coding: utf-8 -*-
"""验收：把 16 张成品图拼成总览（4 列），并打印尺寸/时间。"""
import os
from PIL import Image, ImageDraw, ImageFont

PROJ = r"C:\Users\28466\AppData\Roaming\MriteUltra-2.6.13\Mrite-Agent-Space\数学建模\projects\通用练习_2026-11-22_09-12-35\求解"
FIGS = [
    r"问题一\结果\图1_曝光与分组分布.png",
    r"问题一\结果\图2_粉丝规模与月份共线.png",
    r"问题一\结果\图3_相关系数热力图.png",
    r"问题二\结果\图4_类别结构与缺失.png",
    r"问题二\结果\图5_变换前后分布.png",
    r"问题三\结果\图6_最终模型系数森林图.png",
    r"问题三\结果\图7_共线性诊断.png",
    r"问题三\结果\图8_残差诊断.png",
    r"问题三\结果\图9_预测能力验证.png",
    r"问题三\结果\图10_方差贡献Shapley.png",
    r"问题四\结果\图11_调整预测效应.png",
    r"问题四\结果\图12_效应稳健性.png",
    r"临时产物\图13_核心结论总览.png",
    r"问题一\结果\图14_变量字典与缺失.png",
    r"问题三\结果\图15_模型绩效评分表.png",
    r"问题四\结果\图16_系数稳健性矩阵.png",
    r"问题四\结果\图17_付费效应异质性森林.png",
    r"临时产物\补充图1_样本结构.png",
    r"临时产物\补充图2_时间结构.png",
    r"临时产物\补充图3_付费可比性.png",
]

COLS, IW, IH, LH = 4, 470, 360, 24
try:
    FONT = ImageFont.load_default(size=15)
except Exception:
    FONT = ImageFont.load_default()

rows = (len(FIGS) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * IW, rows * (IH + LH)), (247, 247, 247))
for i, rel in enumerate(FIGS):
    p = os.path.join(PROJ, rel)
    tile = Image.new("RGB", (IW, IH + LH), "white")
    d0 = ImageDraw.Draw(tile)
    if os.path.exists(p):
        im = Image.open(p).convert("RGB")
        w0, h0 = im.size
        im.thumbnail((IW - 12, IH - 12))
        tile.paste(im, ((IW - im.width) // 2, (IH - im.height) // 2))
        label = f"{i+1:02d} {os.path.basename(rel)[:-4]}  {w0}x{h0}"
        st = os.path.getmtime(p)
        import datetime
        label += "  " + datetime.datetime.fromtimestamp(st).strftime("%H:%M")
    else:
        label = f"{i+1:02d} MISSING {os.path.basename(rel)}"
    d0.rectangle([0, 0, IW - 1, IH + LH - 1], outline=(185, 185, 185))
    d0.rectangle([0, IH, IW - 1, IH + LH - 1], fill=(235, 235, 235))
    d0.text((6, IH + 4), label, fill="black", font=FONT)
    sheet.paste(tile, ((i % COLS) * IW, (i // COLS) * (IH + LH)))

out = os.path.join(PROJ, "临时产物", "验收总览.png")
sheet.save(out)
print("saved", out, sheet.size)
for rel in FIGS:
    p = os.path.join(PROJ, rel)
    print(("OK  " if os.path.exists(p) else "MISS"), rel,
          (Image.open(p).size if os.path.exists(p) else ""))
