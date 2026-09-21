# -*- coding: utf-8 -*-
"""
生成「105118 麻醉学专硕 · 三年录取分数总表（2024—2026）」→ docs/score-table.html

数据源：src/data.json（已由 src/harvest/ 的并行采集与 merge_backfill.py 逐校核对回填）。
本页只做一件事：把核对后的 2024/2025/2026 三年录取（最低分 / 均分 / 人数）排成一张大表，
支持按地区、判定筛选，按院校名 / 2026 均分 / 2026 最低分排序，并可点击行展开查看复试线、
分培养单位、核对说明与来源链接。整页离线可用、可直接打印。
"""
import json
import pathlib
from html import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data.json"
DOCS = ROOT / "docs"
OUT = DOCS / "score-table.html"

B_ZONE = {"新疆", "西藏", "广西", "宁夏", "内蒙古", "甘肃", "青海", "云南", "贵州", "海南"}
YEARS = ("2024", "2025", "2026")
VERDICT_ORDER = ["修正", "补充", "确认", "无法核实"]

data = json.load(open(DATA, encoding="utf-8"))

rows = []
for x in data:
    h = x.get("hist")
    if not h:
        continue
    region = x.get("region") or "—"
    rows.append({
        "name": x["name"],
        "region": region,
        "city": x.get("city") or "",
        "level": x.get("level") or "",
        "zone": "B区" if region in B_ZONE else "A区",
        "hist": h,
        "units": x.get("hist_units") or [],
        "verdict": x.get("verdict") or "",
        "reason": x.get("verdict_reason") or "",
        "sources": x.get("sources") or [],
        "fy": x.get("fy") or "",
        "lo": x.get("lo"),
        "avg": x.get("avg"),
        "n": x.get("n"),
        "basis": x.get("basis") or "",
    })

rows.sort(key=lambda r: (-(r["avg"] or 0), r["name"]))

regions = sorted({r["region"] for r in rows})
vcount = {v: sum(1 for r in rows if r["verdict"] == v) for v in VERDICT_ORDER}
vcount = {k: v for k, v in vcount.items() if v}
n_with_2026 = sum(1 for r in rows if (r["hist"].get("2026") or {}).get("avg") is not None)

CSS = """
:root{
  color-scheme:light;
  --paper:#f7f4ee; --paper-deep:#efe9de; --card:#fffdf9; --ink:#22303f; --ink-soft:#5a6a7d;
  --line:#ddd5c7; --navy:#1c3a5e; --navy-deep:#132c49; --accent:#b93a2b;
  --t-fix:#b93a2b; --t-add:#2d6fbf; --t-ok:#2e7d54; --t-na:#8a94a6;
  --focus:#2d6fbf;
}
*{box-sizing:border-box}
html{background:var(--navy-deep);scroll-behavior:smooth}
body{margin:0;min-height:100vh;color:var(--ink);background:var(--paper);
  font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;line-height:1.55;font-variant-numeric:tabular-nums}
a{color:inherit}
button,input,select{font:inherit;min-height:40px}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.masthead{background:var(--navy);color:#f2ede3;padding:1.9rem clamp(1rem,5vw,3rem) 1.6rem;border-bottom:5px solid var(--accent)}
.masthead a.back{color:#e8eef5;text-decoration:none;font-weight:600;font-size:.85rem}
.masthead h1{margin:.5rem 0 .3rem;font-family:"Songti SC","STSong",Georgia,serif;font-size:clamp(1.4rem,4.4vw,2.2rem);letter-spacing:-.02em}
.masthead p{margin:.15rem 0;color:#c9d4e2;font-size:.88rem}
.eyebrow{margin:0;color:#d9bb85;font-size:.72rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
main{max-width:1500px;margin:0 auto;padding:1.2rem clamp(.7rem,3vw,2rem) 3rem}
.cards{display:flex;flex-wrap:wrap;gap:.6rem;margin:.8rem 0 1.1rem}
.card{background:var(--card);border:1px solid var(--line);border-top:4px solid var(--navy);border-radius:4px;padding:.6rem .95rem;min-width:106px}
.card b{display:block;font-size:1.45rem;font-family:Georgia,serif;color:var(--navy)}
.card span{font-size:.76rem;color:var(--ink-soft)}
.card.fix{border-top-color:var(--t-fix)} .card.add{border-top-color:var(--t-add)}
.card.ok{border-top-color:var(--t-ok)} .card.na{border-top-color:var(--t-na)}
.controls{display:flex;flex-wrap:wrap;gap:.55rem;align-items:center;margin:0 0 .9rem;padding:.7rem .8rem;background:var(--paper-deep);border:1px solid var(--line);border-radius:6px}
.controls input,.controls select{padding:.45rem .65rem;border:1px solid var(--line);border-radius:6px;background:#fff}
.controls input#q{flex:1;min-width:150px}
.controls .lbl{font-size:.76rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-soft)}
.count{margin-left:auto;font-size:.85rem;color:var(--ink-soft)}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card);-webkit-overflow-scrolling:touch}
table{border-collapse:separate;border-spacing:0;width:100%;min-width:1340px;font-size:.86rem}
thead th{position:sticky;top:0;z-index:2;background:#ebe4d7;color:var(--ink);font-size:.78rem;padding:.45rem .5rem;border-bottom:1px solid var(--line);white-space:nowrap;text-align:center}
thead tr.sub th{top:34px;font-weight:600;color:var(--ink-soft);font-size:.74rem}
th.th-sch{text-align:left}
thead th.sortable{cursor:pointer;user-select:none}
thead th.sortable:hover{background:#e2d9c8}
tbody td{padding:.42rem .5rem;border-bottom:1px solid #efe9de;text-align:center;white-space:nowrap;vertical-align:middle}
tbody tr.row{cursor:pointer}
tbody tr.row:hover{background:#f6f1e6}
td.name{text-align:left;font-weight:700;font-size:.86rem}
td.name small{display:block;font-weight:400;color:var(--ink-soft);font-size:.72rem}
td.region{text-align:left;font-size:.76rem;color:var(--ink-soft);white-space:normal;min-width:96px}
td.g24{background:rgba(217,187,133,.10)}
td.g25{background:rgba(140,170,200,.10)}
td.g26{background:rgba(185,58,43,.06)}
.num b{font-weight:700;color:var(--ink)}
.num.miss{color:#b3b9c2}
td.fs{font-size:.79rem;color:var(--ink-soft)}
/* 快照高亮：采用年度 */
.hcell.hi{background:rgba(185,58,43,.14);box-shadow:inset 0 0 0 1px rgba(185,58,43,.28);border-radius:3px}
.badge{display:inline-block;padding:.12rem .55rem;border-radius:999px;color:#fff;font-size:.74rem;font-weight:700;white-space:nowrap}
.v-修正{background:var(--t-fix)} .v-补充{background:var(--t-add)}
.v-确认{background:var(--t-ok)} .v-无法核实{background:var(--t-na)}
tr.detail td{background:#faf6ee;text-align:left;white-space:normal;padding:.7rem .9rem}
tr.detail .dgrid{display:grid;gap:.5rem;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr))}
tr.detail .box{border:1px dashed var(--line);padding:.5rem .65rem;font-size:.8rem;background:#fffdf9}
tr.detail .box h4{margin:0 0 .3rem;font-size:.74rem;letter-spacing:.06em;text-transform:uppercase;color:var(--navy)}
tr.detail .units span{display:block}
tr.detail .srcs a{display:inline-block;color:var(--t-add);margin:.1rem .7rem .1rem 0;font-size:.78rem;word-break:break-word}
tr.detail .reason{font-size:.8rem;color:var(--ink-soft);line-height:1.55}
.foot{margin-top:1.1rem;font-size:.8rem;color:var(--ink-soft);line-height:1.7}
.foot code{background:#efe9de;padding:.08rem .35rem;border-radius:4px}
@media print{
  .masthead{background:#fff;color:#000;border-bottom:2px solid #000}
  .masthead a,.controls,.eyebrow{display:none}
  .masthead h1,.masthead p{color:#000}
  .wrap{border:0}
  thead th{position:static;background:#f0f0f0}
  table{font-size:9px;min-width:0}
  tr.detail{display:none}
}
"""

HTML = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#132c49">
<title>三年录取分数总表 · 105118 麻醉学专硕（2024—2026）</title>
<style>__CSS__</style>
</head>
<body>
<header class="masthead">
  <a class="back" href="nav.html">&larr; 返回资料导航</a>
  <p class="eyebrow">Three-Year Score Master Table</p>
  <h1>105118 麻醉学专硕 · 三年录取分数总表</h1>
  <p>覆盖院校：__N__ 所（350 分以下范围，逐校核对） · 年度：2024 / 2025 / 2026 · 口径：仅 105118 专业学位硕士 · 核对日期 2026-09-21</p>
  <p>每年度列出「录取最低分 / 录取均分 / 录取人数 / 复试线」；空白「—」表示未检索到可核验的官方数据。点击任意行可展开分培养单位、口径说明与来源。</p>
</header>
<main>
  <div class="cards" id="cards"></div>
  <div class="controls">
    <span class="lbl">筛选</span>
    <input id="q" placeholder="搜索院校 / 地区…">
    <select id="fRegion"><option value="">全部地区</option></select>
    <select id="fVerdict">
      <option value="">全部判定</option>
      <option value="修正">仅「修正」</option>
      <option value="补充">仅「补充」</option>
      <option value="确认">仅「确认」</option>
      <option value="无法核实">仅「无法核实」</option>
    </select>
    <select id="sort">
      <option value="avg-desc">按 2026 均分降序</option>
      <option value="avg-asc">按 2026 均分升序</option>
      <option value="lo-asc">按 2026 最低分升序</option>
      <option value="name">按院校名</option>
      <option value="region">按地区</option>
    </select>
    <span class="count" id="count"></span>
  </div>
  <div class="wrap">
    <table id="tbl">
      <thead>
        <tr>
          <th>#</th>
          <th class="th-sch">院校</th>
          <th>地区</th>
          <th colspan="4">2024</th>
          <th colspan="4">2025</th>
          <th colspan="4">2026</th>
          <th>判定</th>
        </tr>
        <tr class="sub">
          <th></th><th class="th-sch"></th><th></th>
          <th>最低</th><th>均分</th><th>人数</th><th>线</th>
          <th>最低</th><th>均分</th><th>人数</th><th>线</th>
          <th>最低</th><th>均分</th><th>人数</th><th>线</th>
          <th></th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
  <p class="foot" id="foot"></p>
  <p class="foot">数据来源：各校研究生院官网拟录取名单 / 复试线公告 &gt; 二级学院官网 &gt; 省考试院 · 研招网 &gt; 机构整理（仅作线索，须回官方核对）。
  「修正」= 与旧库口径不符已更正；「补充」= 旧库缺该数据已补录；「确认」= 与旧库一致；「无法核实」= 官方渠道需验证码 / 公示期已过，保留旧值。
  B 区国家线：2024 = 294 · 2025 = 283 · 2026 = 284；A 区：2024 = 304 · 2025 = 293 · 2026 = 294。</p>
</main>
<script>
const ROWS = __ROWS__;
const YEARS = ["2024","2025","2026"];
const state = { q:"", region:"", verdict:"", sort:"avg-desc", open:new Set() };

function dash(v){ return (v === null || v === undefined) ? "—" : v; }
function num(v){ return (v === null || v === undefined); }
function cellClass(v){ return "num" + (num(v) ? " miss" : ""); }
function yv(r, y){ return (r.hist && r.hist[y]) || {}; }

function match(r){
  if (state.region && r.region !== state.region) return false;
  if (state.verdict && r.verdict !== state.verdict) return false;
  if (state.q){ const k = state.q.trim().toLowerCase();
    if (!(r.name.toLowerCase().includes(k) || (r.region+r.city).toLowerCase().includes(k))) return false; }
  return true;
}
function sortRows(rs){
  const s = state.sort;
  return rs.sort((a,b) => {
    if (s === "name") return a.name.localeCompare(b.name, "zh-Hans-CN");
    if (s === "region") return (a.region||"").localeCompare(b.region||"","zh-Hans-CN") || a.name.localeCompare(b.name,"zh-Hans-CN");
    const av = (yv(a,"2026").avg), bv = (yv(b,"2026").avg);
    const al = (yv(a,"2026").lo), bl = (yv(b,"2026").lo);
    if (s === "lo-asc"){ const x=al==null?1e9:al, y=bl==null?1e9:bl; return x-y || a.name.localeCompare(b.name,"zh-Hans-CN"); }
    const x=av==null?-1:av, y=bv==null?-1:bv;
    return s === "avg-asc" ? (x-y || a.name.localeCompare(b.name,"zh-Hans-CN")) : (y-x || a.name.localeCompare(b.name,"zh-Hans-CN"));
  });
}
function yCells(r, y, grp){
  const v = yv(r, y);
  const hi = r.fy === y ? " hcell hi" : "";
  return '<td class="'+cellClass(v.lo)+grp+hi+'">'+dash(v.lo)+'</td>'
       + '<td class="'+cellClass(v.avg)+grp+hi+'">'+dash(v.avg)+'</td>'
       + '<td class="'+cellClass(v.n)+grp+hi+'">'+dash(v.n)+'</td>'
       + '<td class="'+cellClass(v.fs)+grp+' fs">'+dash(v.fs)+'</td>';
}
function detail(r){
  const lines = YEARS.map(y => {
    const v = yv(r, y);
    const fs = (v.fs == null) ? "—" : (v.fs + (v.fs_kind && v.fs_kind !== "未公布" ? "（"+v.fs_kind+"）" : ""));
    const note = v.note ? ' · '+v.note : '';
    return '<span><b>'+y+'</b> 复试线 '+fs+note+'</span>';
  }).join("");
  const units = (r.units && r.units.length)
    ? '<div class="box units"><h4>分培养单位</h4>' + r.units.map(u => '<span>'+u.year+' '+u.unit+'：最低 '+dash(u.lo)+' / 均分 '+dash(u.avg)+' / '+dash(u.n)+' 人</span>').join("") + '</div>'
    : "";
  const reason = r.reason ? '<div class="box"><h4>核对说明</h4><div class="reason">'+r.reason+'</div></div>' : "";
  const srcs = (r.sources && r.sources.length)
    ? '<div class="box"><h4>来源</h4><div class="srcs">' + r.sources.map(s => '<a href="'+s.url+'" target="_blank" rel="noopener">'+(s.year?s.year+' ':'')+(s.kind||'链接')+'</a>').join("") + '</div></div>'
    : "";
  return '<td colspan="16"><div class="dgrid">'
    + '<div class="box"><h4>三年复试线与口径</h4>'+lines+'</div>'
    + (r.basis ? '<div class="box"><h4>数据依据</h4>'+r.basis+'</div>' : "")
    + units + reason + srcs + '</div></td>';
}
function render(){
  const rs = sortRows(ROWS.filter(match).slice());
  const tb = document.getElementById("tbody");
  tb.innerHTML = "";
  rs.forEach((r, i) => {
    const tr = document.createElement("tr");
    tr.className = "row";
    tr.innerHTML =
      '<td class="num">'+(i+1)+'</td>'
      + '<td class="name">'+r.name+'<small>'+r.level+(r.zone?' · '+r.zone:'')+'</small></td>'
      + '<td class="region">'+r.region+(r.city && r.city!==r.region?' · '+r.city:'')+'</td>'
      + yCells(r,"2024"," g24") + yCells(r,"2025"," g25") + yCells(r,"2026"," g26")
      + '<td>'+(r.verdict?'<span class="badge v-'+r.verdict+'">'+r.verdict+'</span>':'—')+'</td>';
    tb.appendChild(tr);
    const dt = document.createElement("tr");
    dt.className = "detail"; dt.hidden = true;
    dt.innerHTML = detail(r);
    tr.addEventListener("click", () => {
      dt.hidden = !dt.hidden;
      tr.classList.toggle("open", !dt.hidden);
    });
    tb.appendChild(dt);
  });
  document.getElementById("count").textContent = "共 " + rs.length + " 所匹配";
}
// init controls
const reg = [...new Set(ROWS.map(r => r.region))].sort((a,b)=>a.localeCompare(b,"zh-Hans-CN"));
reg.forEach(x => { const o=document.createElement("option"); o.value=x; o.textContent=x; document.getElementById("fRegion").appendChild(o); });
document.getElementById("q").addEventListener("input", e => { state.q = e.target.value; render(); });
document.getElementById("fRegion").addEventListener("change", e => { state.region = e.target.value; render(); });
document.getElementById("fVerdict").addEventListener("change", e => { state.verdict = e.target.value; render(); });
document.getElementById("sort").addEventListener("change", e => { state.sort = e.target.value; render(); });
document.getElementById("foot").textContent = ROWS.length + " 所院校逐校核对；其中含 2026 年可核实录取数据的院校 " + ROWS.filter(r => yv(r,"2026").avg != null).length + " 所。";
render();
</script>
</body>
</html>
"""

cards = (
    f'<div class="card"><b>{len(rows)}</b><span>覆盖院校</span></div>'
    + "".join(
        f'<div class="card {"fix" if v=="修正" else "add" if v=="补充" else "ok" if v=="确认" else "na"}"><b>{vcount.get(v,0)}</b><span>{v}</span></div>'
        for v in VERDICT_ORDER
    )
    + f'<div class="card"><b>{n_with_2026}</b><span>含 2026 可核实数据</span></div>'
    + f'<div class="card"><b>{len([r for r in rows if r["zone"]=="B区"])}</b><span>B 区院校</span></div>'
)

html_out = (HTML
            .replace("__CSS__", CSS)
            .replace("__ROWS__", json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
            .replace("__N__", str(len(rows)))
            .replace('<div class="cards" id="cards"></div>', f'<div class="cards" id="cards">{cards}</div>'))

OUT.write_text(html_out, encoding="utf-8")
print(f"OK -> {OUT.relative_to(ROOT)}")
print(f"  覆盖院校 {len(rows)} 所 | 判定 {vcount} | 含2026均分 {n_with_2026} 所")
print(f"  体积 {len(html_out.encode('utf-8'))/1024:.1f} KB")
