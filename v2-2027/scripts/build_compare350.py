# -*- coding: utf-8 -*-
"""
择校分数对照 · 三年分数与人数对照（实测版）仪表盘生成器
核心纪律：
  - lo/hi/avg/n 仅来自真实录取公示/机构交叉验证；未查到即为 null -> 页面显示 "—"
  - 绝不把「国家线 / 复试线」当作「录取最低/最高分」展示
  - 每所院校标注 实测(有真实录取分) / 线估(仅复试线)
  - 页面文案回避「350 分」等带压迫感的硬门槛表述，档位改用温和的梯度命名
数据源：data/years3.json（单一事实源）+ data/plan2027.json（2027 计划招生，检索整理）
输出：html/compare.html + data/择校分数对照_实测版.csv
"""
import json, os, csv

BASE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(BASE)
DATA = os.path.join(V2, 'data', 'years3.json')
OUT_HTML = os.path.join(V2, 'html', 'compare.html')
OUT_PREVIEW = os.path.join(V2, 'html', 'mobile-summary-preview.html')
OUT_CSV = os.path.join(V2, 'data', '择校分数对照_实测版.csv')
YEARS = ['2024', '2025', '2026']

d = json.load(open(DATA, encoding='utf-8'))
schools_src = d['schools']


def tier_of(g):
    if g is None:
        return ''
    if g <= 300:
        return '从容区'
    if g <= 320:
        return '稳健区'
    if g <= 335:
        return '进取区'
    return '冲刺区'


TIER_COLOR = {'从容区': '#2f9e6f', '稳健区': '#2f7fd1', '进取区': '#e0913a', '冲刺区': '#b25fd1'}

# ---- 过滤 350 候选并计算审计字段 ----
cands = []
for s in schools_src:
    g = s.get('gate')
    if g is None or g > 350:
        continue
    real_years = sum(1 for y in YEARS if s['y'][y].get('lo') is not None)
    basis = '实测' if real_years > 0 else '线估'
    tier = tier_of(g)
    rec = {
        'n': s['name'],
        'r': s.get('region', ''),
        'c': s.get('city', ''),
        'z': s.get('zone', ''),
        'lv': s.get('level', ''),
        'gate': g,
        'tier': tier,
        'basis': basis,
        'real_years': real_years,
        'y': {},
    }
    for y in YEARS:
        r = s['y'][y]
        rec['y'][y] = {
            'fs': r.get('fs'),
            'fsKind': r.get('fs_kind') or '',
            'lo': r.get('lo'),
            'hi': r.get('hi'),
            'avg': r.get('avg'),
            'n': r.get('n'),
            'note': r.get('note') or '',
            'src': r.get('src') or '',
        }
    cands.append(rec)

cands.sort(key=lambda x: (x['gate'], x['n']))

# ---- 2027 计划招生（联网检索整理，2026-10-08；查不到的为 null） ----
try:
    PLAN27 = json.load(open(os.path.join(V2, 'data', 'plan2027.json'), encoding='utf-8')).get('plans', {})
except Exception:
    PLAN27 = {}
for c in cands:
    p = PLAN27.get(c['n'], {})
    c['plan27'] = p.get('plan')
    c['plan27Basis'] = p.get('basis') or ''
    c['plan27Src'] = p.get('source') or ''

NATLINE = {'2024': [304, 294], '2025': [293, 283], '2026': [294, 284]}

payload = {
    'years': YEARS,
    'natline': NATLINE,
    'tierColor': TIER_COLOR,
    'schools': cands,
}

n_total = len(cands)
n_real = sum(1 for c in cands if c['basis'] == '实测')
n_est = n_total - n_real
from collections import Counter
tier_dist = dict(Counter(c['tier'] for c in cands))

# ================= CSV 导出 =================
headers = ['院校', '地区', '城市', '区', '层次', '档位', '数据状态', '门槛(三年最低)', '真实录取分年份数']
for y in YEARS:
    headers += [f'{y}复试线', f'{y}录取最低', f'{y}录取最高', f'{y}录取均分', f'{y}统考人数']
with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(headers)
    for c in cands:
        row = [c['n'], c['r'], c['c'], c['z'], c['lv'], c['tier'], c['basis'], c['gate'], c['real_years']]
        for y in YEARS:
            r = c['y'][y]
            row += [r['fs'] if r['fs'] is not None else '',
                    r['lo'] if r['lo'] is not None else '',
                    r['hi'] if r['hi'] is not None else '',
                    r['avg'] if r['avg'] is not None else '',
                    r['n'] if r['n'] is not None else '']
        w.writerow(row)
print('CSV written:', OUT_CSV, 'rows:', len(cands))

# ================= HTML 生成 =================
DATA_JSON = json.dumps(payload, ensure_ascii=False)

html = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>麻醉学专硕择校 · 三年分数与人数对照（实测版）</title>
<style>
:root{
  color-scheme:light;
  --paper:#f6f4ef; --card:#ffffff; --ink:#27303d; --ink-soft:#56616f; --ink-faint:#8a93a0;
  --navy:#1f3a52; --navy-deep:#16283a; --line:#e3ddd2; --line-soft:#efeae1;
  --t-bg:#dff1e6; --t-st:#e6f0fb; --t-jq:#fbee E0; --t-lj:#fbe3e1;
  --accent:#c0492f; --focus:#2f7fd1;
  --t-bg:#dff1e6; --t-st:#e6f0fb; --t-jq:#fbeee0; --t-lj:#fbe3e1;
}
*{box-sizing:border-box}
html{background:var(--navy-deep)}
body{margin:0;font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;color:var(--ink);
  background:var(--paper);line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:inherit}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px 90px}
.masthead{position:relative;overflow:hidden;color:#f4efe6;background:linear-gradient(135deg,var(--navy),var(--navy-deep));
  margin:0 -16px 22px;padding:30px 24px 26px;border-bottom:5px solid var(--accent)}
.masthead .crumb{margin:0 0 12px;position:relative;z-index:2;display:flex;gap:7px;flex-wrap:wrap}
.masthead .crumb a{color:#e9e2d6;text-decoration:none;font-size:12.5px;border:1px solid rgba(255,255,255,.28);
  padding:4px 11px;border-radius:20px;background:rgba(255,255,255,.08)}
.masthead .crumb a:hover{background:rgba(255,255,255,.2)}
.masthead h1{font-family:"Songti SC",serif;font-size:25px;letter-spacing:.5px;margin:0}
.masthead .sub{margin-top:8px;font-size:13px;opacity:.85;max-width:760px}
.masthead .kpis{display:flex;gap:14px;margin-top:18px;flex-wrap:wrap}
.kpi{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);border-radius:10px;padding:10px 14px;min-width:96px}
.kpi b{display:block;font-size:22px;font-family:"Songti SC",serif;line-height:1.1}
.kpi span{font-size:11.5px;opacity:.8}
.kpi.warn b{color:#ffd9cf}
.kpi.ok b{color:#bfe9cd}

.notice{background:#fff7ef;border:1px solid #f0d9c6;border-left:4px solid var(--accent);
  border-radius:8px;padding:13px 16px;margin-bottom:16px;font-size:13px;color:#5a4636}
.notice b{color:var(--accent)}

/* controls */
.ctrl{position:sticky;top:0;z-index:30;background:rgba(246,244,239,.96);backdrop-filter:blur(6px);
  padding:12px 0 10px;border-bottom:1px solid var(--line);margin-bottom:14px}
.viewtabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.vtab{padding:8px 14px;border:1px solid var(--line);border-radius:8px;background:#fff;font-size:13px;cursor:pointer;color:var(--ink-soft);font-weight:600}
.vtab.on{background:var(--navy);color:#fff;border-color:var(--navy)}
.ctrl2{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.ctrl2 input[type=text]{flex:1;min-width:160px;padding:9px 12px;border:1px solid var(--line);border-radius:20px;font-size:14px;background:#fff;outline:none}
.ctrl2 input[type=text]:focus{border-color:var(--focus)}
select{padding:9px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;font-size:13px;outline:none;max-width:220px}
.chip{padding:7px 12px;border:1px solid var(--line);border-radius:20px;background:#fff;font-size:12.5px;cursor:pointer;color:var(--ink-soft);white-space:nowrap}
.chip.on{background:var(--focus);color:#fff;border-color:var(--focus)}
.chip[aria-pressed="false"]{opacity:.65}
.toggles{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-top:9px;font-size:12.5px;color:var(--ink-soft)}
.toggles label{display:flex;gap:6px;align-items:center;cursor:pointer}
.count{font-size:12.5px;color:var(--ink-faint);margin:10px 2px 4px}

/* legend */
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--ink-soft);margin:4px 0 16px;
  background:#fff;border:1px solid var(--line);border-radius:8px;padding:10px 14px}
.legend .it{display:flex;gap:6px;align-items:center}
.swatch{width:14px;height:14px;border-radius:3px;display:inline-block}
.swatch.band{height:9px;border-radius:5px}
.dash{width:18px;height:0;border-top:2px dashed #b9a; display:inline-block}

/* ---- 表格/卡片 工具栏 ---- */
.toolbar{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:0 0 10px;font-size:12.5px;color:var(--ink-soft)}
.toolbar .tbinfo{font-weight:700;color:var(--ink)}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:9px;overflow:hidden;background:#fff}
.seg .sg{border:0;background:#fff;padding:8px 13px;font-size:12.5px;cursor:pointer;color:var(--ink-soft);font-weight:600}
.seg .sg+.sg{border-left:1px solid var(--line)}
.seg .sg.on{background:var(--navy);color:#fff}
.mini{padding:8px 10px;border:1px solid var(--line);border-radius:9px;background:#fff;font-size:12.5px;color:var(--ink-soft);outline:none}
.yearnav{display:none;align-items:center;gap:5px}
.yearnav span{font-size:12px;color:var(--ink-soft);white-space:nowrap}
.yearnav button{padding:7px 9px;border:1px solid var(--line);border-radius:7px;background:#fff;color:var(--navy);font-size:12px;font-weight:700;cursor:pointer}
.yearnav button:focus-visible,.vtab:focus-visible,.chip:focus-visible,.sg:focus-visible,.btn:focus-visible,.fsexit:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.scrollhint{display:none;color:var(--ink-soft);font-size:12px}

/* ---- 表格 ---- */
.gridwrap{position:relative}
.tablewrap{overflow:auto;max-height:74vh;border:1px solid var(--line);border-radius:10px;background:#fff;
  box-shadow:0 1px 2px rgba(0,0,0,.03);-webkit-overflow-scrolling:touch;scrollbar-width:thin;overscroll-behavior:contain}
.tablewrap table{width:100%;border-collapse:separate;border-spacing:0;font-size:12.5px;min-width:1140px}
/* 年度分区竖线：明显分隔 2026 / 2025 / 2024 */
.tablewrap th.sep,.tablewrap td.sep{border-left:2px solid #c3b9a7}
.tablewrap td.plan{font-weight:700;color:var(--navy)}
.tablewrap td.plan sup{color:#c0492f;font-weight:700;margin-left:1px}
.planbtn{border:0;background:transparent;color:var(--navy);font-weight:700;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:3px;cursor:pointer;padding:4px}
.planbtn:focus-visible{outline:3px solid var(--focus);outline-offset:2px;border-radius:4px}
.tablewrap th,.tablewrap td{padding:8px 9px;text-align:center;border-bottom:1px solid var(--line-soft);white-space:nowrap;background:#fff}
.tablewrap thead th{background:#f0ece4;color:var(--navy);font-weight:700;cursor:pointer;user-select:none;
  position:sticky;z-index:2;border-bottom:1px solid var(--line)}
.tablewrap thead tr:first-child th{top:0}
.tablewrap thead tr:nth-child(2) th{top:36px}
.tablewrap thead th:hover{background:#e6e0d4}
.tablewrap th.noSort{cursor:default;color:var(--navy)}
/* 首列吸附（横向滚动时院校名始终可见） */
.tablewrap th.col-name,.tablewrap td.name{position:sticky;left:0;z-index:1;text-align:left}
.tablewrap th.col-name{z-index:4;border-right:1px solid var(--line)}
.tablewrap td.name{background:#fff;border-right:1px solid var(--line)}
.tablewrap td.name{font-weight:600;white-space:normal;min-width:150px;max-width:190px;line-height:1.35}
.tablewrap thead tr:nth-child(2) th.col-name{z-index:4}
.tablewrap td .yr{color:var(--ink-faint);font-size:11px;font-weight:400}
.tablewrap tbody tr:hover td{background:#faf8f3}
.tablewrap tbody tr:hover td.name{background:#f6f2ea}
.cellnull{color:#c2bdb2}
.cellnum{font-weight:600}
.tbadge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:700;color:#fff}
.bbadge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:700}
.bbadge.real{background:#e6f6ec;color:#1f7a45;border:1px solid #b9e3c8}
.bbadge.est{background:#f3eee4;color:#8a7a4f;border:1px solid #e0d6bf}

/* ---- 卡片视图：每张卡片完整展示三个年度 ---- */
.cards{display:grid;grid-template-columns:1fr;gap:10px}
.scard{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;box-shadow:0 1px 2px rgba(0,0,0,.03)}
.sc-h{display:flex;justify-content:space-between;gap:8px;align-items:flex-start;flex-wrap:wrap}
.sc-name{font-weight:700;font-size:14.5px;line-height:1.3}
.sc-badges{display:flex;gap:5px;flex-wrap:wrap}
.sc-meta{font-size:11.5px;color:var(--ink-faint);margin:3px 0 8px}
.sc-facts{display:flex;gap:18px;font-size:12px;color:var(--ink-soft);margin-bottom:8px;flex-wrap:wrap}
.sc-facts b{color:var(--navy);font-size:14px}
.sc-year{border-top:1px solid var(--line-soft);padding:8px 0}
.sc-year:last-child{padding-bottom:0}
.sc-year h4{margin:0 0 5px;color:var(--navy);font-size:13px}
.sc-metrics{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:3px}
.sc-metrics span{min-width:0;text-align:center;border-right:1px solid var(--line-soft);font-size:12.5px;font-weight:700;white-space:nowrap}
.sc-metrics span:last-child{border:0}
.sc-metrics small{display:block;font-size:10.5px;font-weight:400;color:var(--ink-soft);white-space:nowrap}
@media(min-width:721px){.cards{grid-template-columns:repeat(auto-fill,minmax(340px,1fr))}}

/* ---- 专注模式：筛选、排序和完整矩阵一起进入视口 ---- */
.fsbar{display:none}
.workarea.fs{position:fixed;inset:0;z-index:999;background:var(--paper);width:100%;height:100dvh;overflow:auto;padding:0 12px 24px;overscroll-behavior:contain}
.workarea.fs .fsbar{display:flex;position:sticky;top:0;z-index:50;min-height:48px;align-items:center;justify-content:space-between;gap:10px;background:var(--navy);color:#fff;margin:0 -12px 8px;padding:env(safe-area-inset-top) 12px 0}
.workarea.fs .fsexit{min-height:40px;padding:7px 12px;border:1px solid rgba(255,255,255,.5);border-radius:8px;background:transparent;color:#fff;font-size:13px;font-weight:700;cursor:pointer}
.workarea.fs .ctrl{top:48px}
.workarea.fs .tablewrap{max-height:calc(100dvh - 210px);min-height:240px}
.workarea.fs .legend{display:none}
body.noscroll{overflow:hidden}
.plandialog{width:min(92vw,430px);border:1px solid var(--line);border-radius:12px;padding:18px;background:#fff;color:var(--ink);box-shadow:0 12px 40px rgba(0,0,0,.18)}
.plandialog::backdrop{background:rgba(22,40,58,.55)}
.plandialog h2{font-size:17px;margin:0 0 10px}
.plandialog p{font-size:13px;margin:7px 0;overflow-wrap:anywhere}
.plandialog button{min-height:40px;margin-top:12px;padding:8px 16px;border:0;border-radius:8px;background:var(--navy);color:#fff;font-weight:700;cursor:pointer}

/* horizontal band rows */
.hrow{display:grid;grid-template-columns:210px 1fr 64px;gap:10px;align-items:center;background:#fff;
  border:1px solid var(--line);border-radius:9px;padding:9px 12px;margin-bottom:8px}
.hrow .meta{font-size:13px}
.hrow .meta .nm{font-weight:700}
.hrow .meta .sub{font-size:11px;color:var(--ink-faint);margin-top:2px}
.hrow .chart{flex:1}
.hrow .nn{text-align:right;font-size:12px;color:var(--ink-soft)}
.hrow .nn b{font-size:15px;color:var(--ink)}
.axis{display:flex;justify-content:space-between;font-size:10.5px;color:var(--ink-faint);margin:2px 0 6px;padding-left:220px}
@media(max-width:720px){.hrow{grid-template-columns:1fr;}.hrow .meta{display:flex;justify-content:space-between;align-items:baseline}.axis{padding-left:0}}

/* vertical */
.vwrap{display:grid;grid-template-columns:1fr;gap:16px}
.vcard{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.vcard h3{margin:0 0 4px;font-family:"Songti SC",serif;font-size:17px}
.vcard .vsub{font-size:12px;color:var(--ink-faint);margin-bottom:12px}
.metricline{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;margin-top:10px}
.metricline .m{display:flex;gap:6px;align-items:center}
.note{font-size:11.5px;color:var(--ink-faint);margin-top:8px;line-height:1.5}
.src{font-size:11px;color:#a89; margin-top:4px}
select.school{width:100%;max-width:none}

.foot{margin-top:26px;font-size:11.5px;color:var(--ink-faint);line-height:1.7;border-top:1px solid var(--line);padding-top:14px}
.empty{text-align:center;color:var(--ink-faint);padding:40px;font-size:14px}
.btn{padding:7px 13px;border:1px solid var(--line);border-radius:8px;background:#fff;font-size:12.5px;cursor:pointer;color:var(--ink-soft)}
.btn:hover{border-color:var(--focus);color:var(--focus)}
@media(max-width:720px){
  .wrap{padding:0 10px 48px}
  .masthead{margin:0 -10px 12px;padding:16px 14px 14px}
  .masthead h1{font-size:20px;line-height:1.32}
  .masthead .sub{font-size:12px;line-height:1.55}
  .masthead .kpis{gap:6px;margin-top:11px;overflow-x:auto;flex-wrap:nowrap;padding-bottom:4px}
  .kpi{min-width:94px;padding:7px 9px;flex:0 0 auto}
  .kpi b{font-size:18px}
  .notice{font-size:12px;padding:10px 11px;margin-bottom:10px}
  .ctrl{position:static;backdrop-filter:none;padding:3px 0 10px;margin-bottom:8px}
  .viewtabs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:4px}
  .vtab{min-width:0;min-height:44px;padding:6px 3px;font-size:11.5px;line-height:1.25;text-align:center}
  .ctrl2 input[type=text]{flex-basis:100%;min-width:0;min-height:44px;border-radius:8px}
  .ctrl2 select{flex:1;min-width:0;max-width:none;min-height:42px}
  .toggles{gap:6px;margin-top:8px}
  .toggles .tier-label{flex-basis:100%}
  .toggles .chip{min-height:38px;padding:7px 9px;font-size:11.5px}
  .toggles label{flex-basis:100%;min-height:36px}
  .legend{margin-bottom:8px;font-size:11px;gap:8px;padding:8px}
  .toolbar{gap:7px;margin-bottom:7px}
  .toolbar .tbinfo{flex-basis:100%}
  .seg .sg{min-height:40px;padding:7px 10px}
  .mini,.btn{min-height:40px}
  #sortSel{flex:1;min-width:118px}
  .yearnav{display:flex;flex-basis:100%;overflow-x:auto;padding:2px 0}
  .scrollhint{display:block;flex-basis:100%}
  #modeTip{display:none}
  .tablewrap{height:min(68dvh,680px);max-height:none;border-radius:8px}
  .tablewrap table{min-width:1170px;font-size:12px}
  .tablewrap td.name{min-width:116px;max-width:116px;font-size:11.5px}
  .tablewrap th,.tablewrap td{padding:8px 7px}
  .tablewrap thead tr:nth-child(2) th{top:36px}
  .workarea.fs .ctrl{position:static}
  .workarea.fs .tablewrap{height:calc(100dvh - 72px);max-height:none}
  .workarea.fs .scrollhint{display:none}
  .scard{padding:11px 12px}
  .sc-metrics{gap:0}
}
@media(max-width:360px){
  .sc-metrics small{font-size:9.5px}
  .sc-metrics span{font-size:11.5px}
  .toggles .chip{font-size:11px;padding:6px 7px}
}
</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <div class="crumb"><a href="nav.html">← 资料导航</a><a href="mobile-summary-preview.html">手机端精简方案预览</a></div>
    <h1>麻醉学专硕择校参考 · 三年分数与人数对照</h1>
    <div class="sub">105118 麻醉学专硕 · 2024–2026 三年实际复试线与录取分数/人数。本页只展示「查得到」的真实录取最低/最高分，查不到的留空（—），<b>绝不把国家线或复试线当作录取分</b>。分数只是参考，找到与你合拍的城市和平台才是关键，别被任何一个数字吓到。</div>
    <div class="kpis" id="kpis"></div>
  </header>

  <div class="notice">
    <b>数据说明：</b> ① <b>录取最低 / 录取最高</b>来自各校拟录取名单公示或机构交叉验证，是「真实进面并上岸」的分数区间；② <b>复试线</b>只是入场券，往往远低于实际录取分；③ <b>国家线（A区 304/293/294，B区 294/283/284）</b>仅为政策参考，<u>不是任何院校的实际门槛</u>；④ <b>—</b> 表示「未检索到可核验的公开录取分」<b>不代表 0 分或未招生</b>；⑤ 每校带 <span class="bbadge real">实测</span>/<span class="bbadge est">线估</span> 标记，线估=仅有复试线、实际录取分未知；⑥ <b>27计划</b>为 2027 年（27考研）招生目录的检索整理值（多为不含推免），带 <b style="color:#c0492f">*</b> 者含推免或为总数，<b>—</b> 表示暂未检索到。
  </div>

  <div class="workarea" id="workArea">
    <div class="fsbar"><strong>三年数据对照</strong><button class="fsexit" id="fsExit" type="button">退出专注模式</button></div>
  <div class="ctrl">
    <div class="viewtabs">
      <button class="vtab on" data-view="table" type="button">数据总表</button>
      <button class="vtab" data-view="h" type="button">同年横向对比</button>
      <button class="vtab" data-view="v" type="button">同校三年趋势</button>
    </div>
    <div class="ctrl2">
      <input type="text" id="search" placeholder="搜索院校 / 地区 / 城市…">
      <select id="yearSel"></select>
      <select id="schoolSel"></select>
    </div>
    <div class="toggles">
      <span class="tier-label" style="font-weight:700;color:var(--ink)">梯度参考：</span>
      <button class="chip on" data-tier="从容区" aria-pressed="true" type="button">从容区 ≤300</button>
      <button class="chip on" data-tier="稳健区" aria-pressed="true" type="button">稳健区 301–320</button>
      <button class="chip on" data-tier="进取区" aria-pressed="true" type="button">进取区 321–335</button>
      <button class="chip on" data-tier="冲刺区" aria-pressed="true" type="button">冲刺区 336+</button>
      <label><input type="checkbox" id="onlyReal"> 只显示「实测录取分」院校</label>
    </div>
  </div>

  <div class="legend" id="legend"></div>

  <div class="count" id="count"></div>

  <div class="toolbar" id="tabletoolbar">
    <span class="tbinfo" id="tbInfo"></span>
    <span class="seg" id="modeSeg">
      <button class="sg" data-mode="card" type="button">逐校卡片</button>
      <button class="sg" data-mode="table" type="button">完整表格</button>
    </span>
    <select class="mini" id="sortSel" title="排序方式">
      <option value="" disabled>按表头排序中</option>
      <option value="gate:1">门槛 低→高</option>
      <option value="gate:-1">门槛 高→低</option>
      <option value="name:1">院校名 A→Z</option>
      <option value="name:-1">院校名 Z→A</option>
    </select>
    <button class="btn" id="fsBtn" type="button">专注查看</button>
    <div class="yearnav" id="yearNav" aria-label="表格年份定位"><span>跳至</span><button type="button" data-jump="start">院校</button><button type="button" data-jump="2026">2026</button><button type="button" data-jump="2025">2025</button><button type="button" data-jump="2024">2024</button></div>
    <span class="scrollhint" id="scrollHint">表格可左右滑动；院校列固定，三年数据均在表内。</span>
    <span class="mini" id="modeTip" style="border-style:dashed"></span>
  </div>

  <div class="gridwrap" id="gridWrap">
    <div id="viewTable"></div>
  </div>
  <div id="viewH"></div>
  <div id="viewV"></div>
  <dialog class="plandialog" id="planDialog"><h2 id="planTitle"></h2><p id="planBasis"></p><p id="planSource"></p><button id="planClose" type="button">关闭</button></dialog>
  </div>

  <div class="foot" id="foot"></div>
</div>

<script>
const DATA = __DATA_JSON__;
const YEARS = DATA.years;
const TABLE_YEARS = [...YEARS].reverse();
const TIER_COLOR = DATA.tierColor;
const NAT = DATA.natline;
let state = { view:'table', year:'2026', tier:{从容区:true,稳健区:true,进取区:true,冲刺区:true}, onlyReal:false, q:'' };

function tierBadge(t){ const c=TIER_COLOR[t]||'#888'; return `<span class="tbadge" style="background:${c}">${t}</span>`; }
function basisBadge(b){ return b==='实测'?`<span class="bbadge real">实测</span>`:`<span class="bbadge est">线估</span>`; }
function fmt(v){ return v===null||v===undefined||v===''?`<span class="cellnull">—</span>`:`<span class="cellnum">${v}</span>`; }

function filtered(){
  const q = state.q.trim().toLowerCase();
  return DATA.schools.filter(s=>{
    if(!state.tier[s.tier]) return false;
    if(state.onlyReal && s.basis!=='实测') return false;
    if(q && !(s.n.toLowerCase().includes(q)||s.r.toLowerCase().includes(q)||(s.c||'').toLowerCase().includes(q))) return false;
    return true;
  });
}

// ---------- KPIs ----------
function renderKpis(){
  const total=DATA.schools.length;
  const real=DATA.schools.filter(s=>s.basis==='实测').length;
  const est=total-real;
  const td={};DATA.schools.forEach(s=>td[s.tier]=(td[s.tier]||0)+1);
  const el=document.getElementById('kpis');
  el.innerHTML=`
    <div class="kpi"><b>${total}</b><span>纳入院校</span></div>
    <div class="kpi ok"><b>${real}</b><span>实测录取分</span></div>
    <div class="kpi warn"><b>${est}</b><span>仅复试线（线估）</span></div>
    <div class="kpi"><b>${td['从容区']||0}</b><span>从容区 ≤300</span></div>
    <div class="kpi"><b>${td['稳健区']||0}</b><span>稳健区 301–320</span></div>
    <div class="kpi"><b>${td['进取区']||0}</b><span>进取区 321–335</span></div>
    <div class="kpi"><b>${td['冲刺区']||0}</b><span>冲刺区 336+</span></div>`;
}

// ---------- Legend ----------
function renderLegend(){
  document.getElementById('legend').innerHTML=`
    <div class="it"><span class="swatch band" style="background:${TIER_COLOR['从容区']}"></span>录取区间(最低→最高)</div>
    <div class="it"><span class="swatch" style="background:#3b4a5a;border-radius:50%"></span>复试线(fs)</div>
    <div class="it"><span class="swatch" style="background:#c0492f;border-radius:50%"></span>录取均分(avg)</div>
    <div class="it"><span class="dash"></span>仅复试线·录取分未知</div>
    <div class="it"><span class="bbadge real">实测</span>有真实录取最低/最高分</div>
    <div class="it"><span class="bbadge est">线估</span>仅复试线·未知</div>`;
}

// ---------- Table view ----------
let sortKey='gate', sortDir=1;
let cardPref = false;           // 完整矩阵是手机与桌面的默认视图
function useCard(){ return cardPref; }

function sortList(list){
  list.sort((a,b)=>{
    let va,vb;
    if(sortKey==='gate'){va=a.gate;vb=b.gate;}
    else if(sortKey==='name'){va=a.n;vb=b.n;return sortDir*va.localeCompare(vb,'zh');}
    else if(sortKey==='basis'){va=a.basis;vb=b.basis;return sortDir*va.localeCompare(vb);}
    else { const y=sortKey.slice(0,4); const m=sortKey.slice(4); va=a.y[y][m]; vb=b.y[y][m]; }
    if(va===vb) return 0; if(va===null) return 1; if(vb===null) return -1; return sortDir*(va-vb);
  });
  return list;
}

function renderTable(){
  const list=sortList(filtered().slice());
  const head=`<tr>
    <th class="col-name" data-k="name">院校 ⇅</th><th data-k="gate">门槛 ⇅</th><th class="noSort">梯度</th><th class="noSort">状态</th><th class="noSort sep">27计划</th>
    ${TABLE_YEARS.map(y=>`<th class="sep" colspan="5" data-year="${y}">${y} 年</th>`).join('')}
  </tr><tr>
    <th class="col-name noSort"></th><th class="noSort"></th><th class="noSort"></th><th class="noSort"></th><th class="noSort sep"></th>
    ${TABLE_YEARS.map(y=>`<th class="sep" data-k="${y}fs">线</th><th data-k="${y}lo">最低</th><th data-k="${y}hi">最高</th><th data-k="${y}avg">均分</th><th data-k="${y}n">人数</th>`).join('')}
  </tr>`;
  const body=list.map(s=>{
    const cells=TABLE_YEARS.map(y=>{const r=s.y[y];return `<td class="sep">${fmt(r.fs)}</td><td>${fmt(r.lo)}</td><td>${fmt(r.hi)}</td><td>${fmt(r.avg)}</td><td>${fmt(r.n)}</td>`;}).join('');
    const hasPlan = s.plan27!==null && s.plan27!==undefined;
    const mark = (hasPlan && s.plan27Basis!=='统考/不含推免') ? '<sup>*</sup>' : '';
    const planCell = hasPlan ? `<span class="cellnum">${s.plan27}</span>${mark}` : `<span class="cellnull">—</span>`;
    const idx=DATA.schools.indexOf(s);
    return `<tr>
      <td class="name">${s.n}<div class="yr">${s.r}·${s.c} ${s.z}${s.lv?' · '+s.lv:''}</div></td>
      <td><b>${s.gate}</b></td><td>${tierBadge(s.tier)}</td><td>${basisBadge(s.basis)}</td>
      <td class="plan sep"><button class="planbtn" type="button" data-plan-index="${idx}" aria-label="${s.n} 2027 计划口径与来源">${planCell}</button></td>
      ${cells}</tr>`;
  }).join('');
  document.getElementById('viewTable').innerHTML=`<div class="tablewrap"><table><thead>${head}</thead><tbody>${body||'<tr><td colspan="20" class="empty">无匹配院校</td></tr>'}</tbody></table></div>`;
  document.querySelectorAll('#viewTable th[data-k]').forEach(th=>th.onclick=()=>{
    const k=th.getAttribute('data-k'); if(sortKey===k)sortDir*=-1; else{sortKey=k;sortDir=1;} renderListView();
  });
}

// ---------- Mobile card view ----------
function renderCards(){
  const list=sortList(filtered().slice());
  const metrics=[['复试线','fs'],['最低','lo'],['最高','hi'],['均分','avg'],['人数','n']];
  const cards=list.map(s=>{
    const years=YEARS.map(y=>`<section class="sc-year"><h4>${y} 年</h4><div class="sc-metrics">${metrics.map(([lab,k])=>`<span><small>${lab}</small>${fmt(s.y[y][k])}</span>`).join('')}</div></section>`).join('');
    const hasPlan=s.plan27!==null&&s.plan27!==undefined;
    const mark=(hasPlan&&s.plan27Basis!=='统考/不含推免')?'<sup>*</sup>':'';
    const idx=DATA.schools.indexOf(s);
    return `<div class="scard">
      <div class="sc-h"><div class="sc-name">${s.n}</div><div class="sc-badges">${tierBadge(s.tier)}${basisBadge(s.basis)}</div></div>
      <div class="sc-meta">${s.r}·${s.c} ${s.z}${s.lv?' · '+s.lv:''}</div>
      <div class="sc-facts"><span>门槛 <b>${s.gate}</b></span><button class="planbtn" type="button" data-plan-index="${idx}">27计划 ${hasPlan?s.plan27+mark:'—'} · 查看口径</button></div>
      ${years}
    </div>`;
  }).join('');
  document.getElementById('viewTable').innerHTML=`<div class="cards">${cards||'<div class="empty">无匹配院校</div>'}</div>`;
}

function syncToolbar(){
  const onCard=useCard();
  document.querySelectorAll('#modeSeg .sg').forEach(b=>{
    const active=(b.getAttribute('data-mode')==='card')===onCard;
    b.classList.toggle('on',active); b.setAttribute('aria-pressed',String(active));
  });
  const ss=document.getElementById('sortSel'); const val=sortKey+':'+sortDir;
  ss.value=[...ss.options].some(o=>o.value===val)?val:'';
  document.getElementById('tbInfo').textContent=`共 ${filtered().length} 所`;
  const tip=document.getElementById('modeTip');
  tip.textContent = cardPref?'三年全部字段逐校展示':'三年全部字段横向展开';
  document.getElementById('yearNav').style.display=onCard?'none':'';
  document.getElementById('scrollHint').style.display=onCard?'none':'';
}

function renderListView(){
  const old=document.querySelector('#viewTable .tablewrap');
  const left=old?old.scrollLeft:0, top=old?old.scrollTop:0;
  syncToolbar();
  if(useCard()) renderCards();
  else { renderTable(); const wrap=document.querySelector('#viewTable .tablewrap'); wrap.scrollLeft=left;wrap.scrollTop=top; }
}

function jumpToYear(year){
  if(useCard()){cardPref=false;renderListView();}
  const wrap=document.querySelector('#viewTable .tablewrap');
  if(!wrap) return;
  const th=year==='start'?null:wrap.querySelector(`th[data-year="${year}"]`);
  const target=th?wrap.scrollLeft+th.getBoundingClientRect().left-wrap.getBoundingClientRect().left-wrap.querySelector('th.col-name').offsetWidth:0;
  wrap.scrollTo({left:Math.max(0,target),behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
}

function showPlanInfo(index){
  const s=DATA.schools[index];
  if(!s) return;
  document.getElementById('planTitle').textContent=`${s.n} · 2027 计划`;
  document.getElementById('planBasis').textContent=`招生计划：${s.plan27===null?'暂未检索到':s.plan27}；口径：${s.plan27Basis||'未知'}`;
  document.getElementById('planSource').textContent=`来源：${s.plan27Src||'暂未检索到'}`;
  document.getElementById('planDialog').showModal();
}

// ---------- Horizontal view ----------
function renderH(){
  const y=state.year;
  let list=filtered().filter(s=>s.y[y].fs!==null||s.y[y].lo!==null);
  list.sort((a,b)=>{
    const av=a.y[y].lo!==null?a.y[y].lo:a.y[y].fs;
    const bv=b.y[y].lo!==null?b.y[y].lo:b.y[y].fs;
    return av-bv;
  });
  const nat=NAT[y];
  const SCORE_MIN=280, SCORE_MAX=440, W=720;
  const X=v=>((Math.max(SCORE_MIN,Math.min(SCORE_MAX,v))-SCORE_MIN)/(SCORE_MAX-SCORE_MIN))*W;
  document.getElementById('count').textContent=`横向对比 · ${y} 年（按录取最低分升序；无真实录取分者按复试线排，标「仅线」）｜ 共 ${list.length} 所（未列无当年线院校）`;
  const axis=`<div class="axis"><span>${SCORE_MIN}</span><span>320</span><span>360</span><span>400</span><span>${SCORE_MAX}</span></div>`;
  const rows=list.map(s=>{
    const r=s.y[y]; const c=TIER_COLOR[s.tier];
    let svg=`<svg viewBox="0 0 ${W} 34" width="100%" height="34" preserveAspectRatio="none" style="display:block">`;
    // baseline
    svg+=`<line x1="0" y1="17" x2="${W}" y2="17" stroke="#eee" stroke-width="1"/>`;
    // national line markers
    svg+=`<line x1="${X(nat[0])}" y1="2" x2="${X(nat[0])}" y2="32" stroke="#d9c9b8" stroke-dasharray="3 3"/>`;
    svg+=`<line x1="${X(nat[1])}" y1="2" x2="${X(nat[1])}" y2="32" stroke="#cdb89e" stroke-dasharray="3 3"/>`;
    if(r.lo!==null && r.hi!==null){
      svg+=`<rect x="${X(r.lo)}" y="9" width="${Math.max(2,X(r.hi)-X(r.lo))}" height="16" rx="6" fill="${c}" opacity="0.85"/>`;
      if(r.avg!==null) svg+=`<circle cx="${X(r.avg)}" cy="17" r="3.2" fill="#c0492f" stroke="#fff" stroke-width="1"/>`;
    } else {
      svg+=`<rect x="0" y="13" width="${W}" height="8" rx="4" fill="none" stroke="#cdbfa6" stroke-dasharray="4 4"/>`;
    }
    if(r.fs!==null) svg+=`<circle cx="${X(r.fs)}" cy="17" r="3.6" fill="#3b4a5a" stroke="#fff" stroke-width="1"/>`;
    svg+=`</svg>`;
    const tag = r.lo!==null ? `${r.lo}–${r.hi}${r.avg!==null?' ·均'+r.avg:''}` : `<span style="color:#a8946f">仅线 ${r.fs}${r.fsKind?('·'+r.fsKind):''}</span>`;
    return `<div class="hrow">
      <div class="meta"><div class="nm">${s.n} ${tierBadge(s.tier)}</div><div class="sub">${s.r}·${s.c} ${s.z} ${basisBadge(s.basis)}</div></div>
      <div class="chart">${svg}</div>
      <div class="nn">${tag}<br><span style="font-size:11px">${r.n!==null?('录'+r.n+'人'):'人数—'}</span></div>
    </div>`;
  }).join('');
  document.getElementById('viewH').innerHTML=axis+rows;
}

// ---------- Vertical view ----------
function renderV(){
  const name=state.schoolSel;
  const s=DATA.schools.find(x=>x.n===name);
  if(!s){ document.getElementById('viewV').innerHTML=`<div class="empty">请选择院校</div>`; return; }
  const SCORE_MIN=280, SCORE_MAX=440, W=640, H=240, PAD=38;
  const X=i=>PAD+ i*( (W-PAD-20)/(YEARS.length-1) );
  const Y=v=>H-PAD-((Math.max(SCORE_MIN,Math.min(SCORE_MAX,v))-SCORE_MIN)/(SCORE_MAX-SCORE_MIN))*(H-PAD-20);
  function path(key,color,dash){
    let pts=[],seg=[];
    YEARS.forEach((y,i)=>{const v=s.y[y][key]; if(v===null){if(seg.length>1)pts.push(seg);seg=[];}else{seg.push([X(i),Y(v),y,v]);}});
    if(seg.length>1)pts.push(seg);
    let p='';pts.forEach(seg=>{p+='<polyline points="'+seg.map(p=>p[0]+','+p[1]).join(' ')+'" fill="none" stroke="'+color+'" stroke-width="2.4" '+(dash?'stroke-dasharray="5 4"':'')+'/>';
      seg.forEach(pt=>{p+='<circle cx="'+pt[0]+'" cy="'+pt[1]+'" r="3.6" fill="'+color+'"/>';p+='<text x="'+pt[0]+'" y="'+(pt[1]-9)+'" font-size="11" fill="'+color+'" text-anchor="middle">'+pt[3]+'</text>';});});
    return p;
  }
  let svg=`<svg viewBox="0 0 ${W} ${H}" width="100%" style="max-width:680px">`;
  // grid + y labels
  for(let v=SCORE_MIN; v<=SCORE_MAX; v+=20){ const yy=Y(v); svg+=`<line x1="${PAD}" y1="${yy}" x2="${W-20}" y2="${yy}" stroke="#eee"/><text x="6" y="${yy+4}" font-size="10" fill="#9aa">${v}</text>`; }
  // x labels
  YEARS.forEach((y,i)=>{ svg+=`<text x="${X(i)}" y="${H-14}" font-size="12" fill="#567" text-anchor="middle" font-weight="700">${y}</text>`;
    const n=s.y[y].n; svg+=`<text x="${X(i)}" y="${H-1}" font-size="10" fill="#8a93a0" text-anchor="middle">${n!==null?('录'+n+'人'):'人数—'}</text>`; });
  svg+=path('fs','#3b4a5a',true);
  svg+=path('lo',TIER_COLOR[s.tier],false);
  svg+=path('hi',TIER_COLOR[s.tier],false);
  svg+=path('avg','#c0492f',false);
  svg+=`</svg>`;
  const ml=YEARS.map(y=>{const r=s.y[y];return `<div class="m"><b>${y}</b> 线${fmt(r.fs)} / 最低${fmt(r.lo)} / 最高${fmt(r.hi)} / 均${fmt(r.avg)} / 人${fmt(r.n)}</div>`;}).join('');
  const notes=YEARS.map(y=>{const r=s.y[y];return r.note?`<div class="note">${y}：${r.note}</div>`:'';}).join('');
  document.getElementById('viewV').innerHTML=`<div class="vcard">
    <h3>${s.n} ${tierBadge(s.tier)} ${basisBadge(s.basis)}</h3>
    <div class="vsub">${s.r}·${s.c} ${s.z}${s.lv?' · '+s.lv:''} ｜ 门槛(三年最低) ${s.gate} ｜ 27计划 ${s.plan27!==null&&s.plan27!==undefined?s.plan27:'—'}</div>
    ${svg}
    <div class="metricline">${ml}</div>
    ${notes}
    <div class="metricline" style="margin-top:6px"><span style="color:#3b4a5a">— — 复试线</span><span style="color:${TIER_COLOR[s.tier]}">—— 录取最低/最高</span><span style="color:#c0492f">—— 录取均分</span></div>
  </div>`;
}

// ---------- 专注模式 ----------
function setFs(on){
  const area=document.getElementById('workArea');
  area.classList.toggle('fs', !!on);
  document.body.classList.toggle('noscroll', !!on);
  if(on){ area.scrollTop=0; if(area.requestFullscreen){ const p=area.requestFullscreen(); if(p&&p.catch) p.catch(()=>{}); } }
  else if(document.fullscreenElement===area && document.exitFullscreen){ const p=document.exitFullscreen(); if(p&&p.catch) p.catch(()=>{}); }
}
document.addEventListener('fullscreenchange', ()=>{
  const area=document.getElementById('workArea');
  if(!document.fullscreenElement && area.classList.contains('fs')) setFs(false);
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.getElementById('workArea').classList.contains('fs'))setFs(false);});

function showView(){
  document.querySelectorAll('.vtab').forEach(t=>{const active=t.getAttribute('data-view')===state.view;t.classList.toggle('on',active);t.setAttribute('aria-pressed',String(active));});
  const isTable = state.view==='table';
  document.getElementById('tabletoolbar').style.display = isTable?'flex':'none';
  document.getElementById('gridWrap').style.display = isTable?'block':'none';
  document.getElementById('viewH').style.display = state.view==='h'?'block':'none';
  document.getElementById('viewV').style.display = state.view==='v'?'block':'none';
  document.getElementById('yearSel').style.display=state.view==='h'?'block':'none';
  document.getElementById('schoolSel').style.display=state.view==='v'?'block':'none';
  document.getElementById('count').textContent='';
  if(isTable) renderListView();
  else if(state.view==='h') renderH();
  else renderV();
}

function refresh(){ renderKpis(); renderLegend(); showView(); }

function init(){
  // year select
  const ys=document.getElementById('yearSel'); ys.innerHTML=YEARS.map(y=>`<option value="${y}">横向年份：${y}</option>`).join('');
  ys.value=state.year; ys.onchange=()=>{state.year=ys.value;if(state.view==='h')renderH();};
  // school select
  const ss=document.getElementById('schoolSel');
  ss.innerHTML=`<option value="">纵向院校：选择…</option>`+DATA.schools.map(s=>`<option value="${s.n}">${s.n}（${s.tier}·${s.basis}）</option>`).join('');
  ss.onchange=()=>{ state.schoolSel=ss.value; if(state.view!=='v'){state.view='v';} showView(); };
  // tabs
  document.querySelectorAll('.vtab').forEach(t=>t.onclick=()=>{ state.view=t.getAttribute('data-view'); if(state.view==='v'&&!state.schoolSel){state.schoolSel=DATA.schools[0].n;ss.value=state.schoolSel;} showView(); });
  // chips
  document.querySelectorAll('.chip[data-tier]').forEach(c=>c.onclick=()=>{ const t=c.getAttribute('data-tier'); state.tier[t]=!state.tier[t]; c.classList.toggle('on',state.tier[t]);c.setAttribute('aria-pressed',String(state.tier[t])); refresh(); });
  document.getElementById('onlyReal').onchange=e=>{ state.onlyReal=e.target.checked; refresh(); };
  document.getElementById('search').oninput=e=>{ state.q=e.target.value; refresh(); };
  // 视图模式（卡片 / 表格）
  document.querySelectorAll('#modeSeg .sg').forEach(b=>b.onclick=()=>{ cardPref=b.getAttribute('data-mode')==='card'; renderListView(); });
  // 排序
  document.getElementById('sortSel').onchange=e=>{ const p=e.target.value.split(':'); sortKey=p[0]; sortDir=parseInt(p[1],10); renderListView(); };
  // 全屏
  document.getElementById('fsBtn').onclick=()=>setFs(true);
  document.getElementById('fsExit').onclick=()=>setFs(false);
  document.querySelectorAll('#yearNav button').forEach(b=>b.onclick=()=>jumpToYear(b.dataset.jump));
  document.getElementById('viewTable').addEventListener('click',e=>{const b=e.target.closest('.planbtn');if(b)showPlanInfo(Number(b.dataset.planIndex));});
  document.getElementById('planClose').onclick=()=>document.getElementById('planDialog').close();
  // foot
  document.getElementById('foot').innerHTML=`数据基准：2024 / 2025 / 2026 三个完整招生年度。本页收录 ${DATA.schools.length} 所「三年内录取分数相对友好」的院校（含只查到复试线、录取分待核实的）。`+
    `「27计划」= 2027 年（27考研）105118 麻醉学专硕拟招生人数，为联网检索整理值，多为「不含推免」口径；带 <sup style="color:#c0492f">*</sup> 者为含推免或总数口径（点击计划数字查看口径与来源）；「—」表示暂未检索到，报考以各校当年官方招生目录为准。`+
    `「录取最低/最高」= 统考实际录取考生初试总分区间；「复试线」= 该校/院当年公布线（含国家线/校线/院线/自划线，见 fsKind）。`+
    `来源优先级：官方拟录取公示 / 复试线通知 ＞ 研招网 ＞ 启航/路灯/掌上考研/中公等机构整理（已交叉验证）。`+
    `未查到公开录取分的院校标注「线估」，其复试线不代表实际录取门槛。本页仅供初筛，报考请以目标院校当年官方公告为准。`;
  refresh();
}

init();
</script>
</body>
</html>
"""

html = html.replace('__DATA_JSON__', DATA_JSON)
open(OUT_HTML, 'w', encoding='utf-8').write(html)
print('HTML written:', OUT_HTML)

# 独立的手机端精简方案预览。正式主页始终保留完整三年矩阵。
preview = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>手机端精简方案预览 · 麻醉学专硕择校</title>
<style>
:root{color-scheme:light;--navy:#1f3a52;--paper:#f6f4ef;--line:#e3ddd2;--ink:#27303d;--muted:#5d6874;--accent:#c0492f}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.5 "PingFang SC","Microsoft YaHei",sans-serif}
button,input,select{font:inherit}
.page{max-width:720px;margin:auto;padding:0 12px 48px}
header{margin:0 -12px;padding:18px 16px 16px;background:var(--navy);color:#fff}
header a{color:#fff;text-decoration:underline;text-underline-offset:3px}
header h1{margin:9px 0 4px;font-size:21px;line-height:1.3}
header p{margin:0;font-size:12.5px;color:#e0e9ef}
.notice{background:#fff3e7;color:#62452e;border-left:4px solid var(--accent);padding:10px 12px;margin:12px 0;font-size:12px}
.controls{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:12px 0}
.controls input{grid-column:1/-1}
.controls input,.controls select{min-width:0;min-height:44px;border:1px solid var(--line);border-radius:8px;padding:9px;background:#fff;color:var(--ink)}
.count{font-size:12px;color:var(--muted);margin-bottom:8px}
.list{display:grid;gap:9px}
.card{background:#fff;border:1px solid var(--line);border-radius:11px;padding:13px 14px}
.top{display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.name{font-size:16px;font-weight:700;line-height:1.3}
.tier{font-size:11px;font-weight:700;white-space:nowrap}
.meta{font-size:11.5px;color:var(--muted);margin:4px 0 9px}
.primary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:5px;background:#f3f6f7;border-radius:8px;padding:9px}
.primary div{min-width:0}
.primary small,.secondary small{display:block;color:var(--muted);font-size:10.5px;white-space:nowrap}
.primary b{font-size:19px;color:var(--navy);line-height:1.3}
.secondary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:9px;padding-top:8px;border-top:1px solid #eee}
.secondary b{font-size:13px}
.missing{color:#9da4ad}
.foot{font-size:11.5px;color:var(--muted);margin-top:16px;line-height:1.6}
@media(min-width:560px){.list{grid-template-columns:repeat(2,minmax(0,1fr))}}
:focus-visible{outline:3px solid #2f7fd1;outline-offset:2px}
</style>
</head>
<body>
<div class="page">
  <header><a href="index.html">← 返回完整三年数据总表</a><h1>手机端精简方案预览</h1><p>按一个年度快速浏览关键分数，再决定是否适合长期使用。</p></header>
  <div class="notice">这是独立的交互预览。完整三年复试线、最低、最高、均分、人数仍在<a href="index.html">数据总表</a>，本页不用于全量对照。</div>
  <div class="controls"><input id="search" type="search" placeholder="搜索院校、地区或城市" aria-label="搜索院校、地区或城市"><select id="year" aria-label="选择年度"></select><select id="sort" aria-label="排序方式"><option value="gate">门槛从低到高</option><option value="lo">当年录取最低分</option><option value="avg">当年录取均分</option><option value="name">院校名称</option></select></div>
  <div class="count" id="count"></div><div class="list" id="list"></div>
  <div class="foot">“—”表示未检索到可核验数据，不代表 0 分或未招生。分数仅供初筛，报考以学校当年公告为准。</div>
</div>
<script>
const DATA=__DATA_JSON__;
const $=id=>document.getElementById(id);
const fmt=v=>v===null||v===undefined?'<span class="missing">—</span>':String(v);
function render(){
  const year=$('year').value, key=$('sort').value, q=$('search').value.trim().toLowerCase();
  const list=DATA.schools.filter(s=>!q||[s.n,s.r,s.c].some(v=>(v||'').toLowerCase().includes(q)));
  list.sort((a,b)=>{
    if(key==='name')return a.n.localeCompare(b.n,'zh');
    const av=key==='gate'?a.gate:a.y[year][key],bv=key==='gate'?b.gate:b.y[year][key];
    return (av===null?Infinity:av)-(bv===null?Infinity:bv)||a.n.localeCompare(b.n,'zh');
  });
  $('count').textContent=`${year} 年 · 共 ${list.length} 所院校`;
  $('list').innerHTML=list.map(s=>{
    const r=s.y[year];
    return `<article class="card"><div class="top"><div class="name">${s.n}</div><span class="tier">${s.tier}</span></div>
      <div class="meta">${s.r} · ${s.c} · ${s.basis}</div>
      <div class="primary"><div><small>三年门槛</small><b>${fmt(s.gate)}</b></div><div><small>${year} 录取最低</small><b>${fmt(r.lo)}</b></div><div><small>${year} 录取均分</small><b>${fmt(r.avg)}</b></div></div>
      <div class="secondary"><div><small>复试线</small><b>${fmt(r.fs)}</b></div><div><small>录取人数</small><b>${fmt(r.n)}</b></div><div><small>2027 计划</small><b>${fmt(s.plan27)}${s.plan27!==null&&s.plan27Basis!=='统考/不含推免'?'*':''}</b></div></div></article>`;
  }).join('')||'<div class="card">没有匹配的院校，请调整搜索词。</div>';
}
$('year').innerHTML=DATA.years.map(y=>`<option value="${y}">${y} 年</option>`).join('');
$('year').value='2026';
['search','year','sort'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',render));
render();
</script>
</body></html>
""".replace('__DATA_JSON__', DATA_JSON)
open(OUT_PREVIEW, 'w', encoding='utf-8').write(preview)
print('HTML written:', OUT_PREVIEW)
print('candidates:', n_total, '| 实测:', n_real, '| 线估:', n_est, '| tier:', tier_dist)
