# -*- coding: utf-8 -*-
"""
blog_hero_shot_classes.py — та же идея, что в tools/hero_shot_classes.py
(поставить фото раздела в мобильный герой), только для статей блога.

Почему отдельный скрипт, а не расширение SHOTS в hero_shot_classes.py:
у категорий (avtokrany/, gusenichnye-krany/...) снимок = сама техника этого
раздела, один в один. У статьи блога такого прямого соответствия нет —
тема шире одного класса техники ("сколько стоит аренда", "как выбрать") —
поэтому это отдельная, более мягкая карта «слаг → ближайший по теме снимок».
Ни одной новой картинки: используются те же 9 фото, что уже отсняты и
используются в каталоге техники — просто с другим списком страниц.

Запуск (из kran365_site):
    python tools/blog_hero_shot_classes.py            # что изменится
    python tools/blog_hero_shot_classes.py --apply
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# слаг статьи → класс снимка (используются только уже существующие 9 ph-*
# классов из assets/pages.css — новых картинок и CSS не добавлено)
SHOTS = {
    "kak-vybrat-avtokran": "ph-crane-100",
    "skolko-stoit-arenda-krana": "ph-crane-100",
    "kran-ili-manipulyator": "ph-manip",
    "podgotovka-ploshchadki": "ph-crane-25",
    "vyvoz-grunta-kak-schitat": "ph-samosval",
    "arenda-na-mesyac": "ph-crane-100",
    "arenda-avtokrana-50-tonn": "ph-crane-100",
    "razreshenie-na-rabotu-krana-moskva": "ph-crane-25",
    "ppr-na-kran-kto-sostavlyaet": "ph-crane-25",
    "gruzovaya-harakteristika-avtokrana": "ph-crane-25",
    "arenda-krana-zimoy": "ph-crane-100",
    "stropalshik-i-takelazh": "ph-crane-25",
    "montazh-metallokonstrukciy-avtokranom": "ph-crane-25",
    "arenda-gusenichnogo-krana": "ph-gusen",
    "bashennyy-kran-arenda-montazh-demontazh": "ph-bashen",
    "avtovyshka-arenda-vysota-teleskop-ili-kolenchataya": "ph-lift",
    "yamobur-burilno-kranovaya-mashina-zadachi-raschet": "ph-exc",
    "arenda-manipulyatora-gruzopodemnost-borta-i-strely": "ph-manip",
    "razgruzka-fury-manipulyatorom": "ph-manip",
    "perevozka-negabarita-tralom": "ph-tral",
    "arenda-ekskavatora-pogruzchika": "ph-exc",
    "dogovor-arendy-spectehniki-s-ekipazhem": "ph-crane-100",
}

MARK = 'class="page-hero"'


def main() -> int:
    apply = "--apply" in sys.argv
    changed = skipped = 0
    for slug, cls in SHOTS.items():
        f = ROOT / "blog" / slug / "index.html"
        if not f.exists():
            print(f"нет файла: blog/{slug}/")
            continue
        html = f.read_text(encoding="utf-8")
        if f'page-hero--shot {cls}' in html:
            print(f"уже стоит: /blog/{slug}/")
            skipped += 1
            continue
        if html.count(MARK) != 1:
            print(f"пропуск (героев {html.count(MARK)}): /blog/{slug}/")
            skipped += 1
            continue
        new = html.replace(MARK, f'class="page-hero page-hero--shot {cls}"', 1)
        print(f"{'пишу' if apply else 'будет'}: /blog/{slug}/ -> {cls}")
        if apply:
            f.write_text(new, encoding="utf-8")
        changed += 1
    print(f"\nизменено: {changed}, пропущено: {skipped}"
          + ("" if apply else "  (пробный прогон, добавьте --apply)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
