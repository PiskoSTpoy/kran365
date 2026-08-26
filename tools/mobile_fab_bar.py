# -*- coding: utf-8 -*-
"""
Мобильная волна 2026-08-26: подпись на кнопке звонка + сброс кэша стилей.

Зачем подпись. Плавающие кружки WhatsApp/Telegram/звонок на телефоне
собираются в нижнюю панель (см. блок «ПАНЕЛЬ СВЯЗИ» в assets/style.css).
В панели кнопка звонка растягивается на всю свободную ширину, и внутри
неё нужна настоящая подпись «Позвонить» — текстом в разметке, а не
через CSS content, чтобы её видели и читалки, и поиск.

Зачем ?v=7. Правки этой волны живут в style.css; без нового параметра
вернувшийся посетитель получит старый файл из кэша браузера и увидит
и кружки поверх текста, и надзаголовок под шапкой.

Запуск:  python tools/mobile_fab_bar.py [--dry]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CALL_OPEN = ('<a class="fab__call" href="tel:+79055535869" '
             'aria-label="Позвонить" title="Позвонить">')
# aria-label на ссылке уже озвучивает действие, поэтому саму подпись прячем
# от скринридера — иначе кнопка читается как «Позвонить Позвонить».
LABEL = '<b class="fab__txt" aria-hidden="true">Позвонить</b>'

CSS_SUBS = [
    ('href="assets/style.css?v=6"', 'href="assets/style.css?v=7"'),
    ('href="/assets/style.css"', 'href="/assets/style.css?v=7"'),
    ('href="assets/style.css"', 'href="assets/style.css?v=7"'),
    ('href="/assets/pages.css"', 'href="/assets/pages.css?v=7"'),
    ('href="assets/pages.css"', 'href="assets/pages.css?v=7"'),
]


# Подпись должна стоять ПОСЛЕ иконки: в панели кнопка читается как «трубка →
# Позвонить». Первая версия скрипта вставляла её сразу за открывающим тегом,
# и трубка уезжала на правый край кнопки — поэтому здесь не просто вставка,
# а нормализация: вырезаем подпись, где бы она ни стояла, и кладём перед </a>.
CALL_BLOCK = re.compile(
    r'(<a class="fab__call"[^>]*>)(.*?)(</a>)', re.DOTALL)


def _place_label(match: re.Match) -> str:
    open_tag, inner, close_tag = match.groups()
    inner = re.sub(r'<b class="fab__txt".*?</b>\s*', '', inner, flags=re.DOTALL)
    return f'{open_tag}{inner.rstrip()}{LABEL}\n  {close_tag}'


def patch(text: str) -> str:
    if '<a class="fab__call"' in text:
        text = CALL_BLOCK.sub(_place_label, text, count=1)
    for src, dst in CSS_SUBS:
        if src in text:
            text = text.replace(src, dst)
    return text


def main() -> int:
    dry = '--dry' in sys.argv
    changed = 0
    for path in sorted(ROOT.rglob('*.html')):
        old = path.read_text(encoding='utf-8')
        new = patch(old)
        if new == old:
            continue
        changed += 1
        if not dry:
            path.write_text(new, encoding='utf-8')
    print(f"{'проверено' if dry else 'обновлено'}: {changed} стр.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
