# -*- coding: utf-8 -*-
"""
fix_geo_area_served.py — Service.areaServed на гео-страницах называет
конкретный город, а не общий московский дефолт.

build_pages.py собирает JSON-LD через service_ld(), у которого раньше
areaServed был жёстко зашит как "Москва и Московская область" — это
верно для главной страницы бизнеса (LocalBusiness, её не трогаем), но
неверно для Service-блока гео-страницы /geo/{city}/: serviceType там уже
называет конкретный город ("Аренда спецтехники в Воронеже"), а areaServed
противоречил ему тем же дефолтом на 43 из 44 страниц.

service_ld() в build_pages.py уже поправлен (принимает area=), но полная
пересборка build_pages.py трогает вообще все страницы и откатывает кучу
ручных пост-правок (mobile-волны, врезки картинок, кэш-баст версии и т.д.
— см. content-plan.md и rebuild_blog_hub_cards.py). Поэтому здесь —
точечный патч уже собранных geo/*/index.html по той же схеме, что и
tools/fix_schema.py: разобрать JSON-LD, поправить только узел с
"@type":"Service", записать обратно. Идемпотентно.

Название города — nom (третье поле в кортежах GEO/GEO_RF), то есть тот же
формат, что уже используется в generator'е как отображаемое имя города
(см. related_geo(): текст ссылки на другую гео-страницу — g[2], то есть
именно nom).

Запуск (из kran365_site):  python tools/fix_geo_area_served.py [--check]
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import htmlio  # noqa: E402
import build_pages  # noqa: E402 — только за данными GEO/GEO_RF, build() не вызывается

OLD_DEFAULT = "Москва и Московская область"
LD_RE = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)

# slug -> nom (именительный падеж города — тот же, что в related_geo())
CITY_NOM = {slug: nom for slug, prep, nom, route, neigh, spec in build_pages.GEO}
CITY_NOM.update({slug: nom for slug, prep, nom, route, neigh, spec in build_pages.GEO_RF})


def patch_html(text: str, nom: str) -> tuple[str, bool]:
    hit = False

    def repl(m: re.Match[str]) -> str:
        nonlocal hit
        open_tag, body, close_tag = m.groups()
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return m.group(0)
        if not isinstance(data, dict) or data.get("@type") != "Service":
            return m.group(0)
        if data.get("areaServed") == nom:
            return m.group(0)
        data["areaServed"] = nom
        hit = True
        return open_tag + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + close_tag

    return LD_RE.sub(repl, text), hit


def main() -> int:
    check = "--check" in sys.argv
    touched: list[str] = []

    for slug, nom in sorted(CITY_NOM.items()):
        path = ROOT / "geo" / slug / "index.html"
        if not path.is_file():
            print("нет файла:", path)
            continue
        src = htmlio.read(path)
        out, hit = patch_html(src, nom)
        if hit:
            touched.append(slug)
            if not check:
                htmlio.write(path, out)

    print(("нужно поправить: " if check else "поправлено: ") + str(len(touched)) +
          " из %d гео-страниц" % len(CITY_NOM))
    return 1 if (check and touched) else 0


if __name__ == "__main__":
    raise SystemExit(main())
