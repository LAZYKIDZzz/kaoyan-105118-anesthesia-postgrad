#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2-2027：由 data/master.json 生成 Excel 决策总表"""
import json, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = json.load(open(os.path.join(BASE, 'data/master.json'), encoding='utf-8'))['schools']

wb = Workbook()

HDR_FILL = PatternFill('solid', fgColor='1F3A5F')
HDR_FONT = Font(color='FFFFFF', bold=True, size=10.5, name='PingFang SC')
THIN = Side(style='thin', color='D6D2C8')
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

# 门槛配色（中国习惯：低分=绿=安全，高分=红=危险）
FILL_SAFE = PatternFill('solid', fgColor='DFF3E4')   # ≤310
FILL_OK = PatternFill('solid', fgColor='FFF6DC')     # 311-340
FILL_WARN = PatternFill('solid', fgColor='FDE8D7')   # 341-350
FILL_HOT = PatternFill('solid', fgColor='FADBD8')    # >350


def style_header(ws, headers, widths):
    for c, (h, w) in enumerate(zip(headers, widths), start=1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = BORDER
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = 'A2'


HEADERS = ['序', '院校名称', '省份', '城市', '层次', '区', '2026统考\n计划', '2026\n复试线',
           '线别', '实录\n最低分', '实录\n均分', '实录\n人数', '参考门槛', '置信度',
           '关键提示', '数据来源']
WIDTHS = [4, 20, 8, 8, 8, 5, 8, 7, 14, 7, 7, 6, 9, 12, 62, 46]


def fill_row(ws, r, i, row):
    vals = [i, row['name'], row['region'], row['city'], row['level'], row['zone'],
            row['plan'], row['fs'], row['fs_kind'], row['lo'], row['avg'], row['cnt'],
            row['gate'], row['conf'],
            (row['note'] or row['unit_detail'] or '')[:400],
            (row['source'] or row['old_source'] or '')[:300]]
    for c, v in enumerate(vals, start=1):
        cell = ws.cell(row=r, column=c, value=v)
        cell.border = BORDER
        cell.font = Font(size=10, name='PingFang SC')
        if c in (1, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13):
            cell.alignment = Alignment(horizontal='center', vertical='center')
        else:
            cell.alignment = Alignment(vertical='center', wrap_text=True)
    g = row['gate']
    fill = None
    if g is not None:
        fill = FILL_SAFE if g <= 310 else (FILL_OK if g <= 340 else (FILL_WARN if g <= 350 else FILL_HOT))
    elif row['conf'].startswith('D'):
        fill = PatternFill('solid', fgColor='F0EFEA')
    if fill:
        for c in range(1, len(vals) + 1):
            ws.cell(row=r, column=c).fill = fill


# ---------- Sheet1 总表 ----------
ws = wb.active
ws.title = '总表·99所'
style_header(ws, HEADERS, WIDTHS)
for i, row in enumerate(M, start=1):
    fill_row(ws, i + 1, i, row)
ws.auto_filter.ref = f"A1:P{len(M)+1}"

# ---------- Sheet2 350以下专题 ----------
ws2 = wb.create_sheet('350分以下专题')
style_header(ws2, HEADERS, WIDTHS)
sub = [r for r in M if r['gate'] is not None and r['gate'] <= 350]
for i, row in enumerate(sub, start=1):
    fill_row(ws2, i + 1, i, row)
ws2.auto_filter.ref = f"A1:P{len(sub)+1}"

# ---------- Sheet3 350以下·按安全度分档 ----------
ws3 = wb.create_sheet('350以下·分档')
H3 = ['档位', '参考门槛区间', '院校', '省份', '区', '2026计划', '2026复试线', '实录最低', '关键提示']
W3 = [16, 14, 20, 8, 5, 8, 9, 9, 86]
style_header(ws3, H3, W3)
TIERS = [
    ('★保底档', '≤300', lambda g: g <= 300),
    ('◆稳妥档', '301-320', lambda g: 301 <= g <= 320),
    ('▲进取档', '321-335', lambda g: 321 <= g <= 335),
    ('⚠临界档', '336-350', lambda g: 336 <= g <= 350),
]
r = 2
for label, rng, fn in TIERS:
    grp = [x for x in sub if fn(x['gate'])]
    grp.sort(key=lambda x: x['gate'])
    for j, row in enumerate(grp):
        vals = [label if j == 0 else '', rng if j == 0 else '', row['name'], row['region'], row['zone'],
                row['plan'], row['fs'], row['lo'], (row['note'] or row['unit_detail'] or '')[:500]]
        for c, v in enumerate(vals, start=1):
            cell = ws3.cell(row=r, column=c, value=v)
            cell.border = BORDER
            cell.font = Font(size=10, name='PingFang SC')
            cell.alignment = Alignment(vertical='center', wrap_text=True,
                                       horizontal='center' if c in (1, 2, 4, 5, 6, 7, 8) else 'left')
        g = row['gate']
        f = FILL_SAFE if g <= 310 else (FILL_OK if g <= 335 else FILL_WARN)
        for c in range(1, len(vals) + 1):
            ws3.cell(row=r, column=c).fill = f
        r += 1

# ---------- Sheet4 数据说明 ----------
ws4 = wb.create_sheet('数据说明')
ws4.column_dimensions['A'].width = 22
ws4.column_dimensions['B'].width = 110
NOTES = [
    ('主题', '105118 麻醉学（专业学位硕士）2027 年度报考决策数据表'),
    ('院校范围', f'共 {len(M)} 所。已排除云南、新疆、西藏、青海、广西五省区院校（用户指定）。'),
    ('数据年度', '以 2026 年（最新完整招生年度）为主；无 2026 数据时回落到旧库 2025 年值并标注。'),
    ('国家线', '2026 年 A 区：总分 294（政治/外语 36，业务课 108）；B 区：总分 284（33 / 99）。'),
    ('参考门槛', '优先取「实录最低分」；无实录时取「复试线」；再无取旧库值。这是报考的实务参考分。'),
    ('⚠ 校线≠录取线', '多数院校校线仅为国家线，但实际录取分数远高于此。例如：西南医科大校线 325 而实录下沿 341；'
                    '长江大学校线 294 而实录下沿 353。请以「实录最低分」为准。'),
    ('⚠ 同校不同单位', '同一所大学的不同临床医学院/附属医院常独立划线、独立录取，分差可达 60-80 分。'
                    '例如：徐州医科大学麻醉学院 332 而附属淮安医院 294；青岛大学一临 341 而四临 300。'),
    ('置信度 A', '2026 年官方复试线 + 实录最低分/录取人数，双重确认。'),
    ('置信度 B', '仅有 2026 年官方复试线，实录分数待补。'),
    ('置信度 C', '无 2026 数据，回落旧库值（已标注年份）。'),
    ('置信度 D', '暂缺可用数据，需进一步核实（多为顶尖院校，官方未公布分专业明细）。'),
    ('颜色含义', '绿 = 门槛 ≤310（安全）；浅黄 = 311-340（较稳）；橙 = 341-350（临界）；'
              '红 = >350（高分）；灰 = 数据待核实。'),
    ('专业代码口径', '多数院校以独立代码 105118 招生；少数院校在 105100 临床医学大类下以「麻醉学临床技能训练与研究」'
                  '方向招生（已在提示中注明）。东南大学 105100 下麻醉方向仅招推免，统考不可报。'),
    ('考试科目', '绝大多数为：101 思想政治理论 + 201 英语（一）+ 306 临床医学综合能力（西医）。'
              '延边大学可选用 203 日语；内蒙古民族大学可选用日语。'),
    ('数据来源', '各校研究生院/研究生招生网官方公告（复试分数线通知、复试录取办法、拟录取名单公示）、'
              '中国研究生招生信息网、新东方在线、掌上考研、路灯考研、研大医学、宏医教育等公开整理。'
              '每条数据在「数据来源」列标注具体出处。'),
    ('免责', '本表为择校参考，2027 年招生政策以各校当年正式公告为准。填报前请务必回到官网核对。'),
]
for i, (k, v) in enumerate(NOTES, start=1):
    a = ws4.cell(row=i, column=1, value=k)
    a.font = Font(bold=True, size=10.5, name='PingFang SC')
    a.fill = PatternFill('solid', fgColor='EDEAE3')
    a.alignment = Alignment(vertical='top', horizontal='left')
    a.border = BORDER
    b = ws4.cell(row=i, column=2, value=v)
    b.font = Font(size=10, name='PingFang SC')
    b.alignment = Alignment(vertical='top', wrap_text=True)
    b.border = BORDER
    ws4.row_dimensions[i].height = 34

out = os.path.join(os.path.dirname(BASE), '105118麻醉学专硕2027报考决策总表.xlsx')
wb.save(out)
print('已生成:', out)
print('总表:', len(M), '所｜350以下:', len(sub), '所')
from collections import Counter
print(Counter(True if r['gate'] and r['gate'] <= 300 else False for r in sub))
