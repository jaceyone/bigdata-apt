# -*- coding: utf-8 -*-
"""定位报告中的目录页与结论页，渲染为 PNG 供检查。"""
import os
import sys
import pymupdf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(os.path.dirname(os.path.dirname(HERE)), "论文", "论文.pdf")

doc = pymupdf.open(PDF)
print("pages:", doc.page_count)
for i, page in enumerate(doc):
    text = page.get_text("text")
    flags = [key for key in ("目录", "分问题分析与结果", "主要结论", "核心结论总览", "符号说明") if key in text]
    if flags:
        print(f"p{i + 1}: {'/'.join(flags)}")

targets = [(2, "目录页")]
for i, page in enumerate(doc):
    if i < 2:
        continue
    if "主要结论" in page.get_text("text"):
        targets.append((i + 1, "结论页"))
        break

for page_no, name in targets:
    pix = doc[page_no - 1].get_pixmap(dpi=130)
    out = os.path.join(HERE, f"检查_{name}.png")
    pix.save(out)
    print("render", name, "page", page_no, "->", out)
