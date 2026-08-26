"""width/height у изображений — чтобы браузер знал размер до загрузки.

Делает две вещи:

1. Сверяет width/height у КАЖДОГО локального <img> с реальным размером файла
   на диске. Не «проставляет по памяти», а открывает картинку и меряет.
   Расхождение — это тоже сдвиг макета, только незаметный в разметке.

2. Проставляет размеры счётчику Яндекс.Метрики. Все 172 изображения без
   width/height на сайте — это один и тот же пиксель счётчика из <noscript>.
   Он лежит в потоке абсолютно спозиционированным за экраном (left:-9999px),
   то есть на макет не влияет и CLS не давал никогда. Атрибуты ставятся,
   потому что размер пикселя счётчика — действительно 1×1, и разметка должна
   это говорить; выигрыша в CLS от этой правки ждать не нужно.

Запуск:  python tools/fix_img_dims.py [--check]
"""
from __future__ import annotations

import pathlib
import re
import sys

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import htmlio  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Пиксель счётчика Метрики: ровно та строка, что стоит на 172 страницах.
COUNTER_OLD = ('<img src="https://mc.yandex.ru/watch/111188532" '
               'style="position:absolute; left:-9999px;" alt="" />')
COUNTER_NEW = ('<img src="https://mc.yandex.ru/watch/111188532" width="1" height="1" '
               'style="position:absolute; left:-9999px;" alt="" />')

IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
ATTR_RE = re.compile(r'(\w[\w-]*)\s*=\s*"([^"]*)"')
# <picture> с webp-источником: сверять надо с тем файлом, который браузер
# реально возьмёт, а не с jpg-подложкой для тех, кто webp не умеет.
PICTURE_RE = re.compile(r"<picture>(.*?)</picture>", re.I | re.S)
SOURCE_RE = re.compile(r'<source\b[^>]*srcset="([^"]+)"', re.I)

_measured: dict[pathlib.Path, tuple[int, int]] = {}


def measure(path: pathlib.Path) -> tuple[int, int] | None:
    if path not in _measured:
        try:
            with Image.open(path) as im:
                _measured[path] = im.size
        except Exception:  # noqa: BLE001 — нет файла или не картинка
            return None
    return _measured[path]


def _served_sources(html: str, tag: str) -> list[str]:
    """Файлы-кандидаты для этого <img>: сначала <source> своего <picture>, потом src."""
    for block in PICTURE_RE.findall(html):
        if tag in block:
            return SOURCE_RE.findall(block) + [dict(ATTR_RE.findall(tag)).get("src", "")]
    return [dict(ATTR_RE.findall(tag)).get("src", "")]


def audit_local_images() -> list[str]:
    """Расхождения между разметкой и реальными файлами.

    CLS определяется соотношением сторон: браузер резервирует место по
    width/height как по пропорции, а не по абсолютным пикселям. Поэтому
    ругаемся, когда пропорция в разметке расходится с пропорцией файла —
    именно это двигает макет. Разные абсолютные размеры webp и jpg внутри
    одного <picture> — норма и к сдвигу не ведут.
    """
    problems: list[str] = []
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT).as_posix()
        html = htmlio.read(p)
        for tag in IMG_RE.findall(html):
            attrs = dict(ATTR_RE.findall(tag))
            src = attrs.get("src", "")
            if not src or src.startswith(("http://", "https://", "data:")):
                continue
            w, h = attrs.get("width"), attrs.get("height")
            if not w or not h:
                problems.append(f"{rel}: нет width/height — {src}")
                continue
            declared = int(w) / int(h)
            for cand in _served_sources(html, tag):
                if not cand or cand.startswith(("http://", "https://", "data:")):
                    continue
                target = (ROOT / cand.lstrip("/")) if cand.startswith("/") else (p.parent / cand)
                real = measure(target.resolve())
                if real is None:
                    problems.append(f"{rel}: файл не найден — {cand}")
                    continue
                if abs(declared - real[0] / real[1]) > 0.01:
                    problems.append(
                        f"{rel}: пропорция в разметке {w}x{h} ({declared:.3f}) "
                        f"не совпадает с файлом {real[0]}x{real[1]} "
                        f"({real[0] / real[1]:.3f}) — {cand}")
    return problems


def main() -> int:
    check = "--check" in sys.argv

    problems = audit_local_images()
    print(f"локальных картинок с расхождением размеров: {len(problems)}")
    for line in problems[:20]:
        print("   ", line)

    touched = 0
    for p in sorted(ROOT.rglob("*.html")):
        src = htmlio.read(p)
        if COUNTER_OLD not in src:
            continue
        touched += 1
        if not check:
            htmlio.write(p, src.replace(COUNTER_OLD, COUNTER_NEW))

    print(("счётчик Метрики нужно поправить на: " if check else "счётчик Метрики поправлен на: ")
          + f"{touched} стр.")
    return 1 if (check and (touched or problems)) else (1 if problems else 0)


if __name__ == "__main__":
    raise SystemExit(main())
