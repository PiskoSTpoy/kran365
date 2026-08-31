# -*- coding: utf-8 -*-
"""Полная таблица цен по всем 10 классам техники, вставленная целиком в тело
каждой из 10 тоннажных страниц автокрана — источник ~54% побайтового
совпадения текста между соседними страницами (внешний SEO-аудит, 31.08.2026).

Таблица уже есть на /avtokrany/ (там ей и место — сравнение всех классов),
а цена ЭТОЙ страницы уже названа абзацем выше по тексту. Полная таблица здесь
не добавляет уникального смысла и разбавляет плотность собственного контента
страницы. Меняем таблицу на одну ссылку сравнения; ссылки на соседние тоннажи
по-прежнему есть в сайдбаре ("Другие грузоподъёмности").

Правит уже собранные HTML-страницы (аналог других tools/fix_*.py), а не
build_pages.py напрямую, — источник построения таблицы (`tonnage_table`)
используется и на /avtokrany/, где таблица нужна, поэтому автономный фикс
безопаснее правки общей функции.

Заодно чинит источник (data_tonnage.py уже поправлен отдельно): здесь только
патч уже готового HTML, если кто-то пересоберёт страницы без source-фикса.

Скрипт идемпотентен: если ссылка уже стоит вместо таблицы, страница
пропускается.

Запуск:  python tools/fix_tonnage_price_dup.py [--check]
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

TONNAGES = [25, 32, 40, 50, 60, 70, 90, 100, 150, 250]

TABLE_RE = re.compile(
    r'(<h2>Стоимость аренды автокрана \d+ тонн</h2><p>.*?</p>)'
    r'<div class="ptable-wrap">.*?</div>'
    r'(?=<h2>Типовые задачи</h2>)',
    re.DOTALL,
)
LINK = r'\1<p><a href="/avtokrany/">Сравнить цены по всем грузоподъёмностям →</a></p>'

INTRO_RE = re.compile(
    r'скорее всего понадобится 32 или 40 тонн\.'
)
INTRO_FIX = (
    'скорее всего понадобится '
    '<a href="/avtokrany/32-tonn/">32</a> или <a href="/avtokrany/40-tonn/">40 тонн</a>.'
)


def apply(check: bool = False) -> None:
    changed = []
    for tn in TONNAGES:
        path = ROOT / "avtokrany" / ("%d-tonn" % tn) / "index.html"
        if not path.exists():
            print("нет файла: %s" % path)
            continue
        raw = path.read_text(encoding="utf-8")
        out, n = TABLE_RE.subn(LINK, raw)
        if tn == 25:
            out, n2 = INTRO_RE.subn(INTRO_FIX, out)
            n += n2
        if n and out != raw:
            changed.append(str(path.relative_to(ROOT)))
            if not check:
                path.write_text(out, encoding="utf-8")

    if changed:
        print("%s: %d страниц" % ("изменится" if check else "изменено", len(changed)))
        for c in changed:
            print("   %s" % c)
    else:
        print("без изменений (уже применено)")


if __name__ == "__main__":
    apply(check="--check" in sys.argv)
