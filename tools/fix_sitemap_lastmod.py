"""Честный lastmod в карте сайта — по дате, когда менялось содержимое страницы.

Раньше генератор ставил всем 169 страницам дату сборки. Одинаковая дата у всего
домена — это не сигнал: Google учитывает lastmod, только пока тот последовательно
и проверяемо точен, а «сегодня у всех» проверку не проходит и обесценивает
сигнал для всего сайта разом.

Источник даты — git-история. Но брать `git log -1` по файлу нельзя: массовая
правка разметки (businessFunction, @id организации, размеры пикселя счётчика)
трогает почти все файлы разом и снова красит карту в один день. Для читателя
такая страница не изменилась. Поэтому дата берётся по последнему коммиту, в
котором изменилось ВИДИМОЕ содержимое: текст страницы, заголовки и <title>.
Правки в JSON-LD, meta и атрибутах на дату не влияют.

Страницы, которой в истории нет вообще, lastmod не достаётся: пустой элемент
честнее выдуманной даты.

Запуск:  python tools/fix_sitemap_lastmod.py [--check]
"""
from __future__ import annotations

import hashlib
import html
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://kran365.ru"

DROP_BLOCKS = re.compile(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>")
VISIBLE_HEAD = re.compile(r"(?is)<title>(.*?)</title>")
BODY = re.compile(r"(?is)<body[^>]*>(.*?)</body>")
TAGS = re.compile(r"<[^>]+>")

# Обвязка, одинаковая на всех страницах: шапка, меню, хлебные крошки, форма
# в правой колонке, баннер призыва и подвал. Google прямо пишет, что правка
# шаблонных блоков — не повод менять lastmod, и это не формальность: когда
# в подвал добавили ссылку на политику, «изменились» разом все 172 страницы,
# хотя ни на одной не поменялось ни слова о технике.
BOILERPLATE_TAGS = ("header", "footer", "aside", "nav")
BOILERPLATE_BLOCKS = (('section', 'class="cta"'), ('div', 'class="fab"'))


def strip_element(raw: str, tag: str, start: int) -> str:
    """Вырезать элемент вместе с содержимым, считая вложенность одноимённых тегов."""
    depth, pos = 0, start
    open_re = re.compile(r"(?i)<%s\b" % tag)
    close_re = re.compile(r"(?i)</%s\s*>" % tag)
    while pos < len(raw):
        o = open_re.search(raw, pos)
        c = close_re.search(raw, pos)
        if c is None:
            return raw[:start]
        if o is not None and o.start() < c.start():
            depth += 1
            pos = o.end()
            continue
        depth -= 1
        pos = c.end()
        if depth == 0:
            return raw[:start] + raw[pos:]
    return raw[:start]


def drop_boilerplate(raw: str) -> str:
    for tag in BOILERPLATE_TAGS:
        while (m := re.search(r"(?i)<%s\b" % tag, raw)) is not None:
            raw = strip_element(raw, tag, m.start())
    for tag, marker in BOILERPLATE_BLOCKS:
        while (m := re.search(r'(?i)<%s [^>]*%s' % (tag, re.escape(marker)), raw)) is not None:
            raw = strip_element(raw, tag, m.start())
    return raw


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, encoding="utf-8", errors="replace").stdout


def visible_hash(raw: str) -> str:
    """Отпечаток собственного содержимого страницы: <title> + текст без обвязки.

    Разметка, JSON-LD и meta выброшены: их правка страницу для человека не
    меняет. Шапка, подвал, форма и баннер — тоже: они одинаковы на всём сайте,
    и их правка не делает страницу обновлённой.
    """
    title = " ".join(VISIBLE_HEAD.findall(raw))
    body_match = BODY.search(raw)
    body = drop_boilerplate(body_match.group(1)) if body_match else ""
    text = TAGS.sub(" ", DROP_BLOCKS.sub(" ", title + " " + body))
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def read_blobs(shas: list[str]) -> dict[str, str]:
    """Достать содержимое blob-ов одним вызовом git cat-file --batch.

    Читаем БАЙТЫ: в заголовке `<sha> blob <size>` размер указан в байтах, а в
    кириллическом тексте байт и символ — разные вещи. По декодированной строке
    отрезать ровно size невозможно, и границы блобов поехали бы.
    """
    if not shas:
        return {}
    proc = subprocess.run(["git", "cat-file", "--batch"], cwd=ROOT,
                          input=("\n".join(shas) + "\n").encode("ascii"),
                          capture_output=True)
    out, pos, result = proc.stdout, 0, {}
    for sha in shas:
        nl = out.index(b"\n", pos)
        header = out[pos:nl].split()
        size = int(header[2])
        body = out[nl + 1: nl + 1 + size]
        result[sha] = body.decode("utf-8", "replace")
        pos = nl + 1 + size + 1        # +1 — перевод строки после содержимого
    return result


def content_dates() -> dict[str, str]:
    """path -> YYYY-MM-DD последнего коммита, изменившего видимое содержимое."""
    log = git("rev-list", "--reverse", "--pretty=format:%cI", "HEAD").splitlines()
    commits = [(log[i][len("commit "):], log[i + 1][:10])
               for i in range(0, len(log) - 1, 2)]

    blob_cache: dict[str, str] = {}
    last_seen: dict[str, str] = {}
    result: dict[str, str] = {}

    for sha, day in commits:
        tree = {}
        for line in git("ls-tree", "-r", sha).splitlines():
            meta, _, path = line.partition("\t")
            if path.endswith(".html"):
                tree[path] = meta.split()[2]

        # один и тот же blob переходит из коммита в коммит — считаем отпечаток раз
        need = sorted({b for b in tree.values() if b not in blob_cache})
        for blob, raw in read_blobs(need).items():
            blob_cache[blob] = visible_hash(raw)

        for path, blob in tree.items():
            h = blob_cache[blob]
            if last_seen.get(path) != h:
                last_seen[path] = h
                result[path] = day

    return result


def url_for(path: str) -> str:
    return "/" + path[: -len("index.html")] if path.endswith("index.html") else "/" + path


def apply(check: bool = False, quiet: bool = False) -> None:
    sitemap = ROOT / "sitemap.xml"
    raw = sitemap.read_text(encoding="utf-8")
    dates = content_dates()
    by_url = {url_for(p): d for p, d in dates.items()}

    missing: list[str] = []

    def repl(m: re.Match[str]) -> str:
        loc = m.group("loc")
        url = loc[len(SITE):] or "/"
        date = by_url.get(url)
        if not date:
            missing.append(url)
            return "<url><loc>%s</loc></url>" % loc
        return "<url><loc>%s</loc><lastmod>%s</lastmod></url>" % (loc, date)

    out = re.sub(r"<url><loc>(?P<loc>[^<]+)</loc>(?:<lastmod>[^<]*</lastmod>)?</url>",
                 repl, raw)

    spread: dict[str, int] = {}
    for d in re.findall(r"<lastmod>([^<]+)</lastmod>", out):
        spread[d] = spread.get(d, 0) + 1

    if not quiet:
        print("дат в карте: %d разных" % len(spread))
        for d in sorted(spread):
            print("   %s — %d стр." % (d, spread[d]))
        if missing:
            print("без lastmod (нет в истории): %d — %s"
                  % (len(missing), ", ".join(missing[:5])))

    if not check and out != raw:
        sitemap.write_text(out, encoding="utf-8")
        if not quiet:
            print("sitemap.xml обновлён")


if __name__ == "__main__":
    apply(check="--check" in sys.argv)
