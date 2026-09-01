# -*- coding: utf-8 -*-
"""
insert_mid_images.py — разбивает «стену текста» статей блога фотографиями.

Правило плотности не выдумано: замерено на реальной статье partnerkin.com
(пользователь прислал её как образец «красиво») — 5 картинок на 9651 знак
текста, разрывы между ними 437–2531, медиана ~1200 знаков. Плюс это
попадает в общий диапазон веб-редакторской практики (визуальный якорь
каждые 150–250 слов). Взято ~1300 знаков как порог.

Идемпотентно: если в файле уже есть blog-body-img--mid, статья пропускается
(перезапуск не наштампует дублей). Не трогает сам prose-текст — только
вставляет <figure> между существующими блоками по границам <h2>, и не
трогает финальный CTA-блок «Нужна техника под вашу задачу?» и всё что
после него (перелинковка).

Картинки — из уже отснятого набора assets/img/obj-1..6.jpg (объекты/работы
сайта), по кругу, а не сток и не повтор темы шапки/первой картинки статьи.

Запуск (из kran365_site):
    python tools/insert_mid_images.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(ROOT, "blog")

OBJ_POOL = ["obj-1.jpg", "obj-2.jpg", "obj-3.jpg", "obj-4.jpg", "obj-5.jpg", "obj-6.jpg"]
THRESHOLD = 1300  # знаков с последней картинки, после которых вставляем следующую
CTA_MARKER = "<h2>Нужна техника под вашу задачу?</h2>"


def make_figure(img, idx):
    return (
        '<figure class="blog-body-img blog-body-img--mid" data-mid="%d">'
        '<img src="/assets/img/%s" alt="" loading="lazy" width="1280" height="960">'
        '</figure>' % (idx, img)
    )


def process(path, pool_start):
    content = open(path, encoding="utf-8").read()
    if 'class="prose reveal"' not in content or "blog-body-img--mid" in content:
        return None
    m = re.search(r'(<div class="prose reveal">.*?)(%s)' % re.escape(CTA_MARKER), content, re.S)
    if not m:
        return "нет CTA-маркера"

    prose_head, cta = m.group(1), m.group(2)
    parts = re.split(r"(?=<h2>)", prose_head)
    out = [parts[0]]
    since_img = 0
    pool_i = pool_start
    inserted = 0
    for chunk in parts[1:]:
        chunk_len = len(re.sub("<[^>]+>", "", chunk))
        if since_img >= THRESHOLD:
            out.append(make_figure(OBJ_POOL[pool_i % len(OBJ_POOL)], pool_i + 1))
            pool_i += 1
            inserted += 1
            since_img = 0
        out.append(chunk)
        since_img += chunk_len

    new_content = content[: m.start()] + "".join(out) + cta + content[m.end():]
    open(path, "w", encoding="utf-8").write(new_content)
    return inserted, pool_i


def main():
    pool_i = 0
    total = 0
    for slug in sorted(os.listdir(BLOG_DIR)):
        path = os.path.join(BLOG_DIR, slug, "index.html")
        if not os.path.isfile(path):
            continue
        result = process(path, pool_i)
        if result is None:
            continue
        if isinstance(result, str):
            print("пропуск (%s):" % result, slug)
            continue
        inserted, pool_i = result
        total += inserted
        print("%s: +%d картинок в тексте" % (slug, inserted))
    print("\nвсего вставлено:", total)


if __name__ == "__main__":
    main()
