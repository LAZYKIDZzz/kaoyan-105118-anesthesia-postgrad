# -*- coding: utf-8 -*-
"""把根目录的两个 HTML 产物同步到 docs/ 发布目录。

背景：docs/ 下的页面比根目录原件多一个「← 返回导航页」的入口（因为 docs/ 内是
一个多页站点，需要有回导航页的路径）。此前这一步是手工粘贴，容易漏做或做偏。

本脚本把该步骤固化：
  105118麻醉学专硕择校速查-编辑版.html   -> docs/index.html
  105118麻醉学考研报考决策表-手机版.html -> docs/decision-mobile.html

注入位置用锚点定位，锚点找不到时直接报错退出，避免产物风格悄悄漂移。

其余 docs 页面由各自脚本直接写入 docs/，不经过本脚本：
  docs/tier350.html / tier350-strategy.html  <- build7_阶梯分析.py
  docs/ranking.html                          <- build5_排名页.py（读 docs/index.html）
  docs/sources.html                          <- build6_来源页.py（读 docs/index.html）
所以本脚本必须在 build4 / build3 之后、build5 / build6 之前运行。
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# 择校速查页（纸感版式，深色 masthead）
INDEX_CSS = """    .masthead-nav { position: relative; z-index: 2; margin: 0 0 1.5rem; }
    .masthead-nav a {
      display: inline-flex; align-items: center; gap: .4rem;
      min-height: 42px; padding: 0 .9rem;
      border: 1px solid oklch(62% 0.05 235);
      color: oklch(93% 0.02 236);
      background: color-mix(in oklch, var(--paper) 10%, transparent);
      font-size: .8rem; font-weight: 700; letter-spacing: .04em;
      text-decoration: none;
    }
    .masthead-nav a:hover { border-color: var(--paper); background: color-mix(in oklch, var(--paper) 22%, transparent); }
"""
INDEX_CSS_ANCHOR = "    @media (min-width: 420px) { .kpi { grid-template-columns: repeat(4, minmax(0,1fr)); } }"
INDEX_HTML = """  <nav class="masthead-nav" aria-label="页面导航">
    <a href="nav.html"><span aria-hidden="true">←</span> 返回导航页</a>
  </nav>
"""
INDEX_HTML_ANCHOR = '<header class="masthead">'

# 手机版决策表（浅色卡片版式）
MOBILE_CSS = """    .back{display:inline-flex;align-items:center;gap:.25rem;margin:0 0 8px;padding:5px 10px;border:1px solid var(--line);border-radius:6px;color:var(--accent);background:var(--card);font-size:12px;font-weight:600;text-decoration:none}
    .back:hover{border-color:var(--accent);background:var(--accent-soft)}
"""
MOBILE_CSS_ANCHOR = "@media (min-width:640px){main{max-width:680px;margin:0 auto}.topbar>div{max-width:680px;margin:0 auto}}"
MOBILE_HTML = '  <a class="back" href="nav.html"><span aria-hidden="true">←</span> 返回导航页</a>\n'
MOBILE_HTML_ANCHOR = '<header class="topbar">'


def inject(html: str, anchor: str, payload: str, before: bool, label: str) -> str:
    """在锚点行之前/之后插入 payload；锚点必须唯一命中。"""
    hits = html.count(anchor)
    if hits != 1:
        raise SystemExit(
            f"[sync_docs] 锚点命中 {hits} 次（期望 1 次）：{label}\n  锚点：{anchor[:80]}"
        )
    if before:
        return html.replace(anchor, payload + anchor, 1)
    return html.replace(anchor, anchor + "\n" + payload.rstrip("\n"), 1)


def sync(src_name: str, dst_name: str, css: str, css_anchor: str,
         html_frag: str, html_anchor: str) -> None:
    src_path = ROOT / src_name
    if not src_path.exists():
        raise SystemExit(f"[sync_docs] 找不到源文件，请先运行对应 build 脚本：{src_path}")
    html = src_path.read_text(encoding="utf-8")
    html = inject(html, css_anchor, css, before=True, label=f"{dst_name} 样式锚点")
    html = inject(html, html_anchor, html_frag, before=False, label=f"{dst_name} 导航锚点")
    dst_path = DOCS / dst_name
    dst_path.write_text(html, encoding="utf-8")
    print(f"OK -> docs/{dst_name}  ({dst_path.stat().st_size/1024:.1f} KB, {len(html)} chars)")


def main() -> int:
    sync("105118麻醉学专硕择校速查-编辑版.html", "index.html",
         INDEX_CSS, INDEX_CSS_ANCHOR, INDEX_HTML, INDEX_HTML_ANCHOR)
    sync("105118麻醉学考研报考决策表-手机版.html", "decision-mobile.html",
         MOBILE_CSS, MOBILE_CSS_ANCHOR, MOBILE_HTML, MOBILE_HTML_ANCHOR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
