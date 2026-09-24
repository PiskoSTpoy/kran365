"""Патч под скилл seo-2026-playbook: id на H2, оглавление (TOC), строка автора+дат.

Работает так же, как fix_schema.py — принимает собранный HTML-документ в
памяти (не трогает исходные *_prose-функции) и возвращает пропатченную
строку. Правит только область <main>...</main>, поэтому не задевает
повторяющийся <h2> в футере/cta_band (они вне <main>).

Даты берутся из реальной git-истории файла (--follow, чтобы пережить
переименования): самый старый коммит по этому пути = "опубликовано", самый
новый = "обновлено" (не показывается отдельно, если совпадает с первым —
страницу с момента публикации не правили, показывать нечего). Для файла,
которого ещё не было в git (первая сборка новой страницы), доступна только
сегодняшняя дата — она ставится как "опубликовано" без "обновлено".

Запуск отдельно не предусмотрен — вызывается из build_pages.py:page().
"""
from __future__ import annotations

import datetime
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
    "я": "ya",
}


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def slugify(text: str) -> str:
    text = _strip_tags(text).lower()
    out = []
    for ch in text:
        if ch in _TRANSLIT:
            out.append(_TRANSLIT[ch])
        elif ch.isalnum() and ch.isascii():
            out.append(ch)
        else:
            out.append("-")
    slug = re.sub(r"-+", "-", "".join(out)).strip("-")
    return slug or "section"


def _git_dates(rel_path: str) -> tuple[str, str | None]:
    """(опубликовано, обновлено|None) в формате YYYY-MM-DD, из git-истории файла."""
    try:
        r = subprocess.run(
            ["git", "log", "--follow", "--format=%ad", "--date=short", "--", rel_path],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
    except Exception:
        r = None
    dates = [d.strip() for d in (r.stdout.splitlines() if r and r.returncode == 0 else []) if d.strip()]
    if not dates:
        today = datetime.date.today().isoformat()
        return today, None
    updated, published = dates[0], dates[-1]
    return published, (updated if updated != published else None)


def _fmt(iso: str) -> str:
    y, m, d = iso.split("-")
    return "%s.%s.%s" % (d, m, y)


def _meta_row_html(rel_path: str) -> str:
    published, updated = _git_dates(rel_path)
    parts = [
        "Редакция КРАН365",
        "опубликовано <time datetime=\"%s\">%s</time>" % (published, _fmt(published)),
    ]
    if updated:
        parts.append("обновлено <time datetime=\"%s\">%s</time>" % (updated, _fmt(updated)))
    return '<p class="small muted meta-row">%s</p>' % " · ".join(parts)


_H2_RE = re.compile(r"<h2(?P<attrs>[^>]*)>(?P<text>.*?)</h2>", re.S)
_LEAD_RE = re.compile(r'(<p class="lead">.*?</p>)', re.S)
_MAIN_RE = re.compile(r"(<main>)(.*?)(</main>)", re.S)


def _add_ids_and_collect(main_html: str) -> tuple[str, list[tuple[str, str]]]:
    used: set[str] = set()
    items: list[tuple[str, str]] = []

    def repl(m: re.Match) -> str:
        attrs, text = m.group("attrs"), m.group("text")
        if "id=" in attrs:
            existing = re.search(r'id="([^"]*)"', attrs)
            hid = existing.group(1) if existing else slugify(text)
        else:
            hid = slugify(text)
            base, i = hid, 2
            while hid in used:
                hid = "%s-%d" % (base, i)
                i += 1
            attrs = ' id="%s"%s' % (hid, attrs)
        used.add(hid)
        items.append((hid, _strip_tags(text).strip()))
        return "<h2%s>%s</h2>" % (attrs, text)

    return _H2_RE.sub(repl, main_html), items


def _toc_html(items: list[tuple[str, str]]) -> str:
    lis = "".join('<li><a href="#%s">%s</a></li>' % (hid, text) for hid, text in items)
    return '<nav class="toc" aria-label="Содержание"><b>Содержание</b><ol>%s</ol></nav>' % lis


def patch_html(doc: str, rel_path: str) -> tuple[str, bool]:
    m = _MAIN_RE.search(doc)
    if not m:
        return doc, False
    main_html = m.group(2)
    changed = False

    main_html, h2_items = _add_ids_and_collect(main_html)
    if h2_items:
        changed = True

    if len(h2_items) >= 3 and 'class="toc"' not in main_html:
        toc = _toc_html(h2_items)
        first_h2_pos = main_html.find("<h2")
        if first_h2_pos != -1:
            main_html = main_html[:first_h2_pos] + toc + main_html[first_h2_pos:]
            changed = True

    if "meta-row" not in main_html:
        lead_m = _LEAD_RE.search(main_html)
        if lead_m:
            row = _meta_row_html(rel_path)
            insert_at = lead_m.end(1)
            main_html = main_html[:insert_at] + row + main_html[insert_at:]
            changed = True

    if not changed:
        return doc, False
    doc = doc[: m.start(2)] + main_html + doc[m.end(2) :]
    return doc, True


if __name__ == "__main__":
    print("Вызывается из build_pages.py:page() — отдельного режима запуска нет.", file=sys.stderr)
    sys.exit(1)
