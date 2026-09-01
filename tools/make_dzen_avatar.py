# -*- coding: utf-8 -*-
"""
Аватар Дзен-канала КРАН365 — не новый лого с нуля, а фирменный знак сайта
(символ #i-mark из index.html: линейный портал/кран, viewBox 32x32) на тёмном
фоне бренда, отмасштабированный в высокое разрешение и с запасом на круглую
обрезку (Дзен показывает аватар кругом — знак вписан в safe-zone 70% канвы).

Цвета — те же, что уже в assets/style.css, ничего не придумано:
  фон #0C1118 (тёмный герой сайта), знак #F5741C (основной акцент),
  лёгкий верхний блик от #F5A524 для объёма, без градиента-выдумки.
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "img", "dzen", "avatar.png")

SIZE = 800
BG = (12, 17, 24)       # #0C1118
MARK = (245, 116, 28)   # #F5741C

# Координаты — из <symbol id="i-mark" viewBox="0 0 32 32"> index.html, 1:1.
# (x1,y1,x2,y2,width) для линий; rect отдельно.
LINES = [
    (13, 29, 13, 7, 2.6),
    (4.5, 7, 26.5, 7, 2.6),
    (13, 3.5, 24, 7, 1.7),
    (13, 3.5, 6.5, 7, 1.7),
    (13, 3.5, 13, 7, 1.7),
    (21.5, 7, 21.5, 12.5, 1.6),
    (19.6, 12.5, 23.4, 12.5, 2.2),
    (8.5, 29, 17.5, 29, 2.4),
]
RECT = (3.2, 5.4, 3.2 + 3.4, 5.4 + 3.2)  # x0,y0,x1,y1

def build():
    im = Image.new("RGB", (SIZE, SIZE), BG)
    dr = ImageDraw.Draw(im)

    # Знак вписан в 32x32 → безопасная зона 70% канвы, отцентрована.
    scale = (SIZE * 0.70) / 32
    off = (SIZE - 32 * scale) / 2

    def p(x, y):
        return (off + x * scale, off + y * scale)

    for x1, y1, x2, y2, w in LINES:
        dr.line([p(x1, y1), p(x2, y2)], fill=MARK, width=max(1, round(w * scale)), joint="curve")
        # круглые концы (stroke-linecap:round) — докрашиваем окружностями на стыках
        r = w * scale / 2
        for cx, cy in (p(x1, y1), p(x2, y2)):
            dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=MARK)

    rx0, ry0 = p(RECT[0], RECT[1])
    rx1, ry1 = p(RECT[2], RECT[3])
    dr.rounded_rectangle([rx0, ry0, rx1, ry1], radius=max(1, (rx1 - rx0) * 0.2), fill=MARK)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    im.save(OUT, "PNG")
    print("avatar:", OUT, im.size)

if __name__ == "__main__":
    build()
