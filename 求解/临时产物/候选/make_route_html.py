# -*- coding: utf-8 -*-
"""图0 技术路线：用 HTML + CSS 绘制，再由 Chrome 无头浏览器截图成 PNG。

坐标唯一来源 = LAYOUT。绘制代码只引用下面派生的 ROW/COL 变量，不出现手调数字。
设计画布 1440x640；窄版按 A4 版心 1180 宽等比缩放（同一份布局，S=1180/1440）。

运行： & 'E:\\python.exe' '临时产物\\候选\\make_route_html.py'
产出： 图0_技术路线.html      (1440x640  -> 截图 2880x1280)
        图0_技术路线_窄版.html (1180x524  -> 截图 2360x1048)
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ======================================================================
# 1. LAYOUT —— 全部几何常量（设计单位 = 1440 宽画布上的像素）
# ======================================================================
LAYOUT = {
    "canvas": {"w": 1440, "h": 1160, "narrow_w": 1180},

    "font": {
        "family": '"Times New Roman","SimSun",serif',
        # 与全篇一致的三档字号（pt）：标题条 11 / 正文 9.5 / 小注 8.5
        "pt_head": 21.0, "pt_body": 18.5, "pt_small": 16.0,
        "px_per_pt": 1.3333,          # 96dpi：1pt = 1.3333px（0.8pt ≈ 1.07px 同源）
        "lh": 1.32,
    },
    "color": {
        "deep": "#3C5488",            # NPG 深蓝：标题条文字 + 下划线 + 数据框左竖条
        "edge": "#9FA9B4",            # 普通框边
        "dash": "#C9D2DC",            # 任务分组虚线框
        "dash_sub": "#DDE3EA",        # 小组虚线框（更浅一档）
        "ink": "#26282D",
        "wire": "#5A6068",            # 箭头
    },
    # 线宽统一到 0.8pt 一档（0.8pt = 1.07px）；数据框左竖条按指定用 1.5px 强调
    "stroke": {"wire": 1.07, "marker": 5.5, "border": 1.07, "accent": 1.5},

    # 纵向：四个任务组共用一套行网格 —— 并列小框行同高 => 组间箭头同高
    "row": {
        "top": 36,          # 任务虚线框顶边（T1/T2/T3 齐平）
        "head_off": 16,     # 标题条距框顶
        "head_h": 58,       # 标题条高
        "r1": 140,          # 第 1 级步骤顶边（其余行由 r1 递推）
        "h": 86,            # 单行框高
        "h_small": 80,      # 并列小框高
        "h_tall": 146,       # 任务 3 首框（两行文字）
        "gap": 30,          # 普通行间距（也是 1->1 箭头长度）
        "gap_merge": 40,    # 汇合行间距（并列小框 -> 产出，留出 bus 空间）
        "pad": 36,          # 任务框底边内边距（要求 30–45）
        "sub_off": 18,      # 小组框距上方步骤框
        "sub_inset": 12,    # 小组框内边距
        "sub_gap": 20,      # 小组框内两行小框间距
        "frame_gap": 14,    # 任务 3 框底 -> 任务 4 框顶
        "t4_pair_off": 92,  # 任务 4 框顶 -> 其并列小框行
        "col_gap": 30,      # 列间距（组间水平箭头长度）
        "left_gap": 42,     # 左列 -> 任务 1 框的水平箭头长度
    },

    # 横向：每列 cx + 宽度；组内所有框共用 cx，成对小框 ±dx
    "col": {
        "left": {"cx": 111, "w": 150, "h1": 56, "h2": 64, "gap": 22},
        "t1": {"cx": 428, "frame_w": 430, "head_w": 300, "box_w": 372,
               "sub_w": 260, "sub_box_w": 112, "sub_dx": 62},
        "t2": {"cx": 818, "frame_w": 330, "head_w": 286, "box_w": 268,
               "pair_w": 140, "pair_dx": 74},
        "t34": {"cx": 1130, "frame_w": 280, "head_w": 262, "box_w": 250,
                "pair_w": 118, "pair_dx": 62},   # 任务 3 与任务 4 共用 => 同 x 同宽
        "out": {"cx": 1342, "w": 132, "h": 96, "elbow": 20},
    },

    "text": {
        "given": "给定数据",
        "sample": "帖级截面样本\n500 条 × 8 列",
        "t1_head": "任务 1\u00a0\u00a0数据理解",
        "t1_a": "识别变量类型与取值范围",
        "t1_subs": ["连续 2", "名义 2", "循环 3", "指示 1"],
        "t1_c": "判定粒度与结构：一行 = 一条帖子",
        "t1_d": "输出变量字典与因果角色",
        "t2_head": "任务 2\u00a0\u00a0清洗与编码",
        "t2_a": "缺失检查：仅 1 条",
        "t2_b": "填补与编码",
        "t2_p": ["X7 众数填补", "X2/X3 独热"],
        "t2_c": "log1p：偏度 0.73",
        "t3_head": "任务 3\u00a0\u00a0回归与诊断",
        "t3_a": "OLS + HC3\n稳健标准误",
        "t3_p": ["VIF 共线", "BP / JB 残差"],
        "t3_c": "10 折 CV：R² = 0.101",
        "t4_head": "任务 4\u00a0\u00a0效应与检验",
        "t4_p": ["付费 +40.1%", "视频 ×4.90"],
        "t4_c": "六种设定稳健性",
        "out": "结论与\n行动建议",
    },
}

# ======================================================================
# 2. 派生几何（全部由 LAYOUT 算出）
# ======================================================================
CW, CH = LAYOUT["canvas"]["w"], LAYOUT["canvas"]["h"]
NW = LAYOUT["canvas"]["narrow_w"]
R, COL, TXT = LAYOUT["row"], LAYOUT["col"], LAYOUT["text"]
CLR, FNT, STK = LAYOUT["color"], LAYOUT["font"], LAYOUT["stroke"]

TOP = R["top"]
HEAD_Y = TOP + R["head_off"]
HEAD_H = R["head_h"]
HEAD_B = HEAD_Y + HEAD_H
H, HSM, HTALL = R["h"], R["h_small"], R["h_tall"]
GAP, GAPM, PAD = R["gap"], R["gap_merge"], R["pad"]

# 行锚点：由 r1 按统一间距递推，全部组共用
R1 = R["r1"]
R2 = R1 + H + GAP                    # 第 2 级步骤（仅任务 2）
PAIR = R2 + H + GAP                  # 并列小框行（T1 组内 / T2 / T3 / T4 同高）
FIN = PAIR + H + GAPM                # 产出行（浅蓝）
PAIR_C = PAIR + H / 2                # 并列小框行中心 => 组间水平箭头高度

# 任务 1 内部小组框（2x2 小框）
SUB_Y = R1 + H + R["sub_off"]
SUB_H = R["sub_inset"] * 2 + HSM * 2 + R["sub_gap"]
SUB_B = SUB_Y + SUB_H

# 任务 1 第 3 / 4 级
T1_C_Y = SUB_B + GAPM                        # 判定粒度与结构
T1_D_Y = T1_C_Y + H + GAP                    # 输出变量字典（浅蓝）
T1_B = T1_D_Y + H + PAD                      # 任务 1 框底边

# 任务 2 / 3 框底边（同一行网格 => 同高）
MAIN_B = FIN + H + PAD

# 任务 4（任务 3 框下方）
T4_TOP = MAIN_B + R["frame_gap"]
T4_HEAD_Y = T4_TOP + R["head_off"]
T4_PAIR = T4_TOP + R["t4_pair_off"]
T4_FIN = T4_PAIR + H + GAPM
T4_B = T4_FIN + H + PAD

# 右侧输出框：右列（TOP..T4_B）垂直居中
OUT_H = COL["out"]["h"]
OUT_Y = (TOP + T4_B) / 2 - OUT_H / 2
OUT_C = OUT_Y + OUT_H / 2

# 左列：数据入口水平箭头与组间箭头同高（PAIR_C）
LEFT2_C = PAIR_C
LEFT2_Y = LEFT2_C - COL["left"]["h2"] / 2
LEFT_Y = LEFT2_Y - COL["left"]["gap"] - COL["left"]["h1"]

# 各列关键 x
L_CX, L_W = COL["left"]["cx"], COL["left"]["w"]
T1_CX, T1_FW = COL["t1"]["cx"], COL["t1"]["frame_w"]
T2_CX, T2_FW = COL["t2"]["cx"], COL["t2"]["frame_w"]
T3_CX, T3_FW = COL["t34"]["cx"], COL["t34"]["frame_w"]
O_CX, O_W = COL["out"]["cx"], COL["out"]["w"]

T1_L, T1_R = T1_CX - T1_FW / 2, T1_CX + T1_FW / 2
T2_L, T2_R = T2_CX - T2_FW / 2, T2_CX + T2_FW / 2
T3_L, T3_R = T3_CX - T3_FW / 2, T3_CX + T3_FW / 2
O_L, O_R = O_CX - O_W / 2, O_CX + O_W / 2


# ======================================================================
# 3. 绘制器
# ======================================================================
class Painter:
    """把设计单位翻成 CSS 像素；scale=1 时全部整数，窄版按比例缩放。"""

    def __init__(self, scale):
        self.s = scale
        self.nodes = []
        self.paths = []
        k = FNT["px_per_pt"] * scale
        self.fs_head = FNT["pt_head"] * k      # 已含缩放，直接写进 CSS
        self.fs_body = FNT["pt_body"] * k
        self.fs_small = FNT["pt_small"] * k

    # ---- 数值格式化 ----
    def n(self, v):
        v = v * self.s
        r = round(v, 2)
        return str(int(round(r))) if abs(r - round(r)) < 1e-6 else f"{r:.2f}"

    # ---- 元素 ----
    def box(self, cx, y, w, h, text, light=False, small=False, nowrap=True):
        cls = "b" + (" lt" if light else "") + (" sm" if small else "")
        lines = text.split("\n")
        style = (f"left:{self.n(cx - w / 2)}px;top:{self.n(y)}px;"
                 f"width:{self.n(w)}px;height:{self.n(h)}px")
        if len(lines) > 1:
            style += ";flex-direction:column"
        inner = "".join(f"<span>{ln}</span>" for ln in lines)
        self.nodes.append(f'<div class="{cls}" style="{style}">{inner}</div>')
        return (cx - w / 2, y, cx + w / 2, y + h)

    def head(self, cx, y, w, h, text):
        """任务标题条：深蓝字 + 下方 0.8pt 下划线（宽度 = 文字宽 + 20px），无底色。"""
        pad = 10
        lh_design = (self.fs_head / self.s) * FNT["lh"]      # 设计单位行高
        top = y + (h - lh_design) / 2.0
        self.nodes.append(
            f'<div class="hd" style="left:{self.n(cx)}px;top:{self.n(top)}px;'
            f'line-height:{self.n(lh_design)}px;'
            f'padding:0 {self.n(pad)}px;"><span>{text}</span></div>')
        return (cx - w / 2, y, cx + w / 2, y + h)

    def frame(self, cx, y, w, h, sub=False):
        cls = "sg" if sub else "g"
        self.nodes.insert(0,  # 虚线框永远在最底层
            f'<div class="{cls}" style="left:{self.n(cx - w / 2)}px;top:{self.n(y)}px;'
            f'width:{self.n(w)}px;height:{self.n(h)}px;"></div>')
        return (cx - w / 2, y, cx + w / 2, y + h)

    # ---- 连线（存设计单位，出 CSS 时才缩放）----
    def wire(self, pts, tip=False):
        self.paths.append((list(pts), tip))

    def _d(self, pts):
        return "M " + " L ".join(f"{self.n(x)} {self.n(y)}" for x, y in pts)

    def down(self, x, y0, y1):
        """竖直箭头，箭尖精确落在 y1（目标框上边）"""
        self.wire([(x, y0), (x, y1)], tip=True)

    def bus_merge(self, xs, y_src, y_dst, cx):
        """多路汇合：各源竖直下到 bus（取行间中点），横线连通，
        再由目标框中心 x 单箭头进入目标框，箭尖精确落在框边。"""
        bus_y = (y_src + y_dst) / 2
        for x in xs:
            self.wire([(x, y_src), (x, bus_y)])
        self.wire([(min(xs), bus_y), (max(xs), bus_y)])
        self.down(cx, bus_y, y_dst)

    def split(self, cx, y_src, y_dst, xs):
        """一对并列小框：从中心框下边分叉到两列（两条箭头各自落在小框中心 x）"""
        for x in xs:
            self.down(x, y_src, y_dst)

    # ---- 输出 ----
    def html(self, w, h):
        s = self.s
        fb, fs, fh = self.fs_body, self.fs_small, self.fs_head
        css = f"""
 html,body{{margin:0;padding:0;background:#fff}}
 #cv{{position:relative;width:{w}px;height:{h}px;background:#fff;overflow:hidden;
     font-family:{FNT['family']};color:{CLR['ink']};-webkit-font-smoothing:antialiased}}
 .b{{position:absolute;box-sizing:border-box;display:flex;align-items:center;
     justify-content:center;text-align:center;background:#fff;
     border:{STK['border']}px solid {CLR['edge']};border-radius:0;
     font-size:{fb:g}px;line-height:{FNT['lh']};padding:0 6px;z-index:2}}
 .b span{{display:block;white-space:nowrap}}
 .b.lt{{background:#fff;border-color:{CLR['edge']};
     border-left:{STK['accent']}px solid {CLR['deep']}}}
 .b.sm{{font-size:{fs:g}px}}
 .hd{{position:absolute;transform:translateX(-50%);box-sizing:border-box;
     white-space:nowrap;background:transparent;color:{CLR['deep']};
     border-bottom:{STK['border']}px solid {CLR['deep']};border-radius:0;
     font-size:{fh:g}px;z-index:2}}
 .hd span{{display:block;white-space:nowrap}}
 .g{{position:absolute;border:{STK['border']}px dashed {CLR['dash']};
     border-radius:0;z-index:1}}
 .sg{{position:absolute;border:{STK['border']}px dashed {CLR['dash_sub']};
      border-radius:0;z-index:1}}
 svg{{position:absolute;left:0;top:0;z-index:1}}
"""
        body = []
        for pts, tip in self.paths:
            m = ' marker-end="url(#ar)"' if tip else ""
            body.append(f'<path d="{self._d(pts)}"{m}/>')
        mw = round(STK["marker"] * s, 2)
        svg = (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
               f'<defs><marker id="ar" viewBox="0 0 10 10" refX="10" refY="5" '
               f'markerWidth="{mw}" markerHeight="{mw}" orient="auto">'
               f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{CLR["wire"]}"/></marker></defs>'
               f'<g stroke="{CLR["wire"]}" stroke-width="{STK["wire"]}" stroke-linecap="square" fill="none">'
               + "".join(body) + '</g></svg>')
        node_html = "\n".join(self.nodes)
        return (f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
                f'<title>图0 技术路线</title><style>{css}</style></head>'
                f'<body><div id="cv">\n{node_html}\n{svg}\n</div></body></html>')


# ======================================================================
# 4. 画图（只引用派生变量）
# ======================================================================
def draw(scale=1.0):
    p = Painter(scale)

    # ---------- 左列：给定数据 ----------
    p.box(L_CX, LEFT_Y, L_W, COL["left"]["h1"], TXT["given"], light=True)
    p.box(L_CX, LEFT2_Y, L_W, COL["left"]["h2"], TXT["sample"], light=True)
    p.down(L_CX, LEFT_Y + COL["left"]["h1"], LEFT2_Y)
    # 左列 -> 任务 1（水平箭头，落在虚线框左边）
    p.wire([(L_CX + L_W / 2, LEFT2_C), (T1_L, LEFT2_C)], tip=True)

    # ---------- 任务 1 ----------
    p.frame(T1_CX, TOP, T1_FW, T1_B - TOP)
    p.head(T1_CX, HEAD_Y, COL["t1"]["head_w"], HEAD_H, TXT["t1_head"])
    p.box(T1_CX, R1, COL["t1"]["box_w"], H, TXT["t1_a"])
    p.frame(T1_CX, SUB_Y, COL["t1"]["sub_w"], SUB_H, sub=True)
    dx1 = COL["t1"]["sub_dx"]
    for i, t in enumerate(TXT["t1_subs"]):
        col = -1 if i % 2 == 0 else 1
        row = 0 if i < 2 else 1
        y = SUB_Y + R["sub_inset"] + row * (HSM + R["sub_gap"])
        p.box(T1_CX + col * dx1, y, COL["t1"]["sub_box_w"], HSM, t, small=True)
    p.box(T1_CX, T1_C_Y, COL["t1"]["box_w"], H, TXT["t1_c"])
    p.box(T1_CX, T1_D_Y, COL["t1"]["box_w"], H, TXT["t1_d"], light=True)
    # 分叉：上框 -> 两列小框（箭头落在各列小框中心 x）
    p.split(T1_CX, R1 + H, SUB_Y, [T1_CX - dx1, T1_CX + dx1])
    # 小组框（虚线框整体）-> 判定粒度：单箭头落在目标框中心 x
    p.down(T1_CX, SUB_B, T1_C_Y)
    p.down(T1_CX, T1_C_Y + H, T1_D_Y)

    # ---------- 任务 2 ----------
    p.frame(T2_CX, TOP, T2_FW, MAIN_B - TOP)
    p.head(T2_CX, HEAD_Y, COL["t2"]["head_w"], HEAD_H, TXT["t2_head"])
    p.box(T2_CX, R1, COL["t2"]["box_w"], H, TXT["t2_a"])
    p.box(T2_CX, R2, COL["t2"]["box_w"], H, TXT["t2_b"])
    dx2 = COL["t2"]["pair_dx"]
    for i, t in enumerate(TXT["t2_p"]):
        p.box(T2_CX + (-1 if i == 0 else 1) * dx2, PAIR,
              COL["t2"]["pair_w"], H, t, small=True)
    p.box(T2_CX, FIN, COL["t2"]["box_w"], H, TXT["t2_c"], light=True)
    p.down(T2_CX, R1 + H, R2)
    p.split(T2_CX, R2 + H, PAIR, [T2_CX - dx2, T2_CX + dx2])
    p.bus_merge([T2_CX - dx2, T2_CX + dx2], PAIR + H, FIN, T2_CX)

    # ---------- 任务 3 ----------
    p.frame(T3_CX, TOP, T3_FW, MAIN_B - TOP)
    p.head(T3_CX, HEAD_Y, COL["t34"]["head_w"], HEAD_H, TXT["t3_head"])
    p.box(T3_CX, R1, COL["t34"]["box_w"], HTALL, TXT["t3_a"])
    dx3 = COL["t34"]["pair_dx"]
    for i, t in enumerate(TXT["t3_p"]):
        p.box(T3_CX + (-1 if i == 0 else 1) * dx3, PAIR,
              COL["t34"]["pair_w"], H, t, small=True)
    p.box(T3_CX, FIN, COL["t34"]["box_w"], H, TXT["t3_c"], light=True)
    p.split(T3_CX, R1 + HTALL, PAIR, [T3_CX - dx3, T3_CX + dx3])
    p.bus_merge([T3_CX - dx3, T3_CX + dx3], PAIR + H, FIN, T3_CX)

    # ---------- 任务 4 ----------
    p.frame(T3_CX, T4_TOP, T3_FW, T4_B - T4_TOP)
    p.head(T3_CX, T4_HEAD_Y, COL["t34"]["head_w"], HEAD_H, TXT["t4_head"])
    for i, t in enumerate(TXT["t4_p"]):
        p.box(T3_CX + (-1 if i == 0 else 1) * dx3, T4_PAIR,
              COL["t34"]["pair_w"], H, t, small=True)
    p.box(T3_CX, T4_FIN, COL["t34"]["box_w"], H, TXT["t4_c"])
    p.bus_merge([T3_CX - dx3, T3_CX + dx3], T4_PAIR + H, T4_FIN, T3_CX)

    # ---------- 右侧输出 ----------
    p.box(O_CX, OUT_Y, O_W, OUT_H, TXT["out"], light=True)

    # ---------- 组间水平箭头（同一条水平线 = 并列小框行中心）----------
    y_bus = PAIR_C
    p.wire([(T1_R, y_bus), (T2_L, y_bus)], tip=True)
    p.wire([(T2_R, y_bus), (T3_L, y_bus)], tip=True)

    # ---------- 任务 3 -> 输出：进入框左中 ----------
    elbow = T3_R + COL["out"]["elbow"]
    p.wire([(T3_R, y_bus), (elbow, y_bus), (elbow, OUT_C), (O_L, OUT_C)], tip=True)
    # ---------- 任务 4 -> 输出：进入框下中 ----------
    y_t4 = T4_PAIR + H / 2
    p.wire([(T3_R, y_t4), (O_CX, y_t4), (O_CX, OUT_Y + OUT_H)], tip=True)

    return p


def emit(scale, w, h, out_name):
    p = draw(scale)
    html = p.html(w, h)
    path = HERE / out_name
    path.write_text(html, encoding="utf-8")
    return path


if __name__ == "__main__":
    wide = emit(1.0, CW, CH, "图0_技术路线.html")
    s = NW / CW
    nh = round(CH * s)
    narrow = emit(s, NW, nh, "图0_技术路线_窄版.html")
    print("wide  ->", wide, f"({CW}x{CH})")
    k = FNT["px_per_pt"]
    print("narrow->", narrow,
          f"({NW}x{nh}, scale={s:.5f}, 正文 {FNT['pt_body']*k*s:.2f}px"
          f" = {FNT['pt_body']*k*s/2:.2f}pt@2x)")
    print("\n截图（宽版 2880x1280 / 窄版 2360x{}）：".format(nh * 2))
    print(f'  chrome --headless=new --disable-gpu --hide-scrollbars '
          f'--force-device-scale-factor=2 --window-size={CW},{CH} '
          f'--screenshot="临时产物\\候选\\图0_技术路线.png" "{wide.as_uri()}"')
    print(f'  chrome --headless=new --disable-gpu --hide-scrollbars '
          f'--force-device-scale-factor=2 --window-size={NW},{nh} '
          f'--screenshot="临时产物\\候选\\图0_技术路线_窄版.png" "{narrow.as_uri()}"')
    print("\n若本机已有 Chrome 在跑导致无头截图静默失败(exit 1)，加一个独立用户目录即可：")
    print('  --user-data-dir=%TEMP%\\dsh-chrome-shot --no-first-run --no-default-browser-check')
