"""Заголовки колонок подвала: h4 → h3.

В документе подряд шли h2 («Назовём цену и подадим в день заявки») и сразу h4
в подвале. Пропуск уровня ломает навигацию по заголовкам: тот, кто идёт по
странице скринридером, проваливается через несуществующий h3 и теряет структуру.

Правка идёт ТОЛЬКО внутри <footer class="footer">. Собственные h4 на /rosilka/
не трогаем: там своя вёрстка коммерческого предложения со своей иерархией,
к подвалу сайта отношения не имеющая.

Основную часть страниц собирает build_pages.py — там разметка подвала уже
исправлена. Этот скрипт добирает те, что генератор не пересобирает: главную
и страницы, куда подвал копируется готовым куском.

Запуск:  python tools/fix_footer_headings.py [--check]
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import htmlio  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
FOOTER_RE = re.compile(r'<footer class="footer".*?</footer>', re.S)


def main() -> int:
    check = "--check" in sys.argv
    touched = []

    for p in sorted(ROOT.rglob("*.html")):
        src = htmlio.read(p)

        def lift(m: re.Match[str]) -> str:
            return re.sub(r"<h4>(.*?)</h4>", r"<h3>\1</h3>", m.group(0), flags=re.S)

        out = FOOTER_RE.sub(lift, src)
        if out != src:
            touched.append(p.relative_to(ROOT).as_posix())
            if not check:
                htmlio.write(p, out)

    print(("нужно поправить: " if check else "поправлено: ") + str(len(touched)))
    for t in touched[:10]:
        print("   ", t)
    return 1 if (check and touched) else 0


if __name__ == "__main__":
    raise SystemExit(main())
