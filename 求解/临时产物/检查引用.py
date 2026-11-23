# -*- coding: utf-8 -*-
"""检查 PDF 中是否存在未解析的引用或交叉引用。"""
import os
import sys
import pymupdf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(os.path.dirname(os.path.dirname(HERE)), "论文", "论文.pdf")
doc = pymupdf.open(PDF)

print("pages:", doc.page_count)
hits = []
for i, page in enumerate(doc):
    text = page.get_text("text")
    if "??" in text:
        hits.append(i + 1)
print("question marks on pages:", hits or "none")

for key in ("符号说明", "模型的建立与求解", "模型的评价", "模型的改进与推广"):
    pages = [i + 1 for i, p in enumerate(doc) if key in p.get_text("text")]
    print(key, "->", pages or "none")
