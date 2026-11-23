# -*- coding: utf-8 -*-
"""生成 支撑材料\00_材料总览.docx

版式按论文表 21（源码与结果索引）的三线表：环节 / 脚本 / 输出，
行序严格跟着「求解\支撑材料」的 01–06 目录走；后续各表是它的明细索引。
数据只从支撑材料内的 md/CSV 读取，不重算、不改论文。
"""
import os
import re
import sys

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = r"C:\Users\28466\AppData\Roaming\MriteUltra-2.6.13\Mrite-Agent-Space\数学建模\projects\通用练习_2026-11-22_09-12-35\求解"
S = os.path.join(ROOT, "支撑材料")
OUT = os.path.join(S, "00_材料总览.docx")

CN_FONT = "宋体"
EN_FONT = "Times New Roman"
C = WD_ALIGN_PARAGRAPH.CENTER
L = WD_ALIGN_PARAGRAPH.LEFT


# ────────────────────────── 排版工具 ──────────────────────────
def set_run(run, size=9, bold=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = EN_FONT
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), EN_FONT)
    rfonts.set(qn("w:hAnsi"), EN_FONT)
    rfonts.set(qn("w:eastAsia"), CN_FONT)
    return run


def para(doc, text="", size=10.5, bold=False, align=L, before=0, after=0,
         line=1.25, indent=0, keep_next=False):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    if indent:
        pf.first_line_indent = Pt(indent)
    pf.keep_with_next = keep_next
    if text:
        set_run(p.add_run(text), size=size, bold=bold)
    return p


def caption(doc, number, title):
    p = doc.add_paragraph()
    p.alignment = C
    pf = p.paragraph_format
    pf.space_before = Pt(10)
    pf.space_after = Pt(3)
    pf.keep_with_next = True          # 表题不与表体分离
    set_run(p.add_run("表 %d  " % number), size=10.5, bold=True)
    set_run(p.add_run(title), size=10.5, bold=True)
    return p


def note(doc, text):
    p = doc.add_paragraph()
    p.alignment = L
    pf = p.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(8)
    pf.line_spacing = 1.0
    pf.keep_with_next = True          # 表注跟着下一节走，避免孤零零掉页
    set_run(p.add_run(text), size=8)
    return p


def _border(tag, val="single", sz=12):
    el = OxmlElement("w:%s" % tag)
    el.set(qn("w:val"), val)
    el.set(qn("w:sz"), str(sz))
    el.set(qn("w:space"), "0")
    el.set(qn("w:color"), "000000")
    return el


def three_line(table):
    """三线表：表顶粗线 + 表头下细线 + 表底粗线，其余线全去。"""
    tbl = table._tbl
    tblPr = tbl.tblPr
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    borders = OxmlElement("w:tblBorders")
    borders.append(_border("top", "single", 12))
    borders.append(_border("left", "none", 0))
    borders.append(_border("bottom", "single", 12))
    borders.append(_border("right", "none", 0))
    borders.append(_border("insideH", "none", 0))
    borders.append(_border("insideV", "none", 0))
    tblPr.append(borders)

    for cell in table.rows[0].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        for old in tcPr.findall(qn("w:tcBorders")):
            tcPr.remove(old)
        tcb = OxmlElement("w:tcBorders")
        tcb.append(_border("bottom", "single", 6))
        tcPr.append(tcb)


def fill_cell(cell, text, size=8.5, bold=False, align=C):
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = cell.paragraphs[0]
    p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(1.5)
    pf.space_after = Pt(1.5)
    pf.line_spacing = 1.05
    for i, piece in enumerate(str(text).split("\n")):
        if i:
            p.add_run().add_break()
        set_run(p.add_run(piece), size=size, bold=bold)


def build_table(doc, headers, rows, widths, size=8.5, body_align=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    table._tbl.tblPr.append(layout)

    for j, w in enumerate(widths):
        for row in table.rows:
            row.cells[j].width = Cm(w)

    for j, h in enumerate(headers):
        fill_cell(table.rows[0].cells[j], h, size=size, bold=True)

    # 表头重复 + 所有行禁止跨页断开
    trPr = table.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)
    for row in table.rows:
        trPr2 = row._tr.get_or_add_trPr()
        cs = OxmlElement("w:cantSplit")
        cs.set(qn("w:val"), "true")
        trPr2.append(cs)

    body_align = body_align or [C] * len(headers)
    for i, r in enumerate(rows, start=1):
        for j, v in enumerate(r):
            fill_cell(table.rows[i].cells[j], v, size=size, align=body_align[j])

    three_line(table)
    return table


def clean(s):
    s = str(s).replace("**", "")
    s = re.sub(r"`([^`]*)`", r"\1", s)
    return s.replace("\\", "/").replace("　", " ").strip()


def parse_speed_table():
    path = os.path.join(S, "06_答辩备忘", "关键数字速查.md")
    rows = []
    for line in open(path, encoding="utf-8").read().splitlines():
        line = line.strip()
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        rows.append((cells[0], clean(cells[1]), clean(cells[2]), clean(" ".join(cells[3:]))))
    return rows


# ────────────────────────── 正文 ──────────────────────────
def main():
    doc = Document()
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.PORTRAIT
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.54)
    sec.top_margin = sec.bottom_margin = Cm(2.54)

    st = doc.styles["Normal"]
    st.font.name = EN_FONT
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), CN_FONT)

    para(doc, "赛题支撑材料目录", size=16, bold=True, align=C, after=4)
    para(doc, "全国大学生大数据分析技术技能决赛（本科 Python 组）", size=10.5, align=C, after=2)
    para(doc, "题目：社交帖子曝光的影响因素与投放效应测算", size=10.5, align=C, after=2)
    para(doc, "材料根目录：求解 / 支撑材料        编制日期：2026-11-22", size=9, align=C, after=12)

    para(doc, "本目录按「求解/支撑材料」的 01–06 目录顺序编排，每一行对应一个材料环节，"
              "列出其来源脚本与产出文件。全部数值均由支撑材料内的 CSV 现读核对，未重算、未改动求解结果；"
              "路径一律相对「求解」目录。",
         size=10.5, indent=21, after=2)
    para(doc, "论文插图 14 张、表格 21 张的编号与文件名不是同一套（插图按出现顺序重编，文件名按出图顺序编），"
              "表 3、表 4 给出完整对照。",
         size=10.5, indent=21, after=2)

    # ── 表 1：目录（严格照论文表 21：环节 / 脚本 / 输出 三列五行） ──
    caption(doc, 1, "源码与结果索引")
    rows1 = [
        ("数据理解", "求解/问题一/代码/主程序.py",
         "表 1–3、相关系数.csv、绘图数据_分布.csv、绘图数据_月份.csv、图 1–3"),
        ("清洗与编码", "求解/问题二/代码/主程序.py",
         "表 4–6、表 6b、清洗数据.csv、绘图数据_类别/小时/变换.csv、图 4–5"),
        ("回归与诊断", "求解/问题三/代码/主程序.py",
         "表 7–12、VIF.csv、CV结果.csv、Shapley.csv、绘图数据_森林/残差/预测.csv、图 6–10、图 15"),
        ("效应与稳健性", "求解/问题四/代码/主程序.py",
         "表 13–16、调整预测.csv、稳健性系数.csv、效应测算.csv、图 11–12、图 16"),
        ("子样本异质性", "求解/问题四/代码/图17_付费效应异质性森林.py",
         "子样本异质性.csv、论文表 19、图 17"),
    ]
    build_table(doc, ("环节", "脚本", "输出"), rows1, (3.2, 6.0, 6.7), size=8.5,
                body_align=[C, L, L])
    note(doc, "注：表 17 的数据源（稳健性系数矩阵.csv）由 求解/问题四/代码/表17_稳健性系数矩阵.py 单独生成，"
              "不在上述四个主程序内。论文附录表 21 的输出列用的是旧编号（问题一写「图 2、图 3、图 6、图 7」，"
              "问题三写「图 10–13」），与终稿实际插图不符，本表已按真实文件编号订正。"
              "材料落盘位置为 01_原始数据 / 02_清洗数据 / 03_结果表 / 04_图表 / 05_代码 / 06_答辩备忘，共 69 个文件、13.8 MB。")

    # ── 表 2：题面索引 ──
    caption(doc, 2, "题面 2.1–2.4 要求与材料对应")
    rows2 = [
        ("2.1.1 单位与粒度", "§2.1", "01_原始数据、表 1、表 3", "500 行 = 500 条帖子；8 字段；重复行 0"),
        ("2.1.2 截面还是时序", "§2.1、§3.3", "表 3、图 2", "ρ = 0.995966；辅助 R² = 0.991730；月内方差占比 0.008254"),
        ("2.1.3 因果角色", "§2.1、§2.2", "表 1（因果角色列）", "6 个发帖决策 + 1 个账号状态 + 1 个结果"),
        ("2.2.1 缺失值处理", "§3.1", "表 4、表 6b、图 5", "缺失 1 条（0.2%）；众数填补；与删除版差 0.001084"),
        ("2.2.2 类型与编码", "§3.2", "表 5、表 6、清洗数据", "偏度 8.3259→0.7341；峰度 93.0526→0.8209"),
        ("2.3.1-A 系数表", "§4.2", "表 11", "付费 0.3374；Status 1.1538；Video 1.5896；主题 2 −0.4784"),
        ("2.3.1-B p 值", "§4.2", "表 11（p 值列）", "付费 0.0050；主题 3 0.0190；Link 0.6428"),
        ("2.3.1-C R²", "§4.1–§4.2", "表 10", "R² = 0.2068；调整 R² = 0.1650"),
        ("2.3.2-A 共线性诊断", "§4.3", "表 8、VIF.csv、图 10", "M1 最大 VIF 142.9938 → M2 3.2320"),
        ("2.3.2-B 残差诊断", "§4.3", "表 9、绘图数据_残差.csv、图 9", "JB 120.3604；BP 54.7371（p = 0.0005）；Cook 0.0377；超阈 30 个"),
        ("2.3.2-C 整体显著性与拟合", "§4.2", "表 10", "F = 4.9443（p < 0.001，26 参数）；残差标准误 1.0765"),
        ("2.3.2-D 预测能力", "§4.4", "表 10（CV 列）、图 11", "CV R² 0.1010；RMSE 1.1007；MAE 0.8328；基线 −0.0212"),
        ("2.4.1 付费的额外曝光", "§5.2", "表 13、调整预测.csv、图 12", "+40.1325%（CI 10.7962–77.2364）；画像 +16,142 次；ATE +10,907 次"),
        ("2.4.2 Video 比 Photo 高多少", "§5.2", "表 14", "×4.9017（CI 2.2262–10.7925）；n = 7"),
        ("2.4.3 主题是否显著", "§5.2", "表 15", "联合 Wald 12.6783（p = 0.0018）；×0.6198 与 ×0.7300"),
    ]
    build_table(doc, ("题面条目", "报告章节", "支撑文件（相对 求解/）", "关键数值"), rows2,
                (3.9, 2.2, 4.6, 5.2), size=8, body_align=[L, C, L, L])
    note(doc, "注：题面第三节要求报告含「项目概述 / 分析目标 / 运用方法概述 / 结果分析 / 结论」，"
              "分别对应 §1、§1.2、§1.4 与算法 1、§2–§5、§6。")

    # ── 表 3：插图对照 ──
    caption(doc, 3, "论文插图与文件对照")
    rows3 = [
        ("图 1", "4", "图0_技术路线.png", "四环节数据流与判据（0.9 / 0.9 / 5% / CV R² / VIF < 5）"),
        ("图 2", "7", "图1_曝光与分组分布.png", "均值 29,586；中位 9,051；偏度 8.33；付费中位 12,060 vs 自然 8,443"),
        ("图 3", "8", "补充图1_样本结构.png", "307/119、35/10、16/6、3/4；r(logX1, logY) = −0.082（p = 0.066）"),
        ("图 4", "8", "图3_相关系数热力图.png", "logX1 × X4 = 0.996（黑圈）；与 logY 各项 |r| < 0.17"),
        ("图 5", "11", "图4_类别结构与缺失.png", "Photo 426（85.2%）、Video 7（1.4%）；3 时 105、10 时 78"),
        ("图 6", "11", "图5_变换前后分布.png", "偏度 8.33→0.73；峰度 93.05→0.82；首箱 79.2% / 82.8%"),
        ("图 7", "13", "图2_粉丝规模与月份共线.png", "r = 0.941；ρ = 0.996；R² = 0.992；月内 SD 0.013"),
        ("图 8", "16", "图6_最终模型系数森林图.png", "付费 ×1.40；Status ×3.17；Video ×4.90；主题 ×0.62 / ×0.73"),
        ("图 9", "16", "图8_残差诊断.png", "BP = 54.7（p = 0.0005）；JB = 120.4；Cook > 4/n 共 30 个"),
        ("图 10", "17", "图7_共线性诊断.png", "月份 143.0→3.2；logX1 124.9 已剔除；M2 最大 3.23"),
        ("图 11", "18", "图9_预测能力验证.png", "0.207→0.101；RMSE 1.101；MAE 0.833；M0 −0.021"),
        ("图 12", "21", "图11_调整预测效应.png", "4.02→5.64 万（+40.1%，+16,142 次）；Video 19.72 万；交互 p = 0.530"),
        ("图 13", "22", "图12_效应稳健性.png", "40.1%（37.4–49.6%）；×4.90（×3.52–×5.41）"),
        ("图 14", "23", "图13_核心结论总览.png", "+40.1% / ×4.90 / R² = 0.207 / VIF 143.0→3.23"),
    ]
    build_table(doc, ("论文图号", "页码", "实际文件（04_图表/）", "数据源与图内关键量"), rows3,
                (1.8, 1.3, 5.0, 7.8), size=8, body_align=[C, C, L, L])
    note(doc, "注：页码为 2026-11-22 20:30 重编译版编号；论文每重编译一次页码会漂 1–2 页，图号不变，复核请按图题对。"
              "图 10、图 14–17 与补充图 2–3 已出图但未入正文，见图号对照表第二节。")

    # ── 表 4：表格对照 ──
    caption(doc, 4, "论文表格与结果 CSV 对照")
    rows4 = [
        ("表 1", "原始数据前 10 行", "清洗数据.csv（前 10 行）"),
        ("表 2", "原始数据后 10 行", "清洗数据.csv（后 10 行）"),
        ("表 3", "各环节采用的方法与判别标准", "正文内联（无 CSV）"),
        ("表 4", "主要变量的描述统计", "表2_描述性统计.csv"),
        ("表 5", "变量字典、类型与建模角色", "表1_变量字典.csv"),
        ("表 6", "缺失、异常与一致性检查", "表4_缺失与异常检查.csv"),
        ("表 7", "缺失处理方案比较", "表6b_缺失处理敏感性.csv"),
        ("表 8", "变量编码与变换方案", "表5_编码与变换方案.csv"),
        ("表 9", "样本结构与共线判别指标", "表3_共线与分布指标.csv"),
        ("表 10", "五个候选模型的拟合、整体显著性与十折交叉验证", "表10_模型比较与交叉验证.csv（= CV结果.csv）"),
        ("表 11", "最终模型 M2 的系数估计", "表11_最终模型系数表.csv"),
        ("表 12", "残差诊断检验结果", "表9_残差诊断检验.csv"),
        ("表 13", "七个变量组的 Shapley R² 分解", "表12_Shapley方差分解.csv（= Shapley.csv）"),
        ("表 14", "三个代表性新观测的预测曝光与区间", "调整预测.csv（面板 a / b / c）"),
        ("表 15", "付费投放的曝光效应测算", "表13_付费效应测算.csv"),
        ("表 16", "内容类型相对 Photo 的曝光差异", "表14_内容类型效应与两两对比.csv"),
        ("表 17", "内容主题的联合检验与两两对比", "表15_内容主题X3效应与两两对比.csv"),
        ("表 18", "六种模型设定下的效应稳健性", "表16_效应稳健性对比.csv"),
        ("表 19", "付费效应的子样本异质性", "子样本异质性.csv"),
        ("表 20", "分析任务、方法与核心结果", "正文内联（无 CSV）"),
        ("表 21", "源码与结果索引", "正文内联（无 CSV）"),
    ]
    build_table(doc, ("论文表号", "表题", "源 CSV（03_结果表/ 或 02_清洗数据/）"), rows4,
                (1.8, 7.0, 7.1), size=8, body_align=[C, L, L])
    note(doc, "注：论文表号与 CSV 编号不是一套（论文表 4 才是 表2_描述性统计.csv）。"
              "表6_变换前后分布特征.csv 与 表8_共线性诊断.csv 已生成但未入正文，其数字仍被 §3.2、§4.3 引用。"
              "求解目录里没有名为「表17_*.csv」的文件：表 17 的数据源是 稳健性系数矩阵.csv。")

    # ── 表 5：关键数字速查 ──
    speed = parse_speed_table()
    caption(doc, 5, "关键数字速查（%d 条）" % len(speed))
    build_table(doc, ("序号", "数值", "含义", "出处（文件 → 列名 / 行）"),
                speed, (1.0, 3.9, 3.5, 7.5), size=7.5, body_align=[C, L, L, L])
    note(doc, "注：全部数值由 pandas 从支撑材料内的 CSV 现读核对，未重算、未改动结果。"
              "第 63–65 条是两种缺失处置口径的对照：500 行（填补）与 499 行（删除），"
              "论文 §2.3 用 499 行口径，表 13 用 500 行口径。")

    # ── 表 6：缺失与偏差 ──
    caption(doc, 6, "材料缺失与偏差说明")
    rows6 = [
        ("原始数据文件名", "题面写 dataset_facebook_bk.csv，Downloads 中实际为 "
                          "dataset_Facebook_bk_1795187258429.csv；已按题面名另存并记录原名与 SHA256。"),
        ("表 17 的 CSV", "求解目录只有脚本 表17_稳健性系数矩阵.py，无同名 CSV；"
                        "以其输出 稳健性系数矩阵.csv 作为表 17 数据源索引。"),
        ("大文件", "无 png / csv 超过 2 MB，21 张 PNG 与 35 个 CSV 全部按原名复制；"
                  "脚本、主模型.pkl、论文 PDF 未复制，只建索引。"),
        ("未入正文的图", "图 10、图 14、图 15、图 16、图 17 与补充图 2、补充图 3 已产出但未插入论文，保留备查。"),
        ("正文与表格的口径差异", "§2.3 的自然组中位 8,443（+42.8%）、主题 2 中位 8,962 属 499 行删缺失口径；"
                              "表 13 的 8,387（+43.79%）、8,870.5 属 500 行填补口径。两套同源，结论不变。"),
        ("残差检验的表述", "§4.3 引的 JB 118.97、BP 56.52 是 M1 的值（M2 为 120.3604、54.7371）；"
                        "「White 与 RESET 同样拒绝」在 M2 下仅 White 成立（RESET p = 0.0591 未拒绝）。"),
    ]
    build_table(doc, ("项目", "说明"), rows6, (3.6, 12.3), size=8, body_align=[C, L])

    para(doc, "材料根目录：求解 / 支撑材料        生成时间：2026-11-22", size=8,
         align=WD_ALIGN_PARAGRAPH.RIGHT, before=8)

    doc.save(OUT)
    print("saved:", OUT)
    print("tables:", len(doc.tables), "| 速查行数:", len(speed))


if __name__ == "__main__":
    main()
