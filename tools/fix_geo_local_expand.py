# -*- coding: utf-8 -*-
"""Второй абзац в «Местной особенности» на 23 гео-страницах, у которых
основной текст был короче внутреннего порога сайта (300 слов основного
текста, tools/audit_uniqueness.py). Абзацы — не вода: под каждый город
свой факт, найденный через WebSearch и не пересекающийся с уже написанным
текстом (ограничение на мосту, сезонная просушка дорог, зонирование
грузового транспорта, геология конкретного района и т.п.).

Источник текста — GEO_RF_DATA[slug]["local"] в data_geo_rf.py (уже
дополнен вторым элементом списка отдельным патчем данных). Здесь только
патч уже собранного HTML — по образцу fix_tonnage_price_dup.py и
fix_hub_faq_dup.py, чтобы не гонять build_pages.py целиком.

Скрипт идемпотентен: если на странице уже два абзаца под «Местной
особенностью», страница пропускается.

Запуск:  python tools/fix_geo_local_expand.py [--check]
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from build_pages import GEO_RF_DATA, esc  # noqa: E402

SLUGS = [s for s, d in GEO_RF_DATA.items() if isinstance(d["local"], list) and len(d["local"]) == 2]


def patch_page(path: pathlib.Path, new_paragraph: str, check: bool) -> bool:
    raw = path.read_text(encoding="utf-8")
    m = re.search(r'<h2>Местная особенность</h2><p>.*?</p>', raw, re.DOTALL)
    if not m:
        print("  не нашёл блок 'Местная особенность': %s" % path)
        return False
    if raw[m.end():m.end() + 3] == "<p>":
        # уже есть второй абзац сразу после первого — считаем применённым
        return False
    insertion = "<p>%s</p>" % esc(new_paragraph)
    out = raw[:m.end()] + insertion + raw[m.end():]
    if not check:
        path.write_text(out, encoding="utf-8")
    return True


def apply(check: bool = False) -> None:
    changed = []
    for slug in SLUGS:
        path = ROOT / "geo" / slug / "index.html"
        if not path.exists():
            print("нет файла: %s" % path)
            continue
        new_paragraph = GEO_RF_DATA[slug]["local"][1]
        if patch_page(path, new_paragraph, check):
            changed.append(slug)
    if changed:
        print("%s: %d страниц — %s" % ("изменится" if check else "изменено", len(changed), ", ".join(changed)))
    else:
        print("без изменений (уже применено)")


if __name__ == "__main__":
    apply(check="--check" in sys.argv)
