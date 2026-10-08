# -*- coding: utf-8 -*-
"""
将 v2-2027/html/ 的页面同步到 GitHub Pages 发布目录 docs/。

映射：
  html/compare.html   -> docs/index.html       （首页：三年分数与人数对照）
  html/index.html     -> docs/v2/index.html    （2027 报考速查总表）
  html/tier350.html   -> docs/v2/tier350.html
  html/years3.html    -> docs/v2/years3.html
并在 docs/v2/*.html 末尾注入「← 资料导航」返回链接（指向 ../nav.html）。

注意：本脚本只写 docs/index.html 与 docs/v2/ 下的文件，
     不触碰 docs/ 的旧站页面（lookup.html、score-*.html、tier350*.html 等）与 docs/nav.html。
"""
import os
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))   # v2-2027/scripts
V2 = os.path.dirname(BASE)                          # v2-2027
ROOT = os.path.dirname(V2)                          # 仓库根
SRC = os.path.join(V2, 'html')
DOCS = os.path.join(ROOT, 'docs')
V2DOCS = os.path.join(DOCS, 'v2')

BACKLINK = (
    '<a href="../nav.html" id="wb-navback" style="position:fixed;left:14px;bottom:14px;z-index:99999;'
    "font:600 12.5px/1 'PingFang SC','Microsoft YaHei',sans-serif;color:#fff;"
    'background:rgba(31,58,82,.92);padding:9px 13px;border-radius:20px;text-decoration:none;'
    'box-shadow:0 2px 10px rgba(0,0,0,.25)">← 资料导航</a>'
)


def inject_backlink(html):
    if 'wb-navback' in html:
        return html
    return html.replace('</body>', BACKLINK + '\n</body>')


def main():
    os.makedirs(V2DOCS, exist_ok=True)
    pairs = [
        (os.path.join(SRC, 'compare.html'), os.path.join(DOCS, 'index.html'), False),
        (os.path.join(SRC, 'index.html'), os.path.join(V2DOCS, 'index.html'), True),
        (os.path.join(SRC, 'tier350.html'), os.path.join(V2DOCS, 'tier350.html'), True),
        (os.path.join(SRC, 'years3.html'), os.path.join(V2DOCS, 'years3.html'), True),
    ]
    for s, d, wrap in pairs:
        if not os.path.exists(s):
            print('MISSING source:', s)
            continue
        shutil.copyfile(s, d)
        if wrap:
            t = open(d, encoding='utf-8').read()
            open(d, 'w', encoding='utf-8').write(inject_backlink(t))
        print('->', os.path.relpath(d, ROOT))
    print('done.')


if __name__ == '__main__':
    main()
