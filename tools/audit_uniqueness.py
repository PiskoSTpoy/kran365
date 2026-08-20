# -*- coding: utf-8 -*-
"""
Сквозной аудит сайта на клоны и типовые SEO-дефекты.

Проверяет по всем собранным страницам:
  • схожесть основного текста между всеми парами страниц (шинглы, не просто словарь);
  • объём основного текста — ищет оставшиеся «тонкие» страницы;
  • дубликаты title и description;
  • битые внутренние ссылки;
  • соответствие sitemap.xml фактическим страницам.

Запуск:  python tools/audit_uniqueness.py
"""
import os, re, io, sys, itertools

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

THIN_WORDS = 300          # порог «тонкой» страницы
SIMILAR = 0.25            # порог схожести по шинглам, выше — подозрение на клон


def read(p):
    return io.open(p, encoding="utf-8").read()


def collect():
    """Все страницы сайта: путь → (url, html)."""
    out = {}
    for dirpath, dirnames, files in os.walk(ROOT):
        if ".git" in dirpath or "tools" in dirpath:
            continue
        for f in files:
            if not f.endswith(".html"):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            url = "/" + rel[:-len("index.html")] if rel.endswith("index.html") else "/" + rel
            out[url] = read(full)
    return out


def main_text(html):
    """Основной текст страницы — без шапки, футера, форм и перелинковки."""
    m = re.search(r'<div class="prose reveal">(.*?)</div>\s*<aside', html, re.S)
    if not m:
        m = re.search(r"<main>(.*?)</main>", html, re.S)
        if not m:
            return ""
    body = m.group(1)
    body = re.sub(r'<div class="related".*', "", body, flags=re.S)   # блоки перелинковки
    body = re.sub(r"<script.*?</script>", " ", body, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", text).strip()


def shingles(text, n=4):
    """Множество n-грамм: ловит переставленные шаблонные фразы, а не просто общий словарь."""
    words = re.findall(r"[А-Яа-яA-Za-z0-9ёЁ]+", text.lower())
    return {tuple(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}


def jaccard(a, b):
    return len(a & b) / len(a | b) if (a or b) else 0.0


def meta(html, name):
    m = re.search(r'<meta name="%s" content="([^"]*)"' % name, html)
    return m.group(1) if m else ""


def title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return m.group(1).strip() if m else ""


def main():
    pages = collect()
    texts = {u: main_text(h) for u, h in pages.items()}
    content = {u: t for u, t in texts.items() if len(t.split()) > 50}
    print("=" * 70)
    print("Страниц всего: %d, из них содержательных: %d" % (len(pages), len(content)))

    # --- 1. тонкие страницы
    thin = sorted(((len(t.split()), u) for u, t in content.items()))
    thin = [(n, u) for n, u in thin if n < THIN_WORDS]
    print("\n1. ТОНКИЕ СТРАНИЦЫ (< %d слов основного текста): %d" % (THIN_WORDS, len(thin)))
    for n, u in thin[:15]:
        print("   %4d сл  %s" % (n, u))
    if not thin:
        print("   нет")

    # --- 2. клоны по шинглам
    sh = {u: shingles(t) for u, t in content.items()}
    pairs = []
    for a, b in itertools.combinations(sorted(sh), 2):
        j = jaccard(sh[a], sh[b])
        if j >= SIMILAR:
            pairs.append((j, a, b))
    pairs.sort(reverse=True)
    print("\n2. ПОХОЖИЕ ПАРЫ (схожесть по 4-граммам >= %.0f%%): %d из %d пар" % (
        SIMILAR * 100, len(pairs), len(content) * (len(content) - 1) // 2))
    for j, a, b in pairs[:15]:
        print("   %.0f%%  %s  <->  %s" % (j * 100, a, b))
    if not pairs:
        print("   нет")

    # --- 3. дубликаты title / description
    for what, fn in (("title", title), ("description", lambda h: meta(h, "description"))):
        seen = {}
        for u, h in pages.items():
            v = fn(h)
            if v:
                seen.setdefault(v, []).append(u)
        dups = {v: us for v, us in seen.items() if len(us) > 1}
        print("\n3. ДУБЛИКАТЫ %s: %d" % (what.upper(), len(dups)))
        for v, us in list(dups.items())[:5]:
            print("   «%s» — %s" % (v[:70], ", ".join(us[:3])))
        if not dups:
            print("   нет")

    # --- 4. битые внутренние ссылки
    bad = set()
    for u, h in pages.items():
        for href in re.findall(r'href="(/[^"#?]*)"', h):
            t = href.lstrip("/")
            cand = os.path.join(ROOT, t, "index.html") if not os.path.splitext(t)[1] else os.path.join(ROOT, t)
            if t and not os.path.exists(cand):
                bad.add(href)
    print("\n4. БИТЫЕ ВНУТРЕННИЕ ССЫЛКИ: %d" % len(bad))
    for b in sorted(bad)[:10]:
        print("   %s" % b)
    if not bad:
        print("   нет")

    # --- 5. sitemap
    sp = os.path.join(ROOT, "sitemap.xml")
    if os.path.exists(sp):
        urls = set(re.findall(r"<loc>https://kran365\.ru(/[^<]*)</loc>", read(sp)))
        missing = urls - set(pages)
        print("\n5. SITEMAP: %d URL, отсутствующих страниц: %d" % (len(urls), len(missing)))
        for m_ in sorted(missing)[:10]:
            print("   %s" % m_)
    print("=" * 70)


if __name__ == "__main__":
    main()
