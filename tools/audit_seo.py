# -*- coding: utf-8 -*-
"""
Технический и on-page SEO-аудит собранного сайта.

Проверяет то, что видно в статике: длины title/description, структуру
заголовков, alt у изображений, canonical, вес страниц, внутреннюю
перелинковку (орфаны, глубина клика от главной), микроразметку,
вес и формат картинок.

Запуск:  python tools/audit_seo.py
"""
import os, re, io, sys, json
from collections import defaultdict, deque

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TITLE_MIN, TITLE_MAX = 30, 65
DESC_MIN, DESC_MAX = 110, 165


def read(p):
    return io.open(p, encoding="utf-8").read()


def collect():
    pages = {}
    for dirpath, _, files in os.walk(ROOT):
        if ".git" in dirpath or os.sep + "tools" in dirpath:
            continue
        for f in files:
            if not f.endswith(".html"):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            if rel.startswith("google") or rel.startswith("yandex"):
                continue  # файлы верификации
            url = "/" + rel[:-len("index.html")] if rel.endswith("index.html") else "/" + rel
            pages[url] = (full, read(full))
    return pages


def tag(html, pattern, group=1):
    m = re.search(pattern, html, re.S | re.I)
    return m.group(group).strip() if m else None


def main():
    pages = collect()
    print("=" * 72)
    print("SEO-АУДИТ kran365.ru — %d страниц" % len(pages))
    print("=" * 72)

    # ---------- 1. TITLE / DESCRIPTION ----------
    long_t, short_t, long_d, short_d, no_d = [], [], [], [], []
    for u, (p, h) in pages.items():
        t = tag(h, r"<title>(.*?)</title>") or ""
        d = tag(h, r'<meta name="description" content="([^"]*)"') or ""
        if len(t) > TITLE_MAX: long_t.append((len(t), u))
        if 0 < len(t) < TITLE_MIN: short_t.append((len(t), u))
        if not d: no_d.append(u)
        elif len(d) > DESC_MAX: long_d.append((len(d), u))
        elif len(d) < DESC_MIN: short_d.append((len(d), u))

    print("\n[1] TITLE и DESCRIPTION")
    print("  title длиннее %d симв. (обрежется в выдаче): %d" % (TITLE_MAX, len(long_t)))
    for n, u in sorted(long_t, reverse=True)[:5]:
        print("      %3d  %s" % (n, u))
    print("  title короче %d: %d" % (TITLE_MIN, len(short_t)))
    print("  description длиннее %d: %d" % (DESC_MAX, len(long_d)))
    for n, u in sorted(long_d, reverse=True)[:5]:
        print("      %3d  %s" % (n, u))
    print("  description короче %d: %d | без description: %d" % (DESC_MIN, len(short_d), len(no_d)))

    # ---------- 2. ЗАГОЛОВКИ ----------
    no_h1, many_h1, skips = [], [], []
    for u, (p, h) in pages.items():
        body = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", h, flags=re.S | re.I)
        h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", body, re.S | re.I)
        if not h1: no_h1.append(u)
        elif len(h1) > 1: many_h1.append((len(h1), u))
        levels = [int(x) for x in re.findall(r"<h([1-6])\b", body, re.I)]
        for a, b in zip(levels, levels[1:]):
            if b - a > 1:
                skips.append((u, "h%d→h%d" % (a, b)))
                break

    print("\n[2] СТРУКТУРА ЗАГОЛОВКОВ")
    print("  без H1: %d | несколько H1: %d | пропуск уровня: %d" % (len(no_h1), len(many_h1), len(skips)))
    for u in no_h1[:5]: print("      нет H1: %s" % u)
    for u, s in skips[:5]: print("      %s  %s" % (s, u))

    # ---------- 3. КАРТИНКИ ----------
    no_alt, empty_alt, total_img = [], [], 0
    for u, (p, h) in pages.items():
        for img in re.findall(r"<img\b[^>]*>", h, re.I):
            total_img += 1
            m = re.search(r'alt="([^"]*)"', img)
            if not m: no_alt.append((u, img[:70]))
            elif not m.group(1).strip(): empty_alt.append(u)
    print("\n[3] ИЗОБРАЖЕНИЯ")
    print("  всего <img>: %d | без alt: %d | пустой alt: %d" % (total_img, len(no_alt), len(empty_alt)))
    for u, s in no_alt[:5]: print("      %s  %s" % (u, s))

    # ---------- 4. CANONICAL ----------
    no_can, wrong_can = [], []
    for u, (p, h) in pages.items():
        c = tag(h, r'<link rel="canonical" href="([^"]*)"')
        if not c: no_can.append(u)
        else:
            expect = "https://kran365.ru" + u
            if c.rstrip("/") != expect.rstrip("/"): wrong_can.append((u, c))
    print("\n[4] CANONICAL")
    print("  без canonical: %d | не self-canonical: %d" % (len(no_can), len(wrong_can)))
    for u in no_can[:8]: print("      нет: %s" % u)
    for u, c in wrong_can[:5]: print("      %s -> %s" % (u, c))

    # ---------- 5. МИКРОРАЗМЕТКА ----------
    types_count = defaultdict(int)
    no_ld = []
    for u, (p, h) in pages.items():
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
        if not blocks:
            no_ld.append(u); continue
        for b in blocks:
            try:
                obj = json.loads(b)
            except Exception:
                types_count["!невалидный JSON"] += 1
                continue
            for o in (obj if isinstance(obj, list) else [obj]):
                types_count[o.get("@type", "?")] += 1
    print("\n[5] МИКРОРАЗМЕТКА (JSON-LD)")
    print("  страниц без разметки: %d" % len(no_ld))
    for u in no_ld[:5]: print("      %s" % u)
    for t, n in sorted(types_count.items(), key=lambda x: -x[1]):
        print("      %-18s %d" % (t, n))

    # ---------- 6. ВЕС СТРАНИЦ ----------
    sizes = sorted(((os.path.getsize(p), u) for u, (p, _) in pages.items()), reverse=True)
    print("\n[6] ВЕС HTML")
    print("  средний: %.0f КБ | самые тяжёлые:" % (sum(s for s, _ in sizes) / len(sizes) / 1024))
    for s, u in sizes[:5]:
        print("      %5.0f КБ  %s" % (s / 1024, u))

    # ---------- 7. ПЕРЕЛИНКОВКА ----------
    graph, inbound = {}, defaultdict(set)
    for u, (p, h) in pages.items():
        links = set()
        for href in re.findall(r'href="(/[^"#?]*)"', h):
            t = href if href.endswith("/") or "." in href.rsplit("/", 1)[-1] else href + "/"
            if t in pages: links.add(t)
        graph[u] = links
        for l in links:
            if l != u: inbound[l].add(u)

    orphans = [u for u in pages if not inbound[u] and u != "/"]
    depth = {"/": 0}
    q = deque(["/"])
    while q:
        cur = q.popleft()
        for nxt in graph.get(cur, ()):
            if nxt not in depth:
                depth[nxt] = depth[cur] + 1
                q.append(nxt)
    unreachable = [u for u in pages if u not in depth]
    deep = sorted(((d, u) for u, d in depth.items() if d >= 3), reverse=True)
    weak = sorted(((len(inbound[u]), u) for u in pages if u != "/"))[:8]

    print("\n[7] ВНУТРЕННЯЯ ПЕРЕЛИНКОВКА")
    print("  страниц-сирот (нет входящих ссылок): %d" % len(orphans))
    for u in orphans[:8]: print("      %s" % u)
    print("  недостижимо с главной по ссылкам: %d" % len(unreachable))
    for u in unreachable[:8]: print("      %s" % u)
    print("  глубина >= 3 клика: %d" % len(deep))
    for d, u in deep[:5]: print("      %d клика  %s" % (d, u))
    print("  меньше всего входящих ссылок:")
    for n, u in weak: print("      %2d  %s" % (n, u))

    # ---------- 8. РЕСУРСЫ ----------
    print("\n[8] СТАТИЧЕСКИЕ РЕСУРСЫ")
    img_dir = os.path.join(ROOT, "assets", "img")
    if os.path.isdir(img_dir):
        imgs = []
        for f in os.listdir(img_dir):
            fp = os.path.join(img_dir, f)
            if os.path.isfile(fp): imgs.append((os.path.getsize(fp), f))
        imgs.sort(reverse=True)
        total = sum(s for s, _ in imgs)
        webp = sum(1 for _, f in imgs if f.lower().endswith((".webp", ".avif")))
        print("  картинок: %d, суммарно %.1f МБ, в webp/avif: %d" % (len(imgs), total / 1048576, webp))
        for s, f in imgs[:6]:
            print("      %6.0f КБ  %s" % (s / 1024, f))
    print("=" * 72)


if __name__ == "__main__":
    main()
