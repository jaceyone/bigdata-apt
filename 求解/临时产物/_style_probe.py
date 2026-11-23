# -*- coding: utf-8 -*-
"""样式探针：确认 nature plot_style 接管成功、中文字体可用。"""
import matplotlib
matplotlib.use("Agg")
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import nature_style
import matplotlib.pyplot as plt

print("font.family   :", matplotlib.rcParams["font.family"])
print("font.serif[:3]:", matplotlib.rcParams["font.serif"][:3])
print("axes.linewidth:", matplotlib.rcParams.get("axes.linewidth"))
print("xtick.direction:", matplotlib.rcParams.get("xtick.direction"))
print("savefig.dpi   :", matplotlib.rcParams.get("savefig.dpi"))
print("axes.spines.top:", matplotlib.rcParams.get("axes.spines.top"))

import sys
sys.path.insert(0, nature_style.NATURE_DIR)
import plot_style
print("palette       :", plot_style.active_palette() if hasattr(plot_style, "active_palette") else "n/a")

fig, ax = plt.subplots(figsize=(3.2, 2.2))
ax.plot([1, 2, 3], [3, 1, 2], marker="o", label="测试曲线")
ax.set_xlabel("月份")
ax.set_ylabel("曝光（次）")
ax.legend()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_style_probe.png")
fig.savefig(out, dpi=150, bbox_inches="tight")
print("probe ->", out)
