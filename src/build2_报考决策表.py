# -*- coding: utf-8 -*-
"""105118 麻醉学（专硕）考研报考决策表 —— 含复试/录取人数、分档底色、报考建议

路径说明：脚本位于 <项目>/src/，读写的 xlsx 均在上一级目录 <项目>/。
"""
import os

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "105118麻醉学考研三年数据统计表.xlsx")
OUT = os.path.join(BASE, "105118麻醉学考研报考决策表.xlsx")
TITLE = "105118 麻醉学（专业学位硕士）考研报考决策表"


def xl(c):
    v = c.removeprefix("#").upper()
    return "FF" + v


C_HEAD, C_HEADTXT = xl("#2F5597"), xl("#FFFFFF")
C_BORDER, C_TITLE = xl("#BFBFBF"), xl("#1F3864")
thin = Side(style="thin", color=C_BORDER)
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
F_TITLE = Font(name="微软雅黑", size=14, bold=True, color=C_TITLE)
F_SUB = Font(name="微软雅黑", size=10, bold=True, color=C_HEADTXT)
F_BODY = Font(name="微软雅黑", size=10)
F_BOLD = Font(name="微软雅黑", size=10, bold=True)
F_NOTE = Font(name="微软雅黑", size=9, color=xl("#595959"))
AL_C = Alignment(horizontal="center", vertical="center", wrap_text=True)
AL_L = Alignment(horizontal="left", vertical="center", wrap_text=True)
AX = Alignment(horizontal="left", vertical="top", wrap_text=True)

# ============================================================
# 一、分数档位定义（5档 + 待定）
# ============================================================
TIERS = [
    (1, "第一档 · 顶尖冲击", "录取均分 ≥ 375", "#FFC7CE", "#9C0006",
     "全国最高难度梯队。推免占比高、统考名额常为个位数，对本科出身、科研经历与临床技能敏感。"
     "建议初试目标 {t} 分以上，复试（技能操作+专业英语）需提前 3 个月专项突击；本科为临床/麻醉强势院校者更稳。"),
    (2, "第二档 · 高难冲刺", "录取均分 365 – 374", "#FCD5B4", "#B85C00",
     "985 及强势医科大学主战场。建议初试目标 {t} 分以上，并同步准备 1–2 所同档备选；"
     "务必查清目标院区的【院线】而非只看校线。"),
    (3, "第三档 · 中坚匹配", "录取均分 355 – 364", "#FFF2CC", "#7F6000",
     "省属重点医科大学主力区间，性价比最高。建议初试目标 {t} 分以上，基础扎实、求稳的考生首选此档。"),
    (4, "第四档 · 相对稳妥", "录取均分 345 – 354", "#E2EFDA", "#375623",
     "上岸概率明显提升，适合求稳或有明确地域规划的考生。建议初试目标 {t} 分以上，复试正常发挥即可。"),
    (5, "第五档 · 友好保底", "录取均分 < 345", "#C6EFCE", "#006100",
     "过国家线即有较大机会，多为 B 区院校、省属医学院与非直属附属医院。建议初试目标 {t} 分以上，适合压线求稳或求保底。"),
]
TIER_BY_NO = {t[0]: t for t in TIERS}
TIER_UNK = (0, "数据有限 · 待定", "2025年均分未完整披露", "#F2F2F2", "#7F7F7F",
            "该校 2025 年录取均分未公开披露，档位无法量化。请以目标院校研究生院最新公告为准，"
            "并按同类院校同档次准备，初试目标建议不低于 355 分。")

DIFF_STAR = {1: "★★★★★", 2: "★★★★☆", 3: "★★★☆☆", 4: "★★☆☆☆", 5: "★☆☆☆☆", 0: "—"}


def tier_of(avg):
    if avg is None:
        return 0
    if avg >= 375:
        return 1
    if avg >= 365:
        return 2
    if avg >= 355:
        return 3
    if avg >= 345:
        return 4
    return 5


# ============================================================
# 二、从原表读取院校基础数据
# ============================================================
src = openpyxl.load_workbook(SRC, data_only=True)
ws_a = src["三年复试线对比"]
ws_b = src["2025录取明细"]

schools = {}   # name -> dict
order = []
for r in range(3, ws_a.max_row + 1):
    name = ws_a.cell(r, 2).value
    if not name:
        continue
    schools[name] = {
        "region": ws_a.cell(r, 3).value or "",
        "city": ws_a.cell(r, 4).value or "",
        "level": ws_a.cell(r, 5).value or "",
        "y24": ws_a.cell(r, 6).value,
        "y25": ws_a.cell(r, 7).value,
        "y26": ws_a.cell(r, 8).value,
        "sub26": ws_a.cell(r, 9).value or "",
        "nature": ws_a.cell(r, 12).value or "",
        "note": ws_a.cell(r, 13).value or "",
        "source24": ws_a.cell(r, 14).value or "",
        "source25": ws_a.cell(r, 15).value or "",
        "source26": ws_a.cell(r, 16).value or "",
        "n": None, "lo": None, "hi": None, "avg": None, "units": 0,
    }
    order.append(name)

# 从 2025 录取明细聚合到院校层面
agg = {}
for r in range(3, ws_b.max_row + 1):
    sch = ws_b.cell(r, 3).value
    if not sch:
        continue
    n, hi, lo, avg = (ws_b.cell(r, c).value for c in (5, 6, 7, 8))
    d = agg.setdefault(sch, {"n": 0, "los": [], "avg_pairs": []})
    if isinstance(n, (int, float)) and n:
        d["n"] += n
    if isinstance(lo, (int, float)):
        d["los"].append(lo)
    if isinstance(hi, (int, float)):
        d.setdefault("his", []).append(hi)
    if isinstance(avg, (int, float)) and isinstance(n, (int, float)) and n:
        d["avg_pairs"].append((n, avg))

for sch, d in agg.items():
    if sch not in schools:
        continue
    s = schools[sch]
    s["n"] = d["n"] or None
    s["lo"] = min(d["los"]) if d["los"] else None
    s["hi"] = max(d.get("his", [])) if d.get("his") else None
    tot = sum(p[0] for p in d["avg_pairs"])
    s["avg"] = round(sum(p[0] * p[1] for p in d["avg_pairs"]) / tot) if tot else None
    s["units"] = 1

# ============================================================
# 三、2025 年录取人数 / 均分（第三方不完全统计，覆盖更广）
# ============================================================
ENROLL25 = {
    "浙江大学": (6, 383), "重庆医科大学": (26, 380), "北京大学医学部": (8, 378),
    "南方医科大学": (25, 378), "天津医科大学": (10, 376), "吉林大学": (28, 375),
    "西安交通大学": (10, 374), "中南大学": (24, 374), "四川大学": (7, 372),
    "陆军军医大学": (3, 372), "电子科技大学": (9, 372), "西南医科大学": (26, 371),
    "福建医科大学": (34, 369), "北京协和医学院": (8, 366), "徐州医科大学": (None, 365),
    "中山大学": (29, 364), "山东大学": (7, 364), "中国医科大学": (42, 363),
    "哈尔滨医科大学": (46, 363), "宁波大学": (13, 362), "河北医科大学": (44, 362),
    "济宁医学院": (4, 360), "安徽医科大学": (47, 360), "川北医学院": (22, 359),
    "南昌大学": (61, 359), "首都医科大学": (12, 358), "苏州大学": (13, 356),
    "湖州师范学院": (5, 356), "广东医科大学": (31, 354), "兰州大学": (16, 354),
    "暨南大学": (14, 354), "齐齐哈尔医学院": (5, 354), "广州医科大学": (27, 354),
    "海南医科大学": (9, 353), "海军军医大学": (1, 353), "河南大学": (18, 353),
    "青岛大学": (22, 352), "武汉大学": (19, 352), "华中科技大学": (8, 362),
    "山西医科大学": (31, 351), "佳木斯大学": (6, 351), "温州医科大学": (49, 351),
    "西北民族大学": (2, 350), "贵州医科大学": (21, 349), "昆明医科大学": (42, 349), "江苏大学": (8, 345),
    "蚌埠医科大学": (29, 349), "成都医学院": (14, 349), "浙江中医药大学": (30, 348),
    "汕头大学": (None, 347), "绍兴文理学院": (5, 346), "西北大学": (None, 346),
    "华北理工大学": (9, 346), "山东第一医科大学": (28, 344), "杭州师范大学": (3, 344),
    "沈阳医学院": (8, 343), "遵义医科大学": (24, 343), "宁夏医科大学": (20, 342),
    "赣南医科大学": (14, 342), "山东第二医科大学": (30, 342), "延安大学": (29, 341),
    "南通大学": (19, 341), "西安医学院": (18, 341), "河北北方学院": (22, 341),
    "广东药科大学": (2, 340), "成都中医药大学": (5, 340), "大连医科大学": (48, 340),
    "大理大学": (15, 339), "江南大学": (9, 337), "承德医学院": (17, 337),
    "河南科技大学": (10, 336), "青海大学": (17, 336), "湖南师范大学": (7, 336),
    "厦门大学": (3, 336), "延边大学": (37, 336), "内蒙古医科大学": (43, 335),
    "皖南医学院": (42, 335), "长春中医药大学": (2, 334), "扬州大学": (8, 333),
    "甘肃中医药大学": (14, 333), "桂林医学院": (17, 333), "锦州医科大学": (42, 332),
    "长江大学": (7, 331), "大连大学": (4, 327), "河北大学": (3, 326),
    "长治医学院": (17, 326), "昆明理工大学": (4, 325), "新疆医科大学": (62, 324),
    "湖北医药学院": (19, 324), "西藏大学": (3, 321), "广东省心血管病研究所": (2, 321),
    "石河子大学": (3, 320), "滨州医学院": (18, 318), "吉首大学": (10, 318),
    "右江民族医学院": (10, 316), "武汉科技大学": (12, 315), "陕西中医药大学": (2, 308),
    "内蒙古民族大学": (2, 286), "牡丹江医科大学": (18, None),
}

for name, (n, avg) in ENROLL25.items():
    if name in schools:
        s = schools[name]
        if n:
            s["n"] = n
        if avg:
            s["avg"] = avg

# 原表中未进入 ENROLL25 的院校，用其备注中的均分补齐
NOTE_AVG = {"皖南医学院": 335, "安徽医科大学": 360, "山东第二医科大学": 342,
            "武汉大学": 352, "华中科技大学": 362}
for k, v in NOTE_AVG.items():
    if k in schools and schools[k]["avg"] is None:
        schools[k]["avg"] = v

# ============================================================
# 四、新增院校（原表未收录，来自新检索）
# ============================================================
NEW_SCHOOLS = {}
for name, (reg, cty, lvl, y24, y25, y26, sub, nat, note, n, avg) in NEW_SCHOOLS.items():
    if name not in schools:
        schools[name] = {"region": reg, "city": cty, "level": lvl, "y24": y24, "y25": y25, "y26": y26,
                         "sub26": sub, "nature": nat, "note": note,
                         "n": n, "lo": None, "hi": None, "avg": avg, "units": 0}
        order.append(name)

# 手动档位（2025 均分未披露，但难度梯队明确）
MANUAL_TIER = {
    "复旦大学": 1, "上海交通大学": 1, "南京医科大学": 2, "郑州大学": 2,
    "同济大学": 3, "新乡医学院": 3, "南华大学": 3, "广西医科大学": 3,
    "牡丹江医科大学": 4, "南京大学": 3, "大连理工大学": 4,
}

# ============================================================
# 五、进入复试人数 / 差额复试比 / 2026 招生计划
# ============================================================
# 名称 -> (进入复试人数, 复试差额比, 数据年份, 依据说明)
FS = {
    "徐州医科大学": ("约 90 人", "约 1:1.4", "2026", "麻醉学院专硕计划 80 人（含推免 16），统考约 64 人按 1:1.4 划线"),
    "南昌大学": ("约 62 人", "1:1.5", "2026", "第一临床医学院统考 33 人、江西医学院 8 人，均按 1:1.5 确定复试名单"),
    "首都医科大学": ("约 15 人", "1:1.5", "2026", "复试资格按招生计划数的 150% 确定；麻醉统考约 10 人"),
    "哈尔滨医科大学": ("按 120% 划定", "1:1.2", "2026", "按各方向招生计划数的 120% 确定复试名单"),
    "南京医科大学": ("按 150% 划定", "1:1.5", "2026", "按统考招生人数 1:1.5 确定复试名单"),
    "牡丹江医科大学": ("—", "≥ 1:1.2", "2026", "复试比例不低于 1:1.2，进入复试最低线 322 分（含）"),
    "南华大学": ("约 5 人", "≥ 1:1.2", "2026", "南华临床学院麻醉学专硕计划 4 人"),
    "山西医科大学": ("约 34 人", "1:1.3", "2025", "麻醉学院专硕计划 26 人，进入复试约 34 人，实际录取 26 人"),
    "天津医科大学": ("约 13 人", "1:1.3", "2025", "专硕进入复试约 13 人，实际录取 10 人"),
    "宁夏医科大学": ("18 – 20 人", "约 1:1.3", "2025", "第一临床医学院专硕计划 14 人；第三临床医学院招生 6 人、进入复试约 8 人"),
    "兰州大学": ("约 23 人", "—", "2025", "第二临床医学院麻醉学报考 23 人、录取 9 人，复试淘汰率约 60.9%"),
    "郑州大学": ("9 人", "1:1.3", "2025", "第二临床医学院麻醉学拟招生 7 人，复试名单公示 9 人"),
    "中山大学": ("16 人", "—", "2025", "附属第三医院 105100 麻醉学方向报考 16 人、录取 3 人"),
    "宁波大学": ("—", "—", "2025", "麻醉学报考 15 人、录取 13 人，报录比约 1.15:1"),
}

PLAN26 = {
    "徐州医科大学": "80（含推免16）", "南昌大学": "一临35 / 江西医学院8", "首都医科大学": "约10",
    "天津医科大学": "17（较2025年扩招70%）", "四川大学": "8", "中山大学": "29（不含推免）",
    "西安交通大学": "6", "江苏大学": "7", "北京协和医学院": "7", "同济大学": "13",
    "川北医学院": "30", "湖州师范学院": "3", "南华大学": "4", "暨南大学": "1",
    "大连理工大学": "1", "南京医科大学": "一临 / 四临分列", "郑州大学": "一临 / 二临 / 三临分列",
    "宁夏医科大学": "21（一临16 / 三临5）", "兰州大学": "一临16", "新疆医科大学": "一临31",
}

# ============================================================
# 六、生成工作簿
# ============================================================
wb = Workbook()
wb.properties.title = TITLE

# ---------- Sheet 1 · 报考决策总表 ----------
ws1 = wb.create_sheet("报考决策总表", 0)
if "Sheet" in wb.sheetnames:
    del wb["Sheet"]
ws1.sheet_properties.tabColor = xl("#2F5597")

HDR1 = ["序号", "地区", "城市", "院校名称", "院校层次", "2026复试线", "2025录取最低分", "2025录取平均分",
        "2025录取人数", "进入复试人数", "复试差额比", "难度星级", "录取难度档位", "报考建议"]
NCOL1 = len(HDR1)


def put_title(ws, text, ncol, row=1):
    ws.cell(row=row, column=1, value=text)
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncol)
    c = ws.cell(row=row, column=1)
    c.font = F_TITLE
    c.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[row].height = 26


def style_header(ws, row, ncol):
    for c in range(1, ncol + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = F_SUB
        cell.fill = PatternFill("solid", fgColor=C_HEAD)
        cell.alignment = AL_C
        cell.border = BORDER


put_title(ws1, "105118 麻醉学（专硕）· 各院校报考决策总表（按难度档位排序，底色＝档位）", NCOL1)
ws1.cell(row=2, column=1, value="说明：底色按 2025 年录取平均分划分 5 档 —— 红=顶尖冲击 / 橙=高难冲刺 / 黄=中坚匹配 / 浅绿=相对稳妥 / 绿=友好保底；灰=数据有限。")
ws1.merge_cells(start_row=2, start_column=1, end_row=2, end_column=NCOL1)
ws1.cell(row=2, column=1).font = F_NOTE
ws1.cell(row=2, column=1).alignment = AL_L
ws1.row_dimensions[2].height = 18

HR = 3
for i, h in enumerate(HDR1, start=1):
    ws1.cell(row=HR, column=i, value=h)
style_header(ws1, HR, NCOL1)


TIER_TARGET = {1: 390, 2: 375, 3: 365, 4: 355, 5: 345, 0: 355}


def build_advice(tno, name, s):
    t = TIER_BY_NO.get(tno, TIER_UNK)
    avg = s["avg"]
    target = int(round((avg + 8) / 5.0) * 5) if avg else TIER_TARGET.get(tno, 355)
    txt = t[5].format(t=target)
    warn = []
    note = s["note"] or ""
    if "推免" in note or "统考" in note or "个位数" in note:
        warn.append("⚠ 推免占比高，统考名额有限")
    if "实际录取" in note and ("远高于" in note or "高于" in note):
        warn.append("⚠ 实际录取分显著高于公布复试线")
    if s["n"] and s["n"] <= 5:
        warn.append("⚠ 年录取≤5人，名额极少")
    if s["y26"] and s["y25"] and s["y26"] - s["y25"] >= 15:
        warn.append("⚠ 2026年院线大幅上调")
    if warn:
        txt += " " + "；".join(warn) + "。"
    if note:
        txt += "（该校要点：" + note.replace("；", "，") + "）"
    return txt


rows1 = []
for name in order:
    s = schools[name]
    avg = s["avg"]
    tno = MANUAL_TIER.get(name) if avg is None else None
    tno = tno if tno is not None else tier_of(avg)
    rows1.append((name, s, tno))

rows1.sort(key=lambda x: (x[2] if x[2] else 9, -(x[1]["avg"] or 0), -(x[1]["n"] or 0), x[0]))

r = HR + 1
for i, (name, s, tno) in enumerate(rows1, start=1):
    t = TIER_BY_NO.get(tno, TIER_UNK)
    fs = FS.get(name, (None, None, None, None))
    vals = [
        i, s["region"], s["city"], name, s["level"], s["y26"], s["lo"], s["avg"], s["n"],
        fs[0] or "未公布", fs[1] or "—", DIFF_STAR.get(tno, "—"), t[1],
        build_advice(tno, name, s),
    ]
    for c, v in enumerate(vals, start=1):
        cell = ws1.cell(row=r, column=c, value=v)
        cell.font = F_BODY
        cell.border = BORDER
        cell.alignment = AL_L if c in (4, 14) else AL_C
        cell.fill = PatternFill("solid", fgColor=xl(t[3]))
    ws1.cell(row=r, column=4).font = F_BOLD
    ws1.cell(row=r, column=13).font = Font(name="微软雅黑", size=10, bold=True, color=xl(t[4]))
    r += 1
LAST1 = r - 1

for col, w in zip("ABCDEFGHIJKLMN",
                  [5, 8, 9, 21, 12, 11, 12, 12, 11, 13, 11, 10, 16, 78]):
    ws1.column_dimensions[col].width = w
ws1.row_dimensions[HR].height = 30
ws1.auto_filter.ref = f"A{HR}:N{LAST1}"
ws1.freeze_panes = "E4"

# ---------- Sheet 2 · 复试与录取人数明细 ----------
ws2 = wb.create_sheet("复试与录取人数明细", 1)
ws2.sheet_properties.tabColor = xl("#ED7D31")
HDR2 = ["序号", "地区", "城市", "院校名称", "2026复试线", "2026招生计划", "2025录取人数",
        "2025录取最低分", "2025录取平均分", "进入复试人数", "复试差额比", "录取数据年份", "复试口径年份", "依据说明"]
NCOL2 = len(HDR2)
put_title(ws2, "105118 麻醉学（专硕）· 复试人数 / 录取人数 / 竞争度明细", NCOL2)
ws2.cell(row=2, column=1, value="⚠ 「进入复试人数」仅统计到公开披露该数据的院校；未公布者标注为「未公布」，可用「复试差额比」按招生计划数自行推算。")
ws2.merge_cells(start_row=2, start_column=1, end_row=2, end_column=NCOL2)
ws2.cell(row=2, column=1).font = F_NOTE
ws2.cell(row=2, column=1).alignment = AL_L
for i, h in enumerate(HDR2, start=1):
    ws2.cell(row=HR, column=i, value=h)
style_header(ws2, HR, NCOL2)

# 先输出有复试数据或计划数据的院校，再输出其余
prio = [n for n in order if n in FS or n in PLAN26]
rest = [n for n in order if n not in FS and n not in PLAN26]
rest.sort(key=lambda n: -(schools[n]["avg"] or 0))

r = HR + 1
idx = 0
for group in (prio, rest):
    for name in group:
        s = schools[name]
        fs = FS.get(name, (None, None, None, None))
        idx += 1
        vals = [idx, s["region"], s["city"], name, s["y26"], PLAN26.get(name, "未公布"),
                s["n"], s["lo"], s["avg"], fs[0] or "未公布", fs[1] or "—",
                "2025" if any(v is not None for v in (s["n"], s["lo"], s["avg"])) else "—",
                fs[2] or "—", fs[3] or (s["note"] or "—")]
        for c, v in enumerate(vals, start=1):
            cell = ws2.cell(row=r, column=c, value=v)
            cell.font = F_BODY
            cell.border = BORDER
            cell.alignment = AL_L if c in (4, 14) else AL_C
        if name in FS:
            for c in range(1, NCOL2 + 1):
                ws2.cell(row=r, column=c).fill = PatternFill("solid", fgColor=xl("#FDF2E9"))
        r += 1
LAST2 = r - 1

for col, w in zip("ABCDEFGHIJKLMN", [5, 8, 9, 21, 11, 19, 12, 12, 12, 13, 12, 11, 11, 62]):
    ws2.column_dimensions[col].width = w
ws2.auto_filter.ref = f"A{HR}:N{LAST2}"
ws2.freeze_panes = "E4"

# 底部：各校复试比例规则
r += 1
ws2.cell(row=r, column=1, value="附：各校差额复试比例规则（2026 年公开口径）")
ws2.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NCOL2)
ws2.cell(row=r, column=1).font = Font(name="微软雅黑", size=11, bold=True, color=C_TITLE)
r += 1
RULES = [
    ("首都医科大学", "复试资格按报考专业招生计划数的 150% 确定（临床医学 1051 校线 330）"),
    ("南京医科大学", "统考招生人数按 1:1.5 确定复试人数和名单（临床医学 1051 校线 315、英语 55）"),
    ("哈尔滨医科大学", "按各学院各专业方向招生计划数的 120% 划定，生源不足按实际人数（1051 校线 310）"),
    ("徐州医科大学", "差额复试比例不低于 1:1.2，麻醉学专硕实操约 1:1.4"),
    ("南昌大学", "第一临床医学院 105118 计划 35 人（含推免 2），复试比例 1:1.5"),
    ("牡丹江医科大学", "麻醉学（附属红旗医院基地）复试比例不低于 1:1.2，进线 322 分"),
    ("南华大学", "差额复试比例一般不低于 120%，生源不足按实际合格生源组织复试"),
    ("山西医科大学（2025）", "专硕计划 26 人、进入复试约 34 人、实际录取 26 人，比例约 1:1.3"),
    ("天津医科大学（2025）", "专硕进入复试约 13 人、录取 10 人，比例约 1:1.3"),
    ("宁夏医科大学（2025）", "一临专硕计划 14 人、进入复试 18–20 人；三临招生 6 人、进入复试约 8 人"),
]
for a, b in RULES:
    ws2.cell(row=r, column=1, value=a).font = F_BOLD
    ws2.cell(row=r, column=1).alignment = AL_C
    ws2.cell(row=r, column=2, value=b).font = F_BODY
    ws2.cell(row=r, column=2).alignment = AL_L
    ws2.merge_cells(start_row=r, start_column=2, end_row=r, end_column=NCOL2)
    ws2.row_dimensions[r].height = 20
    r += 1

# ---------- Sheet 3 · 分档报考策略 ----------
ws3 = wb.create_sheet("分档报考策略", 2)
ws3.sheet_properties.tabColor = xl("#70AD47")
HDR3 = ["档位", "划分标准", "代表院校（举例）", "建议初试目标", "填报策略", "风险提示"]
NCOL3 = len(HDR3)
put_title(ws3, "105118 麻醉学（专硕）· 五档报考策略", NCOL3)
for i, h in enumerate(HDR3, start=1):
    ws3.cell(row=2, column=i, value=h)
style_header(ws3, 2, NCOL3)

STRATEGY = {
    1: ("浙江大学 / 四川大学 / 北京大学医学部 / 复旦大学 / 上海交通大学 / 中南大学 / 南方医科大学、重庆医科大学、天津医科大学、吉林大学、西安交通大学",
        "385 – 400+",
        "只建议本科为临床/麻醉强势院校、有一战实力者报考；同一志愿内优先选择招生人数相对多的院区（如中南湘雅医院、重医、南医一临）。"
        "务必把「院线」而非「校线」作为判断依据。",
        "统考名额多为个位数，推免挤压严重；复试权重高（部分校初试:复试＝5:5），技能操作与专业英语是分水岭。"),
    2: ("福建医科大学 / 中国医科大学 / 哈尔滨医科大学 / 山东大学 / 中山大学 / 南昌大学 / 宁波大学 / 河北医科大学 / 首都医科大学 / 南京医科大学、郑州大学",
        "370 – 385",
        "可作「冲刺主力」；建议按「1 所本档 + 1 所第三档 + 1 所第四档」的梯度组合填报。重点关注院区差异（如郑大一临 370 / 二临 340 / 三临 312）。",
        "院校层次相近但院线差异大，需逐院核对；部分院校单科线极高（如哈医大业务课 160、北大 180）。"),
    3: ("安徽医科大学 / 川北医学院 / 济宁医学院 / 首都医科大学部分院区 / 苏州大学 / 湖州师范学院 / 同济大学 / 南华大学、广西医科大学、新乡医学院",
        "360 – 375",
        "性价比最高的主力区间，适合基础扎实的求稳考生：建议以本档为「主攻」，配 1 所第四档兜底。",
        "同档院校报录比差异大（1.15:1 – 6:1 不等），别只看分数线，要看招生人数与报录比。"),
    4: ("广东医科大学 / 兰州大学 / 暨南大学 / 广州医科大学 / 海南医科大学 / 海军军医大学 / 河南大学 / 青岛大学 / 武汉大学 / 华中科技大学 / 宁夏医科大学",
        "350 – 365",
        "上岸概率明显提升。适合有明确地域就业规划的考生（如想留广州可优先广州医科大、暨南大学）。",
        "部分院校含军队/特殊招生口径（如海军军医大学），报考前须确认身体条件与政审要求。"),
    5: ("新疆医科大学 / 湖北医药学院 / 滨州医学院 / 内蒙古医科大学 / 皖南医学院 / 长治医学院 / 石河子大学 / 右江民族医学院 / 西藏大学 / 陕西中医药大学",
        "330 – 350",
        "压线求稳首选。建议以 B 区院校（新疆医科大、宁夏医科大、甘肃中医药、右江民族医学院）或省属医学院的非直属附属医院基地为主，过线即大概率录取。",
        "地理位置与就业半径有限；B 区院校调剂竞争反而可能激烈；部分院校录取均分低但年度招生人数波动大。"),
}

r = 3
for no in [1, 2, 3, 4, 5]:
    t = TIER_BY_NO[no]
    reps, target, strat, risk = STRATEGY[no]
    vals = [t[1], t[2], reps, target, strat, risk]
    for c, v in enumerate(vals, start=1):
        cell = ws3.cell(row=r, column=c, value=v)
        cell.font = F_BODY
        cell.border = BORDER
        cell.alignment = AX if c in (3, 5, 6) else AL_C
        cell.fill = PatternFill("solid", fgColor=xl(t[3]))
    ws3.cell(row=r, column=1).font = Font(name="微软雅黑", size=11, bold=True, color=xl(t[4]))
    ws3.cell(row=r, column=4).font = Font(name="微软雅黑", size=12, bold=True, color=xl(t[4]))
    ws3.row_dimensions[r].height = 100
    r += 1

t = TIER_UNK
vals = ["备注 · 均分未披露院校", "2025年录取均分未公开",
        "复旦大学、上海交通大学、同济大学、牡丹江医科大学、郑州大学、南京医科大学、新乡医学院、南华大学、广西医科大学、大连理工大学等",
        "按所定档位执行",
        "上述院校 2025 年录取均分未公开披露，已依据 2026 院线、招生计划、报录比与学科实力手动归入相应档位（复旦/上交→第一档，南医/郑大→第二档，同济/新乡/南华/广西医科→第三档，牡丹江/大连理工→第四档）。",
        "手动定档存在主观性，请以目标院校研究生院最新公告为准。"]
for c, v in enumerate(vals, start=1):
    cell = ws3.cell(row=r, column=c, value=v)
    cell.font = F_BODY
    cell.border = BORDER
    cell.alignment = AX if c in (3, 5, 6) else AL_C
    cell.fill = PatternFill("solid", fgColor=xl(t[3]))
ws3.cell(row=r, column=1).font = Font(name="微软雅黑", size=11, bold=True, color=xl(t[4]))
ws3.row_dimensions[r].height = 74

for col, w in zip("ABCDEF", [18, 20, 46, 14, 60, 46]):
    ws3.column_dimensions[col].width = w

# ---------- Sheet 4 · 数据来源与说明 ----------
ws4 = wb.create_sheet("数据来源与说明", 3)
ws4.sheet_properties.tabColor = xl("#A9A9A9")
put_title(ws4, "数据来源、口径说明与免责提示", 2)
NOTES = [
    ("专业代码", "105118 = 麻醉学，专业学位硕士（专硕），隶属临床医学 1051 类别。学硕对应代码为 100217，本表仅统计专硕。"),
    ("统计年度", "覆盖 2024 / 2025 / 2026 三个考研年度。「三年内」＝近三个招生年度。"),
    ("国家线口径", "教育部A区参考总分：2024年304、2025年293、2026年294；B区分别为294、283、284。国家线只作最低参考，不自动等同于院校或培养单位105118复试线。"),
    ("2025 录取人数与均分", "来自第三方对约 150 个培养单位拟录取名单的不完全统计（合计约 1631 人、平均分 349 分），存在少量缺漏，个别院校未列录取人数或分数存疑，表中已标注。"),
    ("进入复试人数", "仅统计到官方公开披露该数据的院校（如南昌大学、首都医科大学、哈尔滨医科大学、南京医科大学、徐州医科大学、天津医科大学、山西医科大学、宁夏医科大学、兰州大学、郑州大学、中山大学、宁波大学等）。多数院校公布的只是「复试差额比例」与「招生计划」，可用 招生计划 × 差额比例 自行推算，本表已在「复试差额比」列给出。"),
    ("分数档位划分依据", "以 2025 年各校录取平均分（而非复试线）为主要依据划分 5 档：≥375 顶尖冲击 / 365–374 高难冲刺 / 355–364 中坚匹配 / 345–354 相对稳妥 / <345 友好保底。刻意不用复试线，因为复试线≠录取线（如中南大学 2026 校线 310，湘雅医院一志愿录取最低约 386）。"),
    ("难度星级", "★ 越多代表报考难度越高（依据档位、招生人数、推免占比、报录比综合判断）。"),
    ("底色说明", "整行底色即档位：红＝顶尖冲击、橙＝高难冲刺、黄＝中坚匹配、浅绿＝相对稳妥、绿＝友好保底、灰＝数据有限待定。"),
    ("院校层次", "「985 / 211 / 双一流 / 省属重点 / 省属 / B区省属」为院校标签，不代表该学科实际实力。典型反例：徐州医科大学为双非，但麻醉学为中国第一个麻醉学本科专业创办单位，学科实力与录取分均居全国前列。"),
    ("地区与城市", "「地区」为院校所属省级行政区，「城市」为院校所在（主校区/研究生培养）地级市，可直接按城市筛选与排序。直辖市地区与城市同名。个别院校多校区办学（如滨州医学院在烟台、滨州两地），城市列取考研院校代码库口径的主校区城市，实际培养校区请以当年招生简章为准。"),
    ("招生计划", "2026 年招生计划中「含推免」者，需扣除推免人数才是统考名额；表中已尽量注明。"),
    ("主要来源", "复试线优先采用院校研究生院/招生网官方公告，并在三年统计表中按院校+年度绑定网址；国家线采用教育部公告；录取分来自拟录取名单或院校录取统计。第三方数据仅作补充并明确标注。"),
    ("重要免责", "所有分数线与人数均可能随院校最新公告调整。第三方整理存在误差，报考前请务必以目标院校研究生院官网的最新公告与调剂细则为准。本表仅供择校参考，不构成报考建议。"),
]
r = 3
for k, v in NOTES:
    ws4.cell(row=r, column=1, value=k).font = F_BOLD
    ws4.cell(row=r, column=1).alignment = AX
    ws4.cell(row=r, column=1).fill = PatternFill("solid", fgColor=xl("#D9E2F3"))
    ws4.cell(row=r, column=1).border = BORDER
    ws4.cell(row=r, column=2, value=v).font = F_BODY
    ws4.cell(row=r, column=2).alignment = AX
    ws4.cell(row=r, column=2).border = BORDER
    ws4.row_dimensions[r].height = max(30, 16 * (len(v) // 62 + 1))
    r += 1
ws4.column_dimensions["A"].width = 20
ws4.column_dimensions["B"].width = 118

wb.save(OUT)
print("saved:", OUT)
print("Sheet1 rows:", LAST1 - HR, "| columns:", NCOL1)
print("Sheet2 rows:", LAST2 - HR)
print("档位分布:", {TIER_BY_NO.get(n, TIER_UNK)[1]: sum(1 for _, _, x in rows1 if x == n) for n in [1, 2, 3, 4, 5, 0]})
print("有进入复试人数的院校数:", sum(1 for n in order if n in FS))
print("有2025录取人数的院校数:", sum(1 for n in order if schools[n]['n']))
print("有2025均分的院校数:", sum(1 for n in order if schools[n]['avg']))
