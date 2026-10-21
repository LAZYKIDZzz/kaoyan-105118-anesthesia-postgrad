# -*- coding: utf-8 -*-
"""
把 reports/ 下的 Markdown 报告渲染成站点可访问的 HTML，输出到 docs/reports/。

用法：
    python3 v2-2027/scripts/build_report_html.py

产物：
    docs/reports/index.html                     报告汇总（枢纽页）
    docs/reports/<slug>.html                    单篇报告
    docs/reports/data/*.json                    随报告一起发布的检索留痕（可选）

设计要点：
  * 不依赖第三方库，自带轻量 Markdown 渲染（标题/表格/列表/引用/代码/分隔线/行内格式）。
  * 版式沿用站点既有色板（纸色 #f6f4ef / 深蓝 #1f3a52 / 陶红 #c0492f），标题用宋体。
  * 自动生成右侧（窄屏为折叠）目录，标题带稳定锚点。
  * 相对链接改写：md 里的 ../docs/xxx 在 docs/reports/ 下等价于 ../xxx。
"""
import html
import os
import re
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))       # v2-2027/scripts
V2 = os.path.dirname(BASE)                              # v2-2027
ROOT = os.path.dirname(V2)                              # 仓库根
REPORTS_SRC = os.path.join(ROOT, 'reports')
OUT = os.path.join(ROOT, 'docs', 'reports')

# ---------------------------------------------------------------- 报告清单
# order 越大越靠前；badge 决定卡片角标配色（review=复核稿 / draft=初稿）
CATALOG = [
    {
        'slug': '2026-fushi-lists-hbnu-czmc',
        'md': '2026复试名单核查-河北北方学院与长治医学院-2026-10-21.md',
        'kicker': '名单核查 · 2026-10-21',
        'badge': 'data',
        'summary': '两校 2026 年 105118 一志愿进入复试的名单原文：河北北方学院 31 人进复试、27 人拟录取，长治医学院 15 人进复试、15 人全部拟录取；含全部考生初试分项与复试成绩。',
        'note': '直接解析两校官网公示的原始 PDF，逐条可比对。',
        'dek': '2026 年 105118 一志愿复试名单：河北北方学院 31 人 / 长治医学院 15 人，均为官方公示原文逐条解析',
    },
    {
        'slug': '2026-two-schools-distribution',
        'md': '2026两校麻醉专硕复试与拟录取分数分布-2026-10-21.md',
        'kicker': '分数分布 · 2026-10-21',
        'badge': 'data',
        'summary': '把两校 2026 年 105118 的复试与拟录取名单按分数段摊开：河北北方录取中位 331、长治 334；300 分以下北院 4 人全刷、长治有 294 分录取，说明「最低分」不是典型录取水平。',
        'note': '分位数为名单描述，不是学校划线；拟录取不等于最终学籍录取。',
        'dek': '2026 年两校 105118 分数分布核验：进复试／拟录取逐段人数、中位数与分位数，附原件页码索引',
    },
    {
        'slug': '2027-four-schools-review',
        'md': '2027四校考研公开讨论检索复核-2026-10-21.md',
        'kicker': '复核稿 · 2026-10-21',
        'badge': 'review',
        'summary': '逐平台核对公开讨论的可见性与可信度，标注哪些说法可用、哪些应放下；含 2027 目录核对表与 26 条可回看条目索引。',
        'note': '本页为复核稿，优先级高于初稿。',
    },
    {
        'slug': '2027-four-schools-draft',
        'md': '2027四校麻醉专硕全网讨论检索总结.md',
        'kicker': '初稿 · 2026-10-21',
        'badge': 'draft',
        'summary': '保留早期检索中的四校讨论与报考分析；部分结论已被复核稿修正，分数数据与建议尚未完成独立复核。',
        'note': '初稿，其中若干结论已在复核稿中修正，请对照阅读。',
    },
]

# 随报告发布的附件：源文件（相对 reports/）→ 目标（相对 docs/reports/）
ASSETS = [
    ('research/2026-10-21-four-schools/search-results.json',
     'data/2026-10-21-four-schools/search-results.json'),
] + [
    ('research/2026-10-21-two-schools-distribution/%s' % name,
     'data/2026-10-21-two-schools-distribution/%s' % name)
    for name in (
        'hebei_retest.pdf', 'hebei_admit_http.pdf', 'hebei_adjust_retest.pdf',
        'hebei_adjust_vacancy.pdf', 'changzhi_retest.pdf', 'changzhi_admit.pdf',
        'changzhi_adjust.pdf', 'distribution.json', 'sources.json',
    )
]

BLANK = '—'


# ---------------------------------------------------------------- 行内渲染
def inline(text):
    """渲染行内格式：`code`、**粗体**、*斜体*、[文字](链接)、裸链接。"""
    stash = []

    def hold(fragment):
        stash.append(fragment)
        return '\x00%d\x00' % (len(stash) - 1)

    text = html.escape(text, quote=False)

    # 行内代码：先摘出来，避免后续正则误伤其中的星号/下划线
    text = re.sub(r'`([^`]+)`',
                  lambda m: hold('<code>%s</code>' % m.group(1)),
                  text)

    # 链接 [文字](地址)
    def link(m):
        label, href = m.group(1), m.group(2)
        # 上方已对整段文字转义；地址须先还原，再作为属性转义一次。
        href = rewrite_href(html.unescape(href))
        ext = ' target="_blank" rel="noopener"' if href.startswith(('http://', 'https://')) else ''
        return hold('<a href="%s"%s>%s</a>' % (html.escape(href, quote=True), ext, label))

    text = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', link, text)

    # 粗体 / 斜体
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', text)

    # 还原占位符
    return re.sub(r'\x00(\d+)\x00', lambda m: stash[int(m.group(1))], text)


def rewrite_href(href):
    """把 md 相对路径改写成 docs/reports/ 下的等价路径。"""
    if re.match(r'^[a-z]+:', href) or href.startswith(('#', '/')):
        return href
    if href.startswith('../docs/'):
        return '../' + href[len('../docs/'):]
    if href.startswith('research/'):
        return 'data/' + href[len('research/'):]
    return href


# ---------------------------------------------------------------- 块级渲染
def slug_seed(idx):
    return 'sec-%d' % idx


def parse_table(lines, start):
    """返回 (表头, 对齐, 行列表, 消耗行数)；不是表格返回 None。"""
    if start + 1 >= len(lines):
        return None
    head = lines[start]
    sep = lines[start + 1]
    if '|' not in head or '|' not in sep:
        return None
    if not re.match(r'^\s*\|?[\s:-]*-[\s:|-]*\|?\s*$', sep):
        return None

    def cells(row):
        row = row.strip()
        if row.startswith('|'):
            row = row[1:]
        if row.endswith('|'):
            row = row[:-1]
        return [c.strip() for c in row.split('|')]

    aligns = []
    for c in cells(sep):
        c = c.strip()
        if c.startswith(':') and c.endswith(':'):
            aligns.append('center')
        elif c.endswith(':'):
            aligns.append('right')
        else:
            aligns.append('')
    rows = []
    i = start + 2
    while i < len(lines) and '|' in lines[i] and lines[i].strip():
        rows.append(cells(lines[i]))
        i += 1
    return cells(head), aligns, rows, i - start


def render_table(head, aligns, rows):
    out = ['<div class="table-wrap"><table>', '<thead><tr>']
    for i, h in enumerate(head):
        style = ' class="ta-%s"' % aligns[i] if i < len(aligns) and aligns[i] else ''
        out.append('<th%s>%s</th>' % (style, inline(h)))
    out.append('</tr></thead><tbody>')
    for r in rows:
        # 补齐/裁剪到表头列数，避免脏表格撑破布局
        r = (r + [''] * len(head))[:len(head)]
        out.append('<tr>' + ''.join(
            '<td%s>%s</td>' % (' class="ta-%s"' % aligns[i] if i < len(aligns) and aligns[i] else '',
                               inline(c)) for i, c in enumerate(r)) + '</tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)


def render_list(items):
    """items: [(level, ordered, text)]，支持 2 空格缩进的嵌套。

    维护一个 (层级, 列表标签) 栈：每层 li 保持打开状态，进入更深层时在
    当前 li 内部开新列表，回到同层时先闭合上一个 li 再开新的。
    """
    out = []
    stack = []

    def close_until(level):
        # 关闭所有比目标层级更深的列表（连同它们所在的 li）
        while stack and stack[-1][0] > level:
            out.append('</li></%s>' % stack.pop()[1])
        # 同层则只闭合上一个 li，为下一个 li 让位
        if stack and stack[-1][0] == level:
            out.append('</li>')

    for level, ordered, text in items:
        tag = 'ol' if ordered else 'ul'
        if stack and level > stack[-1][0]:
            out.append('<%s>' % tag)
            stack.append((level, tag))
        else:
            close_until(level)
            if stack and stack[-1][0] == level and stack[-1][1] != tag:
                out.append('</%s>' % stack.pop()[1])
            if not stack or stack[-1][0] < level:
                out.append('<%s>' % tag)
                stack.append((level, tag))
        out.append('<li>%s' % inline(text))

    while stack:
        out.append('</li></%s>' % stack.pop()[1])
    return ''.join(out)


def md_to_html(md):
    """返回 (标题, 正文 HTML, [(级别, 锚点, 文字)])"""
    lines = md.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    body = []
    toc = []
    title = None
    i = 0
    sec = 0

    def flush_para(buf):
        if buf:
            body.append('<p>%s</p>' % inline(' '.join(x.strip() for x in buf)))
            del buf[:]

    para = []
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_para(para)
            i += 1
            continue

        # 代码块
        if stripped.startswith('```'):
            flush_para(para)
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i])
                i += 1
            i += 1
            body.append('<pre><code>%s</code></pre>' % html.escape('\n'.join(code)))
            continue

        # 分隔线
        if re.match(r'^(-{3,}|\*{3,}|_{3,})$', stripped):
            flush_para(para)
            body.append('<hr>')
            i += 1
            continue

        # 标题
        m = re.match(r'^(#{1,6})\s+(.*)$', stripped)
        if m:
            flush_para(para)
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 1 and title is None:
                title = re.sub(r'\*\*|`', '', text)
                i += 1
                continue
            sec += 1
            anchor = slug_seed(sec)
            toc.append((level, anchor, re.sub(r'[*`]', '', text)))
            body.append('<h%d id="%s">%s<a class="anchor" href="#%s" aria-label="锚点">#</a></h%d>'
                        % (level, anchor, inline(text), anchor, level))
            i += 1
            continue

        # 引用
        if stripped.startswith('>'):
            flush_para(para)
            quote = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote.append(re.sub(r'^\s*>\s?', '', lines[i]))
                i += 1
            body.append('<blockquote>%s</blockquote>' % md_to_inline_join(quote))
            continue

        # 表格
        tbl = parse_table(lines, i)
        if tbl:
            flush_para(para)
            head, aligns, rows, used = tbl
            body.append(render_table(head, aligns, rows))
            i += used
            continue

        # 列表
        if re.match(r'^\s*([-*+]|\d+\.)\s+', line):
            flush_para(para)
            items = []
            while i < len(lines) and re.match(r'^\s*([-*+]|\d+\.)\s+', lines[i]):
                raw = lines[i]
                indent = len(raw) - len(raw.lstrip(' '))
                m2 = re.match(r'^\s*([-*+]|\d+\.)\s+(.*)$', raw)
                items.append((indent // 2, m2.group(1)[0].isdigit(), m2.group(2)))
                i += 1
            body.append(render_list(items))
            continue

        para.append(line)
        i += 1

    flush_para(para)
    return title, '\n'.join(body), toc


def md_to_inline_join(quote_lines):
    """引用块内部：相邻空行分段，其余合并。"""
    parts, buf = [], []
    for q in quote_lines:
        if not q.strip():
            if buf:
                parts.append('<p>%s</p>' % inline(' '.join(x.strip() for x in buf)))
                buf = []
        else:
            buf.append(q)
    if buf:
        parts.append('<p>%s</p>' % inline(' '.join(x.strip() for x in buf)))
    return ''.join(parts)


# ---------------------------------------------------------------- 页面模板
CSS = """
:root{
  color-scheme:light;
  --paper:#f6f4ef; --card:#fff; --ink:#27303d; --ink-soft:#56616f; --ink-faint:#8a93a0;
  --navy:#1f3a52; --navy-deep:#16283a; --line:#e3ddd2; --line-soft:#efeae1;
  --accent:#c0492f; --green:#1f7a45; --focus:#2f7fd1;
}
*{box-sizing:border-box}
html{background:var(--navy-deep);scroll-behavior:smooth}
body{margin:0;font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;color:var(--ink);
  background:var(--paper);line-height:1.75;-webkit-font-smoothing:antialiased;font-size:15.5px}
a{color:#1d5f8a;text-underline-offset:3px;text-decoration-thickness:1px}
a:hover{color:var(--accent)}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.9em;background:#efeae1;
  padding:.1em .38em;border-radius:3px;word-break:break-word}

.masthead{position:relative;overflow:hidden;color:#f4efe6;background:linear-gradient(135deg,var(--navy),var(--navy-deep));
  padding:26px 24px 30px;border-bottom:5px solid var(--accent)}
.masthead .inner{max-width:1180px;margin:0 auto}
.crumb{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 16px}
.crumb a{color:#e9e2d6;text-decoration:none;font-size:12.5px;border:1px solid rgba(255,255,255,.28);
  padding:4px 11px;border-radius:20px;background:rgba(255,255,255,.08)}
.crumb a:hover{background:rgba(255,255,255,.2);color:#fff}
.kicker{margin:0 0 8px;font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:#e6b9a9;font-weight:700}
.masthead h1{margin:0;font-family:"Songti SC","STSong",Georgia,serif;font-size:clamp(22px,4.4vw,32px);
  line-height:1.25;letter-spacing:.02em;max-width:22em}
.dek{margin:12px 0 0;max-width:60em;font-size:13.5px;color:#cfd8e0;line-height:1.7}

.layout{max-width:1180px;margin:0 auto;padding:26px 20px 80px;display:grid;gap:34px;
  grid-template-columns:minmax(0,1fr)}
@media (min-width:1024px){
  .layout{grid-template-columns:minmax(0,1fr) 250px;align-items:start}
  .toc{position:sticky;top:18px}
}
.main-col{min-width:0}
.pre-body{max-width:1180px;margin:0 auto;padding:20px 20px 0}
.pre-body .banner{margin:0}
article{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:clamp(20px,3.2vw,42px);box-shadow:0 1px 2px rgba(31,58,82,.05);min-width:0}

article > *:first-child{margin-top:0}
h2,h3,h4{font-family:"Songti SC","STSong",Georgia,serif;color:var(--navy);line-height:1.35;letter-spacing:.01em}
h2{margin:2.4em 0 .8em;padding-bottom:.4em;border-bottom:2px solid var(--line);font-size:21px}
h2:first-of-type{margin-top:0}
h3{margin:2em 0 .6em;font-size:17.5px}
h3::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;
  background:var(--accent);margin-right:9px;vertical-align:.16em}
h4{margin:1.6em 0 .5em;font-size:15.5px}
.anchor{opacity:0;margin-left:.4em;color:var(--ink-faint);text-decoration:none;font-size:.8em}
h2:hover .anchor,h3:hover .anchor{opacity:1}
p{margin:.85em 0}
strong{color:#1b232e}
hr{border:0;border-top:1px solid var(--line);margin:2.4em 0}
blockquote{margin:1.2em 0;padding:12px 18px;background:#fbf8f2;border-left:4px solid var(--accent);
  border-radius:0 6px 6px 0;color:#5a4636;font-size:14px}
blockquote p{margin:.3em 0}
ul,ol{margin:.7em 0;padding-left:1.5em}
li{margin:.32em 0}
li > ul,li > ol{margin:.28em 0}

.table-wrap{overflow-x:auto;margin:1.2em 0;border:1px solid var(--line);border-radius:8px;background:#fff}
table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:520px}
th,td{padding:9px 13px;border-bottom:1px solid var(--line-soft);text-align:left;vertical-align:top}
th{background:#f1ede4;color:var(--navy);font-weight:700;white-space:nowrap;border-bottom:2px solid var(--line)}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:#fdfbf6}
.ta-center{text-align:center}
.ta-right{text-align:right}

.toc{font-size:13px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 16px 12px}
.toc summary{font-family:"PingFang SC",sans-serif;font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--ink-soft);cursor:pointer}
.toc details[open] summary{margin-bottom:10px}
.toc summary:focus-visible{outline:3px solid var(--focus);outline-offset:4px}
.toc ol{list-style:none;margin:0;padding:0}
.toc li{margin:0}
.toc a{display:block;padding:4px 0 4px 9px;border-left:2px solid transparent;text-decoration:none;color:var(--ink-soft)}
.toc a:hover{color:var(--navy);border-left-color:var(--accent);background:#fbf8f2}
.toc .lv3{padding-left:20px;font-size:12.4px;color:var(--ink-faint)}
.toc .lv4{padding-left:32px;font-size:12px;color:var(--ink-faint)}
@media (max-width:1023px){.toc{order:-1}.toc ol{columns:2;column-gap:18px}}
@media (max-width:560px){.toc ol{columns:1}}

.banner{margin:0 0 22px;padding:13px 16px;border-radius:8px;font-size:13.5px;line-height:1.65}
.banner.warn{background:#fff7ef;border:1px solid #f0d9c6;border-left:4px solid var(--accent);color:#5a4636}
.banner.info{background:#f0f6f1;border:1px solid #cfe0d4;border-left:4px solid var(--green);color:#28503a}
.banner a{font-weight:700}

footer.site{max-width:1180px;margin:0 auto;padding:0 20px 40px;font-size:12px;color:var(--ink-soft)}
footer.site p{margin:.3em 0}

/* ---- 汇总页 ---- */
.hub{max-width:900px;margin:0 auto;padding:30px 20px 70px;display:grid;gap:16px}
.card{display:block;background:var(--card);border:1px solid var(--line);border-top:3px solid var(--accent);
  border-radius:10px;padding:20px 22px;text-decoration:none;color:inherit;transition:.16s}
.card:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(31,58,82,.1);color:inherit}
.card .badge{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.1em;padding:3px 9px;
  border-radius:20px;margin-bottom:9px}
.card .badge.review{background:#e8f3ec;color:#1f7a45;border:1px solid #bfdcc8}
.card .badge.draft{background:#fbe9e4;color:#a83d26;border:1px solid #f1cec3}
.card .badge.data{background:#e9f0f7;color:#1f3a52;border:1px solid #c6d6e6}
.card h2{margin:0 0 .4rem;font-size:18px;border:0;padding:0}
.card h2::before{display:none}
.card p{margin:0 0 .7rem;font-size:13.5px;color:var(--ink-soft);line-height:1.65}
.card .go{font-size:12.5px;font-weight:700;color:var(--navy)}
.card .go::after{content:" →"}
.hub-note{background:#fff;border:1px solid var(--line);border-left:4px solid var(--navy);border-radius:8px;
  padding:14px 18px;font-size:13px;color:var(--ink-soft)}
.hub-note b{color:var(--navy)}
.hub-head{padding:2px 2px 6px}
.hub-head .sep{color:var(--ink-faint);margin:0 8px}
.hub-sub{margin:0 0 8px;font-size:13.5px;color:var(--ink-soft)}
"""


def page(title, kicker, body, toc_html='', banners='', dek='', crumb_extra='', hub=False):
    crumb = ('<div class="crumb"><a href="../index.html">← 三年分数对照</a>'
             '<a href="../nav.html">资料导航</a>'
             '<a href="index.html">检索报告</a>%s</div>' % crumb_extra)
    toc_block = '<nav class="toc" aria-label="目录"><details open><summary>本页目录</summary>%s</details></nav>' % toc_html if toc_html else ''
    toc_script = """<script>
(() => {
  const details = document.querySelector('.toc details');
  if (!details) return;
  const wide = window.matchMedia('(min-width:1024px)');
  const update = () => { details.open = wide.matches; };
  update();
  wide.addEventListener('change', update);
})();
</script>""" if toc_html and not hub else ''
    if hub:
        main_open = '<main class="hub">%s' % banners
        main_close = '</main>'
        toc_block = ''
    else:
        # 提示条放在正文容器之外：手机端先看到提示，再看到目录
        main_open = ('%s<div class="layout"><div class="main-col">'
                     % ('<div class="pre-body">%s</div>' % banners if banners else ''))
        main_close = '</div>'
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#173149">
<title>{html.escape(title)} · 105118 麻醉学专硕</title>
<style>{CSS}</style>
</head>
<body>
<header class="masthead">
  <div class="inner">
    {crumb}
    <p class="kicker">{html.escape(kicker)}</p>
    <h1>{html.escape(title)}</h1>
    {f'<p class="dek">{dek}</p>' if dek else ''}
  </div>
</header>
{main_open}
{body}
{main_close}
{toc_block}
{'</div>' if not hub else ''}
<footer class="site">
  <p>105118 麻醉学专业学位硕士 · 公开信息整理 · 报告生成于 2026-10-21</p>
  <p>报告内容为检索与核对记录，录取数据以各校研究生院公示原文为准。</p>
</footer>
{toc_script}
</body>
</html>
"""


def toc_html(toc):
    items = []
    for level, anchor, text in toc:
        if level > 4:
            continue
        cls = '' if level == 2 else ('lv%d' % level)
        items.append('<li class="%s"><a href="#%s">%s</a></li>' % (cls, anchor, html.escape(text)))
    return '<ol>%s</ol>' % ''.join(items)


def build_report(item, index_of):
    src = os.path.join(REPORTS_SRC, item['md'])
    md = open(src, encoding='utf-8').read()
    title, body, toc = md_to_html(md)

    banners = []
    other = [c for c in CATALOG if c['slug'] != item['slug']]
    if item['badge'] == 'draft':
        review = next((c for c in CATALOG if c['badge'] == 'review'), None)
        if review:
            banners.append(
                f'<div class="banner warn"><b>这是一份初稿。</b>其中「河北北方学院复试占 70%」等结论已在复核稿中修正，'
                f'请以复核稿为准 → <a href="{review["slug"]}.html">阅读《检索与复核总结》</a></div>')
    if item['badge'] == 'review' and other:
        banners.append(
            f'<div class="banner info">建议优先阅读本页。初稿中的部分结论已修正，往年分数数据尚未完成独立复核，'
            f'仅供检索背景参考 → <a href="{other[0]["slug"]}.html">查看初稿</a></div>')

    out = page(
        title=title or item['slug'],
        kicker=item['kicker'],
        body='<article>%s</article>' % body,
        toc_html=toc_html(toc),
        banners=''.join(banners),
        dek=item.get('dek') or ('检索时间 2026-10-21 · 河北北方学院／长治医学院／河南医药大学（原新乡医学院）／山东医药大学（原滨州医学院）'),
    )
    path = os.path.join(OUT, item['slug'] + '.html')
    open(path, 'w', encoding='utf-8').write(out)
    return path, title, len(body)


def build_hub(titles):
    cards = []
    for item in CATALOG:
        label = {'review': '复核稿', 'draft': '初稿', 'data': '名单核查'}.get(item['badge'], '初稿')
        cards.append(
            '<a class="card" href="%s.html">'
            '<span class="badge %s">%s · %s</span>'
            '<h2>%s</h2><p>%s</p><span class="go">阅读全文</span></a>'
            % (item['slug'], item['badge'], label, item['kicker'].split(' · ')[-1],
               html.escape(titles.get(item['slug'], item['slug'])), html.escape(item['summary'])))
    body = ('<div class="hub-head"><p class="hub-sub">河北北方学院 · 长治医学院 · 河南医药大学 · 山东医药大学'
            '<span class="sep">｜</span>共 %d 份检索记录</p></div>' % len(CATALOG)
            + ''.join(cards)
            + '<div class="hub-note"><b>阅读顺序建议：</b>先看复核稿（对公开讨论的可见性与可信度做了逐条核对，'
              '并列出 26 条可回看来源）。初稿仅供检索背景参考，其中的往年分数数据尚未完成独立复核，'
              '分数建议不能当作 2027 录取门槛。报考前请以当年官方招生文件为准。</div>')
    out = page('四校检索报告', 'Reports · 2026-10-21', body, hub=True,
               dek='2027 考研四校麻醉学专硕的公开讨论检索记录：哪些信息可核验、哪些说法应放下。')
    path = os.path.join(OUT, 'index.html')
    open(path, 'w', encoding='utf-8').write(out)
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    # 附件
    for src_rel, dst_rel in ASSETS:
        s = os.path.join(REPORTS_SRC, src_rel)
        d = os.path.join(OUT, dst_rel)
        if not os.path.exists(s):
            print('MISSING asset:', s)
            continue
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copyfile(s, d)
        print('-> docs/reports/%s' % dst_rel)

    titles = {}
    for idx, item in enumerate(CATALOG):
        path, title, n = build_report(item, idx)
        titles[item['slug']] = title or item['slug']
        print('-> docs/reports/%s.html  (%s, %d KB)' % (item['slug'], title, n // 1024))

    hub = build_hub(titles)
    print('-> docs/reports/index.html  (报告汇总)')
    print('done.')


if __name__ == '__main__':
    main()
