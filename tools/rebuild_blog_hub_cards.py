# -*- coding: utf-8 -*-
"""
rebuild_blog_hub_cards.py — перегенерирует блок карточек на /blog/ из
текущего полного списка BLOG (data_blog_base + data_rf + data_blog_new).

Нужен отдельным скриптом (а не частью build_pages.py), потому что
build_pages.py пересобирает вообще все 171+ страниц с нуля, а обновлять
нужно только blog/index.html — остальные страницы правятся руками поверх
генератора (кэш-баст версии, фото в герое и т.д.), полная пересборка их
откатывает. См. историю коммитов: после каждого запуска build_pages.py
```
git checkout -- <всё кроме blog/*/, sitemap.xml, robots.txt>
```
и здесь то же самое — трогаем только карточки, не весь файл целиком.

Запуск (из kran365_site):
    python tools/rebuild_blog_hub_cards.py
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from data_blog_base import BLOG_BASE
from data_rf import BLOG_RF
from data_blog_new import BLOG_NEW
from data_blog_seo_batch1 import BLOG_SEO_BATCH1
from data_blog_daily_20260902 import BLOG_DAILY_20260902
from data_blog_daily_20260903 import BLOG_DAILY_20260903
from data_blog_daily_20260904 import BLOG_DAILY_20260904

BLOG = list(BLOG_BASE) + BLOG_RF + BLOG_NEW + BLOG_SEO_BATCH1 + BLOG_DAILY_20260902 + BLOG_DAILY_20260903 + BLOG_DAILY_20260904


def esc(s):
    return html.escape(str(s), quote=True)


def main():
    cards_html = []
    for s, t, lead, _ in BLOG:
        excerpt = lead[:110].rsplit(" ", 1)[0] + "…"
        cards_html.append(
            '<a class="bt-card reveal" href="/blog/%s/">'
            '<img class="bt-card__img" src="/assets/img/blog-cards/%s.jpg" alt="" loading="lazy" width="800" height="500">'
            '<div class="bt-card__body"><h3>%s</h3><p>%s</p>'
            '<span class="bt-card__go">Читать <svg width="18" height="18"><use href="#i-go"/></svg></span></div></a>'
            % (s, s, esc(t), esc(excerpt))
        )
    grid = '<div class="bt-grid">' + "".join(cards_html) + "</div>"

    path = os.path.join(ROOT, "blog", "index.html")
    content = open(path, encoding="utf-8").read()
    # blog/index.html имеет свою структуру (не ту же, что тизер на главной):
    # сетка карточек стоит перед блоком <div class="related"><h2>Все статьи</h2>.
    # Якорь — конец вводного абзаца (<p>...</p> сразу после prose reveal), а не
    # сам формат блока карточек: после "голого" build_pages.py (без последующего
    # прогона этого скрипта) там оказывается устаревший ptable, а не bt-grid —
    # оба случая должны замениться одинаково, по границам intro/related.
    intro = re.search(r'<div class="prose reveal"><p>.*?</p>', content, re.S)
    related_idx = content.find('<div class="related"><h2>Все статьи</h2>')
    if not intro or related_idx == -1:
        print("PATTERN NOT FOUND — правь вручную")
        return 1
    new_content = content[: intro.end()] + grid + content[related_idx:]
    open(path, "w", encoding="utf-8").write(new_content)
    print("blog/index.html: %d карточек" % len(BLOG))
    return 0


if __name__ == "__main__":
    sys.exit(main())
