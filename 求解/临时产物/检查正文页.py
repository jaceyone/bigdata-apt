# -*- coding: utf-8 -*-
"""按关键词定位改动较大的正文页并渲染。"""
import os
import sys
import pymupdf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(os.path.dirname(os.path.dirname(HERE)), "论文", "论文.pdf")
doc = pymupdf.open(PDF)

targets = [
    ("诊断指标与判别标准", "问题一诊断"),
    ("模型设定与诊断", "问题三方法"),
    ("测算方法", "问题四方法"),
    ("灵敏度分析结果", "稳健性检验"),
]

for key, name in targets:
    for i, page in enumerate(doc):
        if i < 3:
            continue
        text = page.get_text("text")
        if key in text:
            pix = page.get_pixmap(dpi=120)
            out = os.path.join(HERE, f"检查_{name}.png")
            pix.save(out)
            print(name, "page", i + 1, "->", out)
            break
