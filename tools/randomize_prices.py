# -*- coding: utf-8 -*-
"""
Еженедельный ценовой дрейф ±1% — сигнал "сайт живой, цены обновляются",
не выдумка новых цифр. Настоящий источник цен — реальный прайс-лист Аркона,
захардкоженный в build_pages.py (AVTOKRAN/VYSHKI/MANIP/STRELA/EKSK/SAMOSVAL/
TYPES) — этот скрипт его НЕ трогает и НЕ переписывает.

Что делает:
1. Берёт текущий pct из price_drift.json (или 0, если файла нет).
2. Считает новый случайный pct в диапазоне [-1.00, +1.00], шаг 0.01 —
   НЕ кумулятивно от прошлого значения (иначе за много недель могло бы уйти
   за ±1% от настоящей базовой цены), а заново от базы каждый раз.
3. Записывает pct + сегодняшнюю дату в price_drift.json.
4. Обновляет PRICE_UPDATED/PRICE_UPDATED_HUMAN в build_pages.py на сегодня —
   иначе оговорка "Цены актуальны на <дата>" на сайте станет враньём
   (см. комментарий в build_pages.py рядом с PRICE_UPDATED).
5. Пересобирает сайт (build_pages.py) и RSS-ленту (feed_gen.py).
6. Коммитит и пушит в PiskoSTpoy/kran365, main.

Использование: python tools/randomize_prices.py
"""
import json
import os
import random
import subprocess
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIFT_PATH = os.path.join(ROOT, "tools", "price_drift.json")
BUILD_PAGES_PATH = os.path.join(ROOT, "tools", "build_pages.py")

MONTHS_RU = ["января", "февраля", "марта", "апреля", "мая", "июня",
             "июля", "августа", "сентября", "октября", "ноября", "декабря"]


def human_date(d):
    return "%d %s %d" % (d.day, MONTHS_RU[d.month - 1], d.year)


def main():
    today = date.today()

    # Новый случайный дрейф — НЕ кумулятивный, каждую неделю заново от базы.
    new_pct = round(random.uniform(-1.0, 1.0), 2)

    old_pct = 0.0
    if os.path.exists(DRIFT_PATH):
        with open(DRIFT_PATH, encoding="utf-8") as f:
            old_pct = json.load(f).get("pct", 0.0)

    with open(DRIFT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "pct": new_pct,
            "updated": today.isoformat(),
            "note": "Еженедельный ценовой дрейф ±1%, обновляет tools/randomize_prices.py. "
                    "pct=0 = базовые цены Аркона без изменений.",
        }, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("price_drift.json: %.2f%% -> %.2f%% (%s)" % (old_pct, new_pct, today.isoformat()))

    # PRICE_UPDATED / PRICE_UPDATED_HUMAN — иначе оговорка "цены актуальны
    # на <дата>" на сайте разойдётся с фактом (см. комментарий в файле).
    with open(BUILD_PAGES_PATH, encoding="utf-8") as f:
        src = f.read()

    old_line_iso = None
    new_lines = []
    for line in src.splitlines(keepends=True):
        if line.startswith("PRICE_UPDATED = "):
            old_line_iso = line
            line = 'PRICE_UPDATED = "%s"\n' % today.isoformat()
        elif line.startswith("PRICE_UPDATED_HUMAN = "):
            line = 'PRICE_UPDATED_HUMAN = "%s"\n' % human_date(today)
        new_lines.append(line)

    if old_line_iso is None:
        print("randomize_prices: не нашёл строку PRICE_UPDATED = ... в build_pages.py — "
              "формат файла изменился, останавливаюсь, ничего не трогаю.", file=sys.stderr)
        sys.exit(1)

    with open(BUILD_PAGES_PATH, "w", encoding="utf-8") as f:
        f.write("".join(new_lines))

    print("PRICE_UPDATED -> %s" % today.isoformat())

    # Пересборка
    for script in ("build_pages.py", "feed_gen.py"):
        r = subprocess.run([sys.executable, os.path.join("tools", script)], cwd=ROOT)
        if r.returncode != 0:
            print("randomize_prices: %s упал с кодом %d, останавливаюсь до коммита." %
                  (script, r.returncode), file=sys.stderr)
            sys.exit(1)

    # Коммит и пуш
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--stat"], cwd=ROOT,
                           capture_output=True, text=True).stdout
    if not diff.strip():
        print("randomize_prices: изменений нет (pct=0 совпал с прошлым?), коммит не делаю.")
        return

    msg = (
        "Еженедельный ценовой дрейф: %.2f%% (было %.2f%%)\n\n"
        "Автоматический сигнал \"сайт живой\" — сами базовые цены Аркона в "
        "build_pages.py не менялись, дрейф применяется поверх при сборке "
        "(см. tools/price_drift.json, tools/randomize_prices.py).\n"
    ) % (new_pct, old_pct)
    subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=True)
    print("Закоммичено и запушено.")


if __name__ == "__main__":
    main()
