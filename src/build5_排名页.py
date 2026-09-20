# -*- coding: utf-8 -*-
"""从 docs/index.html 内嵌的 DB 提取排名数据，生成 docs/ranking.html"""
import re, json, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = (ROOT / "docs/index.html").read_text(encoding="utf-8")
s = src.index("const DB = ") + len("const DB = ")
e = src.index("\nconst TIER_ORDER")
DB = json.loads(src[s:e].strip().rstrip(";"))

TIER_CN = {"S": "S 顶尖冲击", "A": "A 高难冲刺", "B": "B 中坚匹配",
           "C": "C 相对稳妥", "D": "D 友好保底", "U": "U 数据暂缺"}

rows = sorted([x for x in DB["schools"] if x.get("rank")], key=lambda y: y["rank"])

GRADES = [
    ("A+", "顶尖梯队", "oklch(58% 0.17 31)"),
    ("A",  "领先梯队", "oklch(64% 0.13 58)"),
    ("B+", "中坚梯队", "oklch(70% 0.09 110)"),
    ("B",  "区域梯队", "oklch(74% 0.055 222)"),
]

def esc(v):
    return html.escape(str(v), quote=True)

body = []
for grade, label, tint in GRADES:
    items = [x for x in rows if (x.get("rankGrade") or "") == grade]
    if not items:
        continue
    lis = []
    for x in items:
        province = x.get("province") or "—"
        city = x.get("city") or ""
        place = province if (not city or city == province) else f"{province} · {city}"
        meta = " · ".join([place, x.get("level") or "—",
                           "2026 考取难度 " + TIER_CN.get(x.get("tierCode") or "U", "未知")])
        why = (x.get("rankNote") or "").strip()
        why_html = f'<p class="why">{esc(why)}</p>' if why else ""
        lis.append(
            f'<li><span class="no">{x["rank"]}</span><div class="body">'
            f'<h3>{esc(x["school"])}</h3><p class="meta">{esc(meta)}</p>{why_html}</div></li>'
        )
    body.append(
        f'<section class="group">\n'
        f'  <h2 style="--gtint:{tint}"><span class="grade">{esc(grade)}</span>'
        f'{esc(label)}<span class="cnt">{len(items)} 所</span></h2>\n'
        f'  <ol class="rank-list">\n    ' + "\n    ".join(lis) + '\n  </ol>\n</section>'
    )

HEAD = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#173149">
<title>麻醉学专业排名 · 105118 麻醉学专硕</title>
<style>
  :root {
    color-scheme: light;
    --paper: oklch(96% 0.018 83);
    --paper-deep: oklch(91% 0.026 81);
    --ink: oklch(27% 0.045 242);
    --ink-soft: oklch(43% 0.035 242);
    --navy: oklch(29% 0.065 242);
    --navy-deep: oklch(21% 0.05 242);
    --line: oklch(78% 0.025 82);
    --accent: oklch(58% 0.17 31);
    --focus: oklch(63% 0.16 245);
  }
  * { box-sizing: border-box; }
  html { background: var(--navy-deep); scroll-behavior: smooth; }
  body {
    margin: 0; min-height: 100vh; color: var(--ink);
    background:
      linear-gradient(90deg, transparent 0 1.45rem, color-mix(in oklch, var(--accent) 22%, transparent) 1.45rem 1.5rem, transparent 1.5rem),
      var(--paper);
    font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    line-height: 1.6;
    padding: 0 0 max(2rem, env(safe-area-inset-bottom));
  }
  :focus-visible { outline: 3px solid var(--focus); outline-offset: 3px; }
  .masthead {
    position: relative; overflow: hidden; color: oklch(96% 0.018 83);
    background: var(--navy);
    padding: clamp(2rem, 7vw, 4rem) clamp(1.25rem, 6vw, 5rem) clamp(1.75rem, 5vw, 3rem);
    border-bottom: 5px solid var(--accent);
  }
  .masthead::after {
    content: "RANK"; position: absolute; right: -.04em; bottom: -.42em;
    font-family: Georgia, "Times New Roman", serif;
    font-size: clamp(5rem, 26vw, 14rem); font-weight: 700; line-height: 1;
    letter-spacing: -.07em;
    color: color-mix(in oklch, var(--paper) 7%, transparent); pointer-events: none;
  }
  .masthead-nav { position: relative; z-index: 2; margin: 0 0 1.5rem; }
  .masthead-nav a {
    display: inline-flex; align-items: center; gap: .4rem;
    min-height: 42px; padding: 0 .9rem;
    border: 1px solid oklch(62% 0.05 235); color: oklch(93% 0.02 236);
    background: color-mix(in oklch, var(--paper) 10%, transparent);
    font-size: .8rem; font-weight: 700; letter-spacing: .04em; text-decoration: none;
  }
  .masthead-nav a:hover { border-color: var(--paper); background: color-mix(in oklch, var(--paper) 22%, transparent); }
  .eyebrow { position: relative; z-index: 1; margin: 0 0 .75rem; color: oklch(82% 0.08 70); font-size: .78rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }
  h1 { position: relative; z-index: 1; margin: 0; font-family: "Songti SC", "STSong", Georgia, serif; font-size: clamp(2rem, 8vw, 3.4rem); line-height: 1.02; letter-spacing: -.04em; }
  .dek { position: relative; z-index: 1; max-width: 58ch; margin: 1rem 0 0; color: oklch(87% 0.025 236); font-size: clamp(.95rem, 3vw, 1.06rem); }
  main { max-width: 60rem; margin: 0 auto; padding: clamp(1.5rem, 5vw, 3rem) clamp(1rem, 4vw, 3rem); }
  .intro {
    padding: 1.2rem 1.4rem; background: var(--paper-deep);
    border-left: 3px solid var(--accent); margin-bottom: 1rem;
  }
  .intro p { margin: .3rem 0; font-size: .87rem; color: var(--ink-soft); }
  .intro p b { color: var(--ink); }
  .group h2 {
    display: flex; align-items: baseline; gap: .6rem; flex-wrap: wrap;
    margin: 2.4rem 0 .9rem; padding-bottom: .55rem;
    border-bottom: 2px solid var(--gtint);
    font-size: 1.15rem; font-weight: 700; letter-spacing: -.01em;
  }
  .group h2 .grade {
    padding: .12rem .5rem; color: oklch(99% 0.01 83);
    background: var(--gtint); font-size: .82rem; font-weight: 700; letter-spacing: .04em;
  }
  .group h2 .cnt { margin-left: auto; color: var(--ink-soft); font-size: .78rem; font-weight: 400; }
  .rank-list { list-style: none; margin: 0; padding: 0; display: grid; gap: .7rem; }
  .rank-list li {
    display: grid; grid-template-columns: 3.4rem 1fr; gap: 1rem;
    padding: 1rem 1.15rem;
    background: oklch(98.5% 0.008 83);
    border: 1px solid var(--line); border-left: 3px solid var(--gtint);
  }
  .no {
    font-family: Georgia, "Times New Roman", serif; font-size: 1.7rem; font-weight: 700;
    line-height: 1.1; color: var(--ink-soft); font-variant-numeric: tabular-nums;
  }
  .body h3 { margin: 0 0 .3rem; font-size: 1.06rem; font-weight: 700; letter-spacing: -.01em; }
  .meta { margin: 0; font-size: .76rem; color: var(--ink-soft); letter-spacing: .02em; }
  .why { margin: .5rem 0 0; font-size: .86rem; color: var(--ink); }
  footer {
    max-width: 60rem; margin: 0 auto; padding: 1.5rem clamp(1rem, 4vw, 3rem) 0;
    border-top: 1px solid var(--line); font-size: .8rem; color: var(--ink-soft);
  }
  footer p { margin: .3rem 0; }
  footer a { color: var(--navy); }
</style>
</head>
<body>

<header class="masthead">
  <nav class="masthead-nav" aria-label="页面导航">
    <a href="nav.html"><span aria-hidden="true">&larr;</span> 返回导航页</a>
  </nav>
  <p class="eyebrow">Anesthesiology &middot; Discipline Standing</p>
  <h1>麻醉学专业排名</h1>
  <p class="dek">从学科平台与公开评价信息整理的 33 所院校分档，用于快速判断一所院校的麻醉学底子。注意：学科实力与考取难度是两件事。</p>
</header>

<main>

  <div class="intro">
    <p><b>分档口径</b>：本页分档由资料整理时归纳，依据各校学科平台（国家临床重点专科、国家级一流本科专业、学科创办历史）与公开评价信息，<b>不等同于教育部学科评估的官方结论</b>。</p>
    <p><b>与考取难度的区别</b>：每所院校标注的「考取难度」来自择校速查页，按 2025 年录取平均分划分。两者经常错位——学科底子强的院校未必难考，反之亦然。</p>
    <p><b>未列入的院校</b>：94 所招生院校中另有 61 所暂无可靠的分档依据，因此未在此列示，并不表示其学科水平靠后。</p>
  </div>
"""

FOOT = """
</main>

<footer>
  <p>分档依据各校公开学科信息整理，仅供择校参考，请以院校官方信息为准。</p>
  <p>返回 <a href="nav.html">资料导航</a> 或 <a href="index.html">择校速查</a>。</p>
</footer>

</body>
</html>
"""

out = HEAD + "\n".join(body) + FOOT
(ROOT / "docs/ranking.html").write_text(out, encoding="utf-8")
print("written docs/ranking.html", len(out), "chars,", len(rows), "schools")
