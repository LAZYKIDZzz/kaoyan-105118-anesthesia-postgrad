#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v2-2027 / 105118 麻醉学专硕 —— 主表整合与 Excel 输出
数据源：
  1) 本轮全网采集  data/raw/y2026_core.json   （2026 年，优先采信）
  2) 项目旧库      src/data.json             （2024-2026 三年 hist，作回落与校验）
输出：
  data/master.json
  ../105118麻醉学专硕2027报考决策总表.xlsx
"""
import json, re, os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # v2-2027
ROOT = os.path.dirname(BASE)                                          # 项目根

OLD = json.load(open(os.path.join(ROOT, 'src/data.json'), encoding='utf-8'))
NEW = json.load(open(os.path.join(BASE, 'data/raw/y2026_core.json'), encoding='utf-8'))['schools']
LIST = json.load(open(os.path.join(BASE, 'data/schools_2027.json'), encoding='utf-8'))['schools']

EXCLUDED = {'云南', '新疆', '西藏', '青海', '广西'}
B_ZONE = {'内蒙古', '贵州', '甘肃', '宁夏', '海南', '青海', '西藏', '新疆', '广西', '云南'}
# 延边大学虽在吉林，但国家按 B 区划定复试线
B_SCHOOL = {'延边大学'}

old_map = {x['name']: x for x in OLD if x['region'] not in EXCLUDED}


def norm(n):
    return re.sub(r'[（）()\s]', '', n)


new_map = {}
for s in NEW:
    new_map[norm(s['name'])] = s

rows = []
for s in LIST:
    name = s['name']
    o = old_map.get(name, {})
    n = new_map.get(norm(name))
    if not n:
        for k, v in new_map.items():
            if k and (k in norm(name) or norm(name) in k):
                n = v
                break
    n = n or {}
    h = o.get('hist', {}) or {}
    y26 = h.get('2026', {}) or {}
    y25 = h.get('2025', {}) or {}

    fs = n.get('fs') or y26.get('fs')
    fs_kind = n.get('fs_kind') or y26.get('fs_kind')
    lo = n.get('lo') or y26.get('lo')
    avg = n.get('avg') or y26.get('avg')
    hi = n.get('hi') or y26.get('hi')
    cnt = n.get('n') or y26.get('n')
    plan = n.get('plan_unified') or y26.get('n')

    # 无 2026 数据时回落到旧库主值
    old_lo = o.get('lo')
    old_avg = o.get('avg')
    old_n = o.get('n')
    old_fy = o.get('fy')

    # 实际门槛：实录下沿 > 复试线 > 旧库下沿
    gate = lo or fs or old_lo

    if fs is not None and (lo or cnt):
        conf = 'A｜2026实录'
    elif fs is not None:
        conf = 'B｜2026复试线'
    elif old_lo:
        conf = f'C｜旧库{old_fy}'
    else:
        conf = 'D｜待核实'

    region = s.get('region') or o.get('region', '')
    rows.append({
        'name': name,
        'region': region,
        'city': o.get('city', s.get('city', '')),
        'level': o.get('level', ''),
        'zone': 'B区' if (region in B_ZONE or name in B_SCHOOL) else 'A区',
        'plan': plan,
        'fs': fs,
        'fs_kind': fs_kind,
        'lo': lo,
        'hi': hi,
        'avg': avg,
        'cnt': cnt,
        'old_lo': old_lo,
        'old_avg': old_avg,
        'old_n': old_n,
        'old_fy': old_fy,
        'gate': gate,
        'conf': conf,
        'unit_detail': n.get('unit_detail', ''),
        'note': n.get('note', ''),
        'source': n.get('source', ''),
        'old_source': '; '.join(
            f"{x.get('year')}{x.get('kind')}" for x in (o.get('sources') or [])[:3]
        ),
    })

rows.sort(key=lambda r: (r['gate'] is None, r['gate'] or 0))

json.dump({'meta': {'year': 2026, 'total': len(rows)}, 'schools': rows},
          open(os.path.join(BASE, 'data/master.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print('主表条数:', len(rows))
print(Counter(r['conf'][0] for r in rows))
print('\n门槛最低 25 所：')
for r in rows[:25]:
    print(f"  {r['gate']}\t{r['name']}\t{r['region']}\t{r['zone']}\t{r['conf']}")
