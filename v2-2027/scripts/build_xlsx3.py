# -*- coding: utf-8 -*-
"""生成 105118 麻醉学专硕 2024-2026 三年对照 Excel"""
import json, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(BASE)
ROOT = os.path.dirname(V2)
D = json.load(open(os.path.join(V2, 'data', 'years3.json'), encoding='utf-8'))['schools']
YEARS = ('2024', '2025', '2026')

C_HEAD = 'FF1F3B5C'
C_SUB = 'FFEFE6D6'
C_HI = 'FFFDECEA'    # 高门槛
C_LOW = 'FFE8F5E9'   # 低门槛
C_BORDER = 'FFB9AE97'

thin = Side(style='thin', color=C_BORDER)
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()


def style_header(ws, row, ncol):
    for c in range(1, ncol + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(bold=True, color='FFFFFFFF', size=10)
        cell.fill = PatternFill('solid', fgColor=C_HEAD)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = BORDER


def put(ws, r, c, v, bold=False, fill=None, align='center', size=10, color='FF222222'):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = Font(bold=bold, size=size, color=color)
    cell.alignment = Alignment(horizontal=align, vertical='center', wrap_text=(align == 'left'))
    cell.border = BORDER
    if fill:
        cell.fill = PatternFill('solid', fgColor=fill)
    return cell


def gate_basis(s):
    if s['min_lo'] is not None:
        return '实际录取最低分'
    return '实际进复试线'


# ============ Sheet1: 350以下 三年对照 ============
ws = wb.active
ws.title = '350以下三年对照'
heads = ['序号', '院校', '省份', '区域', '2024线', '2024录取最低', '2024人数',
         '2025线', '2025录取最低', '2025人数', '2026线', '2026录取最低', '2026人数',
         '参考门槛', '门槛依据', '2026招生规模', '三年趋势', '备注']
for i, h in enumerate(heads, 1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, 1, len(heads))

cand = sorted([s for s in D if s['gate'] and s['gate'] <= 350], key=lambda x: x['gate'])
for idx, s in enumerate(cand, 1):
    r = idx + 1
    y = s['y']
    trend = []
    for yr in YEARS:
        if y[yr]['fs']:
            trend.append(str(y[yr]['fs']))
    trend_s = ' → '.join(trend) if trend else '—'
    put(ws, r, 1, idx)
    put(ws, r, 2, s['name'], bold=True, align='left')
    put(ws, r, 3, s['region'])
    put(ws, r, 4, s['zone'])
    col = 5
    for yr in YEARS:
        put(ws, r, col, y[yr]['fs'] or '—')
        put(ws, r, col + 1, y[yr]['lo'] or '—')
        put(ws, r, col + 2, y[yr]['n'] or '—')
        col += 3
    # 门槛
    g = s['gate']
    fill = C_LOW if g <= 310 else (C_HI if g > 335 else None)
    put(ws, r, 14, g, bold=True, fill=fill)
    put(ws, r, 15, gate_basis(s))
    put(ws, r, 16, y['2026']['n'] or '—')
    put(ws, r, 17, trend_s)
    note = s.get('patch_note') or s.get('verify') or ''
    for x in YEARS:
        if not y[x]['fs'] and not y[x]['lo'] and x in ('2024', '2025') and not note:
            note = '部分年份待补'
    put(ws, r, 18, note, align='left', size=9)

widths = [5, 17, 7, 6, 7, 10, 7, 7, 10, 7, 7, 10, 7, 8, 13, 10, 18, 60]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = 'C2'
ws.row_dimensions[1].height = 32

# ============ Sheet2: 分档（低→高） ============
ws2 = wb.create_sheet('350以下分档')
ws2.cell(row=1, column=1, value='按参考门槛分档（门槛=三年最低的实际录取分/进复试线；越低越稳）')
ws2.cell(row=1, column=1).font = Font(bold=True, size=12, color=C_HEAD)
heads2 = ['档位', '门槛区间', '院校数', '院校清单（按门槛升序）']
for i, h in enumerate(heads2, 1):
    ws2.cell(row=2, column=i, value=h)
style_header(ws2, 2, len(heads2))
tiers = [('① 保底档', 0, 300), ('② 稳妥档', 301, 315), ('③ 进取档', 316, 330), ('④ 临界档', 331, 350)]
r = 3
for lab, a, b in tiers:
    grp = sorted([s for s in cand if a <= s['gate'] <= b], key=lambda x: x['gate'])
    put(ws2, r, 1, lab, bold=True)
    put(ws2, r, 2, f'{a}-{b}')
    put(ws2, r, 3, len(grp))
    put(ws2, r, 4, '；'.join(f"{x['name']}({x['gate']})" for x in grp), align='left', size=9)
    r += 1
for i, w in enumerate([10, 10, 8, 120], 1):
    ws2.column_dimensions[get_column_letter(i)].width = w

# ============ Sheet3: 全部99所 ============
ws3 = wb.create_sheet('全部99所三年对照')
h3 = ['序号', '院校', '省份', '区域', '2024线', '2024最低', '2024人数',
      '2025线', '2025最低', '2025人数', '2026线', '2026最低', '2026人数',
      '参考门槛', '依据', '备注摘要']
for i, h in enumerate(h3, 1):
    ws3.cell(row=1, column=i, value=h)
style_header(ws3, 1, len(h3))
all_s = sorted(D, key=lambda x: (x['gate'] or 9999))
for idx, s in enumerate(all_s, 1):
    r = idx + 1
    y = s['y']
    put(ws3, r, 1, idx)
    put(ws3, r, 2, s['name'], bold=True, align='left')
    put(ws3, r, 3, s['region'])
    put(ws3, r, 4, s['zone'])
    col = 5
    for yr in YEARS:
        put(ws3, r, col, y[yr]['fs'] or '—')
        put(ws3, r, col + 1, y[yr]['lo'] or '—')
        put(ws3, r, col + 2, y[yr]['n'] or '—')
        col += 3
    put(ws3, r, 14, s['gate'] or '—', bold=True)
    put(ws3, r, 15, gate_basis(s) if s['gate'] else '—')
    note = (s.get('patch_note') or s.get('verify') or '')[:120]
    put(ws3, r, 16, note, align='left', size=9)
widths3 = [5, 17, 7, 6, 7, 9, 7, 7, 9, 7, 7, 9, 7, 8, 10, 70]
for i, w in enumerate(widths3, 1):
    ws3.column_dimensions[get_column_letter(i)].width = w
ws3.freeze_panes = 'C2'

# ============ Sheet4: 说明 ============
ws4 = wb.create_sheet('数据说明')
lines = [
    ('105118 麻醉学专硕 2024—2026 三年对照数据说明', 14, True),
    ('', 10, False),
    ('一、为什么强调「实际」分数', 12, True),
    ('本表不使用「国家线」充当院校门槛，而是分别列出两年口径：', 10, False),
    ('  · 复试线（fs）：该校/该院当年自行公布的进入复试最低分数线；若该校未自划线、直接执行国家线，会明确标注为「国家线」。', 10, False),
    ('  · 录取最低分（lo）：当年统考实际录取考生中的最低初试总分——这是真正决定能否上岸的门槛。', 10, False),
    ('  · 两者常相差很大：如西南医科大学2026复试线325、实际录取最低341；长江大学复试线294、实际录取353。', 10, False),
    ('', 10, False),
    ('二、区域说明', 12, True),
    ('已按要求排除：云南、新疆、西藏、青海、广西（5省区）的院校。', 10, False),
    ('延边大学地处吉林，但国家按 B 类考生线划定（官方原文确认），故标为 B 区。', 10, False),
    ('', 10, False),
    ('三、数据来源与置信度', 12, True),
    ('优先级：目标院校研究生院官方《复试分数线/进入复试初试成绩基本要求/拟录取名单公示》 > 研招网 >', 10, False),
    ('启航考研/路灯考研/掌上考研/中公考研/昭昭医考等机构整理。部分院校2024年官方名单已过公示期下线，', 10, False),
    ('相关年份以机构来源补齐并保留原始出处记录（见 years3.json 的 src 字段）。', 10, False),
    ('2025年全国录取人数/均分来自机构不完全统计（总量1631人、加权均分349），已与南昌大学(61人)、', 10, False),
    ('河北医科(44)、广东医科(31)、广州医科(27)、苏州大学(13)、蚌埠医科(29)等多校官方数据交叉吻合。', 10, False),
    ('', 10, False),
    ('数据完整性：99 所院校中 89 所已补齐 2024/2025/2026 三年实际数据（无年份缺口）。', 10, False),
    ('  · 4 所（复旦大学、北京协和医学院、北京大学医学部、中南大学）仅公布「临床医学大类」校线，', 10, False),
    ('    南京大学仅公布「100217麻醉学学硕」线，均无 105118 专硕线，其数值仅作参考，不计入350以下候选池。', 10, False),
    ('  · 2 所军队院校（海军军医大学、陆军军医大学）复试线未在公开渠道发布，需查军队招生网。', 10, False),
    ('  · 4 所门槛高于350分（暨南大学、郑州大学、长江大学、重庆医科大学），部分年份待补，不影响350以下择校。', 10, False),
    ('', 10, False),
    ('本轮（第二批）重点补齐院校的三年实际线示例：', 10, False),
    ('  电子科技大学 365→360→305（三年降60分）｜苏州大学 347→318→374（波动56分，2026缩招至6人后暴涨）', 10, False),
    ('  天津医科大学 344→361→344｜华中科技大学协和 340→340→345、同济 340→345→370', 10, False),
    ('  扬州大学 310→298→308｜济宁医学院 复试线恒为国家线但实际录取最低 342(2024)/305(2026)', 10, False),
    ('', 10, False),
    ('四、如何使用', 12, True),
    ('· 横向对比（同年不同校）：看 Sheet「350以下分档」，同一年份下门槛越低的院校越稳。', 10, False),
    ('· 竖向对比（同校不同年）：看 Sheet「350以下三年对照」，观察某校三年分数线是升、降还是波动。', 10, False),
    ('· 参考门槛 = 三年中最低的实际录取最低分（若无则取最低的实际进复试线），代表「历史上最宽松的一年能进的分数」。', 10, False),
    ('· 350分以下择校，优先关注「三年门槛都在330以下」且「录取人数≥10」的院校，波动风险更小。', 10, False),
]
for i, (t, sz, bd) in enumerate(lines, 1):
    c = ws4.cell(row=i, column=1, value=t)
    c.font = Font(size=sz, bold=bd, color=C_HEAD if bd else 'FF333333')
    c.alignment = Alignment(vertical='center', wrap_text=False)
ws4.column_dimensions['A'].width = 130

out = os.path.join(ROOT, '105118麻醉学专硕2024-2026三年对照表.xlsx')
wb.save(out)
print('saved', out)
print('350以下', len(cand), '所；全部', len(D), '所')
