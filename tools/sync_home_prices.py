# -*- coding: utf-8 -*-
"""Цены и дата прайса на главной страницы берутся со страниц-источников.

index.html — статичный файл, его не генерирует build_pages.py, поэтому цены в
карточках и плитках застывали: на 13.10.2026 «Автокраны от 16 300 ₽» на главной
против «от 23 980 ₽» на странице раздела, дата «4 августа 2026» при прайсе от
12 октября. Этот шаг идёт ПОСЛЕ build_pages.py и переписывает в index.html:

  1. блок цены (<span class="cat__price">) в карточках каталога и плитках услуг
     (<a class="cat">) — по плашке героя страницы, на которую ведёт карточка:
     «от N ₽ / смена ≈ M ₽/час» или «от N ₽ / месяц» (башенные краны);
  2. цены в мини-блоке героя (<a class="hero__price">);
  3. дату «Цены актуальны на …» — по PRICE_UPDATED из build_pages.py.

Карточки со ссылкой на страницу без плашки («смотреть →») не трогаются.
Идемпотентен; код выхода 1, если не найдено ни одной карточки (разметка главной
изменилась — правило надо обновить).
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
BUILD = os.path.join(ROOT, "tools", "build_pages.py")

MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня",
          "июля", "августа", "сентября", "октября", "ноября", "декабря"]

# плашка героя: цена, единица, (необязательно) «≈ M ₽/час»
BADGE = re.compile(
    r'<div class="price-badge"><b>(?:от\s+)?([\d   ]+)\s*₽</b><span>([^<]*)</span>'
    r'(?:\s*<span class="price-hour">≈\s*([\d   ]+)\s*₽/час</span>)?')


def money(n):
    return format(n, ",d").replace(",", " ")


def page_badge(href):
    """(цена, единица, час|None) из плашки страницы или None."""
    p = os.path.join(ROOT, href.strip("/"), "index.html")
    if not os.path.isfile(p):
        return None
    m = BADGE.search(io.open(p, encoding="utf-8").read())
    if not m:
        return None
    price = int(re.sub(r"\D", "", m.group(1)))
    hour = int(re.sub(r"\D", "", m.group(3))) if m.group(3) else None
    return price, m.group(2).strip(), hour


def main():
    html = io.open(INDEX, encoding="utf-8").read()
    html0 = html
    changed = []
    seen = 0

    def card(m):
        nonlocal seen
        head, href, body, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        badge = page_badge(href)
        if badge is None or 'class="cat__price"' not in body:
            return m.group(0)
        price, unit, hour = badge
        seen += 1
        block = '<span class="cat__price"><b>от %s ₽</b> <span>%s</span>%s</span>' % (
            money(price), unit,
            ('<span class="cat__price-hour">≈ %s ₽/час</span>' % money(hour)) if hour else "")
        new = re.sub(r'<span class="cat__price">.*?</span>(?:</span>)?(?=\s*<span class="cat__go">)', block,
                     body, count=1, flags=re.S)
        if new != body:
            changed.append((href, price))
        return head + new + tail

    html = re.sub(r'(<a class="cat reveal" href="(/[^"]+)">)(.*?)(</a>)', card, html, flags=re.S)

    def hero(m):
        nonlocal seen
        badge = page_badge(m.group(2))
        if badge is None:
            return m.group(0)
        seen += 1
        price, unit, _ = badge
        new = m.group(1) + "<b>от %s ₽</b><i>%s</i></a>" % (money(price), unit)
        if new != m.group(0):
            changed.append((m.group(2), price))
        return new

    html = re.sub(r'(<a class="hero__price" href="(/[^"]+)"><span>[^<]*</span>)<b>[^<]*</b><i>[^<]*</i></a>',
                  hero, html)

    # дата прайса — из build_pages.py
    src = io.open(BUILD, encoding="utf-8").read()
    iso = re.search(r'^PRICE_UPDATED = "(\d{4}-\d{2}-\d{2})"', src, re.M)
    if iso:
        y, mo, d = (int(x) for x in iso.group(1).split("-"))
        human = "%d %s %d" % (d, MONTHS[mo - 1], y)
        html, n = re.subn(r'(Цены актуальны на\s+<time datetime=")[\d-]+(">)[^<]+(</time>)',
                          r"\g<1>%s\g<2>%s\g<3>" % (iso.group(1), human), html)
        if n and ('datetime="%s"' % iso.group(1)) not in html0:
            changed.append(("дата прайса", human))

    if not seen:
        print("sync_home_prices: карточки с ценами не найдены — разметка главной изменилась", file=sys.stderr)
        return 1
    io.open(INDEX, "w", encoding="utf-8").write(html)
    print("sync_home_prices: карточек с ценой %d, обновлено %d" % (seen, len(changed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
