# -*- coding: utf-8 -*-
"""
生成「105118 麻醉学专硕 · 择校速查」移动端 HTML。
版式风格复用参考页：105118麻醉学专硕_2024-2026移动端择校速查.html（纸感底色 + 藏青主色 + 宋体大标题 + 水印大数字）。
数据源：本项目已产出的两个 xlsx。

路径说明：脚本位于 <项目>/src/，两个 xlsx 在上一级 <项目>/，HTML 也输出到 <项目>/。
REF 为**外部**参考页（不属于本项目），仅在需要重新抽取样式时读取；缺失时脚本会明确报错。
"""
import json
import pathlib
import re

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parent.parent
REF = pathlib.Path(
    "/Users/weiyao/Documents/Codex/2026-09-18/bang-w/outputs/105118-national-3-year/"
    "105118麻醉学专硕_2024-2026移动端择校速查.html"
)
OUT = ROOT / "105118麻醉学专硕择校速查-编辑版.html"

DECISION = ROOT / "105118麻醉学考研报考决策表.xlsx"
STATS = ROOT / "105118麻醉学考研三年数据统计表.xlsx"

B_ZONE = {"新疆", "西藏", "广西", "宁夏", "内蒙古", "甘肃", "青海", "云南", "贵州", "海南"}

# 录取均分 → 档位（S 最难 → D 最友好，U 数据不足）
TIERS = [
    ("S", "顶尖冲击", 375, None),
    ("A", "高难冲刺", 365, 375),
    ("B", "中坚匹配", 355, 365),
    ("C", "相对稳妥", 345, 355),
    ("D", "友好保底", None, 345),
]
TIER_BY_CN = {"一": "S", "二": "A", "三": "B", "四": "C", "五": "D"}
TIER_LABEL = {k: f"{k} {v}" for k, v, _, _ in TIERS}
TIER_LABEL["U"] = "U 数据暂缺"


def tier_of(avg, cn_tier):
    """优先按录取均分定档；均分缺失时沿用 xlsx 已人工归入的档位。"""
    if isinstance(avg, (int, float)):
        if avg >= 375:
            return "S"
        if avg >= 365:
            return "A"
        if avg >= 355:
            return "B"
        if avg >= 345:
            return "C"
        return "D"
    if cn_tier:
        for cn, code in TIER_BY_CN.items():
            if str(cn_tier).startswith("第" + cn):
                return code
    return "U"


def clean(v):
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        if v in ("", "—", "-", "未公布", "None"):
            return None if v != "未公布" else "未公布"
    return v


def num(v):
    return v if isinstance(v, (int, float)) else None


def norm(name):
    """院校名归一：去掉括号后缀，便于跨表 JOIN。"""
    if not name:
        return ""
    return re.sub(r"[（(].*?[)）]", "", str(name)).strip()


# ---------------------------------------------------------------- 读取数据
wb_d = openpyxl.load_workbook(DECISION, data_only=True)
wb_s = openpyxl.load_workbook(STATS, data_only=True)

# --- 1) 三年复试线对比（91 校）
cutoffs = []
ws = wb_s["三年复试线对比"]
for r in range(3, ws.max_row + 1):
    name = ws.cell(r, 2).value
    if not name:
        continue
    cutoffs.append({
        "province": clean(ws.cell(r, 3).value) or "",
        "city": clean(ws.cell(r, 4).value) or "",
        "school": str(name).strip(),
        "level": clean(ws.cell(r, 5).value) or "—",
        "scores": {"2024": num(ws.cell(r, 6).value),
                   "2025": num(ws.cell(r, 7).value),
                   "2026": num(ws.cell(r, 8).value)},
        "single": clean(ws.cell(r, 9).value),
        "delta": num(ws.cell(r, 10).value),
        "above": num(ws.cell(r, 11).value),
        "kind": clean(ws.cell(r, 12).value) or "—",
        "note": clean(ws.cell(r, 13).value),
    })
cutoff_by = {norm(c["school"]): c for c in cutoffs}

# --- 2) 软科 2025 麻醉学专业排名
rank_by = {}
ws = wb_s["麻醉学专业排名"]
for r in range(3, ws.max_row + 1):
    nm = ws.cell(r, 2).value
    if not nm:
        continue
    rank_by[norm(nm)] = {
        "rank": num(ws.cell(r, 1).value),
        "grade": clean(ws.cell(r, 3).value) or "—",
        "strength": clean(ws.cell(r, 7).value) or "",
    }

# --- 3) 报考决策总表（94 校）
# 先从人数明细表建「院校 → 2026 招生计划」索引
plan_by = {}
ws = wb_d["复试与录取人数明细"]
for r in range(4, ws.max_row + 1):
    nm = ws.cell(r, 4).value
    if nm:
        plan_by[norm(nm)] = clean(ws.cell(r, 6).value)

schools = []
ws = wb_d["报考决策总表"]
for r in range(4, ws.max_row + 1):
    name = ws.cell(r, 4).value
    if not name:
        continue
    name = str(name).strip()
    key = norm(name)
    province = clean(ws.cell(r, 2).value) or "—"
    city = clean(ws.cell(r, 3).value) or province
    avg = num(ws.cell(r, 8).value)
    cn_tier = ws.cell(r, 13).value
    code = tier_of(avg, cn_tier)

    co = cutoff_by.get(key)
    scores = co["scores"] if co else {"2024": None, "2025": None, "2026": None}
    scores = dict(scores)
    y26 = num(ws.cell(r, 6).value)
    if y26 is not None:
        scores["2026"] = y26
    latest_year = max((int(y) for y, v in scores.items() if isinstance(v, (int, float))), default=None)
    latest = scores.get(str(latest_year)) if latest_year else None
    filled = sum(1 for v in scores.values() if isinstance(v, (int, float)))
    rk = rank_by.get(key, {})
    n = num(ws.cell(r, 9).value)
    schools.append({
        "province": province,
        "city": city,
        "zone": "B区" if province in B_ZONE else "A区",
        "school": name,
        "level": clean(ws.cell(r, 5).value) or "—",
        "scores": scores,
        "already": num(ws.cell(r, 6).value),
        "low": num(ws.cell(r, 7).value),
        "average": avg,
        "admitted": n,
        "reexam": clean(ws.cell(r, 10).value),
        "ratio": clean(ws.cell(r, 11).value),
        "star": clean(ws.cell(r, 12).value) or "",
        "tierCn": clean(cn_tier) or "",
        "tier": TIER_LABEL[code],
        "tierCode": code,
        "manual": avg is None and bool(cn_tier),
        "advice": clean(ws.cell(r, 14).value) or "",
        "plan": plan_by.get(key),
        "single": (co or {}).get("single"),
        "kind": (co or {}).get("kind") or "—",
        "note": (co or {}).get("note"),
        "above": (co or {}).get("above"),
        "delta": (co or {}).get("delta"),
        "rank": rk.get("rank"),
        "rankGrade": rk.get("grade"),
        "rankNote": rk.get("strength"),
        "latest": latest,
        "latestYear": latest_year,
        "completeness": f"{filled}/3年",
        # 大号展示值：优先录取均分，其次最新线，再次录取最低分
        "hero": avg if avg is not None else (latest if latest is not None else num(ws.cell(r, 7).value)),
        "heroUnit": "2025 录取均分" if avg is not None else (f"{latest_year} 复试线" if latest else "—"),
    })

# --- 4) 复试与录取人数明细（94 校）+ 各校复试比例规则
ws = wb_d["复试与录取人数明细"]
counts, rules = [], []
for r in range(4, ws.max_row + 1):
    nm = ws.cell(r, 4).value
    if not nm:
        continue
    counts.append({
        "region": clean(ws.cell(r, 2).value) or "—",
        "city": clean(ws.cell(r, 3).value) or "—",
        "school": str(nm).strip(),
        "already": num(ws.cell(r, 5).value),
        "plan": clean(ws.cell(r, 6).value),
        "admitted": num(ws.cell(r, 7).value),
        "low": num(ws.cell(r, 8).value),
        "avg": num(ws.cell(r, 9).value),
        "reexam": clean(ws.cell(r, 10).value) or "—",
        "ratio": clean(ws.cell(r, 11).value) or "—",
        "year": clean(ws.cell(r, 12).value) or "—",
        "basis": clean(ws.cell(r, 13).value) or "",
    })
for r in range(4, ws.max_row + 1):
    a, b = ws.cell(r, 1).value, ws.cell(r, 2).value
    if a and b and ("比例" in str(b) or "复试" in str(b)) and isinstance(a, str) and a not in ("序号",):
        rules.append((str(a).strip(), str(b).strip()))

# 补一份降序展示用的排序键
for c in counts:
    c["_key"] = c["admitted"] if isinstance(c["admitted"], (int, float)) else -1

# --- 5) 三个视图统一档位：人数 / 复试线 也按所属院校的录取均分档位着色与筛选
tier_by = {norm(s["school"]): (s["tier"], s["tierCode"]) for s in schools}
for bucket in (counts, cutoffs):
    for item in bucket:
        item["tier"], item["tierCode"] = tier_by.get(norm(item["school"]), (TIER_LABEL["U"], "U"))

# 排序主键：复试线视图用最新年线；人数视图用录取平均分
for c in cutoffs:
    c["hero"] = c["scores"]["2026"] if c["scores"]["2026"] is not None else (
        c["scores"]["2025"] if c["scores"]["2025"] is not None else c["scores"]["2024"])
    c["latestYear"] = (2026 if c["scores"]["2026"] is not None
                       else 2025 if c["scores"]["2025"] is not None
                       else 2024 if c["scores"]["2024"] is not None else None)
for c in counts:
    c["hero"] = c["avg"] if c["avg"] is not None else c["low"]

DB = {
    "updated": "2026-09-18",
    "schools": schools,
    "counts": counts,
    "cutoffs": cutoffs,
    "rules": rules,
    "legends": [
        ("S", "顶尖冲击", "录取均分 ≥ 375"),
        ("A", "高难冲刺", "365 – 374"),
        ("B", "中坚匹配", "355 – 364"),
        ("C", "相对稳妥", "345 – 354"),
        ("D", "友好保底", "< 345"),
        ("U", "数据暂缺", "均分未公开"),
    ],
}

# ---------------------------------------------------------------- 复用参考页样式
ref_html = REF.read_text(encoding="utf-8") if REF.exists() else None
if ref_html is None:
    raise SystemExit(
        "找不到版式参考页，无法复刻样式：\n  " + str(REF) +
        "\n该文件是外部参考页（不属于本项目）。若已迁移，请修正脚本顶部的 REF 路径。"
    )
css = re.search(r"<style>(.*?)</style>", ref_html, re.S).group(1)

EXTRA_CSS = """
    /* —— 本页扩展：六年份并排、双列指标、风险提示 —— */
    .snapshot em { font-style: normal; color: oklch(88% 0.075 70); font-weight: 700; }
    .detail-line dd.wrap { font-size: .86rem; line-height: 1.6; }
    .kpi { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: .5rem; margin-top: .9rem; }
    .kpi div { padding: .55rem .7rem; background: color-mix(in oklch, var(--paper) 55%, transparent); border: 1px solid color-mix(in oklch, var(--ink) 14%, transparent); }
    .kpi span { display: block; color: var(--ink-soft); font-size: .7rem; font-weight: 700; letter-spacing: .04em; }
    .kpi b { display: block; margin-top: .15rem; font-size: 1.02rem; font-weight: 700; font-variant-numeric: tabular-nums; }
    .kpi b.sm { font-size: .84rem; font-weight: 600; line-height: 1.4; }
    .advice { margin-top: .9rem; padding: .75rem .85rem; border-left: 4px solid var(--accent); background: color-mix(in oklch, var(--paper) 62%, transparent); font-size: .88rem; line-height: 1.65; }
    .advice strong { display: block; margin-bottom: .25rem; color: var(--accent); font-size: .74rem; letter-spacing: .1em; }
    .warnico { color: oklch(48% 0.19 27); font-weight: 700; }
    .rulelist { margin: .5rem 0 0; padding: 0; list-style: none; font-size: .86rem; }
    .rulelist li { padding: .5rem 0; border-top: 1px dashed var(--line); }
    .rulelist b { color: var(--ink); }
    .badge { display: inline-block; margin-left: .4rem; padding: .05rem .38rem; border: 1px solid currentColor; font-size: .68rem; font-weight: 700; vertical-align: middle; }
    @media (min-width: 420px) { .kpi { grid-template-columns: repeat(4, minmax(0,1fr)); } }
"""

HTML = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#173149">
<title>105118 麻醉学专硕｜择校速查 · 2024—2026</title>
<style>__CSS__</style>
</head>
<body>
<a class="skip-link" href="#results">跳到结果</a>
<header class="masthead">
  <p class="eyebrow">Clinical Master · Selection Index</p>
  <h1>麻醉学专硕择校速查</h1>
  <p class="dek">把三年复试线、录取均分与人数、进入复试人数与差额比，以及分档报考建议，压缩进一张可搜索的移动端页面。</p>
  <div class="snapshot" aria-label="数据概况">
    <span><em>__NS__</em> 所院校</span><span><em>__NC__</em> 组复试线</span>
    <span><em>__NN__</em> 组人数样本</span><span>更新 __UPD__</span>
  </div>
</header>

<section class="controls" aria-label="筛选与排序">
  <div class="controls-inner">
    <div class="tabs" role="tablist" aria-label="数据视图">
      <button class="tab" role="tab" data-view="schools" aria-selected="true">院校</button>
      <button class="tab" role="tab" data-view="counts" aria-selected="false">人数</button>
      <button class="tab" role="tab" data-view="cutoffs" aria-selected="false">复试线</button>
    </div>
    <div class="search-row">
      <label class="search-wrap" for="search"><span aria-hidden="true">⌕</span><input id="search" type="search" placeholder="搜索院校、省份、城市或培养单位" autocomplete="off"></label>
      <select id="sort" aria-label="排序方式">
        <option value="hero-desc">分数从高到低</option>
        <option value="hero-asc">分数从低到高</option>
        <option value="tier">按档位</option>
        <option value="n">按录取人数</option>
        <option value="province">按省份</option>
        <option value="city">按城市</option>
      </select>
    </div>
    <div class="tier-strip" aria-label="分数档位筛选">
      <button class="chip" data-tier="ALL" aria-pressed="true">全部</button>
      <button class="chip" data-tier="S" aria-pressed="false">S 顶尖冲击</button>
      <button class="chip" data-tier="A" aria-pressed="false">A 高难冲刺</button>
      <button class="chip" data-tier="B" aria-pressed="false">B 中坚匹配</button>
      <button class="chip" data-tier="C" aria-pressed="false">C 相对稳妥</button>
      <button class="chip" data-tier="D" aria-pressed="false">D 友好保底</button>
      <button class="chip" data-tier="U" aria-pressed="false">U 数据暂缺</button>
    </div>
  </div>
</section>

<main id="results" class="result-region" tabindex="-1">
  <div class="result-bar"><span id="view-label">院校视图</span><span><strong id="result-count">0</strong> 条结果</span></div>
  <div id="content" class="school-grid" aria-live="polite"></div>
</main>

<section class="method">
  <details open>
    <summary>档位口径与使用方法</summary>
    <div class="method-content">
      <div class="legend" id="legend"></div>
      <p>档位按 <strong>2025 年录取平均分</strong>划分——而不是复试线。原因见下：复试线只是「入场券」，多所院校的实际录取分显著高于公布线（如某校 2026 校线 310，而其附属医院一志愿录取最低约 386）。均分未公开的院校依据 2026 院线、招生计划与报录比人工归入档位，并标注为手动定档。</p>
      <p>「进入复试人数」全国公开披露率不足 15%，未披露者标注「未公布」，可用 <strong>招生计划 × 差额复试比</strong>自行推算，不要理解为该校无数据。所有分数与人数均来自各校研究生院公开公告与拟录取名单，空白代表未检索到可核验的公开数据，不代表 0 分、0 人或未招生。</p>
      <p>页面可离线使用，浏览器直接打开即可；报考前请以目标院校当年招生目录、复试细则与拟录取名单为准。</p>
      <p><strong>各校差额复试比例（公开口径原文）</strong></p>
      <ul class="rulelist" id="rules"></ul>
    </div>
  </details>
</section>

<footer><p>105118 麻醉学专业学位硕士 · 2024—2026 公开信息整理 · 共 __NS__ 所院校 / __NC__ 组复试线 / __NN__ 组人数样本。仅作择校初筛参考。</p></footer>

<script>
const DB = __DB__;

const TIER_ORDER = { S: 0, A: 1, B: 2, C: 3, D: 4, U: 5 };
const state = { view: 'schools', tier: 'ALL', query: '', sort: 'hero-desc' };
const content = document.getElementById('content');
const resultCount = document.getElementById('result-count');
const viewLabel = document.getElementById('view-label');
const search = document.getElementById('search');
const sortSel = document.getElementById('sort');

function node(tag, cls, text) {
  const el = document.createElement(tag);
  if (cls) el.className = cls;
  if (text !== undefined && text !== null) el.textContent = String(text);
  return el;
}
function shown(v, fb) { return (v === null || v === undefined || v === '' || v === '未公布') ? (fb === undefined ? '未公布' : fb) : String(v); }
function esc(s) { return String(s == null ? '' : s); }
function tierCode(t) { return t ? String(t).charAt(0) : 'U'; }
function line(latest, y) { return shown(latest[y] === undefined ? null : latest[y]); }

function searchable(item) {
  return Object.values(item).flatMap(v => (v && typeof v === 'object') ? Object.values(v) : [v]).join(' ').toLowerCase();
}
function matches(item) {
  const qOk = !state.query || searchable(item).includes(state.query);
  const tOk = state.tier === 'ALL' || tierCode(item.tier) === state.tier;
  return qOk && tOk;
}

function detailLine(label, value, wrapCls) {
  const w = node('div', 'detail-line');
  w.append(node('dt', '', label), node('dd', wrapCls || '', shown(value)));
  return w;
}
function kpi(label, value, small) {
  const d = node('div');
  d.append(node('span', '', label), node('b', small ? 'sm' : '', shown(value)));
  return d;
}
function kpiRow(pairs) {
  const g = node('div', 'kpi');
  pairs.forEach(([k, v]) => g.append(kpi(k, v, String(shown(v)).length > 7)));
  return g;
}
function adviceBlock(text) {
  const d = node('div', 'advice');
  d.append(node('strong', '', '报考建议'));
  const p = node('p');
  String(text || '').split('⚠').forEach((seg, i) => {
    if (i > 0) p.append(node('span', 'warnico', '⚠'));
    p.append(document.createTextNode(seg));
  });
  d.append(p);
  return d;
}
function scoreOf(item) {
  const v = item.hero !== undefined ? item.hero : (item.latest !== undefined ? item.latest : item.avg);
  return Number(v === null || v === undefined ? -1 : v);
}
function sortItems(items) {
  const byName = (a, b) => shown(a.school, '').localeCompare(shown(b.school, ''), 'zh-CN');
  return items.sort((a, b) => {
    if (state.sort === 'hero-asc') return scoreOf(a) - scoreOf(b) || byName(a, b);
    if (state.sort === 'tier') return (TIER_ORDER[tierCode(a.tier)] ?? 9) - (TIER_ORDER[tierCode(b.tier)] ?? 9) || scoreOf(b) - scoreOf(a) || byName(a, b);
    if (state.sort === 'n') return Number(b.admitted ?? b.planNum ?? -1) - Number(a.admitted ?? a.planNum ?? -1) || byName(a, b);
    if (state.sort === 'province') return shown(a.province || a.region, '').localeCompare(shown(b.province || b.region, ''), 'zh-CN') || byName(a, b);
    if (state.sort === 'city') return shown(a.city, '').localeCompare(shown(b.city, ''), 'zh-CN') || byName(a, b);
    return scoreOf(b) - scoreOf(a) || byName(a, b);
  });
}

/* —— 视图一：院校 —— */
function schoolCard(item, index) {
  const d = node('details', 'school tier-' + tierCode(item.tier));
  d.style.setProperty('--i', Math.min(index, 8));
  const summary = node('summary');
  const head = node('div', 'school-head');
  const nw = node('div');
  nw.append(node('h2', 'school-name', item.school),
    node('div', 'place', shown(item.province) + ' · ' + shown(item.city) + ' · ' + shown(item.zone) + ' · ' + shown(item.level)));
  const sb = node('div', 'score-block');
  sb.append(node('b', '', shown(item.hero)), node('small', '', item.heroUnit));
  if (item.star) sb.append(node('small', '', '难度 ' + item.star));
  head.append(nw, sb);

  const ql = node('div', 'quickline');
  ql.append(node('span', 'tier-label', shown(item.tier)),
    node('span', '', '2026 线 ' + shown(item.already)),
    node('span', '', '录取 ' + shown(item.admitted) + ' 人'),
    node('span', '', '数据 ' + shown(item.completeness)));
  if (item.manual) {
    const badge = node('span', '', '手动定档');
    badge.className = 'badge';
    ql.append(badge);
  }
  summary.append(head, ql);

  const body = node('div', 'school-detail');
  const dl = node('dl', 'detail-grid');
  const rows = [
    kpiRow([
      ['录取均分', item.average],
      ['录取最低分', item.low],
      ['录取人数', item.admitted],
      ['进入复试', item.reexam],
    ]),
    detailLine('三年复试线', '2024 ' + shown(item.scores['2024']) + '｜2025 ' + shown(item.scores['2025']) + '｜2026 ' + shown(item.scores['2026']), 'wrap'),
  ];
  if (item.single) rows.push(detailLine('2026 单科线', item.single));
  rows.push(
    detailLine('复试差额比', item.ratio),
    detailLine('2026 招生计划', item.plan, 'wrap'),
    detailLine('分数线性质', item.kind),
    detailLine('数据依据', item.note, 'wrap')
  );
  if (item.rank) rows.push(detailLine('软科 2025 专业排名', '第 ' + item.rank + ' 名 · ' + shown(item.rankGrade)));
  if (item.rankNote) rows.push(detailLine('学科实力', item.rankNote, 'wrap'));
  rows.push(adviceBlock(item.advice));
  rows.forEach(x => dl.append(x));
  body.append(dl);
  d.append(summary, body);
  return d;
}

/* —— 视图二：人数样本 —— */
function countCard(item, index) {
  const a = node('article', 'record');
  a.style.setProperty('--i', Math.min(index, 8));
  const top = node('div', 'record-top');
  const t = node('div');
  t.append(node('h2', '', item.school), node('div', 'record-meta', shown(item.year) + ' · ' + shown(item.region) + ' · ' + shown(item.city) + ' · ' + shown(item.tier)));
  const sc = node('div', 'record-score', shown(item.reexam) + ' → ' + shown(item.admitted));
  top.append(t, sc);
  const grid = node('div', 'record-grid');
  grid.append(
    kpiRow([
      ['录取人数', item.admitted],
      ['录取最低分', item.low],
      ['录取平均分', item.avg],
      ['复试差额比', item.ratio],
    ]),
    detailLine('档位', item.tier),
    detailLine('2026 复试线', item.already),
    detailLine('2026 招生计划', item.plan, 'wrap'),
    detailLine('数据年份', item.year),
    detailLine('依据说明', item.basis, 'wrap')
  );
  a.append(top, grid);
  return a;
}

/* —— 视图三：复试线 —— */
function cutoffCard(item, index) {
  const a = node('article', 'record tier-' + tierCode(item.tier));
  a.style.setProperty('--i', Math.min(index, 8));
  const top = node('div', 'record-top');
  const t = node('div');
  t.append(node('h2', '', item.school),
    node('div', 'record-meta', shown(item.latestYear) + ' 年线 · ' + shown(item.province) + ' · ' + shown(item.city) + ' · ' + shown(item.level)));
  top.append(t, node('div', 'record-score', shown(item.hero)));
  const grid = node('div', 'record-grid');
  grid.append(
    detailLine('档位', item.tier),
    detailLine('三年复试线', '2024 ' + shown(item.scores['2024']) + '｜2025 ' + shown(item.scores['2025']) + '｜2026 ' + shown(item.scores['2026']), 'wrap'),
    detailLine('2026 单科线', item.single),
    detailLine('较 2024 变化', item.delta == null ? null : (item.delta > 0 ? '+' + item.delta + ' 分' : item.delta + ' 分')),
    detailLine('高出 A 区国家线', item.above == null ? null : '+' + item.above + ' 分'),
    detailLine('分数线性质', item.kind),
    detailLine('备注', item.note, 'wrap')
  );
  a.append(top, grid);
  return a;
}

function render() {
  let items, renderer, label;
  if (state.view === 'counts') { items = DB.counts.filter(matches); renderer = countCard; label = '人数样本'; }
  else if (state.view === 'cutoffs') { items = DB.cutoffs.filter(matches); renderer = cutoffCard; label = '复试线明细'; }
  else { items = DB.schools.filter(matches); renderer = schoolCard; label = '院校视图'; }
  items = sortItems(items.slice());
  content.className = state.view === 'schools' ? 'school-grid' : 'data-list';
  content.replaceChildren();
  if (!items.length) {
    const e = node('section', 'empty');
    e.append(node('h2', '', '没有匹配结果'), node('p', '', '试试缩短关键词，或切换到「全部」档位。'));
    content.append(e);
  } else items.forEach((it, i) => content.append(renderer(it, i)));
  resultCount.textContent = items.length;
  viewLabel.textContent = label;
}

document.getElementById('legend').replaceChildren(...DB.legends.map(([c, name, range]) => {
  const s = node('span', c.toLowerCase(), c + ' ' + name + ' · ' + range);
  return s;
}));
document.getElementById('rules').replaceChildren(...DB.rules.map(([who, what]) => {
  const li = node('li');
  li.append(node('b', '', who + '：'), document.createTextNode(what));
  return li;
}));
document.querySelectorAll('.tab').forEach(b => b.addEventListener('click', () => {
  state.view = b.dataset.view; state.tier = 'ALL'; state.query = ''; search.value = '';
  sortSel.value = state.view === 'counts' ? 'n' : 'hero-desc'; state.sort = sortSel.value;
  document.querySelectorAll('.tab').forEach(x => x.setAttribute('aria-selected', String(x === b)));
  document.querySelectorAll('.chip').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.tier === 'ALL')));
  render();
}));
document.querySelectorAll('.chip').forEach(b => b.addEventListener('click', () => {
  state.tier = b.dataset.tier;
  document.querySelectorAll('.chip').forEach(x => x.setAttribute('aria-pressed', String(x === b)));
  render();
}));
search.addEventListener('input', () => { state.query = search.value.trim().toLowerCase(); render(); });
sortSel.addEventListener('change', () => { state.sort = sortSel.value; render(); });
render();
</script>
</body>
</html>
"""

css = css.rstrip() + "\n" + EXTRA_CSS
html = (HTML
        .replace("__CSS__", css)
        .replace("__DB__", json.dumps(DB, ensure_ascii=False, separators=(",", ":")))
        .replace("__NS__", str(len(schools)))
        .replace("__NC__", str(len(cutoffs)))
        .replace("__NN__", str(len(counts)))
        .replace("__UPD__", DB["updated"]))

OUT.write_text(html, encoding="utf-8")
print(f"OK -> {OUT.name}")
print(f"  院校 {len(schools)} | 复试线 {len(cutoffs)} | 人数 {len(counts)} | 比例规则 {len(rules)}")
print(f"  体积 {OUT.stat().st_size/1024:.1f} KB")
from collections import Counter
print("  档位分布:", dict(Counter(s['tier'][0] for s in schools)))
