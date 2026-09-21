#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2-2027：生成 HTML 分析页（沿用项目票据式风格）
输出： v2-2027/html/index.html      99 所速查总表
      v2-2027/html/tier350.html     350 分以下专题择校分析
"""
import json, os, html as H

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = json.load(open(os.path.join(BASE, 'data/master.json'), encoding='utf-8'))['schools']
OUT = os.path.join(BASE, 'html')
os.makedirs(OUT, exist_ok=True)

CSS = """
  :root {
    color-scheme: light;
    --paper: oklch(96% 0.018 83);
    --paper-deep: oklch(91% 0.026 81);
    --card: oklch(98.5% 0.008 83);
    --ink: oklch(27% 0.045 242);
    --ink-soft: oklch(43% 0.035 242);
    --ink-faint: oklch(58% 0.022 242);
    --navy: oklch(29% 0.065 242);
    --navy-deep: oklch(21% 0.05 242);
    --line: oklch(78% 0.025 82);
    --accent: oklch(58% 0.17 31);
    --focus: oklch(63% 0.16 245);
    --t1: oklch(58% 0.17 31);
    --t2: oklch(60% 0.13 63);
    --t3: oklch(52% 0.09 152);
    --t4: oklch(52% 0.09 240);
  }
  * { box-sizing: border-box; }
  html { background: var(--navy-deep); scroll-behavior: smooth; }
  body {
    margin: 0; min-height: 100vh; color: var(--ink);
    background: linear-gradient(90deg, transparent 0 1.45rem, color-mix(in oklch, var(--accent) 22%, transparent) 1.45rem 1.5rem, transparent 1.5rem), var(--paper);
    font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    line-height: 1.6; padding: 0 0 max(2rem, env(safe-area-inset-bottom));
  }
  a { color: inherit; }
  button, input, select { font: inherit; min-height: 44px; }
  :focus-visible { outline: 3px solid var(--focus); outline-offset: 3px; }
  .masthead {
    position: relative; overflow: hidden; color: oklch(96% 0.018 83);
    background: var(--navy); padding: clamp(2rem, 7vw, 4.5rem) clamp(1.25rem, 6vw, 5rem) clamp(1.75rem, 5vw, 3rem);
    border-bottom: 5px solid var(--accent);
  }
  .masthead::after {
    content: attr(data-mark); position: absolute; right: -.02em; bottom: -.42em;
    font-family: Georgia, "Times New Roman", serif; font-size: clamp(6rem, 26vw, 15rem);
    font-weight: 700; line-height: 1; letter-spacing: -.07em;
    color: color-mix(in oklch, var(--paper) 7%, transparent); pointer-events: none;
  }
  .nav {
    position: relative; z-index: 2; display: flex; flex-wrap: wrap; gap: .5rem; margin: 0 0 1.2rem;
  }
  .nav a {
    display: inline-flex; align-items: center; gap: .35rem; padding: .45rem .9rem; border-radius: 999px;
    border: 1px solid color-mix(in oklch, var(--paper) 34%, transparent);
    background: color-mix(in oklch, var(--paper) 12%, transparent);
    color: oklch(94% 0.02 236); font-size: .84rem; font-weight: 600; text-decoration: none;
  }
  .nav a:hover { background: color-mix(in oklch, var(--paper) 24%, transparent); }
  .nav a[aria-current="page"] { background: var(--paper); color: var(--navy); border-color: var(--paper); }
  .eyebrow { position: relative; z-index: 1; margin: 0 0 .7rem; color: oklch(82% 0.08 70); font-size: .78rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }
  h1 { position: relative; z-index: 1; margin: 0; font-family: "Songti SC", "STSong", Georgia, serif; font-size: clamp(1.8rem, 6.5vw, 3rem); line-height: 1.06; letter-spacing: -.035em; }
  .dek { position: relative; z-index: 1; max-width: 66ch; margin: 1rem 0 0; color: oklch(88% 0.025 236); font-size: clamp(.93rem, 2.8vw, 1.05rem); }
  main { max-width: 82rem; margin: 0 auto; padding: clamp(1.5rem, 5vw, 3rem) clamp(1rem, 4vw, 3rem) 4rem; }
  h2 { margin: 0 0 .35rem; font-family: "Songti SC", "STSong", Georgia, serif; font-size: clamp(1.3rem, 4vw, 1.75rem); letter-spacing: -.02em; }
  .sec { margin: 0 0 clamp(1.75rem, 5vw, 3rem); }
  .sec-label { margin: 0 0 .5rem; font-size: .76rem; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; color: var(--ink-soft); }
  .sec > p.lead { margin: .5rem 0 1.25rem; max-width: 78ch; color: var(--ink-soft); font-size: .96rem; }
  .kpis { display: grid; gap: .75rem; grid-template-columns: repeat(auto-fit, minmax(9.5rem, 1fr)); margin: 0 0 clamp(1.75rem, 5vw, 2.75rem); }
  .kpi { padding: 1rem 1.05rem; background: var(--card); border: 1px solid var(--line); border-top: 4px solid var(--navy); }
  .kpi b { display: block; font-family: Georgia, serif; font-size: clamp(1.5rem, 5vw, 2.1rem); line-height: 1.05; letter-spacing: -.03em; color: var(--navy); }
  .kpi span { display: block; margin-top: .35rem; font-size: .8rem; color: var(--ink-soft); }
  .grid-cards { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(17rem, 1fr)); }
  .card { padding: 1.15rem 1.25rem; background: var(--card); border: 1px solid var(--line); }
  .card h3 { margin: 0 0 .45rem; font-size: 1rem; }
  .card p { margin: 0; font-size: .89rem; color: var(--ink-soft); }
  .card b { color: var(--ink); }
  .tiercard { border-left: 6px solid var(--navy); }
  .tiercard.s1 { border-left-color: var(--t3); }
  .tiercard.s2 { border-left-color: var(--t4); }
  .tiercard.s3 { border-left-color: var(--t2); }
  .tiercard.s4 { border-left-color: var(--t1); }
  .tiercard .tt { display: flex; align-items: baseline; gap: .6rem; flex-wrap: wrap; margin: 0 0 .4rem; }
  .tiercard .tt h3 { margin: 0; font-family: "Songti SC", serif; font-size: 1.1rem; }
  .tiercard .tt em { font-style: normal; font-size: .8rem; color: var(--ink-faint); }
  .tiercard ul { margin: .5rem 0 0; padding-left: 1.1rem; font-size: .88rem; color: var(--ink-soft); }
  .tiercard li { margin-bottom: .28rem; }
  .tools { display: grid; gap: .85rem; padding: 1rem 1.1rem; background: var(--paper-deep); border: 1px solid var(--line); margin: 0 0 1rem; }
  .toolrow { display: flex; flex-wrap: wrap; gap: .55rem; align-items: center; }
  .toolrow > .lbl { font-size: .78rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-soft); margin-right: .2rem; }
  .chip { padding: .4rem .8rem; border-radius: 999px; border: 1px solid var(--line); background: var(--card); color: var(--ink-soft); font-size: .84rem; font-weight: 600; cursor: pointer; transition: all .18s ease; }
  .chip:hover { border-color: var(--navy); color: var(--navy); }
  .chip[aria-pressed="true"] { background: var(--navy); border-color: var(--navy); color: oklch(96% 0.018 83); }
  #q { flex: 1 1 12rem; min-width: 10rem; padding: .5rem .8rem; border: 1px solid var(--line); background: var(--card); color: var(--ink); min-height: 44px; }
  .count { font-size: .84rem; color: var(--ink-soft); }
  .count b { color: var(--navy); font-family: Georgia, serif; font-size: 1.05rem; }
  .tablewrap { overflow-x: auto; border: 1px solid var(--line); background: var(--card); }
  table { width: 100%; border-collapse: collapse; font-size: .87rem; min-width: 52rem; }
  thead th { position: sticky; top: 0; z-index: 3; background: var(--navy); color: oklch(95% 0.018 83); padding: .6rem .7rem; text-align: left; font-size: .77rem; font-weight: 700; letter-spacing: .04em; white-space: nowrap; }
  thead th.sortable { cursor: pointer; user-select: none; }
  thead th.sortable::after { content: " \\2195"; opacity: .38; font-size: .7rem; }
  thead th[data-dir="asc"]::after { content: " \\2191"; opacity: 1; }
  thead th[data-dir="desc"]::after { content: " \\2193"; opacity: 1; }
  tbody td { padding: .55rem .7rem; border-bottom: 1px solid color-mix(in oklch, var(--line) 55%, transparent); vertical-align: top; }
  tbody tr.row { cursor: pointer; }
  tbody tr.row:hover { background: color-mix(in oklch, var(--navy) 6%, transparent); }
  tbody tr.row.open { background: color-mix(in oklch, var(--navy) 9%, transparent); }
  tbody tr.detail > td { padding: 0; background: var(--paper-deep); }
  tbody tr.detail .box { padding: .9rem 1.1rem; display: grid; gap: .5rem; font-size: .86rem; }
  tbody tr.detail .box p { margin: 0; color: var(--ink-soft); }
  tbody tr.detail .box .src { color: var(--ink-faint); font-size: .8rem; }
  .sch { font-weight: 700; }
  .tag { display: inline-block; padding: .1rem .42rem; border-radius: 3px; font-size: .72rem; font-weight: 700; white-space: nowrap; }
  .tag.t1 { background: color-mix(in oklch, var(--t1) 18%, white); color: oklch(38% 0.15 31); }
  .tag.t2 { background: color-mix(in oklch, var(--t2) 22%, white); color: oklch(38% 0.11 63); }
  .tag.t3 { background: color-mix(in oklch, var(--t3) 18%, white); color: oklch(33% 0.08 152); }
  .tag.t4 { background: color-mix(in oklch, var(--t4) 16%, white); color: oklch(33% 0.08 240); }
  .tag.lv { background: var(--paper-deep); color: var(--ink-soft); }
  .num { font-family: Georgia, "Times New Roman", serif; font-variant-numeric: tabular-nums; }
  .num.hi { color: var(--t1); font-weight: 700; }
  .num.lo { color: var(--t3); font-weight: 700; }
  .bar { display: inline-block; height: 8px; border-radius: 2px; vertical-align: middle; }
  footer { max-width: 82rem; margin: 0 auto; padding: 0 clamp(1rem, 4vw, 3rem) 3rem; font-size: .82rem; color: var(--ink-faint); }
  footer p { max-width: 78ch; }
  @media (max-width: 40rem) { .kpis { grid-template-columns: repeat(2, 1fr); } }
"""


def esc(s):
    return H.escape(str(s)) if s is not None else ''


def gate_cls(g):
    if g is None:
        return 'lv'
    return 't3' if g <= 310 else ('t4' if g <= 335 else ('t2' if g <= 350 else 't1'))


rows_js = json.dumps([{
    'n': r['name'], 'r': r['region'], 'c': r['city'], 'lv': r['level'], 'z': r['zone'],
    'p': r['plan'], 'fs': r['fs'], 'fk': r['fs_kind'], 'lo': r['lo'], 'avg': r['avg'],
    'cnt': r['cnt'], 'g': r['gate'], 'cf': r['conf'],
    'note': r['note'] or r['unit_detail'] or '', 'src': r['source'] or r['old_source'] or '',
} for r in M], ensure_ascii=False)


def page(title, mark, eyebrow, dek, body, cur, h1):
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#173149">
<title>{esc(title)}</title>
<style>{CSS}</style>
</head>
<body>
<header class="masthead" data-mark="{esc(mark)}">
  <nav class="nav">
    <a href="index.html"{' aria-current="page"' if cur == 'index' else ''}>速查总表 · 99 所</a>
    <a href="tier350.html"{' aria-current="page"' if cur == 't350' else ''}>350 分以下专题</a>
  </nav>
  <p class="eyebrow">{esc(eyebrow)}</p>
  <h1>{esc(h1)}</h1>
  <p class="dek">{dek}</p>
</header>
<main>
{body}
</main>
<footer>
  <p>数据以 2026 年（最新完整招生年度）各校研究生院官方公告为主，含复试分数线通知、复试录取办法与拟录取名单公示；
  无 2026 数据者回落到 2025 年值并已标注。<b>“参考门槛”优先取实录最低分，其次复试线。</b>
  校线只是入场券，实际录取分往往高出 20–60 分，请以实录数据为准。2027 年招生政策以各校当年正式公告为准。</p>
</footer>
</body>
</html>
"""


# ============================ index.html ============================
from collections import Counter
total = len(M)
sub = [r for r in M if r['gate'] and r['gate'] <= 350]
b_zone = [r for r in M if r['zone'] == 'B区']
conf_a = [r for r in M if r['conf'].startswith('A')]

index_body = f"""
<section class="sec">
  <p class="sec-label">概览</p>
  <h2>2027 年度 105118 麻醉学专硕 · 全国院校速查</h2>
  <p class="lead">覆盖 {total} 所招生院校（已排除云南、新疆、西藏、青海、广西）。数据以 2026 年官方公告为主，
  按“参考门槛分”升序排列——门槛分优先取<b>实录最低分</b>，其次复试线。点击任意行展开该校完整数据与来源。</p>
  <div class="kpis">
    <div class="kpi"><b>{total}</b><span>招生院校总数</span></div>
    <div class="kpi"><b>{len(sub)}</b><span>门槛 ≤350 分</span></div>
    <div class="kpi"><b>{len([r for r in sub if r['gate'] <= 300])}</b><span>门槛 ≤300 分（保底）</span></div>
    <div class="kpi"><b>294 / 284</b><span>A 区 / B 区国家线</span></div>
    <div class="kpi"><b>{len(conf_a)}</b><span>实录数据双确认院校</span></div>
  </div>
</section>

<section class="sec">
  <p class="sec-label">速查表</p>
  <h2>全院校数据表</h2>
  <div class="tools">
    <div class="toolrow">
      <input id="q" type="search" placeholder="搜索院校 / 省份 / 城市…" aria-label="搜索院校">
      <span class="count">共 <b id="cnt">{total}</b> 所</span>
    </div>
    <div class="toolrow">
      <span class="lbl">分数线档</span>
      <button class="chip" data-f="all" aria-pressed="true">全部</button>
      <button class="chip" data-f="300" aria-pressed="false">≤300 保底</button>
      <button class="chip" data-f="320" aria-pressed="false">301–320 稳妥</button>
      <button class="chip" data-f="350" aria-pressed="false">321–350 进取</button>
      <button class="chip" data-f="hi" aria-pressed="false">&gt;350 高分</button>
    </div>
    <div class="toolrow">
      <span class="lbl">地区</span>
      <button class="chip" data-z="all" aria-pressed="true">全部</button>
      <button class="chip" data-z="B区" aria-pressed="false">B 区（284 线）</button>
      <button class="chip" data-z="A区" aria-pressed="false">A 区（294 线）</button>
    </div>
  </div>
  <div class="tablewrap">
    <table id="tb">
      <thead><tr>
        <th class="sortable" data-k="g" data-dir="asc">门槛</th>
        <th class="sortable" data-k="n">院校</th>
        <th>省份</th>
        <th>区</th>
        <th class="sortable" data-k="p">统考计划</th>
        <th class="sortable" data-k="fs">复试线</th>
        <th>线别</th>
        <th class="sortable" data-k="lo">实录最低</th>
        <th class="sortable" data-k="avg">实录均分</th>
        <th>实录人数</th>
        <th>置信度</th>
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</section>
<script>
const DATA = {rows_js};
let filter = 'all', zone = 'all', kw = '', sortKey = 'g', sortDir = 'asc';
const tb = document.getElementById('tbody'), cnt = document.getElementById('cnt');
const MAXV = 435;
function bar(v) {{
  if (v == null) return '<span class="num" style="color:#9a958c">—</span>';
  const w = Math.max(2, Math.round((v - 280) / (MAXV - 280) * 52));
  const col = v <= 310 ? '#3f7d54' : (v <= 335 ? '#4a6f8f' : (v <= 350 ? '#b8860b' : '#b23b32'));
  return '<span class="bar" style="width:' + w + 'px;background:' + col + '" aria-hidden="true"></span> ' +
         '<span class="num" style="color:' + col + ';font-weight:700">' + v + '</span>';
}}
function pass(r) {{
  if (zone !== 'all' && r.z !== zone) return false;
  if (filter === 'all') {{}}
  else if (filter === 'hi') {{ if (r.g == null || r.g <= 350) return false; }}
  else if (filter === '300') {{ if (r.g == null || r.g > 300) return false; }}
  else if (filter === '320') {{ if (r.g == null || r.g <= 300 || r.g > 320) return false; }}
  else if (filter === '350') {{ if (r.g == null || r.g <= 320 || r.g > 350) return false; }}
  if (kw) {{
    const s = (r.n + r.r + r.c).toLowerCase();
    if (s.indexOf(kw.toLowerCase()) < 0) return false;
  }}
  return true;
}}
function render() {{
  let rows = DATA.filter(pass);
  rows.sort((a, b) => {{
    let x = a[sortKey], y = b[sortKey];
    if (x == null) x = sortDir === 'asc' ? 1e9 : -1e9;
    if (y == null) y = sortDir === 'asc' ? 1e9 : -1e9;
    if (typeof x === 'string') return sortDir === 'asc' ? x.localeCompare(y, 'zh') : y.localeCompare(x, 'zh');
    return sortDir === 'asc' ? x - y : y - x;
  }});
  cnt.textContent = rows.length;
  tb.innerHTML = rows.map(r => {{
    const gc = r.g == null ? 'lv' : (r.g <= 310 ? 't3' : (r.g <= 335 ? 't4' : (r.g <= 350 ? 't2' : 't1')));
    return '<tr class="row" data-n="' + r.n + '">' +
      '<td><span class="tag ' + gc + '">' + (r.g == null ? '待补' : r.g) + '</span></td>' +
      '<td><span class="sch">' + r.n + '</span>' + (r.lv ? ' <span class="tag lv">' + r.lv + '</span>' : '') + '</td>' +
      '<td>' + r.r + '</td><td>' + (r.z === 'B区' ? '<b>B</b>' : 'A') + '</td>' +
      '<td class="num">' + (r.p == null ? '—' : r.p) + '</td>' +
      '<td class="num">' + (r.fs == null ? '—' : r.fs) + '</td>' +
      '<td style="font-size:.78rem;color:#6b665e">' + (r.fk || '—') + '</td>' +
      '<td class="num' + (r.lo != null && r.lo <= 320 ? ' lo' : '') + '">' + (r.lo == null ? '—' : r.lo) + '</td>' +
      '<td class="num">' + (r.avg == null ? '—' : r.avg) + '</td>' +
      '<td class="num">' + (r.cnt == null ? '—' : r.cnt) + '</td>' +
      '<td style="font-size:.75rem">' + r.cf + '</td></tr>' +
      '<tr class="detail" data-for="' + r.n + '" hidden><td colspan="11"><div class="box">' +
        '<p><b>门槛分可视化：</b>' + bar(r.g) + ' （A 区国家线 294 · B 区 284）</p>' +
        (r.note ? '<p>' + r.note + '</p>' : '') +
        (r.src ? '<p class="src">来源：' + r.src + '</p>' : '') +
      '</div></td></tr>';
  }}).join('');
}}
tb.addEventListener('click', e => {{
  const tr = e.target.closest('tr.row'); if (!tr) return;
  const d = tb.querySelector('tr.detail[data-for="' + CSS.escape(tr.dataset.n) + '"]');
  if (d) {{ d.hidden = !d.hidden; tr.classList.toggle('open', !d.hidden); }}
}});
document.getElementById('q').addEventListener('input', e => {{ kw = e.target.value.trim(); render(); }});
document.querySelectorAll('.chip[data-f]').forEach(b => b.addEventListener('click', () => {{
  document.querySelectorAll('.chip[data-f]').forEach(x => x.setAttribute('aria-pressed', 'false'));
  b.setAttribute('aria-pressed', 'true'); filter = b.dataset.f; render();
}}));
document.querySelectorAll('.chip[data-z]').forEach(b => b.addEventListener('click', () => {{
  document.querySelectorAll('.chip[data-z]').forEach(x => x.setAttribute('aria-pressed', 'false'));
  b.setAttribute('aria-pressed', 'true'); zone = b.dataset.z; render();
}}));
document.querySelectorAll('th.sortable').forEach(th => th.addEventListener('click', () => {{
  const k = th.dataset.k;
  if (sortKey === k) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
  else {{ sortKey = k; sortDir = 'asc'; }}
  document.querySelectorAll('th.sortable').forEach(x => x.removeAttribute('data-dir'));
  th.setAttribute('data-dir', sortDir); render();
}}));
render();
</script>
"""

open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(
    page('105118 麻醉学专硕 2027 报考速查总表', '105118',
         '2027 年度 · 全国招生院校数据',
         f'{total} 所院校逐一核验（排除云南、新疆、西藏、青海、广西）。'
         '以 2026 年官方复试线与拟录取名单为准，可搜索、筛选、排序，点击展开完整来源。',
         index_body, 'index', '全国 99 所麻醉学专硕招生院校 · 速查总表'))

# ============================ tier350.html ============================
def tier(a, b):
    return sorted([r for r in sub if a <= r['gate'] <= b], key=lambda x: x['gate'])


def tier_list(rs):
    out = []
    for r in rs:
        out.append(
            f"<li><b>{esc(r['name'])}</b>（{esc(r['region'])}·{esc(r['zone'])}）"
            f" 门槛 <b>{r['gate']}</b> 分"
            + (f"｜计划 {r['plan']} 人" if r['plan'] else '')
            + (f"｜实录最低 {r['lo']} 分" if r['lo'] else '')
            + (f"｜线 {r['fs']}" if r['fs'] else '')
            + "</li>")
    return '<ul>' + ''.join(out) + '</ul>'


t1, t2, t3, t4 = tier(0, 300), tier(301, 320), tier(321, 335), tier(336, 350)

t350_body = f"""
<section class="sec">
  <p class="sec-label">专题分析</p>
  <h2>350 分以下，还有 {len(sub)} 所可以选</h2>
  <p class="lead">350 分不是天花板，而是一个分水岭。全国 {total} 所招生院校中，<b>{len(sub)} 所</b>的参考门槛在 350 分以下，
  其中 <b>{len(t1)} 所</b>在 300 分以下——包括延边大学这样的 211，也包括内蒙古医科大学、宁夏医科大学这类 B 区主力。
  关键在于：<b>不要只看校线，要看实录最低分</b>；<b>不要只看学校，要看具体培养单位</b>。</p>
  <div class="kpis">
    <div class="kpi"><b>{len(sub)}</b><span>门槛 ≤350 分</span></div>
    <div class="kpi"><b>{len(t1)}</b><span>≤300 保底档</span></div>
    <div class="kpi"><b>{len(t2)}</b><span>301–320 稳妥档</span></div>
    <div class="kpi"><b>{len(t3)}</b><span>321–335 进取档</span></div>
    <div class="kpi"><b>{len(t4)}</b><span>336–350 临界档</span></div>
  </div>
</section>

<section class="sec">
  <p class="sec-label">先看清三件事</p>
  <h2>三个会让你误判的陷阱</h2>
  <div class="grid-cards">
    <div class="card">
      <h3>① 校线 ≠ 录取线</h3>
      <p>绝大多数院校校线就是国家线 294，但那只是<b>入场券</b>。西南医科大学校线 325，实录下沿 <b>341</b>；
      长江大学校线 294，实录下沿 <b>353</b>；成都医学院校线 <b>347</b>。真正决定命运的是实录最低分。</p>
    </div>
    <div class="card">
      <h3>② 同校不同单位，分差可达 80 分</h3>
      <p>徐州医科大学麻醉学院 <b>332</b>，而附属淮安医院麻醉专硕按校线 <b>294</b> 执行；
      青岛大学第一临床医学院 <b>341</b>，第四临床医学院（烟台毓璜顶）仅 <b>300</b>；
      郑州大学一附院 <b>370</b>，三附院 <b>310</b>。报之前一定看清备注里的培养单位。</p>
    </div>
    <div class="card">
      <h3>③ B 区是国家线红利，不是降维打击</h3>
      <p>B 区国家线 284，比 A 区低 10 分。延边大学（211）、内蒙古医科大学、宁夏医科大学、甘肃中医药大学都在 B 区。
      但要注意：B 区院校的麻醉专业复试线也可能自划到 305–319（如遵义医科大 305、贵州医科大 319）。</p>
    </div>
  </div>
</section>

<section class="sec">
  <p class="sec-label">四档择校</p>
  <h2>按你的分数定位</h2>

  <div class="card tiercard s1" style="margin-bottom:1rem">
    <div class="tt"><h3>★ 保底档 · 门槛 ≤300 分</h3><em>共 {len(t1)} 所｜过线即大概率上岸</em></div>
    <p>这一档的核心逻辑是<b>过国家线就有复试资格，且一志愿招生未满</b>。典型信号：齐齐哈尔医学院 2026 年麻醉学
    尚有 <b>5 个调剂名额</b>（计划 7 人）、长春中医药大学麻醉学一志愿 0 人录取全靠调剂、南华大学第二临床学院
    麻醉学调剂复试分数下沿 <b>322</b>。B 区院校（284 线）在此档占绝对多数。</p>
    {tier_list(t1)}
  </div>

  <div class="card tiercard s2" style="margin-bottom:1rem">
    <div class="tt"><h3>◆ 稳妥档 · 门槛 301–320 分</h3><em>共 {len(t2)} 所｜招生体量大、规则友好</em></div>
    <p>这一档出现了不少<b>招生大户</b>：锦州医科大学（43 人）、大连医科大学（45 人）、遵义医科大学（25 人）、
    延安大学（20 人）、广州医科大学（28 人）。名额多意味着容错率高。福建医科大学省立临床医学院麻醉学实录最低
    <b>303</b> 分，是全校唯一低于 320 的单位。</p>
    {tier_list(t2)}
  </div>

  <div class="card tiercard s3" style="margin-bottom:1rem">
    <div class="tt"><h3>▲ 进取档 · 门槛 321–335 分</h3><em>共 {len(t3)} 所｜性价比最高的专业实力区</em></div>
    <p>这一档有全国麻醉学最强的徐州医科大学（麻醉学院 <b>332</b>，但附属淮安医院仅 294）；
    也有山东第二医科大学——麻醉学院目录 26 人却<b>实录 47 人</b>，录取下沿 <b>325</b> 分，是同档次里最划算的选择之一。</p>
    {tier_list(t3)}
  </div>

  <div class="card tiercard s4">
    <div class="tt"><h3>⚠ 临界档 · 门槛 336–350 分</h3><em>共 {len(t4)} 所｜需要复试表现兜底</em></div>
    <p>温州医科大学校线 <b>350</b>、西南医科大学校线 325 但实录下沿 <b>341</b>、成都医学院 <b>347</b>。
    这一档的共性：<b>复试线只是门票，录取均分普遍在 360–375</b>。如果初试只有 340 出头，必须在复试上有准备，
    或改报该校的低分培养单位。</p>
    {tier_list(t4)}
  </div>
</section>

<section class="sec">
  <p class="sec-label">组合策略</p>
  <h2>三套推荐组合</h2>
  <div class="grid-cards">
    <div class="card">
      <h3>方案 A · 求稳上岸（预估 300–320）</h3>
      <p><b>冲</b>：赣南医科大学（实录最低 297，17 人全部录取）<br>
      <b>稳</b>：齐齐哈尔医学院 / 佳木斯大学（294 线，一志愿未满）<br>
      <b>保</b>：内蒙古医科大学（实录最低 289）/ 延边大学（B 区 211，284 线，可用日语）</p>
    </div>
    <div class="card">
      <h3>方案 B · 兼顾专业实力（预估 320–340）</h3>
      <p><b>冲</b>：徐州医科大学（全国麻醉第一，附属淮安医院 294 线）<br>
      <b>稳</b>：山东第二医科大学（实录 47 人，下沿 325）<br>
      <b>保</b>：锦州医科大学（43 人，初试权重 70%）/ 沈阳医学院盘锦基地（319）</p>
    </div>
    <div class="card">
      <h3>方案 C · 名校情结（预估 330–350）</h3>
      <p><b>冲</b>：延边大学（211，B 区 284 线，名额 18–23 人）<br>
      <b>稳</b>：郑州大学第三临床医学院（310 线、实录最低 312）—— 注意避开一附院 370<br>
      <b>保</b>：青岛大学第四临床医学院（300）/ 河南大学（294 线、实录最低 314）</p>
    </div>
  </div>
</section>

<section class="sec">
  <p class="sec-label">风险提示</p>
  <h2>四个必须核对的硬门槛</h2>
  <div class="grid-cards">
    <div class="card"><h3>本科专业限制</h3><p>临床专硕普遍<b>只收五年制临床医学 / 麻醉学本科</b>。河南大学更严：
    麻醉学本科只能报 105118。专升本、成人本科、跨考在多数院校直接拒收。</p></div>
    <div class="card"><h3>外语语种</h3><p>河北北方学院<b>只接收初试外语为英语</b>的考生。反之，延边大学可用 203 日语，
    内蒙古民族大学可用日语——这是外语弱势考生的机会。</p></div>
    <div class="card"><h3>单科线卡人</h3><p>哈尔滨医科大学临床专硕总分线仅 310，但<b>政治/外语单科 50 分、业务课 160 分</b>，
    远高于国家线 36/108。总分够而单科不过，一样进不了复试。</p></div>
    <div class="card"><h3>规培与证书</h3><p>已取得规培证或正在规培者，原则上<b>不得报考临床专硕</b>；
    服务期内的农村订单定向免费医学生也受限。部分院校还要求 CET-4 ≥425（山西医科大学）。</p></div>
  </div>
</section>
"""

open(os.path.join(OUT, 'tier350.html'), 'w', encoding='utf-8').write(
    page('350 分以下择校分析 · 105118 麻醉学专硕', '350',
         '2027 年度 · 低分段专项',
         f'{len(sub)} 所院校门槛在 350 分以下，其中 {len(t1)} 所在 300 分以下。'
         '分四档给出可落地的冲/稳/保组合，并标注一志愿未满、分培养单位差异等关键信号。',
         t350_body, 't350', '350 分以下 · 麻醉学专硕择校分析'))

print('已生成：')
for f in ('index.html', 'tier350.html'):
    p = os.path.join(OUT, f)
    print(' ', p, os.path.getsize(p), 'bytes')
