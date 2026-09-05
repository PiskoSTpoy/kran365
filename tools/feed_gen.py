# -*- coding: utf-8 -*-
"""
RSS-лента блога для Дзена (дзен.ru/help/ru/website/rss-modify.html).

ИСТОЧНИК ДАННЫХ — тот же, что у build_pages.py: BLOG_BASE + BLOG_RF.
Ничего не дублируется и не переписывается — правишь статью в data_blog_base.py
или data_rf.py, прогоняешь build_pages.py (сайт) и этот скрипт (лента),
оба берут один и тот же текст.

ДАТЫ — не выдуманы и не хардкожены. Для каждой статьи дата берётся
автоматически: `git log -S"'<slug>'"` находит коммит, которым строка-слаг
впервые попала в data_blog_base.py/data_rf.py — то есть момент, когда
именно ЭТА статья реально появилась на сайте. Не дата сборки (она сегодня
у всех одна и та же и ничего не говорит о свежести) и не единая дата на
всю группу файлов — у каждого слага своя, выведенная из истории, а не
проставленная вручную по батчам. Добавишь новую статью в один из data_*.py
— её дата в ленте посчитается сама при следующем запуске скрипта.

КАРТИНКИ. Требование Дзена — минимум 700 px по ширине. У части фото сайта
(crane-25/100/500, manip-7, excloader, lift-28, tral, samosval, obj-5/6) —
650 px, ниже порога. Для них скрипт делает увеличенную копию в
assets/img/dzen/ (тот же приём, что уже проверен на конвейере AG_LOFT_full:
tools/build.py::_dzen_cover). Фото не заменяются на общие — у каждой статьи
своя, тематически точная картинка из уже отснятых на сайте, просто с копией
нужного размера для Дзена.

ТАБЛИЦЫ. Дзен внутри content:encoded поддерживает только p/a/b/i/u/s/
h1-h4/blockquote/ul/li/ol/figure/img/video — тегов table в списке нет.
7 статей из 22 используют _table() (data_blog_base.py). Не убирать данные и
не выдумывать текст взамен: конвертируем таблицу построчно в маркированный
список («Вылет 5 м — Кран 25 т: 16 т, Кран 50 т: 35 т, ...»), это тот же
набор цифр в поддерживаемой Дзеном разметке.
"""
import html
import os
import re
import subprocess
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from data_blog_base import BLOG_BASE
from data_rf import BLOG_RF
from data_blog_new import BLOG_NEW
from data_blog_seo_batch1 import BLOG_SEO_BATCH1
from data_blog_daily_20260902 import BLOG_DAILY_20260902
from data_blog_daily_20260903 import BLOG_DAILY_20260903
from data_blog_daily_20260904 import BLOG_DAILY_20260904
from data_blog_daily_20260905 import BLOG_DAILY_20260905

SITE = "https://kran365.ru"
IMG_DIR = os.path.join(ROOT, "assets", "img")
DZEN_IMG_DIR = os.path.join(IMG_DIR, "dzen")
MIN_WIDTH = 700

BLOG = list(BLOG_BASE) + BLOG_RF + BLOG_NEW + BLOG_SEO_BATCH1 + BLOG_DAILY_20260902 + BLOG_DAILY_20260903 + BLOG_DAILY_20260904 + BLOG_DAILY_20260905

_DATE_FILES = ["tools/data_blog_base.py", "tools/data_rf.py", "tools/data_blog_new.py", "tools/data_blog_seo_batch1.py", "tools/data_blog_daily_20260902.py", "tools/data_blog_daily_20260903.py", "tools/data_blog_daily_20260904.py", "tools/data_blog_daily_20260905.py"]


def _first_commit_date(slug):
    """Дата коммита, которым слаг-статья впервые попала в один из data_*.py.
    Разные файлы оформляют строки в разной кавычке ('..' vs "..") — пробуем
    обе. Если git недоступен (например, скрипт запущен вне репозитория) —
    явная ошибка, а не тихая заглушка: дата не должна тихо стать сегодняшней."""
    for q in ("'", '"'):
        try:
            out = subprocess.run(
                ["git", "log", "--format=%aI", "--reverse", "-S%s%s%s" % (q, slug, q), "--"] + _DATE_FILES,
                cwd=ROOT, capture_output=True, text=True, check=True,
            ).stdout.strip()
        except subprocess.CalledProcessError:
            continue
        if out:
            return out.splitlines()[0][:10]
    raise RuntimeError(
        "feed_gen: не нашёл дату первого коммита для '%s' ни в одной кавычке — "
        "проверь, что статья реально сохранена в data_blog_base.py/data_rf.py "
        "и закоммичена." % slug
    )


# Дата = дата коммита, которым КОНКРЕТНО эта статья реально попала на сайт
# (см. докстринг наверху) — не единая дата на группу, посчитана автоматически.
PUB_DATE = {slug: _first_commit_date(slug) for slug, *_ in BLOG}

# Тематическая картинка на статью — все файлы реально существуют в assets/img,
# ничего не сгенерировано и не взято со стороны.
IMG_MAP = {
    "kak-vybrat-avtokran": "crane-100.jpg",
    "skolko-stoit-arenda-krana": "crane-100.jpg",
    "kran-ili-manipulyator": "manip-7.jpg",
    "podgotovka-ploshchadki": "obj-1.jpg",
    "vyvoz-grunta-kak-schitat": "samosval.jpg",
    "arenda-na-mesyac": "obj-2.jpg",
    "arenda-avtokrana-50-tonn": "crane-100.jpg",
    "razreshenie-na-rabotu-krana-moskva": "obj-3.jpg",
    "ppr-na-kran-kto-sostavlyaet": "obj-4.jpg",
    "gruzovaya-harakteristika-avtokrana": "crane-25.jpg",
    "arenda-krana-zimoy": "crane-100.jpg",
    "stropalshik-i-takelazh": "obj-5.jpg",
    "montazh-metallokonstrukciy-avtokranom": "crane-25.jpg",
    "arenda-gusenichnogo-krana": "gusenichnyj.jpg",
    "bashennyy-kran-arenda-montazh-demontazh": "bashennyj.jpg",
    "avtovyshka-arenda-vysota-teleskop-ili-kolenchataya": "lift-28.jpg",
    "yamobur-burilno-kranovaya-mashina-zadachi-raschet": "obj-6.jpg",
    "arenda-manipulyatora-gruzopodemnost-borta-i-strely": "manip-7.jpg",
    "razgruzka-fury-manipulyatorom": "manip-7.jpg",
    "perevozka-negabarita-tralom": "tral.jpg",
    "arenda-ekskavatora-pogruzchika": "excloader.jpg",
    "dogovor-arendy-spectehniki-s-ekipazhem": "obj-1.jpg",
    "kran-u-lep-ohrannaya-zona": "crane-25.jpg",
    "zayavki-na-tehniku-teryayutsya-v-chatah": "obj-2.jpg",
    "uchet-topliva-brigady-spectehniki": "obj-3.jpg",
    "kran-dlya-montazha-opor-osveshheniya": "crane-25.jpg",
    "dostavka-bytovki-manipulyatorom-cena": "manip-7.jpg",
    "avtovyshka-spil-vysokih-derevev": "lift-28.jpg",
    "podyom-vanny-kranom-na-etazh": "obj-4.jpg",
    "kran-dlya-ustanovki-bilborda": "crane-25.jpg",
    "evakuaciya-spectehniki-manipulyatorom": "manip-7.jpg",
    "uborka-snega-pogruzchikom-dvor": "excloader.jpg",
    "avtokran-srochno-segodnya-moskva": "crane-100.jpg",
    "razgruzka-plit-perekrytiya-kranom": "crane-25.jpg",
    "montazh-lestnichnyh-marshey-kranom": "crane-25.jpg",
    "montazh-ktp-kranom": "crane-25.jpg",
    "kran-dlya-ustanovki-gazgoldera": "manip-7.jpg",
}

DAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def esc(s):
    return html.escape(str(s), quote=True)


def rfc822(iso_date):
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    # 09:00 — рабочее время публикации, не полночь; секунд/часов реальных
    # не было (это не пост в соцсети с точным временем), поэтому фиксируем
    # один и тот же условный час для всех, а не выдумываем разные.
    return "%s, %02d %s %d 09:00:00 +0300" % (
        DAYS_EN[dt.weekday()], dt.day, MONTHS_EN[dt.month - 1], dt.year
    )


def dzen_cover(filename):
    """Абсолютный URL картинки ≥700px. Меньшие — увеличенная копия в img/dzen/."""
    src = os.path.join(IMG_DIR, filename)
    try:
        from PIL import Image
        im = Image.open(src)
        if im.width >= MIN_WIDTH:
            return SITE + "/assets/img/" + filename
        os.makedirs(DZEN_IMG_DIR, exist_ok=True)
        out = os.path.join(DZEN_IMG_DIR, filename)
        im = im.convert("RGB")
        new_h = int(im.height * MIN_WIDTH / im.width)
        im = im.resize((MIN_WIDTH, new_h))
        im.save(out, "JPEG", quality=88)
        return SITE + "/assets/img/dzen/" + filename
    except Exception as e:
        print("dzen_cover: не смог обработать", filename, "-", e, file=sys.stderr)
        return SITE + "/assets/img/" + filename


_TABLE_RE = re.compile(
    r'<div class="ptable-wrap"><table class="ptable"><thead><tr>(.*?)</tr></thead>'
    r'<tbody>(.*?)</tbody></table></div>',
    re.S,
)
_CELL_RE = re.compile(r"<t[hd]>(.*?)</t[hd]>", re.S)
_ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)


def table_to_dzen(block_html):
    """<table> → <ul><li>·</li></ul>: те же цифры, разметка, которую Дзен понимает."""
    m = _TABLE_RE.match(block_html.strip())
    if not m:
        return block_html  # не таблица (напр. уже готовый <ul> из _ul()) — не трогаем
    headers = _CELL_RE.findall(m.group(1))
    items = []
    for row in _ROW_RE.findall(m.group(2)):
        cells = _CELL_RE.findall(row)
        if not cells:
            continue
        label = cells[0]
        pairs = ", ".join("%s: %s" % (headers[i], cells[i]) for i in range(1, len(cells)) if i < len(headers))
        items.append("<li><b>%s</b> — %s</li>" % (label, pairs))
    return "<ul>%s</ul>" % "".join(items)


def render_content(slug, blocks):
    cover = dzen_cover(IMG_MAP[slug])
    parts = ["<figure><img src=\"%s\"></figure>" % cover]
    for b in blocks:
        h_, txt = b[0], b[1]
        parts.append("<h2>%s</h2><p>%s</p>" % (esc(h_), esc(txt)))
        if len(b) > 2 and b[2]:
            parts.append(table_to_dzen(b[2]))
    return "".join(parts), cover


def rss():
    items = []
    for slug, title, lead, blocks in BLOG:
        url = "%s/blog/%s/" % (SITE, slug)
        content, cover = render_content(slug, blocks)
        items.append(
            "  <item>\n"
            "    <title>%s</title>\n"
            "    <link>%s</link>\n"
            "    <guid>%s</guid>\n"
            "    <pubDate>%s</pubDate>\n"
            "    <category>native-yes</category>\n"
            "    <category>format-article</category>\n"
            "    <category>index</category>\n"
            '    <enclosure url="%s" type="image/jpeg"/>\n'
            "    <description>%s</description>\n"
            "    <content:encoded><![CDATA[%s]]></content:encoded>\n"
            "  </item>\n"
            % (esc(title), url, url, rfc822(PUB_DATE[slug]), cover, esc(lead), content)
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>\n'
        "  <title>Блог КРАН365</title>\n"
        "  <link>%s/blog/</link>\n"
        "  <description>Практические статьи об аренде спецтехники: выбор автокрана, стоимость смены, "
        "подготовка площадки, расчёт вывоза грунта.</description>\n"
        "  <language>ru</language>\n" % SITE
        + "".join(items)
        + "</channel></rss>\n"
    )


if __name__ == "__main__":
    out = rss()
    out_path = os.path.join(ROOT, "feed.xml")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)
    tables_converted = sum(
        1 for _, _, _, blocks in BLOG for b in blocks if len(b) > 2 and b[2] and "ptable-wrap" in b[2]
    )
    print("feed.xml: %d материалов, диапазон дат %s..%s, таблиц сконвертировано в список: %d" % (
        len(BLOG), min(PUB_DATE.values()), max(PUB_DATE.values()), tables_converted
    ))
