"""Release evidence for the five new records; does not modify site files."""
import concurrent.futures
import importlib.util
import json
import re
import sys
import threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit, unquote

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from data_blog_daily_20261124 import BLOG_DAILY_20261124, BLOG_EXTRA_20261124

ROOT = Path(__file__).resolve().parent.parent
OUT = Path('C:/Users/kamne/.codex/automations/kran365-daily-article/evidence-20261124')
OUT.mkdir(parents=True, exist_ok=True)
SKILL = Path('C:/Users/kamne/.agents/skills/seo-2026-playbook/scripts')
spec = importlib.util.spec_from_file_location('unique', SKILL / 'uniqueness_check.py')
unique = importlib.util.module_from_spec(spec)
spec.loader.exec_module(unique)


def source_check(row):
    slug, title, lead, blocks = row
    source = BLOG_EXTRA_20261124[slug]['sources'][0][1]
    r = requests.get(source, timeout=60)
    r.raise_for_status()
    if r.content.startswith(b'%PDF'):
        import fitz
        doc = fitz.open(stream=r.content, filetype='pdf')
        source_text = ' '.join(p.get_text() for p in doc)
    else:
        source_text = BeautifulSoup(r.content, 'html.parser').get_text(' ', strip=True)
    assert len(source_text.split()) > 100, source
    source_path = OUT / (slug + '-source.txt')
    source_path.write_text(source_text, encoding='utf-8')
    own = lead + ' ' + ' '.join(b[1] for b in blocks)
    a = unique.shingles(unique.main_text('<main>' + own + '</main>'), 8)
    b = set(unique.shingles(unique.main_text('<main>' + source_text + '</main>'), 8))
    share = len(set(a) & b) / max(1, len(set(a)))
    run = unique.longest_run(a, b, 8)
    assert share <= .08 and run < 25
    return {'slug': slug, 'source': source, 'status': r.status_code,
            'source_words': len(source_text.split()), 'shared_shingles': share,
            'longest_shared_words': run, 'body_chars': len(own), 'body_words': len(own.split())}


def page_check(row, public, browser):
    slug, title, lead, blocks = row
    path = ROOT / 'blog' / slug / 'index.html'
    url = 'https://kran365.ru/blog/' + slug + '/'
    raw = requests.get(url, timeout=40) if public else None
    if public:
        assert raw.status_code == 200, (url, raw.status_code)
        content = raw.text
    else:
        content = path.read_text(encoding='utf-8')
    soup = BeautifulSoup(content, 'html.parser')
    assert [h.get_text() for h in soup.select('h1')] == [title]
    assert soup.select_one('link[rel=canonical]')['href'] == url
    data = [json.loads(s.string) for s in soup.select('script[type="application/ld+json"]')]
    types = str(data)
    for expected in ('Article', 'FAQPage', 'BreadcrumbList'):
        assert expected in types
    assert '2026-11-24' in str(soup.select('time'))
    for a in soup.select('a[href]'):
        href = a['href']
        parsed = urlsplit(href)
        if parsed.scheme or not href.startswith('/'):
            continue
        dest = ROOT / unquote(parsed.path).lstrip('/')
        if dest.is_dir():
            dest = dest / 'index.html'
        assert dest.exists(), (slug, href)
    page = browser.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=1)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    if not public:
        page.route('**/*', lambda route: route.abort())
        def local_route(route):
            target = ROOT / unquote(urlsplit(route.request.url).path).lstrip('/')
            if target.is_dir():
                target = target / 'index.html'
            if target.exists():
                route.fulfill(path=str(target))
            else:
                route.fulfill(status=404, body='Not found')
        page.route('http://local.kran365.test/**', local_route)
    page.goto(url if public else 'http://local.kran365.test/blog/' + slug + '/', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(1500)
    page.locator('main').wait_for()
    width = page.evaluate('({viewport:innerWidth, document:document.documentElement.scrollWidth})')
    assert width['document'] <= width['viewport'], (slug, width)
    assert not errors, errors
    for y in range(0, page.evaluate('document.documentElement.scrollHeight'), 700):
        page.evaluate('(y) => scrollTo(0,y)', y)
        page.wait_for_timeout(60)
    page.evaluate('scrollTo(0,0)')
    page.wait_for_timeout(600)
    page.screenshot(path=str(OUT / (slug + ('-public' if public else '-local') + '.png')), full_page=True)
    page.screenshot(path=str(OUT / (slug + ('-public' if public else '-local') + '-top.png')))
    page.locator('.prose').first.scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    assert page.locator('.prose').first.evaluate('(e) => +getComputedStyle(e).opacity') > .9
    page.screenshot(path=str(OUT / (slug + ('-public' if public else '-local') + '-body.png')))
    page.close()
    return {'slug': slug, 'url': url, 'h1': title, 'mobile': width, 'json_ld': 'valid', 'links': 'pass'}


if __name__ == '__main__':
    public = '--public' in sys.argv
    if '--sources' in sys.argv:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            result = list(pool.map(source_check, BLOG_DAILY_20261124))
        name = 'sources'
    else:
        server = None
        if not public:
            server = ThreadingHTTPServer(('127.0.0.1', 8765), partial(SimpleHTTPRequestHandler, directory=str(ROOT)))
            threading.Thread(target=server.serve_forever, daemon=True).start()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            result = [page_check(row, public, browser) for row in BLOG_DAILY_20261124]
            browser.close()
        if server:
            server.shutdown()
        for resource in ('blog/index.html', 'sitemap.xml', 'feed.xml'):
            text = requests.get('https://kran365.ru/' + resource.replace('index.html', ''), timeout=40).text if public else (ROOT / resource).read_text(encoding='utf-8')
            for row in BLOG_DAILY_20261124:
                assert '/blog/' + row[0] + '/' in text, (resource, row[0])
        name = 'public' if public else 'local'
    (OUT / (name + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
