# -*- coding: utf-8 -*-
"""渲染指定页码，检查浮动体与空白。"""
import os
import sys
import pymupdf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(os.path.dirname(os.path.dirname(HERE)), "论文", "论文.pdf")
doc = pymupdf.open(PDF)

for page_no in (20, 21, 22, 28, 29, 30):
    pix = doc[page_no - 1].get_pixmap(dpi=110)
    out = os.path.join(HERE, f"检查_第{page_no}页.png")
    pix.save(out)
    print(page_no, "->", out)
