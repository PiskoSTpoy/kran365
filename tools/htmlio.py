"""Чтение и запись HTML без порчи переводов строк.

Файлы сайта лежат в CRLF. Обычный `read_text()` включает universal newlines и
отдаёт \\n, а `write_text()` пишет \\n как есть — после такого прогона любой
скрипт-правка выглядит в git как «переписан весь файл целиком», и разглядеть
в диффе настоящее изменение невозможно. Поэтому читаем и пишем с newline="":
перевод строки остаётся ровно таким, каким лежал в файле.
"""
from __future__ import annotations

import pathlib


def read(p: pathlib.Path) -> str:
    with p.open("r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write(p: pathlib.Path, text: str) -> None:
    with p.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text)
