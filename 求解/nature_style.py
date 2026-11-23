# -*- coding: utf-8 -*-
r"""把 `国赛论文改造\nature风格样式\plot_style.py` 接管为全篇绘图样式。

用法：在绘图脚本里 **先** `import nature_style`，再 `from _common import ...`。
它会：
1) 调 plot_style.apply()（Nature/NPG 配色 + 宋体/Times + 期刊刻度与边框）；
2) 把 _common 的 get_plot_style / apply_plot_material 换成空实现，
   避免 _common 的 per-axes 硬样式覆盖 plot_style 的全局样式。
"""
import os
import sys

NATURE_DIR = r"E:\桌面\国赛论文改造\nature风格样式"
if NATURE_DIR not in sys.path:
    sys.path.insert(0, NATURE_DIR)

import plot_style as _ps  # noqa: E402

_APPLIED = False


def ensure(palette: str = "nature", dpi: int = 400):
    """应用一次全局样式；重复调用无副作用。"""
    global _APPLIED
    if not _APPLIED:
        _ps.apply(dpi=dpi, palette=palette)
        _APPLIED = True
    return _ps


def save(fig, name_cn, dpi: int = 400, **kw):
    """按项目既有约定输出 PNG（复用 _common.save_fig 的路径与可编辑 SVG）。"""
    import _common
    return _common.save_fig(fig, name_cn, dpi=dpi, **kw)


# —— 接管 _common 的两个钩子（必须在脚本 import _common 之前生效）——
def _get_plot_style(scheme=None, *a, **k):
    ensure()
    return None


def _apply_plot_material(ax, profile=None, *a, **k):
    return ax


def install(palette: str = "nature"):
    import _common
    ensure(palette)
    _common.get_plot_style = _get_plot_style
    _common.apply_plot_material = _apply_plot_material
    return _ps


install()
