# -*- coding: utf-8 -*-
"""Массовая правка форм и правовых ссылок на kran365.ru.

Что делает на каждой HTML-странице сайта:

  1. Формы — метки полей. У всех полей ставит связанный <label for>.
     До правки 336 полей на 168 страницах были доступны только по placeholder,
     то есть для скринридера безымянны, а у зрячего подпись исчезала при вводе.
  2. Формы — honeypot. Скрытое поле-ловушка: за экраном, tabindex="-1",
     aria-hidden="true". Заполнено — значит отправляет бот.
  3. Формы — чекбокс согласия на обработку ПД: required, НЕ предзаполнен,
     рядом две раздельные ссылки — на политику и на текст согласия.
  4. Подвал — правовая строка со ссылками на контакты, политику и согласие.
     Ссылка на политику обязана быть на каждой странице, где собираются данные
     (ч. 2 ст. 18.1 152-ФЗ), а по факту — просто на каждой.
  5. Шапка — пункт «Контакты».

Скрипт идемпотентен: повторный запуск ничего не ломает, уже поправленные
страницы пропускаются. Правки точечные, по известной разметке; если разметка
формы или подвала изменится, скрипт не найдёт цель и честно об этом скажет
в сводке, а не поправит наугад.

Запуск из корня сайта:  python tools/patch_forms_legal.py
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

POLICY_URL = "/politika-obrabotki-personalnyh-dannyh/"
CONSENT_URL = "/soglasie-na-obrabotku-personalnyh-dannyh/"
CONTACTS_URL = "/kontakty/"

# Имя поля-ловушки. Правдоподобное для бота и заведомо ненужное человеку.
# Должно совпадать с селектором в assets/app.js.
HP_NAME = "site-url"

SKIP_FILES = {"google40ab8917937280f2.html", "yandex_bea79f73a34179e4.html"}


# ─────────────────────────────────────────────────────────────────────────────
# Куски разметки
# ─────────────────────────────────────────────────────────────────────────────
HONEYPOT = (
    '<div class="hp" aria-hidden="true">'
    f'<input class="hp__f" id="f-{HP_NAME}" name="{HP_NAME}" type="text" tabindex="-1" '
    'autocomplete="off" aria-hidden="true" '
    'style="position:absolute;left:-9999px;width:1px;height:1px;opacity:0"></div>'
)

CONSENT = (
    '<div class="consent">'
    '<input class="consent__box" id="f-consent" name="consent" type="checkbox" '
    'required aria-describedby="f-consent-err">'
    '<label class="consent__label" for="f-consent">'
    'Я даю согласие на обработку моих персональных данных</label>'
    '<span class="consent__docs">'
    f'<a href="{POLICY_URL}">Политика обработки данных</a>'
    f'<a href="{CONSENT_URL}">Текст согласия</a></span>'
    '<p class="consent__err" id="f-consent-err" role="alert" hidden>'
    'Чтобы отправить заявку, отметьте согласие на обработку персональных данных.</p>'
    '</div>'
)

# Метка вставленного блока: по ней скрипт понимает, что страница уже поправлена.
# Проверять по тексту ссылок нельзя — на самих правовых страницах такие ссылки
# есть и в основном тексте, скрипт решил бы, что подвал уже готов.
MARK = "<!--legal-links-->"

FOOTER_LEGAL = (
    f'\n    {MARK}<nav class="footer__legal" aria-label="Правовая информация">'
    f'<a href="{CONTACTS_URL}">Контакты</a>'
    f'<a href="{POLICY_URL}">Политика обработки персональных данных</a>'
    f'<a href="{CONSENT_URL}">Согласие на обработку персональных данных</a></nav>'
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Метки полей + ловушка + согласие в узкой форме («Быстрый расчёт»),
#    она стоит на 168 внутренних страницах и на странице контактов.
# ─────────────────────────────────────────────────────────────────────────────
ASIDE_OLD = (
    '    <div class="field"><input class="input" id="f-phone" name="phone" type="tel" '
    'placeholder="+7 (___) ___-__-__" autocomplete="tel" required></div>\n'
    '    <div class="field" style="margin-top:12px"><input class="input" id="f-comment" '
    'name="comment" type="text" placeholder="Что нужно / объект"></div>\n'
    '    <button class="btn btn--primary btn--block" type="submit" style="margin-top:12px">'
    'Получить расчёт <span class="arr">→</span></button>\n'
)

ASIDE_NEW = (
    '    <div class="field"><label for="f-phone">Ваш телефон</label>'
    '<input class="input" id="f-phone" name="phone" type="tel" '
    'placeholder="+7 (___) ___-__-__" autocomplete="tel" required></div>\n'
    '    <div class="field" style="margin-top:12px"><label for="f-comment">'
    'Что нужно и на какой объект</label>'
    '<input class="input" id="f-comment" name="comment" type="text" '
    'placeholder="Что нужно / объект"></div>\n'
    f'    {HONEYPOT}\n'
    f'    <div class="field" style="margin-top:12px">{CONSENT}</div>\n'
    '    <button class="btn btn--primary btn--block" type="submit" style="margin-top:12px">'
    'Получить расчёт <span class="arr">→</span></button>\n'
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. Широкая форма на главной. Метки у полей там уже были, не хватало ловушки,
#    чекбокса и живой ссылки: в приписке под кнопкой стоял href="#".
# ─────────────────────────────────────────────────────────────────────────────
INDEX_OLD = (
    '        <button class="btn btn--primary btn--block btn--lg" type="submit">'
    'Отправить заявку <span class="arr">→</span></button>\n'
    '        <small>Нажимая кнопку, вы соглашаетесь с <a href="#">политикой обработки '
    'персональных данных</a>.</small>\n'
)

INDEX_NEW = (
    f'        {HONEYPOT}\n'
    f'        {CONSENT}\n'
    '        <button class="btn btn--primary btn--block btn--lg" type="submit">'
    'Отправить заявку <span class="arr">→</span></button>\n'
)


# ─────────────────────────────────────────────────────────────────────────────
# Правки
# ─────────────────────────────────────────────────────────────────────────────
def patch_form(html: str, stats: Counter) -> str:
    if 'id="f-consent"' in html:
        stats["форма: уже поправлена"] += 1
        return html
    if ASIDE_OLD in html:
        stats["форма: узкая (боковая)"] += 1
        return html.replace(ASIDE_OLD, ASIDE_NEW)
    if INDEX_OLD in html:
        stats["форма: широкая (главная)"] += 1
        return html.replace(INDEX_OLD, INDEX_NEW)
    if "<form" in html:
        stats["форма: РАЗМЕТКА НЕ УЗНАНА"] += 1
    return html


def _plain_legal_row(link_style: str, wrap_style: str) -> str:
    """Правовая строка для страниц с собственным оформлением (404, «Росилка»).

    Там нет классов сайта, зато есть свои правила для <a>, поэтому стили задаём
    прямо в атрибуте — иначе ссылки унаследуют вид кнопок с той страницы.
    """
    def a(href: str, text: str) -> str:
        return f'<a href="{href}" style="{link_style}">{text}</a>'
    return (
        f'{MARK}<span style="{wrap_style}">'
        + a(CONTACTS_URL, "Контакты") + " · "
        + a(POLICY_URL, "Политика обработки персональных данных") + " · "
        + a(CONSENT_URL, "Согласие на обработку персональных данных")
        + "</span>"
    )


def patch_footer(html: str, stats: Counter) -> str:
    if MARK in html:
        stats["подвал: уже поправлен"] += 1
        return html

    # Обычный подвал сайта: правовую строку ставим над строкой копирайта.
    m = re.search(r'\n(\s*)<div class="footer__bottom">', html)
    if m:
        stats["подвал: обычный"] += 1
        return html[: m.start()] + FOOTER_LEGAL + html[m.start():]

    # Подвал коммерческого предложения «Росилка» — одна строка моноширинного текста.
    m = re.search(r"<footer>(.*?)</footer>", html, re.S)
    if m:
        stats["подвал: росилка"] += 1
        legal = _plain_legal_row(
            link_style="color:inherit;text-decoration:underline",
            wrap_style="display:block;padding:10px 0 30px",
        )
        return html[: m.end(1)] + legal + html[m.end(1):]

    # Страница 404 — подвала нет вовсе, ставим строку под блоком с телефоном.
    m = re.search(r'(<p class="b404__phone">.*?</p>)', html, re.S)
    if m:
        stats["подвал: 404"] += 1
        legal = "\n    " + _plain_legal_row(
            link_style=("display:inline;padding:0;border-radius:0;font-weight:400;"
                        "color:rgba(255,255,255,.62);text-decoration:underline"),
            wrap_style="display:block;margin-top:18px;font-size:.86rem;color:rgba(255,255,255,.4)",
        )
        return html[: m.end(1)] + legal + html[m.end(1):]

    stats["подвал: ЦЕЛЬ НЕ НАЙДЕНА"] += 1
    return html


def patch_nav(html: str, stats: Counter) -> str:
    nav = re.search(r'<nav class="nav__links".*?</nav>', html, re.S)
    if nav and CONTACTS_URL in nav.group(0):
        stats["шапка: уже поправлена"] += 1
        return html
    m = re.search(r'(\s*)<a class="nav__phone"', html)
    if not m:
        stats["шапка: нет (страница без меню)"] += 1
        return html
    stats["шапка: добавлены Контакты"] += 1
    indent = m.group(1)
    return html[: m.start()] + indent + '<a href="/kontakty/">Контакты</a>' + html[m.start():]


def main() -> int:
    files = sorted(p for p in ROOT.rglob("*.html") if p.name not in SKIP_FILES)
    stats: Counter = Counter()
    changed = 0

    for path in files:
        src = path.read_text(encoding="utf-8")
        out = patch_nav(patch_footer(patch_form(src, stats), stats), stats)
        if out != src:
            path.write_text(out, encoding="utf-8")
            changed += 1

    print(f"страниц обработано: {len(files)}, изменено: {changed}")
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")

    bad = [k for k in stats if "НЕ УЗНАНА" in k or "НЕ НАЙДЕНА" in k]
    if bad:
        print("\nВНИМАНИЕ: разметка на части страниц не распознана — проверьте вручную:")
        for k in bad:
            print(f"  {k}: {stats[k]}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
