# -*- coding: utf-8 -*-
"""Цены и дата прайса на главной страницы берутся со страниц-источников.

index.html — статичный файл, его не генерирует build_pages.py, поэтому цены в
карточках и плитках застывали: на 13.10.2026 «Автокраны от 16 300 ₽» на главной
против «от 23 980 ₽» на странице раздела, дата «4 августа 2026» при прайсе от
12 октября. Этот шаг идёт ПОСЛЕ build_pages.py и переписывает в index.html:

  1. цену «от N ₽» и «≈ M ₽/час» в карточках каталога и плитках услуг (<a class="cat">)
     — равной цене в плашке героя страницы, на которую ведёт карточка;
  2. цены в мини-блоке героя (<a class="hero__price">);
  3. дату «Цены актуальны на …» — по PRICE_UPDATED из build_pages.py.

Карточки со ссылкой на страницу без цены («под запрос», «смотреть →») не
трогаются. Скрипт идемпотентен; код выхода 1, если не найдено ни одной
карточки (значит, разметка главной изменилась и правило надо обновить).
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
NBSP = " "

BADGE = re.compile(r'<div class="price-badge"><b>(?:от\s+)?([\d   ]+)\s*₽</b>')


def money(n):
    return format(n, ",d").replace(",", " ")


def hour(n):
    # как hour_price() в build_pages.py: 8-часовая смена, округление до 10 ₽
    return int(round(n / 8 / 10.0)) * 10


def page_price(href):
    """Цена из плашки героя страницы или None («под запрос», нет плашки)."""
    p = os.path.join(ROOT, href.strip("/"), "index.html")
    if not os.path.isfile(p):
        return None
    m = BADGE.search(io.open(p, encoding="utf-8").read())
    return int(re.sub(r"\D", "", m.group(1))) if m else None


def main():
    html = io.open(INDEX, encoding="utf-8").read()
    html0 = html
    changed = []
    seen = 0

    def card(m):
        nonlocal seen
        head, href, body, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        price = page_price(href)
        if price is None or "<b>от " not in body:
            return m.group(0)
        seen += 1
        new = re.sub(r"<b>от [\d   ]+ ₽</b>", "<b>от %s ₽</b>" % money(price), body, count=1)
        new = re.sub(r"≈ [\d   ]+ ₽/час", "≈ %s ₽/час" % money(hour(price)), new, count=1)
        if new != body:
            changed.append((href, price))
        return head + new + tail

    html = re.sub(r'(<a class="cat reveal" href="(/[^"]+)">)(.*?)(</a>)', card, html, flags=re.S)

    def hero(m):
        nonlocal seen
        price = page_price(m.group(2))
        if price is None:
            return m.group(0)
        seen += 1
        new = m.group(1) + "<b>от %s ₽</b>" % money(price)
        if new != m.group(0):
            changed.append((m.group(2), price))
        return new

    html = re.sub(r'(<a class="hero__price" href="(/[^"]+)"><span>[^<]*</span>)<b>от [\d   ]+ ₽</b>',
                  hero, html)

    # дата прайса — из build_pages.py
    src = io.open(BUILD, encoding="utf-8").read()
    iso = re.search(r'^PRICE_UPDATED = "(\d{4}-\d{2}-\d{2})"', src, re.M)
    if iso:
        y, mo, d = (int(x) for x in iso.group(1).split("-"))
        human = "%d %s %d" % (d, MONTHS[mo - 1], y)
        html, n = re.subn(r'(Цены актуальны на\s+<time datetime=")[\d-]+(">)[^<]+(</time>)',
                          r"\g<1>%s\g<2>%s\g<3>" % (iso.group(1), human), html)
        if n and ("datetime=\"%s\"" % iso.group(1)) not in html0:
            changed.append(("дата прайса", human))

    if not seen:
        print("sync_home_prices: карточки с ценами не найдены — разметка главной изменилась", file=sys.stderr)
        return 1
    io.open(INDEX, "w", encoding="utf-8").write(html)
    print("sync_home_prices: карточек с ценой %d, обновлено %d" % (seen, len(changed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
