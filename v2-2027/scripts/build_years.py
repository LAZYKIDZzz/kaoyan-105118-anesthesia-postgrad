# -*- coding: utf-8 -*-
"""
105118 麻醉学专硕 2024-2026 三年对照数据构建
数据优先级：手采补丁 years_patch.json（最高） > 本轮 2026 新采 y2026_core.json > 旧库 hist
2025 录取人数/均分不足时，用 summary2025.json（机构全国汇总，多校与官方吻合）补
输出：data/years3.json
"""
import json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(BASE)
ROOT = os.path.dirname(V2)


def load(rel):
    return json.load(open(os.path.join(V2, rel), encoding='utf-8'))


OLD = json.load(open(os.path.join(ROOT, 'src', 'data.json'), encoding='utf-8'))
NEW = load('data/raw/y2026_core.json')['schools']
LIST = load('data/schools_2027.json')['schools']
# 多批手采补丁，按顺序应用（后面的覆盖前面的）
PATCH_FILES = ['data/raw/years_patch.json', 'data/raw/years_patch2.json']
PATCH_BATCHES = [load(f)['schools'] for f in PATCH_FILES]
SUMMARY = load('data/raw/summary2025.json')['schools']

EXCLUDED = {'云南', '新疆', '西藏', '青海', '广西'}
YEARS = ('2024', '2025', '2026')


def norm(n):
    return re.sub(r'[（）()\s·]', '', n or '')


old_map = {x['name']: x for x in OLD if x['region'] not in EXCLUDED}
old_norm = {norm(k): v for k, v in old_map.items()}
new_map, new_norm = {}, {}
for s in NEW:
    new_map[s['name']] = s
    new_norm[norm(s['name'])] = s
patch_batches = []          # [(map, nmap), ...] 按优先级从低到高
for batch in PATCH_BATCHES:
    m, nm = {}, {}
    for s in batch:
        m[s['name']] = s
        nm[norm(s['name'])] = s
    patch_batches.append((m, nm))
sum_map, sum_norm = {}, {}
for s in SUMMARY:
    sum_map[s['name']] = s
    sum_norm[norm(s['name'])] = s


def get(m, n):
    return m.get(n) or m.get(norm(n)) or {}


B_ZONE = {'内蒙古', '贵州', '甘肃', '宁夏', '海南', '青海', '西藏', '新疆', '广西', '云南'}
B_SCHOOL = {'延边大学'}

schools = []
for item in LIST:
    name = item['name']
    o = get(old_map, name) or get(old_norm, name)
    n = get(new_map, name) or get(new_norm, name)
    pms = [get(m, name) for m, _ in patch_batches]
    pms = [p for p in pms if p]
    pm = pms[-1] if pms else {}
    sm = get(sum_map, name) or get(sum_norm, name)
    hist = o.get('hist') or {}

    y = {}
    for yr in YEARS:
        h = hist.get(yr) or {}
        y[yr] = {
            'fs': h.get('fs'), 'fs_kind': h.get('fs_kind') or '', 'fs_sub': h.get('fs_sub') or '',
            'fs_scope': h.get('fs_scope') or '',
            'lo': h.get('lo'), 'hi': h.get('hi'), 'avg': h.get('avg'), 'n': h.get('n'),
            'unit': h.get('unit') or '', 'note': h.get('note') or '', 'src': 'old',
        }

    # 2026 用本轮新采覆盖
    if n:
        r = y['2026']
        for k_src, k_dst in (('fs', 'fs'), ('fs_kind', 'fs_kind'), ('lo', 'lo'), ('hi', 'hi'),
                             ('avg', 'avg'), ('n', 'n')):
            if n.get(k_src) is not None:
                r[k_dst] = n[k_src]
        if n.get('unit_detail') or n.get('note'):
            r['unit'] = n.get('unit_detail') or r['unit']
            r['note'] = n.get('note') or r['note']
        if n.get('source'):
            r['src'] = n['source']

    # 手采补丁覆盖（逐批应用，后面的覆盖前面的；最高优先级）
    patch_note = ''
    for pm_ in pms:
        for yr in YEARS:
            pr = pm_.get('y' + yr)
            if pr:
                r = y[yr]
                for k in ('fs', 'fs_kind', 'fs_sub', 'fs_scope', 'lo', 'hi', 'avg', 'n', 'unit'):
                    if pr.get(k) is not None:
                        r[k] = pr[k]
                if pr.get('src'):
                    r['src'] = pr['src']
        if pm_.get('note'):
            patch_note = pm_['note']

    # 2025 全国汇总补 n/avg
    if sm and y['2025']['n'] is None and sm.get('n') is not None:
        y['2025']['n'] = sm['n']
        y['2025']['n_src'] = '机构全国汇总'
    if sm and y['2025']['avg'] is None and sm.get('avg') is not None:
        y['2025']['avg'] = sm['avg']
        y['2025']['avg_src'] = '机构全国汇总'

    schools.append({
        'name': name,
        'region': item.get('region') or o.get('region', ''),
        'city': o.get('city', item.get('city', '')),
        'zone': 'B区' if ((item.get('region') or o.get('region', '')) in B_ZONE or name in B_SCHOOL) else 'A区',
        'level': o.get('level', ''),
        'code': item.get('code', '105118'),
        'verify': item.get('note', ''),
        'patch_note': patch_note,
        'y': y,
    })

# 门槛计算：优先实际录取最低分(三年最低)，其次实际进复试线(三年最低)
# 注意：fs_scope 非空（'大类'=仅公布临床医学大类线、'学硕'=仅公布100217学硕线）的数值不计入门槛，
#       避免高门槛院校或学硕线被误判进350以下池（105118为专硕，学硕线不适用）
NON_MAJOR_SCOPE = ('大类', '学硕')
for s in schools:
    spec = [yr for yr in YEARS if s['y'][yr]['fs'] and s['y'][yr].get('fs_scope') not in NON_MAJOR_SCOPE]
    fs_list = [(int(yr), s['y'][yr]['fs'], s['y'][yr].get('fs_kind', '')) for yr in spec]
    lo_list = [(int(yr), s['y'][yr]['lo']) for yr in YEARS if s['y'][yr]['lo']]
    has_generic = any(s['y'][yr]['fs'] and s['y'][yr].get('fs_scope') in NON_MAJOR_SCOPE for yr in YEARS)
    s['fs_years'] = fs_list
    s['lo_years'] = lo_list
    s['min_fs'] = min([x[1] for x in fs_list], default=None)
    s['min_lo'] = min([x[1] for x in lo_list], default=None)
    s['generic_only'] = bool(has_generic and not fs_list and not lo_list)
    s['gate'] = s['min_lo'] if s['min_lo'] is not None else s['min_fs']

out = {
    'meta': {
        'title': '105118 麻醉学专硕 2024-2026 三年对照数据',
        'years': list(YEARS),
        'total': len(schools),
        'excluded_regions': sorted(EXCLUDED),
        'note': 'fs=该校该年公布的进入复试分数线（fs_kind 区分 国家线/校线/院线/自划线）；lo=实际录取最低分(统考)；'
                'avg=录取均分；n=统考录取人数。gate=三年最低门槛(优先实际录取最低分)。'
                '来源优先级：官方分数线/拟录取公示 > 启航/路灯/掌上考研/中公等机构整理。',
    },
    'schools': schools,
}
json.dump(out, open(os.path.join(V2, 'data', 'years3.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ---- 报告 ----
print('总数', len(schools))
cand = [s for s in schools if s['gate'] and s['gate'] <= 350]
print('350 以下候选:', len(cand))
print('\n=== 350 以下三年对照（gate 升序）===')
miss, generic, nodata = [], [], []
for s in sorted(cand, key=lambda x: x['gate']):
    def cell(r):
        if r['fs'] or r['lo']:
            return f"{(r['fs'] or '--')}/{(r['lo'] or '--')}"
        return '  --/--  '
    gaps = [yr for yr in YEARS if not s['y'][yr]['fs'] and not s['y'][yr]['lo']]
    if gaps:
        miss.append((s['name'], gaps))
    print(f"{s['gate']:>4} {s['name']:<16}{s['region']:<4}{s['zone']} | 24:{cell(s['y']['2024']):<12} 25:{cell(s['y']['2025']):<12} 26:{cell(s['y']['2026']):<12}")
print('\n350 以下候选仍缺年份的:', len(miss))
for nm, g in miss:
    print(' ', nm, ','.join(g))

for s in schools:
    if s['gate'] is None:
        if s.get('generic_only'):
            generic.append(s['name'])
        else:
            nodata.append(s['name'])
print('\n仅公布临床医学大类线（不列入350以下池）:', len(generic))
print(' ', '、'.join(generic) if generic else '（无）')
print('\n无可靠公开麻醉学分数线（军队院校/未公布）:', len(nodata))
print(' ', '、'.join(nodata) if nodata else '（无）')
