# -*- coding: utf-8 -*-
"""105118 麻醉学考研报考决策表 —— 生成手机版单文件 HTML

路径说明：脚本位于 <项目>/src/，data.json 与脚本同目录，HTML 输出到上一级 <项目>/。
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
BASE = HERE.parent
REF = HERE
OUT = BASE / "105118麻醉学考研报考决策表-手机版.html"

rows = json.loads((REF / "data.json").read_text(encoding="utf-8"))
DATA = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))

TIERS = [
    (1, "第一档 · 顶尖冲击", "录取均分 ≥ 375"),
    (2, "第二档 · 高难冲刺", "365 – 374"),
    (3, "第三档 · 中坚匹配", "355 – 364"),
    (4, "第四档 · 相对稳妥", "345 – 354"),
    (5, "第五档 · 友好保底", "< 345"),
]

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#2F5597">
<meta name="format-detection" content="telephone=no">
<title>105118 麻醉学考研报考决策表</title>
<style>
:root{
  --bg:#F4F5F7; --card:#FFFFFF; --text:#1F2328; --muted:#6B7280;
  --line:rgba(0,0,0,.09); --accent:#2F5597; --accent-soft:#E8EEF9;
  --warn:#B25E00; --warn-bg:#FDF3E6;
}
@media (prefers-color-scheme:dark){
  :root{ --bg:#14161A; --card:#1D2025; --text:#E9EBEE; --muted:#9AA1AA;
    --line:rgba(255,255,255,.13); --accent:#8AB4F8; --accent-soft:#1E2A3D;
    --warn:#F0B36C; --warn-bg:#3A2A16; }
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;
  padding-bottom:calc(28px + env(safe-area-inset-bottom));}
h1{font-size:18px;font-weight:600;margin:0 0 4px}
h3{font-size:13px;font-weight:600;margin:0 0 6px;color:var(--muted)}
p{margin:0}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.topbar{position:sticky;top:0;z-index:20;background:var(--card);
  border-bottom:1px solid var(--line);padding:calc(10px + env(safe-area-inset-top)) 14px 10px;
  box-shadow:0 1px 8px rgba(0,0,0,.05)}
.sub{font-size:12.5px;color:var(--muted);margin-bottom:10px}
input[type=search]{width:100%;font-size:16px;padding:10px 12px;border-radius:10px;
  border:1px solid var(--line);background:var(--bg);color:var(--text);outline:none}
input[type=search]:focus{border-color:var(--accent)}
.chips{display:flex;gap:8px;overflow-x:auto;margin:10px -14px 0;padding:0 14px 2px;
  scrollbar-width:none;-webkit-overflow-scrolling:touch}
.chips::-webkit-scrollbar{display:none}
.chip{flex:0 0 auto;font-size:13px;padding:7px 12px;border-radius:999px;border:1px solid var(--line);
  background:transparent;color:var(--muted);white-space:nowrap}
.chip[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:500}
.rows{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:10px}
.count{font-size:12.5px;color:var(--muted)}
select{font-size:13.5px;padding:7px 10px;border-radius:9px;border:1px solid var(--line);
  background:var(--bg);color:var(--text)}
main{padding:12px 12px 0}
.legend{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px 12px;margin-bottom:12px}
.legend b{font-size:12.5px;font-weight:600}
.lg{display:flex;flex-wrap:wrap;gap:6px 12px;margin-top:6px;font-size:12px;color:var(--muted)}
.lg span{display:flex;align-items:center;gap:5px}
.dot{width:10px;height:10px;border-radius:3px;flex:0 0 auto}
.card{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--tbar,#999);
  border-radius:12px;margin-bottom:10px;overflow:hidden}
.card[open]{box-shadow:0 2px 10px rgba(0,0,0,.06)}
summary{list-style:none;cursor:pointer;padding:11px 13px;position:relative}
summary::-webkit-details-marker{display:none}
.r1{display:flex;align-items:baseline;gap:8px}
.idx{font-size:11.5px;color:var(--muted);min-width:20px;font-variant-numeric:tabular-nums}
.nm{font-size:16px;font-weight:600;flex:1;min-width:0}
.lv{font-size:11px;padding:2px 7px;border-radius:6px;background:var(--accent-soft);
  color:var(--accent);white-space:nowrap;flex:0 0 auto}
.r2{display:flex;align-items:center;gap:9px;margin-top:5px;padding-left:28px;flex-wrap:wrap}
.tag{font-size:11.5px;font-weight:600;padding:2px 8px;border-radius:6px;
  background:var(--tb);color:var(--tt);white-space:nowrap}
.loc{font-size:11.5px;color:var(--muted);white-space:nowrap}
.star{font-size:11px;color:var(--warn);letter-spacing:-1px}
.r3{display:flex;gap:14px;margin-top:7px;padding-left:28px;flex-wrap:wrap}
.m{font-size:12.5px;color:var(--muted)}
.m b{font-size:14px;color:var(--text);font-weight:600;font-variant-numeric:tabular-nums}
.chev{position:absolute;right:13px;bottom:12px;width:8px;height:8px;border-right:1.6px solid var(--muted);
  border-bottom:1.6px solid var(--muted);transform:rotate(45deg);transition:transform .18s}
.card[open] .chev{transform:rotate(-135deg)}
.body{padding:2px 13px 14px;border-top:1px solid var(--line);margin-top:2px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line);
  border:1px solid var(--line);border-radius:10px;overflow:hidden;margin:12px 0}
.grid>div{background:var(--card);padding:9px 10px}
.grid span{display:block;font-size:11.5px;color:var(--muted)}
.grid b{display:block;font-size:15px;font-weight:600;line-height:1.35;
  font-variant-numeric:tabular-nums;word-break:break-word;overflow-wrap:anywhere}
.grid b.sm{font-size:13px;font-weight:500}
.adv{background:var(--tb);border-radius:10px;padding:11px 12px;margin-bottom:10px}
.adv h3{color:var(--tt);opacity:.85}
.adv p{font-size:13.5px;line-height:1.68}
.warnico{color:#C0392B;font-weight:600}
@media (prefers-color-scheme:dark){.warnico{color:#F09595}}
.basis{background:var(--warn-bg);border-radius:10px;padding:10px 12px}
.basis p{font-size:12.5px;line-height:1.65;color:var(--warn)}
.t1{--tb:#FDE8EA;--tt:#9C0006;--tbar:#A32D2D}
.t2{--tb:#FDF0E4;--tt:#B85C00;--tbar:#D85A30}
.t3{--tb:#FEF8E0;--tt:#7F6000;--tbar:#EF9F27}
.t4{--tb:#EAF4E4;--tt:#375623;--tbar:#97C459}
.t5{--tb:#DEF3E6;--tt:#006100;--tbar:#1D9E75}
.t0{--tb:#EFEFEF;--tt:#5F5E5A;--tbar:#B4B2A9}
@media (prefers-color-scheme:dark){
  .t1{--tb:#3A1519;--tt:#F7C1C1}
  .t2{--tb:#3A2712;--tt:#FAC775}
  .t3{--tb:#34300F;--tt:#F0DC8A}
  .t4{--tb:#1D3318;--tt:#C0DD97}
  .t5{--tb:#12352A;--tt:#9FE1CB}
  .t0{--tb:#2A2C30;--tt:#C7CAD0}
}
.empty{text-align:center;color:var(--muted);padding:40px 0;font-size:14px}
footer{padding:22px 16px calc(10px + env(safe-area-inset-bottom));font-size:11.5px;
  line-height:1.7;color:var(--muted);text-align:center}
.totop{position:fixed;right:16px;bottom:calc(20px + env(safe-area-inset-bottom));z-index:30;
  width:44px;height:44px;border-radius:50%;border:1px solid var(--line);background:var(--card);
  color:var(--text);font-size:18px;box-shadow:0 2px 10px rgba(0,0,0,.14)}
@media (min-width:640px){main{max-width:680px;margin:0 auto}.topbar>div{max-width:680px;margin:0 auto}}
</style>
</head>
<body>
<h2 class="sr">105118 麻醉学专业学位硕士考研报考决策表，含 94 所院校的复试线、录取人数、进入复试人数与分档报考建议。</h2>

<header class="topbar">
  <h1>105118 麻醉学考研报考决策表</h1>
  <p class="sub">2024 / 2025 / 2026 三年 · 94 所院校 · 五档底色 · 逐校报考建议</p>
  <input id="q" type="search" placeholder="搜索院校、省份或城市，如「徐州」「四川」" autocomplete="off" enterkeyhint="search">
  <div class="chips" id="chips"></div>
  <div class="rows">
    <span class="count" id="count"></span>
    <select id="sort">
      <option value="tier">按难度档位排序</option>
      <option value="avg">按录取均分从高到低</option>
      <option value="n">按录取人数从多到少</option>
      <option value="y26">按 2026 复试线从高到低</option>
      <option value="city">按城市排序</option>
    </select>
  </div>
</header>

<main>
  <div class="legend">
    <b>底色 = 录取难度档位</b><span style="font-size:12px;color:var(--muted)">（依据 2025 年录取平均分）</span>
    <div class="lg" id="lg"></div>
  </div>
  <div id="list"></div>
  <p class="empty" id="empty" hidden>没有匹配的院校，换个关键词试试</p>
</main>

<button class="totop" id="toTop" hidden aria-label="回到顶部">↑</button>

<footer>
  数据来源：各院校研究生院复试公告 / 复试录取工作办法 / 拟录取名单公示；研招网国家线；软科中国大学专业排名；第三方考研数据整理。<br>
  「进入复试人数」仅 14 所院校公开披露，其余以「复试差额比」替代（可用 招生计划 × 比例 推算）。<br>
  第三方整理存在误差，报考前请以目标院校研究生院最新公告为准。本表仅供择校参考。
</footer>

<script id="d" type="application/json">__DATA__</script>
<script>
var ALL = JSON.parse(document.getElementById('d').textContent);
var TIERS = __TIERS__;
var DOTS = {1:'#A32D2D',2:'#D85A30',3:'#EF9F27',4:'#97C459',5:'#1D9E75'};
var state = {q:'', tier:0, sort:'tier'};

function tierNo(name){
  if(!name) return 0;
  if(name.indexOf('第一档')>-1) return 1;
  if(name.indexOf('第二档')>-1) return 2;
  if(name.indexOf('第三档')>-1) return 3;
  if(name.indexOf('第四档')>-1) return 4;
  if(name.indexOf('第五档')>-1) return 5;
  return 0;
}
function shortTier(name){
  var p = String(name).split('·');
  return p.length>1 ? p[1].trim() : name;
}
function val(v){
  if(v===null||v===undefined||v===''||v==='未公布') return '—';
  return v;
}
// 直辖市省份与城市同名（北京/天津/上海/重庆），去重后只显示一次
function loc(r){
  var p = r.region || '', c = r.city || '';
  if(!p) return c || '—';
  if(!c || c === p) return p;
  return p + ' · ' + c;
}
function num(v){ return (v===null||v===undefined||v==='未公布')? -1 : Number(v); }
function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }

function renderChips(){
  var h = '<button class="chip" data-tier="0" aria-pressed="'+ (state.tier===0) +'">全部 '+ALL.length+'</button>';
  TIERS.forEach(function(t){
    var c = ALL.filter(function(r){return tierNo(r.tier)===t[0];}).length;
    h += '<button class="chip" data-tier="'+t[0]+'" aria-pressed="'+ (state.tier===t[0]) +'">'
       + shortTier(t[1]) + ' ' + c + '</button>';
  });
  document.getElementById('chips').innerHTML = h;
}

function renderLegend(){
  document.getElementById('lg').innerHTML = TIERS.map(function(t){
    return '<span><i class="dot" style="background:'+DOTS[t[0]]+'"></i>'+t[1]+'（'+t[2]+'）</span>';
  }).join('');
}

function cardHTML(r, i){
  var t = tierNo(r.tier), tn = shortTier(r.tier);
  var adv = esc(r.adv).replace(/⚠/g,'<span class="warnico">⚠</span>');
  function b(v){ var t = val(v); var sm = String(t).length>8 ? ' class="sm"' : ''; return '<b'+sm+'>'+t+'</b>'; }
  return '<details class="card t'+t+'">'
    + '<summary>'
    +   '<div class="r1"><span class="idx">'+i+'</span><span class="nm">'+esc(r.name)+'</span>'
    +   (r.level?'<span class="lv">'+esc(r.level)+'</span>':'')+'</div>'
    +   '<div class="r2"><span class="tag">'+esc(tn)+'</span>'
    +   '<span class="loc">'+esc(loc(r))+'</span>'
    +   '<span class="star">'+esc(r.star)+'</span></div>'
    +   '<div class="r3">'
    +     '<span class="m"><b>'+val(r.avg)+'</b> 录取均分</span>'
    +     '<span class="m"><b>'+val(r.n)+'</b> 录取人数</span>'
    +     '<span class="m"><b>'+val(r.y26)+'</b> 2026线</span>'
    +   '</div>'
    +   '<span class="chev"></span>'
    + '</summary>'
    + '<div class="body">'
    +   '<div class="grid">'
    +     '<div><span>2026 复试线</span><b>'+val(r.y26)+'</b></div>'
    +     '<div><span>2025 录取最低分</span><b>'+val(r.lo)+'</b></div>'
    +     '<div><span>2025 录取平均分</span><b>'+val(r.avg)+'</b></div>'
    +     '<div><span>2025 录取人数</span><b>'+val(r.n)+'</b></div>'
    +     '<div><span>进入复试人数</span>'+b(r.fs)+'</div>'
    +     '<div><span>复试差额比</span><b>'+val(r.ratio)+'</b></div>'
    +     '<div><span>2026 招生计划</span>'+b(r.plan)+'</div>'
    +     '<div><span>数据年份</span><b>'+esc(r.fy||'2025')+'</b></div>'
    +   '</div>'
    +   '<div class="adv"><h3>报考建议</h3><p>'+adv+'</p></div>'
    +   (r.basis && r.basis!=='—' ? '<div class="basis"><p>依据：'+esc(r.basis)+'</p></div>' : '')
    + '</div></details>';
}

function currentList(){
  var q = state.q.trim();
  var list = ALL.filter(function(r){
    if(state.tier && tierNo(r.tier)!==state.tier) return false;
    if(q){
      var hay = (r.name+' '+r.region+' '+r.city+' '+r.level).toLowerCase();
      if(hay.indexOf(q.toLowerCase())<0) return false;
    }
    return true;
  });
  var s = state.sort;
  list.sort(function(a,b){
    if(s==='avg') return num(b.avg)-num(a.avg);
    if(s==='n') return num(b.n)-num(a.n);
    if(s==='y26') return num(b.y26)-num(a.y26);
    if(s==='city') return String(a.city||a.region||'').localeCompare(String(b.city||b.region||''),'zh-CN');
    var d = tierNo(a.tier)-tierNo(b.tier);
    if(d) return d;
    return num(b.avg)-num(a.avg);
  });
  return list;
}

function render(){
  var list = currentList();
  var box = document.getElementById('list');
  box.innerHTML = list.map(function(r,i){ return cardHTML(r,i+1); }).join('');
  document.getElementById('empty').hidden = list.length>0;
  document.getElementById('count').textContent = '共 '+ALL.length+' 所，当前显示 '+list.length+' 所';
}

document.getElementById('chips').addEventListener('click',function(e){
  var b = e.target.closest('.chip'); if(!b) return;
  state.tier = Number(b.dataset.tier);
  renderChips(); render();
  window.scrollTo({top:0,behavior:'smooth'});
});
var timer;
document.getElementById('q').addEventListener('input',function(e){
  clearTimeout(timer);
  timer = setTimeout(function(){ state.q = e.target.value; render(); },160);
});
document.getElementById('sort').addEventListener('change',function(e){
  state.sort = e.target.value; render();
});
var toTop = document.getElementById('toTop');
window.addEventListener('scroll',function(){ toTop.hidden = window.scrollY < 500; },{passive:true});
toTop.addEventListener('click',function(){ window.scrollTo({top:0,behavior:'smooth'}); });

renderChips(); renderLegend(); render();
</script>
</body>
</html>
"""

TIERS_JS = json.dumps([[t[0], t[1], t[2]] for t in TIERS], ensure_ascii=False)

html = HTML.replace("__DATA__", DATA).replace("__TIERS__", TIERS_JS)
OUT.write_text(html, encoding="utf-8")
print("saved:", OUT)
print("size:", OUT.stat().st_size, "bytes")
print("data rows:", len(rows))
