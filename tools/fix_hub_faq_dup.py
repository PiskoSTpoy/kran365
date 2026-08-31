# -*- coding: utf-8 -*-
"""FAQ на хабах техники — раньше один и тот же блок из 4 вопросов дословно
повторялся на /avtokrany/, /avtovyshki/, /manipulyatory/, /ekskavatory/,
/samosvaly/, включая разметку FAQPage (внешний SEO-аудит, 31.08.2026:
100% совпадение текста между минимум 4 страницами). Источник новых,
различающихся по видам техники вопросов — HUB_FAQS в build_pages.py;
здесь только патч уже собранного HTML (по образцу других tools/fix_*.py),
чтобы не гонять полный build_pages.py и не терять правки других скриптов
(?v=8, подпись кнопки звонка, лейблы форм и т.д. — они не в общем шаблоне,
их отдельно накатывают mobile_fab_bar.py / patch_forms_legal.py).

Правит и видимый HTML (<div class="faq">), и JSON-LD FAQPage — раздельно,
оба должны совпадать (Google сверяет видимый текст с разметкой).

Скрипт идемпотентен: если на странице уже стоит нужный текст, она
пропускается.

Запуск:  python tools/fix_hub_faq_dup.py [--check]
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from build_pages import HUB_FAQS, esc  # noqa: E402

FAQ_DIV_RE = re.compile(r'<div class="faq">.*?</div></div>', re.DOTALL)
# Внутри одной .faq-обёртки только <details> без вложенных div — но details
# сам оборачивает ответ в <div>, поэтому закрывающий паттерн — до ПЕРВОГО
# "</div></div>" после открытия не годится при нескольких вопросах (каждый
# details даёт свой </div>). Матчим честно: <div class="faq"> и всё до
# закрывающего тега того же уровня — количество </details> известно заранее.


def faq_html(faqs):
    rows = "".join('<details><summary>%s</summary><div>%s</div></details>' % (esc(q), esc(a)) for q, a in faqs)
    return '<div class="faq">%s</div>' % rows


def faq_ld_json(faqs):
    obj = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs
    ]}
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def patch_page(path: pathlib.Path, faqs, check: bool) -> bool:
    raw = path.read_text(encoding="utf-8")
    out = raw

    # 1) видимый блок — считаем details по количеству открывающих тегов,
    # чтобы не зависеть от точного числа вопросов в старом контенте.
    m = re.search(r'<h2>Частые вопросы</h2><div class="faq">', out)
    if not m:
        print("  не нашёл блок FAQ: %s" % path)
        return False
    start = m.end() - len('<div class="faq">')
    # ищем закрывающий </div> самого .faq — считаем баланс <details>/</details>
    pos = m.end()
    depth = 0
    close_re = re.compile(r'<details>|</details>')
    end = None
    for dm in close_re.finditer(out, pos):
        if dm.group() == "<details>":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                end = dm.end()
                break
    if end is None:
        print("  не нашёл конец блока FAQ: %s" % path)
        return False
    # сразу после последнего </details> должен идти </div>, закрывающий .faq
    close_div = out.index("</div>", end)
    old_block = out[start:close_div + len("</div>")]
    new_block = faq_html(faqs)
    out = out[:start] + new_block + out[close_div + len("</div>"):]

    # 2) JSON-LD FAQPage
    ld_re = re.compile(r'\{"@context":"https://schema\.org","@type":"FAQPage".*?\}\]\}')
    ld_m = ld_re.search(out)
    if not ld_m:
        print("  не нашёл JSON-LD FAQPage: %s" % path)
        return False
    out = out[:ld_m.start()] + faq_ld_json(faqs) + out[ld_m.end():]

    if out == raw:
        return False
    if not check:
        path.write_text(out, encoding="utf-8")
    return True


def apply(check: bool = False) -> None:
    changed = []
    for slug in HUB_FAQS:
        path = ROOT / slug / "index.html"
        if not path.exists():
            print("нет файла: %s" % path)
            continue
        if patch_page(path, HUB_FAQS[slug], check):
            changed.append(slug)
    if changed:
        print("%s: %d страниц — %s" % ("изменится" if check else "изменено", len(changed), ", ".join(changed)))
    else:
        print("без изменений (уже применено)")


if __name__ == "__main__":
    apply(check="--check" in sys.argv)
