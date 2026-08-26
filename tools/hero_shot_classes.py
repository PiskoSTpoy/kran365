# -*- coding: utf-8 -*-
"""
hero_shot_classes.py — поставить фотографию раздела в мобильный герой.

На кадрах 375×812 внутренние страницы открывались белым листом: из 172 страниц
сайта фотография была ровно на одной, на главной. Здесь мы не добавляем новых
картинок — только помечаем герой раздела классом, а какой именно снимок
подставить, решает pages.css. Пары «раздел → снимок» взяты один в один
с карточек каталога главной, чтобы на странице автовышек не оказался кран.

Запуск (из kran365_site):
    python tools/hero_shot_classes.py            # показать, что изменится
    python tools/hero_shot_classes.py --apply
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# раздел → класс снимка (сами url лежат в assets/pages.css)
SHOTS = {
    "avtokrany":          "ph-crane-100",   # Автокран Liebherr — как на главной
    "avtokrany/25-tonn":  "ph-crane-25",    # Галичанин 25 т на КамАЗ — та самая машина
    "gusenichnye-krany":  "ph-gusen",
    "bashennye-krany":    "ph-bashen",
    "manipulyatory":      "ph-manip",
    "avtovyshki":         "ph-lift",
    "ekskavatory":        "ph-exc",
    "samosvaly":          "ph-samosval",
    "traly":              "ph-tral",
}

MARK = 'class="page-hero"'


def main() -> int:
    apply = "--apply" in sys.argv
    changed = skipped = 0
    for rel, cls in SHOTS.items():
        f = ROOT / rel / "index.html"
        if not f.exists():
            print(f"нет файла: {rel}")
            continue
        html = f.read_text(encoding="utf-8")
        if f'page-hero--shot {cls}' in html:
            print(f"уже стоит: /{rel}/")
            skipped += 1
            continue
        if html.count(MARK) != 1:
            print(f"пропуск (героев {html.count(MARK)}): /{rel}/")
            skipped += 1
            continue
        new = html.replace(MARK, f'class="page-hero page-hero--shot {cls}"', 1)
        print(f"{'пишу' if apply else 'будет'}: /{rel}/ → {cls}")
        if apply:
            f.write_text(new, encoding="utf-8")
        changed += 1
    print(f"\nизменено: {changed}, пропущено: {skipped}"
          + ("" if apply else "  (пробный прогон, добавьте --apply)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
