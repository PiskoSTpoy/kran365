"""Разметка Offer и узел организации.

Две правки, обе идемпотентные:

1. `businessFunction` у Offer. Значение по умолчанию в schema.org — Sell.
   Без явного businessFunction разметка цены формально объявляет ПРОДАЖУ
   техники за эту сумму, а не аренду. Значение выбирается по смыслу страницы,
   а не подставляется одно на всех (см. PROVIDE_SERVICE ниже).

2. Общий `@id` у организации. На странице два узла LocalBusiness: верхний
   (с @id, телефоном, адресом) и вложенный `provider` внутри Service — без @id.
   Для парсера это две РАЗНЫЕ организации: одна с реквизитами, вторая пустышка
   с тем же названием. Вложенный узел заменяется ссылкой на @id верхнего,
   и обе разметки схлопываются в одну сущность.

Запуск:  python tools/fix_schema.py [--check]
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import htmlio  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
ORG_ID = "https://kran365.ru/#business"
LEASE_OUT = "https://schema.org/LeaseOut"
PROVIDE_SERVICE = "https://schema.org/ProvideService"

# ---------------------------------------------------------------------------
# Страницы, где заказчик покупает РЕЗУЛЬТАТ, а не машино-смену.
#
# Техника с оператором приезжает и уезжает, в распоряжение заказчика её не
# передают, а счёт выставляется за выполненную работу — это ProvideService.
# Всё остальное на сайте — аренда с экипажем (ГК РФ ст. 632): машина на смену
# поступает в распоряжение заказчика, он решает, что ею делать. Это LeaseOut.
#
# Отдельная группа — четыре страницы про подбор, поставку и монтаж крана,
# который остаётся у заказчика насовсем. Аренды там нет вообще, цены в Offer
# тоже нет (только priceCurrency + availability): предмет предложения —
# собственная услуга КРАН365 по подбору, организации поставки и шеф-монтажу.
# Поэтому ProvideService. Если владелец продаёт эти краны со своего склада как
# товар, значение нужно поменять на Sell — тогда линтер будет ругаться, но
# правдой будет Sell, а не LeaseOut.
# ---------------------------------------------------------------------------
PROVIDE_SERVICE_PAGES = {
    # услуги: демонтаж, монтаж, разгрузка, вывоз, установка, такелаж
    "uslugi",
    "uslugi/demontazh-zdaniy",
    "uslugi/montazh-angara",
    "uslugi/montazh-metallokonstrukciy",
    "uslugi/podem-na-kryshu",
    "uslugi/razgruzka-fur",
    "uslugi/takelazhnye-raboty",
    "uslugi/ustanovka-bytovki",
    "uslugi/ustanovka-septika",
    "uslugi/ustanovka-stolbov",
    "uslugi/vyvoz-grunta",
    # подбор + поставка + монтаж стационарного крана (не аренда)
    "kozlovye-krany",
    "kran-balki-konsolnye-krany",
    "mostovye-krany",
    "portalnye-krany",
}

LD_RE = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)


def slug(p: pathlib.Path) -> str:
    return p.parent.relative_to(ROOT).as_posix()


def business_function(page: str) -> str:
    return PROVIDE_SERVICE if page in PROVIDE_SERVICE_PAGES else LEASE_OUT


# Свойства, в которых организация упоминается второй раз: у Service это
# исполнитель, у Article — автор и издатель. Везде это одна и та же КРАН365,
# и везде она была продублирована узлом-пустышкой без @id.
ORG_REFS = {"Service": ("provider",), "Article": ("author", "publisher")}


def patch_node(node: dict, page: str) -> bool:
    """Правит один узел JSON-LD на месте. True — если что-то изменилось."""
    changed = False
    node_type = str(node.get("@type"))
    if node_type not in ORG_REFS:
        return changed

    for prop in ORG_REFS[node_type]:
        val = node.get(prop)
        if isinstance(val, dict) and val.get("@type") in ("LocalBusiness", "Organization"):
            node[prop] = {"@id": ORG_ID}
            changed = True

    if node_type != "Service":
        return changed

    offer = node.get("offers")
    if isinstance(offer, dict) and str(offer.get("@type")) == "Offer":
        want = business_function(page)
        if offer.get("businessFunction") != want:
            # businessFunction ставим первым ключом после @type: так его видно
            # глазами в исходнике, а не приходится искать в конце строки.
            rest = {k: v for k, v in offer.items() if k != "businessFunction"}
            node["offers"] = {"@type": rest.pop("@type"), "businessFunction": want, **rest}
            changed = True
    return changed


def patch_html(text: str, page: str) -> tuple[str, bool]:
    hit = False

    def repl(m: re.Match[str]) -> str:
        nonlocal hit
        open_tag, body, close_tag = m.groups()
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return m.group(0)
        nodes = data if isinstance(data, list) else [data]
        if not any(patch_node(n, page) for n in nodes if isinstance(n, dict)):
            return m.group(0)
        hit = True
        return open_tag + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + close_tag

    return LD_RE.sub(repl, text), hit


def main() -> int:
    check = "--check" in sys.argv
    touched: list[str] = []
    kinds = {LEASE_OUT: 0, PROVIDE_SERVICE: 0}

    for p in sorted(ROOT.rglob("index.html")):
        page = slug(p)
        src = htmlio.read(p)
        if '"@type":"Service"' in src.replace(" ", ""):
            kinds[business_function(page)] += 1
        out, hit = patch_html(src, page)
        if hit:
            touched.append(page)
            if not check:
                htmlio.write(p, out)

    print(f"Service-страниц: {sum(kinds.values())} "
          f"(LeaseOut {kinds[LEASE_OUT]}, ProvideService {kinds[PROVIDE_SERVICE]})")
    print(("нужно поправить: " if check else "поправлено: ") + str(len(touched)))
    return 1 if (check and touched) else 0


if __name__ == "__main__":
    raise SystemExit(main())
