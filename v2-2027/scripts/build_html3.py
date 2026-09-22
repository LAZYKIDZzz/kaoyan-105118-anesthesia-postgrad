# -*- coding: utf-8 -*-
"""生成 105118 麻醉学专硕 2024-2026 三年对照 HTML"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(BASE)
D = json.load(open(os.path.join(V2, 'data', 'years3.json'), encoding='utf-8'))['schools']
YEARS = ('2024', '2025', '2026')

rows = []
for s in sorted(D, key=lambda x: (x['gate'] or 9999, x['name'])):
    y = s['y']
    rows.append({
        'n': s['name'], 'r': s['region'], 'c': s['city'], 'z': s['zone'], 'lv': s['level'],
        'g': s['gate'],
        'basis': '录取最低' if s['min_lo'] is not None else '复试线',
        'y': {yr: {'f': y[yr]['fs'], 'k': y[yr].get('fs_kind', ''), 'l': y[yr]['lo'],
                   'a': y[yr]['avg'], 'd': y[yr]['n']} for yr in YEARS},
        'note': (s.get('patch_note') or s.get('verify') or '')[:400],
    })

DATA = json.dumps(rows, ensure_ascii=False)
cand = [r for r in rows if r['g'] and r['g'] <= 350]
tiers = [('保底 ≤300', 0, 300), ('稳妥 301-315', 301, 315), ('进取 316-330', 316, 330), ('临界 331-350', 331, 350)]
tier_counts = {lab: len([r for r in cand if a <= r['g'] <= b]) for lab, a, b in tiers}

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>105118 麻醉学专硕 2024-2026 三年门槛对照</title>
<style>
:root{
  --paper:oklch(0.968 0.012 85);
  --paper2:oklch(0.945 0.018 82);
  --ink:oklch(0.28 0.03 250);
  --navy:oklch(0.36 0.07 255);
  --navy-d:oklch(0.28 0.06 255);
  --accent:oklch(0.52 0.16 30);
  --green:oklch(0.52 0.12 155);
  --line:oklch(0.86 0.02 80);
  --muted:oklch(0.55 0.02 250);
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--paper);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px 80px}

/* masthead */
.masthead{background:linear-gradient(160deg,var(--navy) 0%,var(--navy-d) 100%);color:#fff;
  margin:0 -16px 24px;padding:34px 24px 28px;position:relative;overflow:hidden}
.masthead::after{content:"";position:absolute;right:-60px;top:-60px;width:220px;height:220px;
  border-radius:50%;background:rgba(255,255,255,.05)}
.masthead h1{font-family:"Songti SC","STSong",serif;font-size:27px;letter-spacing:.5px;font-weight:700}
.masthead .sub{margin-top:8px;font-size:13.5px;opacity:.82}
.masthead .kpis{display:flex;gap:22px;margin-top:20px;flex-wrap:wrap;position:relative;z-index:1}
.kpi b{display:block;font-size:25px;font-family:"Songti SC",serif;line-height:1.15}
.kpi span{font-size:11.5px;opacity:.75}

/* insight */
.insight{background:#fff;border:1px solid var(--line);border-left:4px solid var(--accent);
  border-radius:8px;padding:16px 18px;margin-bottom:14px}
.insight h3{font-family:"Songti SC",serif;font-size:16px;color:var(--navy-d);margin-bottom:8px}
.insight p{font-size:13.5px;color:var(--ink);margin:5px 0}
.insight em{font-style:normal;color:var(--accent);font-weight:700}
.insight .hi{color:var(--navy);font-weight:700}

/* controls */
.ctrl{position:sticky;top:0;z-index:20;background:var(--paper);padding:12px 0;border-bottom:1px solid var(--line);
  display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.ctrl input{flex:1;min-width:150px;padding:9px 12px;border:1px solid var(--line);border-radius:20px;
  font-size:14px;background:#fff;outline:none}
.ctrl input:focus{border-color:var(--navy)}
.chip{padding:7px 13px;border:1px solid var(--line);border-radius:20px;background:#fff;
  font-size:12.5px;cursor:pointer;white-space:nowrap;transition:.15s;color:var(--muted)}
.chip.on{background:var(--navy);color:#fff;border-color:var(--navy)}
.chip:hover{border-color:var(--navy)}
.count{font-size:12px;color:var(--muted);margin:12px 2px 6px}

/* card */
.card{background:#fff;border:1px solid var(--line);border-radius:10px;margin-bottom:11px;
  overflow:hidden;transition:.16s;box-shadow:0 1px 2px rgba(0,0,0,.03)}
.card:hover{box-shadow:0 3px 12px rgba(0,0,0,.07);border-color:var(--line)}
.chead{display:flex;align-items:center;gap:10px;padding:12px 14px;cursor:pointer}
.rank{font-family:"Songti SC",serif;font-size:15px;color:var(--muted);min-width:26px;font-weight:700}
.nm{font-weight:700;font-size:15.5px;color:var(--navy-d);flex:1}
.nm small{font-weight:400;color:var(--muted);font-size:12px;margin-left:6px}
.zonepill{font-size:11px;padding:2px 7px;border-radius:4px;background:var(--paper2);color:var(--muted)}
.zonepill.b{background:oklch(0.93 0.04 250);color:var(--navy)}
.gate{font-family:"Songti SC",serif;font-size:20px;font-weight:700;min-width:52px;text-align:right}
.gate.low{color:var(--green)}
.gate.mid{color:var(--accent)}
.gate.high{color:var(--muted)}
.gate small{display:block;font-size:9.5px;font-weight:400;color:var(--muted);font-family:inherit}

.years{display:grid;grid-template-columns:auto 1fr 1fr 1fr;gap:0;border-top:1px solid var(--line);
  background:var(--paper)}
.ycell{padding:9px 11px;border-right:1px solid var(--line);font-size:12.5px}
.ycell:last-child{border-right:none}
.yh{padding:9px 11px;font-size:10.5px;color:var(--muted);display:flex;align-items:center}
.ycell .yl{display:flex;justify-content:space-between;gap:6px;padding:1.5px 0}
.ycell .yl i{font-style:normal;color:var(--muted);font-size:11px}
.ycell .fs{color:var(--navy);font-weight:600}
.ycell .lo{color:var(--accent);font-weight:700}
.ycell .nl{color:var(--muted)}
.ynote{display:flex;align-items:flex-start;padding:8px 12px;font-size:11px}
.ynote .yl{display:flex;gap:5px}
.detail{max-height:0;overflow:hidden;transition:max-height .28s;border-top:1px dashed var(--line)}
.detail.open{max-height:600px}
.detail .inner{padding:12px 14px;font-size:12.5px;color:var(--ink);background:oklch(0.985 0.008 85)}
.detail .inner b{color:var(--navy-d)}
.arrow{color:var(--muted);font-size:12px;transition:.2s}
.card.open .arrow{transform:rotate(90deg)}

.foot{margin-top:26px;padding-top:16px;border-top:1px solid var(--line);font-size:11.5px;color:var(--muted);line-height:1.8}
.warn{background:oklch(0.97 0.03 60);border:1px solid oklch(0.86 0.06 60);border-radius:8px;
  padding:12px 14px;font-size:12.5px;margin-bottom:14px;color:oklch(0.4 0.08 50)}
@media(max-width:640px){
  .masthead h1{font-size:21px}
  .years{grid-template-columns:auto 1fr 1fr 1fr;font-size:11.5px}
  .ycell{padding:7px 6px}
  .yhead-lb{display:none}
  .ynote{grid-template-columns:1fr}
  .nm{font-size:14px}
  .gate{font-size:17px;min-width:44px}
}
</style>
</head>
<body>
<div class="wrap">
<header class="masthead">
  <h1>105118 麻醉学专硕 · 三年门槛对照</h1>
  <div class="sub">2024 / 2025 / 2026 实际进复试线与录取最低分 · 已排除云南 新疆 西藏 青海 广西</div>
  <div class="kpis">
    <div class="kpi"><b>__TOTAL__</b><span>院校总数</span></div>
    <div class="kpi"><b>__CAND__</b><span>350分以下可选</span></div>
    <div class="kpi"><b>294</b><span>2026 A区国家线</span></div>
    <div class="kpi"><b>284</b><span>2026 B区国家线</span></div>
  </div>
</header>

<div class="insight">
  <h3>三个必须先看懂的区别</h3>
  <p>① <em>复试线 ≠ 录取线</em>。西南医科大学2026复试线325，但实际录取最低341；长江大学复试线只有294，实际录取却要353。<span class="hi">决定能否上岸的是「录取最低分」，不是校线。</span></p>
  <p>② <em>三年波动可能极大</em>。河南大学：343 → 323 → 294（三年降49分）；牡丹江医科大学：304 → 299 → 322（2026 一年涨23分）；西南医科大学：306 → 351 → 325。<span class="hi">只看某一年的线会误判。</span></p>
  <p>③ <em>同校不同培养单位能差 60 分以上</em>。徐州医科大麻醉学院332分，而其鼓楼临床学院、附属淮安医院按校线294执行；郑州大学一附院370，三附院310。<span class="hi">报哪个附院，比考多少分更重要。</span></p>
</div>

<div class="warn">
  <b>参考门槛口径</b>：取该校 2024–2026 三年中<b>最低的实际录取最低分</b>（若三年都未公布录取分，则取最低的实际进复试线）。它代表「历史上最宽松的一年，多少分能进」。卡上的大字即此门槛，下方小字标明依据。
</div>

<div class="ctrl">
  <input id="q" type="search" placeholder="搜索院校 / 省份…">
  <span class="chip on" data-z="all">全部</span>
  <span class="chip" data-z="A区">A区</span>
  <span class="chip" data-z="B区">B区</span>
  <span class="chip" data-t="1">350以下</span>
  <span class="chip" data-t="2">≤315</span>
  <span class="chip" data-t="3">≤300</span>
  <span class="chip" data-s="1">按门槛排序</span>
</div>
<div class="count" id="cnt"></div>
<div id="list"></div>

<div class="foot">
  <b>数据来源与说明</b><br>
  · 复试线（蓝）取自各校研究生院官方《进入复试初试成绩基本要求 / 复试分数线》或官方拟录取公示；标注「国家线」表示该校当年未自划线、直接执行国家线。<br>
  · 录取最低分（红）为当年统考实际录取考生中的最低初试总分，取自官方拟录取名单；部分院校官方名单已过公示期下线，由机构来源补齐并保留出处。<br>
  · 2025 年录取人数/均分含机构全国不完全统计（总量1631人、加权均分349），已与南昌大学61人、河北医科44人、广东医科31人等多校官方数据交叉吻合。<br>
  · 本页仅为数据整理，报考请以目标院校研究生院当年最新公告为准。
</div>
</div>

<script>
const DATA = __DATA__;
const YEARS = ["2024","2025","2026"];
let fz = "all", ft = "0", fs = "1";

function gateClass(g){ return g<=310?"low":(g>335?"high":"mid"); }

function render(){
  const q = document.getElementById('q').value.trim().toLowerCase();
  let list = DATA.filter(d=>{
    if(fz!=="all" && d.z!==fz) return false;
    if(ft==="1" && !(d.g && d.g<=350)) return false;
    if(ft==="2" && !(d.g && d.g<=315)) return false;
    if(ft==="3" && !(d.g && d.g<=300)) return false;
    if(q){
      const hay = (d.n+d.r+(d.c||'')+d.note).toLowerCase();
      if(hay.indexOf(q)<0) return false;
    }
    return true;
  });
  if(fs==="1") list.sort((a,b)=>(a.g||9999)-(b.g||9999));
  document.getElementById('cnt').textContent = "共 "+list.length+" 所院校";
  let h="";
  list.forEach((d,i)=>{
    const g = d.g||"—";
    let yc="";
    YEARS.forEach(yr=>{
      const o = d.y[yr];
      const fl = o.f? o.f : "—";
      const ll = o.l? o.l : "—";
      const nl = o.d? o.d : "—";
      yc += `<div class="ycell">
        <div class="yl"><i>线</i><span class="fs">${fl}</span></div>
        <div class="yl"><i>录取</i><span class="lo">${ll}</span></div>
        <div class="yl"><i>人数</i><span class="nl">${nl}</span></div>
      </div>`;
    });
    h += `<div class="card" data-i="${i}">
      <div class="chead">
        <span class="rank">${i+1}</span>
        <span class="nm">${d.n}<small>${d.r}${d.c?(' · '+d.c):''}${d.lv?(' · '+d.lv):''}</small>
          <span class="zonepill ${d.z==='B区'?'b':''}">${d.z}</span></span>
        <span class="gate ${gateClass(g)}">${g}<small>${d.basis}</small></span>
        <span class="arrow">▶</span>
      </div>
      <div class="years">
        <div class="yh yhead-lb">年份 ▸</div>
        <div class="ycell" style="background:var(--paper2)"><div class="yl" style="justify-content:center"><b>2024</b></div></div>
        <div class="ycell" style="background:var(--paper2)"><div class="yl" style="justify-content:center"><b>2025</b></div></div>
        <div class="ycell" style="background:var(--paper2)"><div class="yl" style="justify-content:center"><b>2026</b></div></div>
      </div>
      <div class="years">${yc}</div>
      <div class="detail" id="d${i}"><div class="inner">${d.note||'暂无补充说明'}</div></div>
    </div>`;
  });
  document.getElementById('list').innerHTML = h;
  document.querySelectorAll('.chead').forEach(el=>{
    el.onclick = ()=>{
      const card = el.parentElement;
      const i = card.dataset.i;
      const d = document.getElementById('d'+i);
      const open = d.classList.toggle('open');
      card.classList.toggle('open', open);
    };
  });
}

document.getElementById('q').oninput = render;
document.querySelectorAll('.chip').forEach(c=>{
  c.onclick = ()=>{
    const z=c.dataset.z, t=c.dataset.t, s=c.dataset.s;
    if(z){ fz=z; document.querySelectorAll('.chip[data-z]').forEach(x=>x.classList.remove('on')); c.classList.add('on'); }
    if(t){ ft=t; document.querySelectorAll('.chip[data-t]').forEach(x=>x.classList.remove('on')); c.classList.add('on'); }
    if(s){ fs=s; document.querySelectorAll('.chip[data-s]').forEach(x=>x.classList.remove('on')); c.classList.add('on'); }
    render();
  };
});
render();
</script>
</body>
</html>
"""
html = html.replace('__DATA__', DATA).replace('__TOTAL__', str(len(rows))).replace('__CAND__', str(len(cand)))
out = os.path.join(V2, 'html', 'years3.html')
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w', encoding='utf-8').write(html)
print('saved', out, len(html), 'bytes; rows', len(rows))
print('分档:', tier_counts)
