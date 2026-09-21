# -*- coding: utf-8 -*-
"""生成 docs/score-check.html —— 105118 麻醉学专硕「三年录取分数核对」页。

读取 src/harvest/_merged.json（67 所范围内院校的规范合并结果），
逐校展示：现有旧基线 / 2024 / 2025 / 2026 三年录取(最低·均分·人数·复试线) /
核对判定(修正·确认·补充·无法核实) / 核对说明 / 来源链接，并支持按地区、判定筛选与排序。
"""
import json
import pathlib
import html as _html

ROOT = pathlib.Path(__file__).resolve().parent.parent
MERGED = ROOT / "src" / "harvest" / "_merged.json"
OUT = ROOT / "docs" / "score-check.html"
SPEC_DATE = "2026-09-21"


def fmt(v, suffix=""):
    if v is None or v == "":
        return "—"
    if isinstance(v, float):
        v = int(round(v))
    return f"{v}{suffix}"


def cell(yv):
    """把某年数据渲染成 (最低/均分/人数, 复试线) 两个部分。"""
    if not yv:
        return ("—", "—")
    score = f"{fmt(yv.get('lo'))} / {fmt(yv.get('avg'))} / {fmt(yv.get('n'))}"
    fs = yv.get("fs")
    fs_kind = yv.get("fs_kind")
    if fs is None:
        fs_txt = "—"
    else:
        fs_txt = f"{fs}" + (f"·{fs_kind}" if fs_kind and fs_kind != "未公布" else "")
    return (score, fs_txt)


def build_rows(data):
    rows = []
    for s in data:
        o = s.get("old_snapshot") or {}
        y24, y25, y26 = (s.get("years", {}).get(y) or {} for y in ("2024", "2025", "2026"))
        c24, f24 = cell(y24)
        c25, f25 = cell(y25)
        c26, f26 = cell(y26)
        units = s.get("units") or []
        srcs = s.get("sources") or []
        rows.append({
            "name": s["name"],
            "region": s.get("region") or "",
            "city": s.get("city") or "",
            "level": s.get("level") or "",
            "verdict": s.get("verdict", "无法核实"),
            "reason": s.get("verdict_reason", ""),
            "old": f"{fmt(o.get('lo'))} / {fmt(o.get('avg'))} / {fmt(o.get('n'))}（{fmt(o.get('fy'))}）",
            "c24": c24, "f24": f24,
            "c25": c25, "f25": f25,
            "c26": c26, "f26": f26,
            "units": [
                {"year": u.get("year"), "unit": u.get("unit"),
                 "lo": fmt(u.get("lo")), "avg": fmt(u.get("avg")), "n": fmt(u.get("n")),
                 "scope": u.get("scope_note") or ""}
                for u in units
            ],
            "srcs": [
                {"year": sr.get("year"), "kind": sr.get("kind"),
                 "title": sr.get("title") or "", "url": sr.get("url") or ""}
                for sr in srcs
            ],
        })
    return rows


def main():
    data = json.load(open(MERGED, encoding="utf-8"))
    rows = build_rows(data)
    regions = sorted({r["region"] for r in rows})
    verdicts = ["修正", "补充", "确认", "无法核实"]
    vc = {v: sum(1 for r in rows if r["verdict"] == v) for v in verdicts}

    payload = {
        "rows": rows,
        "regions": regions,
        "verdicts": verdicts,
        "vc": vc,
        "total": len(rows),
        "spec_date": SPEC_DATE,
    }

    rows_js = json.dumps(payload, ensure_ascii=False)

    doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>105118 麻醉学专硕 · 三年录取分数核对（2024–2026）</title>
<style>
  :root {{
    color-scheme: light;
    --paper: #faf7f2; --card: #ffffff; --ink: #21303f; --ink-soft: #516075;
    --line: #e3ddd2; --navy: #1f3a5f; --accent: #c0392b;
    --t-fix: #c0392b; --t-add: #2d7dd2; --t-ok: #2e8b57; --t-na: #8a94a6;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--paper); color:var(--ink);
    font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif; line-height:1.6; }}
  .masthead {{ background:var(--navy); color:#f3eee4; padding:1.8rem clamp(1rem,5vw,3rem); border-bottom:5px solid var(--accent); }}
  .masthead a {{ color:#f3eee4; text-decoration:none; font-weight:600; font-size:.85rem; }}
  .masthead h1 {{ margin:.4rem 0 .2rem; font-size:clamp(1.3rem,4vw,2rem); }}
  .masthead p {{ margin:.2rem 0; color:#cdd6e2; font-size:.9rem; }}
  main {{ max-width:1180px; margin:0 auto; padding:1.4rem clamp(1rem,4vw,2rem) 3rem; }}
  .cards {{ display:flex; flex-wrap:wrap; gap:.7rem; margin:1rem 0 1.4rem; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:.7rem 1rem; min-width:110px; }}
  .card b {{ display:block; font-size:1.4rem; }}
  .card span {{ font-size:.8rem; color:var(--ink-soft); }}
  .controls {{ display:flex; flex-wrap:wrap; gap:.6rem; align-items:center; margin-bottom:1rem; }}
  .controls select, .controls input {{ padding:.5rem .7rem; border:1px solid var(--line); border-radius:8px; font:inherit; background:#fff; }}
  .controls input {{ flex:1; min-width:160px; }}
  .wrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:12px; background:var(--card); }}
  table {{ border-collapse:collapse; width:100%; min-width:980px; font-size:.86rem; }}
  th, td {{ padding:.55rem .6rem; border-bottom:1px solid var(--line); text-align:center; vertical-align:top; }}
  th {{ background:#f1ece2; position:sticky; top:0; cursor:pointer; user-select:none; white-space:nowrap; }}
  th:hover {{ background:#e7e0d3; }}
  td.name {{ text-align:left; font-weight:700; }}
  td.name small {{ display:block; font-weight:400; color:var(--ink-soft); font-size:.74rem; }}
  .yr {{ font-size:.72rem; color:var(--ink-soft); }}
  .badge {{ display:inline-block; padding:.15rem .55rem; border-radius:999px; color:#fff; font-size:.76rem; font-weight:700; }}
  .v-修正 {{ background:var(--t-fix); }} .v-补充 {{ background:var(--t-add); }}
  .v-确认 {{ background:var(--t-ok); }} .v-无法核实 {{ background:var(--t-na); }}
  tr.detail td {{ background:#fbf9f4; text-align:left; }}
  .units, .srcs {{ font-size:.78rem; }}
  .units b {{ color:var(--navy); }}
  .srcs a {{ color:var(--t-add); }}
  .reason {{ font-size:.8rem; color:var(--ink-soft); text-align:left; max-width:340px; }}
  .foot {{ margin-top:1.4rem; font-size:.82rem; color:var(--ink-soft); }}
  .foot code {{ background:#f1ece2; padding:.1rem .35rem; border-radius:4px; }}
</style>
</head>
<body>
<header class="masthead">
  <a href="nav.html">&larr; 返回资料导航</a>
  <h1>105118 麻醉学专硕 · 三年录取分数核对</h1>
  <p>覆盖院校：350 分以下范围内 67 所 · 核对年度：2024 / 2025 / 2026 · 口径：仅 105118 专业学位硕士</p>
  <p>数据采集与核对日期：{SPEC_DATE} · 来源优先级：院校官网拟录取名单 &gt; 二级学院公告 &gt; 省考试院/研招网 &gt; 机构整理（仅作线索）</p>
</header>
<main>
  <div class="cards" id="cards"></div>
  <div class="controls">
    <input id="q" placeholder="搜索院校名…" oninput="render()">
    <select id="fRegion" onchange="render()"><option value="">全部地区</option></select>
    <select id="fVerdict" onchange="render()">
      <option value="">全部判定</option>
      <option value="修正">修正（旧数据有误）</option>
      <option value="补充">补充（新增年度/院区）</option>
      <option value="确认">确认（旧数据正确）</option>
      <option value="无法核实">无法核实</option>
    </select>
    <select id="sort" onchange="render()">
      <option value="name">排序：院校名</option>
      <option value="region">排序：地区</option>
      <option value="c25">排序：2025 均分↓</option>
      <option value="c26">排序：2026 均分↓</option>
      <option value="verdict">排序：判定</option>
    </select>
  </div>
  <div class="wrap">
    <table id="tbl">
      <thead><tr>
        <th data-k="name">院校</th><th data-k="region">地区</th>
        <th>现有旧基线<br><span class="yr">最低/均分/人数（年）</span></th>
        <th>2024<br><span class="yr">最低/均分/人数</span></th>
        <th>2025<br><span class="yr">最低/均分/人数</span></th>
        <th>2026<br><span class="yr">最低/均分/人数</span></th>
        <th>判定</th><th>核对说明</th><th>来源</th>
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
  <p class="foot">
    说明：表格每格为「最低分 / 均分 / 录取人数」；复试线见各年上方小字（院线·校线·国家线·自划线）。
    同一院校多培养单位（附属院区）分数差异较大，已在「核对说明」与来源中按院区拆分，切勿混读。
    <code>—</code> 表示该年度官方未公布或机构来源未回验、按规范留空。本页为公开名单核对结果，最终以院校当年官方公示为准。
  </p>
</main>
<script>
const DATA = {rows_js};
const tbody = document.getElementById('tbody');
const cards = document.getElementById('cards');
const fRegion = document.getElementById('fRegion');
const VORDER = {{"修正":0,"补充":1,"确认":2,"无法核实":3}};

// 地区下拉
DATA.regions.forEach(r => {{ const o=document.createElement('option'); o.value=r; o.textContent=r; fRegion.appendChild(o); }});
// 概览卡片
const vmap = {{"修正":"较旧库已修正","补充":"较旧库已补充","确认":"旧数据被确认","无法核实":"暂无法核实"}};
DATA.verdicts.forEach(v => {{
  const d=document.createElement('div'); d.className='card';
  d.innerHTML = `<b>${{DATA.vc[v]||0}}</b><span>${{v}} · ${{vmap[v]}}</span>`;
  cards.appendChild(d);
}});
document.getElementById('cards').insertAdjacentHTML('afterbegin',
  `<div class="card"><b>${{DATA.total}}</b><span>范围内院校总数</span></div>`);

function unitsHtml(u) {{
  if(!u.length) return '—';
  return '<div class="units">' + u.map(x =>
    `<b>${{x.year}} ${{x.unit}}</b>：最低${{x.lo}} / 均分${{x.avg}} / ${{x.n}}人${{x.scope?('（'+x.scope+'）'):''}}`).join('<br>') + '</div>';
}}
function srcHtml(s) {{
  if(!s.length) return '—';
  return '<div class="srcs">' + s.map(x => {{
    const t = `${{x.year}}·${{x.kind}} ${{x.title}}`;
    return x.url ? `<a href="${{x.url}}" target="_blank" rel="noopener">${{t}}</a>` : t;
  }}).join('<br>') + '</div>';
}}
function avgOf(c){{ const p=c.split('/')[1]; return p&&p!=='—'? -parseInt(p):9999; }}

function render() {{
  const q = document.getElementById('q').value.trim();
  const fr = fRegion.value, fv = document.getElementById('fVerdict').value;
  const sort = document.getElementById('sort').value;
  let rows = DATA.rows.filter(r =>
    (!q || r.name.includes(q)) && (!fr || r.region===fr) && (!fv || r.verdict===fv));
  if(sort==='name') rows.sort((a,b)=>a.name.localeCompare(b.name,'zh'));
  else if(sort==='region') rows.sort((a,b)=>a.region.localeCompare(b.region,'zh')||a.name.localeCompare(b.name,'zh'));
  else if(sort==='verdict') rows.sort((a,b)=>VORDER[a.verdict]-VORDER[b.verdict]||a.name.localeCompare(b.name,'zh'));
  else if(sort==='c25') rows.sort((a,b)=>avgOf(a.c25)-avgOf(b.c25));
  else if(sort==='c26') rows.sort((a,b)=>avgOf(a.c26)-avgOf(b.c26));
  tbody.innerHTML = rows.map(r => {{
    const detail = (r.units.length? `<div style="margin-top:.3rem">院区明细：<br>${{unitsHtml(r.units)}}</div>`:'');
    return `<tr>
      <td class="name">${{r.name}}<small>${{r.city}} · ${{r.level}}</small></td>
      <td>${{r.region}}</td>
      <td>${{r.old}}</td>
      <td>${{r.c24}}</td>
      <td>${{r.c25}}</td>
      <td>${{r.c26}}</td>
      <td><span class="badge v-${{r.verdict}}">${{r.verdict}}</span></td>
      <td class="reason">${{r.reason}}${{detail}}</td>
      <td style="text-align:left">${{srcHtml(r.srcs)}}</td>
    </tr>`;
  }}).join('');
}}
// 表头点击排序
document.querySelectorAll('th[data-k]').forEach(th => th.onclick = () => {{
  const k = th.dataset.k;
  const sel = document.getElementById('sort');
  sel.value = (k==='name')?'name':(k==='region')?'region':(k==='c25')?'c25':(k==='c26')?'c26':'name';
  render();
}});
render();
</script>
</body>
</html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"OK -> docs/score-check.html  ({OUT.stat().st_size/1024:.1f} KB, {len(rows)} schools)")


if __name__ == "__main__":
    main()
