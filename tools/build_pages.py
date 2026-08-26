# -*- coding: utf-8 -*-
"""
Генератор внутренних SEO-страниц КРАН365.
Делает страницы: хабы типов техники, страницы автокранов по тоннажу, гео-страницы (районы/города).
Каждая страница: уникальные title/description, H1, хлебные крошки, таблица цен, FAQ,
микроразметка Schema.org (BreadcrumbList, Service+Offer, FAQPage, LocalBusiness), перелинковка.
Запуск:  python tools/build_pages.py
"""
import os, json, html, re

# Разметка чекбокса согласия, поля-ловушки и правовой строки подвала живёт
# в patch_forms_legal.py — там же, где ею правят уже существующие страницы.
# Импортируем оттуда, чтобы генератор и патчер не разошлись со временем:
# иначе после ближайшей пересборки сайт снова остался бы без согласия на ПД.
from patch_forms_legal import CONSENT, HONEYPOT, FOOTER_LEGAL, POLICY_URL, CONSENT_URL, CONTACTS_URL
import fix_schema

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://kran365.ru"
PHONE_TEL = "+79055535869"
PHONE_DISP = "+7 (905) 553-58-69"
TG = "https://t.me/usdctrc2o"
WA = "https://wa.me/79055535869"

# Яндекс.Метрика (счётчик 111188532) — на всех страницах
METRIKA = '''<!-- Yandex.Metrika counter -->
<script type="text/javascript">
(function(m,e,t,r,i,k,a){
m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
m[i].l=1*new Date();
for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
})(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=111188532', 'ym');
ym(111188532, 'init', {ssr:true, webvisor:true, clickmap:true, ecommerce:"dataLayer", accurateTrackBounce:true, trackLinks:true});
</script>
<noscript><div><img src="https://mc.yandex.ru/watch/111188532" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
<!-- /Yandex.Metrika counter -->'''

# ---------------------------------------------------------------- общие блоки
SPRITE = '''<svg width="0" height="0" style="position:absolute" aria-hidden="true">
<symbol id="i-crane" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" d="M6 21V4m0 0 13 1L6 8V4M3 21h18M6 5 4 3m8 0-6 1m6 12v3m0-3-2-1h4l-2 1Z"/></symbol>
<symbol id="i-check" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="m4 12 5 5L20 6"/></symbol>
<symbol id="i-shield" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6l-8-3Zm-3 9 2 2 4-4"/></symbol>
<symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" d="M12 7v5l3 2"/></symbol>
<symbol id="i-doc" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M14 3H6v18h12V7l-4-4Zm0 0v4h4M9 12h6M9 16h6"/></symbol>
<symbol id="i-go" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M7 17 17 7M8 7h9v9"/></symbol>
<symbol id="i-mark" viewBox="0 0 32 32"><path d="M13 29V7" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/><path d="M4.5 7h22" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/><path d="M13 3.5 24 7" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><path d="M13 3.5 6.5 7" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><path d="M13 3.5V7" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><rect x="3.2" y="5.4" width="3.4" height="3.2" rx="0.7" fill="currentColor"/><path d="M21.5 7v5.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M19.6 12.5h3.8" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><path d="M8.5 29h9" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></symbol>
</svg>'''

NAV = '''<header class="nav nav--solid" id="nav">
  <a class="brand" href="/" aria-label="КРАН365 — на главную">
    <span class="brand__mark"><svg><use href="#i-mark"/></svg></span><span class="brand__txt"><i>КРАН<b>365</b></i><small>Аренда спецтехники</small></span>
  </a>
  <nav class="nav__links" id="menu">
    <a href="/#catalog">Техника</a>
    <a href="/#live">Свободно сейчас</a>
    <a href="/#how">Как работаем</a>
    <a href="/blog/">Блог</a>
    <a href="/#geo">Зона работы</a>
    <a href="/kontakty/">Контакты</a>
    <a class="nav__phone" href="tel:%s">%s</a>
  </nav>
  <a class="nav__cta" href="#order">Заказать технику</a>
  <button class="nav__burger" id="burger" aria-label="Меню"><span></span><span></span><span></span></button>
</header>''' % (PHONE_TEL, PHONE_DISP)

FAB = '''<div class="fab">
  <a class="fab__wa" href="%s" target="_blank" rel="noopener" aria-label="Написать в WhatsApp" title="WhatsApp">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.04 2c-5.5 0-9.96 4.46-9.96 9.96 0 1.76.46 3.48 1.34 5L2 22l5.2-1.36a9.9 9.9 0 0 0 4.84 1.23h.01c5.5 0 9.96-4.46 9.96-9.96S17.54 2 12.04 2Zm0 18.2h-.01a8.2 8.2 0 0 1-4.19-1.15l-.3-.18-3.08.81.82-3-.2-.31a8.22 8.22 0 0 1-1.26-4.4c0-4.55 3.7-8.24 8.25-8.24a8.2 8.2 0 0 1 5.83 2.42 8.17 8.17 0 0 1 2.41 5.82c0 4.55-3.7 8.23-8.27 8.23Zm4.52-6.16c-.25-.12-1.47-.72-1.7-.81-.23-.08-.39-.12-.56.13-.17.25-.64.81-.78.97-.14.17-.29.19-.54.06-.25-.12-1.04-.38-1.98-1.22-.73-.65-1.23-1.46-1.37-1.7-.14-.25-.02-.38.11-.51.11-.11.25-.29.37-.43.12-.14.16-.25.25-.41.08-.17.04-.31-.02-.44-.06-.12-.56-1.35-.77-1.85-.2-.48-.41-.42-.56-.43h-.48c-.17 0-.44.06-.67.31-.23.25-.87.85-.87 2.08 0 1.23.89 2.41 1.02 2.58.12.17 1.75 2.67 4.24 3.74.59.26 1.05.41 1.41.52.59.19 1.13.16 1.55.1.47-.07 1.47-.6 1.68-1.18.21-.58.21-1.08.14-1.18-.06-.11-.23-.17-.48-.29Z"/></svg></a>
  <a class="fab__tg" href="%s" target="_blank" rel="noopener" aria-label="Написать в Telegram" title="Telegram">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21.9 4.35 18.62 20c-.24 1.1-.9 1.37-1.83.86l-5.05-3.72-2.44 2.35c-.27.27-.5.5-1.02.5l.36-5.13 9.34-8.44c.4-.36-.09-.56-.63-.2L5.8 13.02l-4.97-1.55c-1.08-.34-1.1-1.08.23-1.6l19.43-7.5c.9-.33 1.69.22 1.4 1.98z"/></svg></a>
  <a class="fab__call" href="tel:%s" aria-label="Позвонить" title="Позвонить">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M6.6 10.8a15.5 15.5 0 0 0 6.6 6.6l2.2-2.2c.3-.3.72-.4 1.1-.28 1.14.38 2.35.58 3.6.58.6 0 1.05.45 1.05 1.05V20c0 .6-.45 1.05-1.05 1.05A17.2 17.2 0 0 1 2.95 4c0-.6.45-1.05 1.05-1.05H7.5c.6 0 1.05.45 1.05 1.05 0 1.25.2 2.46.58 3.6.12.38.02.8-.28 1.1z"/></svg></a>
</div>''' % (WA, TG, PHONE_TEL)

FOOTER = '''<footer class="footer">
  <div class="wrap">
    <div class="footer__top">
      <div>
        <div class="footer__brand">КРАН<b>365</b></div>
        <p class="footer__desc">Аренда кранов и спецтехники в Москве, области и по России. Своя техника и проверенная сеть, оператор в стоимости, подача от 1 дня.</p>
        <div class="footer__nap">Москва, проспект Андропова, 10<br>Работаем круглосуточно, 24/7<br>
          <a href="tel:%s" style="display:inline;padding:0">%s</a> · <a href="mailto:info@kran365.ru" style="display:inline;padding:0">info@kran365.ru</a></div>
      </div>
      <div><h4>Техника</h4>
        <a href="/avtokrany/">Автокраны</a><a href="/avtovyshki/">Автовышки</a><a href="/manipulyatory/">Манипуляторы</a>
        <a href="/ekskavatory/">Экскаваторы</a><a href="/samosvaly/">Самосвалы</a><a href="/traly/">Тралы</a></div>
      <div><h4>Компания</h4>
        <a href="/#how">Как работаем</a><a href="/#live">Свободная техника</a><a href="/uslugi/">Услуги</a>
        <a href="/blog/">Блог</a><a href="/#reviews">Отзывы</a><a href="/#geo">Зона работы</a></div>
      <div><h4>Заказать</h4><p style="font-size:.9rem">Приём заявок круглосуточно. Расчёт и консультация — бесплатно.</p>
        <a class="btn btn--primary" style="margin-top:14px" href="#order">Оставить заявку <span class="arr">→</span></a></div>
    </div>%s
    <div class="footer__bottom"><span>© 2026 КРАН365 · kran365.ru</span><span>Аренда спецтехники в Москве и Московской области</span></div>
  </div>
</footer>''' % (PHONE_TEL, PHONE_DISP, FOOTER_LEGAL)

def cta_section():
    return '''<section class="cta" id="order">
  <div class="wrap"><div class="cta__grid">
    <div class="reveal"><span class="eyebrow">Заявка на технику</span>
      <h2 style="margin-top:14px">Оставьте заявку — перезвоним за 15 минут</h2>
      <p>Подберём технику под задачу, назовём точную цену и подадим на объект в день обращения. Консультация и расчёт бесплатны.</p>
      <a class="cta__phone" href="tel:%s"><b>%s</b><span>Ежедневно, приём заявок 24/7</span></a></div>
    <form class="form reveal" id="orderForm" novalidate>
      <div class="form__row">
        <div class="field"><label for="f-name">Ваше имя</label><input class="input" id="f-name" name="name" type="text" placeholder="Как к вам обращаться" autocomplete="name"></div>
        <div class="field"><label for="f-phone">Телефон *</label><input class="input" id="f-phone" name="phone" type="tel" placeholder="+7 (___) ___-__-__" autocomplete="tel" required></div>
      </div>
      <div class="field"><label for="f-comment">Задача, объект, сроки</label><input class="input" id="f-comment" name="comment" type="text" placeholder="Напр.: монтаж на 30 июля, ЮАО, груз 8 тонн"></div>
      %s
      %s
      <button class="btn btn--primary btn--block btn--lg" type="submit">Отправить заявку <span class="arr">→</span></button>
      <div class="form__ok" id="formOk">✓ Заявка принята! Мы перезвоним в ближайшее время.</div>
    </form>
  </div></div>
</section>''' % (PHONE_TEL, PHONE_DISP, HONEYPOT, CONSENT)

def cta_band():
    return '''<section class="cta"><div class="wrap"><div class="cta__grid">
    <div><span class="eyebrow">Нужна техника?</span><h2 style="margin-top:14px">Назовём цену и подадим в день заявки</h2>
      <p>Оставьте заявку в форме выше или позвоните — расчёт и консультация бесплатны, приём заявок 24/7.</p>
      <a class="cta__phone" href="tel:%s"><b>%s</b><span>Ежедневно, круглосуточно</span></a></div>
    <div style="display:flex;flex-direction:column;gap:12px;align-self:center">
      <a class="btn btn--primary btn--lg" href="#order">Оставить заявку <span class="arr">→</span></a>
      <a class="btn btn--ghost btn--lg" href="%s" target="_blank" rel="noopener">Написать в Telegram</a></div>
  </div></div></section>''' % (PHONE_TEL, PHONE_DISP, TG)

TRUST = '''<div class="trust"><div class="wrap trust__row">
  <span class="trust__item"><svg><use href="#i-crane"/></svg> Найдём и подадим любую технику</span>
  <span class="trust__item"><svg><use href="#i-check"/></svg> Оператор входит в стоимость</span>
  <span class="trust__item"><svg><use href="#i-doc"/></svg> Договор, счёт, ЭДО</span>
  <span class="trust__item"><svg><use href="#i-clock"/></svg> Подача в день заявки</span>
  <span class="trust__item"><svg><use href="#i-shield"/></svg> Техника застрахована и на ТО</span>
</div></div>'''

def esc(s): return html.escape(str(s), quote=True)

def jsonld(objs):
    return "\n".join('<script type="application/ld+json">%s</script>' %
                     json.dumps(o, ensure_ascii=False, separators=(",", ":")) for o in objs)

def breadcrumb_ld(items):
    return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":i+1,"name":n,"item":SITE+u} for i,(n,u) in enumerate(items)]}

def local_business_ld():
    return {"@context":"https://schema.org","@type":"LocalBusiness","@id":SITE+"/#business","name":"КРАН365",
        "image":SITE+"/assets/img/crane-100.jpg","telephone":PHONE_TEL,"email":"info@kran365.ru","url":SITE,
        "priceRange":"₽₽","currenciesAccepted":"RUB","paymentAccepted":"Наличный и безналичный расчёт",
        "address":{"@type":"PostalAddress","addressLocality":"Москва","streetAddress":"проспект Андропова, 10","addressCountry":"RU"},
        "geo":{"@type":"GeoCoordinates","latitude":55.6767,"longitude":37.6654},
        "openingHours":"Mo-Su 00:00-24:00","areaServed":"Москва и Московская область","sameAs":[TG,WA]}

def service_ld(name, desc, price):
    offer = {"@type":"Offer","priceCurrency":"RUB","availability":"https://schema.org/InStock"}
    if price: offer["price"] = str(price)
    return {"@context":"https://schema.org","@type":"Service","serviceType":name,"provider":{"@type":"LocalBusiness","name":"КРАН365"},
        "areaServed":"Москва и Московская область","description":desc,"offers":offer}

def faq_ld(faqs):
    return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faqs]}

def faq_html(faqs):
    rows = "".join('<details><summary>%s</summary><div>%s</div></details>' % (esc(q), esc(a)) for q,a in faqs)
    return '<div class="faq">%s</div>' % rows

def aside_form():
    return '''<aside class="aside reveal" id="order">
  <h3>Быстрый расчёт</h3><p>Оставьте номер — перезвоним за 15 минут, назовём цену и сроки подачи.</p>
  <form class="form" id="orderForm" novalidate style="background:none;border:0;padding:0">
    <div class="field"><label for="f-phone">Ваш телефон</label><input class="input" id="f-phone" name="phone" type="tel" placeholder="+7 (___) ___-__-__" autocomplete="tel" required></div>
    <div class="field" style="margin-top:12px"><label for="f-comment">Что нужно и на какой объект</label><input class="input" id="f-comment" name="comment" type="text" placeholder="Что нужно / объект"></div>
    %s
    <div class="field" style="margin-top:12px">%s</div>
    <button class="btn btn--primary btn--block" type="submit" style="margin-top:12px">Получить расчёт <span class="arr">→</span></button>
    <small style="color:var(--muted-2);font-size:.78rem;display:block;text-align:center;margin-top:10px">Или звоните: <a href="tel:%s" style="color:var(--orange)">%s</a></small>
    <div class="form__ok" id="formOk">✓ Заявка принята!</div>
  </form>
</aside>''' % (HONEYPOT, CONSENT, PHONE_TEL, PHONE_DISP)

def page(rel_path, title, desc, crumbs, hero_html, body_html, ld_objs):
    canonical = SITE + "/" + rel_path.rsplit("index.html",1)[0]
    crumbs_html = ""
    parts = []
    for i,(n,u) in enumerate(crumbs):
        if i < len(crumbs)-1:
            parts.append('<a href="%s">%s</a>' % (u, esc(n)))
        else:
            parts.append('<span style="color:var(--muted)">%s</span>' % esc(n))
    crumbs_html = '<span>/</span>'.join(parts)
    doc = '''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:type" content="website">
<meta property="og:url" content="%s"><meta property="og:site_name" content="КРАН365"><meta property="og:locale" content="ru_RU">
<meta property="og:image" content="https://kran365.ru/assets/img/og-cover.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="%s"><meta name="twitter:description" content="%s"><meta name="twitter:image" content="https://kran365.ru/assets/img/og-cover.jpg">
<link rel="preconnect" href="https://mc.yandex.ru" crossorigin>
<link rel="stylesheet" href="/assets/style.css">
<link rel="stylesheet" href="/assets/pages.css">
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
%s
</head>
<body>
%s
%s
<main>
<div class="page-top"><div class="wrap"><nav class="crumbs">%s</nav></div></div>
%s
%s
%s
</main>
%s
%s
<script src="/assets/app.js"></script>
</body>
</html>''' % (esc(title), esc(desc), canonical, esc(title), esc(desc),
              canonical, esc(title), esc(desc),
              METRIKA + "\n" + jsonld(ld_objs), SPRITE, NAV, crumbs_html, hero_html, body_html,
              cta_band(), FOOTER, FAB)
    # Разметку Offer и узел организации доводит fix_schema — тот же код, что
    # правит уже лежащие на диске страницы. Генератор не знает, аренда на этой
    # странице или услуга: это решение живёт одним списком в fix_schema, иначе
    # правило пришлось бы держать в двух местах и они бы разошлись.
    doc = fix_schema.patch_html(doc, rel_path.rsplit("/index.html", 1)[0])[0]
    out = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    return canonical

def money(p): return "под запрос" if not p else "от %s ₽" % format(p, ",d").replace(",", " ")

def hour_price(p):
    """Оценочная цена за час — из расчёта 8-часовой смены (мин. заказ всё равно смена)."""
    if not p: return None
    return int(round(p / 8 / 10.0)) * 10

def price_hour_html(p):
    hp = hour_price(p)
    return ' <span class="price-hour">≈ %s ₽/час</span>' % format(hp, ",d").replace(",", " ") if hp else ""

# ---------------------------------------------------------------- данные
AVTOKRAN = [(25,16300),(32,19900),(40,29900),(50,34900),(60,44900),(70,54900),(90,None),(100,None),(150,None),(250,None)]

TYPES = [
  dict(slug="avtokrany", name="Автокраны", one="автокрана", price=16300,
       meta="16 – 500 тонн, стрела до 96 м",
       lead="Автокраны грузоподъёмностью от 16 до 500 тонн со стрелой до 96 метров. Своя техника и проверенная сеть, опытные крановщики в стоимости смены, подача от 1 дня по Москве и области."),
  dict(slug="avtovyshki", name="Автовышки", one="автовышки", price=9900,
       meta="высота подъёма 18 – 56 м",
       lead="Автовышки и телескопические подъёмники с высотой подъёма от 18 до 56 метров. Работа на высоте, монтаж, обслуживание фасадов и сетей. Оператор и топливо включены."),
  dict(slug="manipulyatory", name="Манипуляторы", one="манипулятора", price=9900,
       meta="борт до 20 т, стрела 7 – 8 т",
       lead="Краны-манипуляторы (кран-борт) с грузоподъёмностью стрелы 7–8 тонн и бортом до 20 тонн. Погрузка, перевозка и разгрузка за один рейс — дешевле, чем кран плюс отдельная машина."),
  dict(slug="ekskavatory", name="Экскаваторы", one="экскаватора", price=8100,
       meta="мини, колёсные, гусеничные, погрузчики",
       lead="Экскаваторы и экскаваторы-погрузчики: мини от 1,5 т, колёсные и гусеничные до 33 т, с ковшом и гидромолотом. Земляные работы, разработка грунта, снос."),
  dict(slug="samosvaly", name="Самосвалы", one="самосвала", price=10900,
       meta="10 – 20 м³, вывоз грунта и мусора",
       lead="Самосвалы объёмом кузова 10–20 м³ для вывоза грунта, строительного мусора и снега. Свои машины, работа по талонам, вывоз на лицензированные полигоны."),
  dict(slug="traly", name="Тралы и негабарит", one="трала", price=11900,
       meta="перевозка 20 – 40 тонн",
       lead="Низкорамные тралы для перевозки спецтехники и негабаритных грузов массой 20–40 тонн. Погрузка, крепление, сопровождение и оформление негабарита."),
]
TYPES += [
  dict(slug="gusenichnye-krany", name="Гусеничные краны", one="гусеничного крана", price=None,
       meta="50 – 750 тонн, тяжёлый монтаж",
       lead="Гусеничные краны грузоподъёмностью от 50 до 750 тонн для тяжёлого монтажа на объектах с ограниченным доступом. Работают на слабых грунтах, перемещаются с грузом, монтаж и демонтаж — под ключ."),
  dict(slug="bashennye-krany", name="Башенные краны", one="башенного крана", price=None,
       meta="монтаж и аренда на объект",
       lead="Башенные краны в аренду на объект: подбор по вылету и высоте, доставка, монтаж, пусконаладка и обслуживание на весь срок стройки. Оформляем документы для ввода в эксплуатацию."),
]
TYPE_BY_SLUG = {t["slug"]: t for t in TYPES}

# Автовышки по высоте и манипуляторы по тоннажу стрелы
VYSHKI = [(18,9900),(21,10900),(28,12900),(32,14900),(40,19900),(45,21900),(50,25900)]
MANIP  = [(3,9900),(5,10900),(7,12500),(8,14900),(10,17900),(12,None),(15,None)]

# Автокраны по длине стрелы: (метры, цена, минимальный тоннаж такой машины)
STRELA = [(21,16300,25),(28,19900,32),(30,19900,32),(34,29900,40),(40,34900,50),
          (46,44900,60),(50,54900,70),(56,None,90),(60,None,100),(70,None,150)]

# Экскаваторы: (slug, название, ковш/класс, цена)
EKSK = [
  ("mini-1-3","Мини-экскаватор 1,5–3 т","ковш 0,08–0,12 м³, для узких мест",8100),
  ("mini-5","Мини-экскаватор 5 т","ковш 0,2 м³, гидромолот",9900),
  ("mini-7","Мини-экскаватор 7 т","ковш 0,3 м³, гидромолот",11900),
  ("kolesnyj-160","Экскаватор колёсный 160 серии","ковш 1 м³, город",12900),
  ("kolesnyj-200","Экскаватор колёсный 200 серии","ковш 1 м³, гидромолот",14900),
  ("gusenichnyj-130-190","Экскаватор гусеничный 130–190","ковш 0,6–1 м³",12900),
  ("gusenichnyj-200-220","Экскаватор гусеничный 200–220","ковш 1–1,3 м³",14900),
  ("gusenichnyj-320-330","Экскаватор гусеничный 320–330","ковш 1,5–2 м³, тяжёлый",19900),
  ("pogruzchik-3cx","Экскаватор-погрузчик JCB 3CX","ковш + гидромолот, универсал",9900),
  ("pogruzchik-4cx","Экскаватор-погрузчик JCB 4CX","полный привод, больше ковш",10900),
]

# Самосвалы: (slug, название, объём/особенность, цена)
SAMOSVAL = [
  ("10-14-m3","Самосвал 10–14 м³","городской, узкие дворы",10900),
  ("15-m3","Самосвал 15 м³","оптимален по цене за куб",11900),
  ("20-m3","Самосвал 20 м³","максимальный объём за рейс",12900),
  ("vezdehod","Самосвал-вездеход","полный привод, бездорожье",13900),
]

# Блог: (slug, заголовок, лид, содержимое-блоки)
from data_rf import GEO_RF, BLOG_RF   # автоген: 30 городов РФ + 16 статей блога
from data_cat import CATS             # автоген: 12 новых категорий спецтехники
from data_tonnage import TONNAGE      # уникальный контент страниц автокранов по тоннажу
from data_strela import STRELA_DATA   # уникальный контент страниц по длине стрелы (ось: геометрия)
from data_marki import MARKI_DATA     # уникальный контент страниц марок (ось: эксплуатация)
from data_vysh_manip import VYSHKI_DATA, MANIP_DATA  # автовышки (ось: работа на высоте) и манипуляторы (ось: экономика рейса)
from data_zemlya import EKSK_DATA, SAMOSVAL_DATA     # экскаваторы (ось: грунт и производительность) и самосвалы (ось: экономика вывоза)
from data_geo_mo import GEO_MO_DATA   # гео Москвы и области (ось: логистика подачи и местные условия)
from data_tasks import TASKS_DATA     # страницы услуг (ось: ход работы, а не список техники)
from data_hubs import HUBS_DATA, HUB_EXTRA       # хабы без своей ветки: тралы, гусеничные и башенные краны
from data_geo_rf import GEO_RF_DATA   # гео городов России (ось: региональная специфика, честно про партнёрскую сеть)
from data_blog_base import BLOG_BASE   # 6 базовых статей, переписанных из коротких заготовок
BLOG = list(BLOG_BASE) + BLOG_RF

# Марки автокранов
MARKI = [
  ("liebherr","Liebherr","Немецкие автокраны от 40 до 500 тонн — эталон надёжности для тяжёлого монтажа. Телескопическая стрела до 96 м, точная гидравлика, работа в стеснённых условиях."),
  ("ivanovec","Ивановец","Российские автокраны 25–50 тонн на шасси КамАЗ и Урал. Рабочая лошадка стройки: неприхотливы, проходимы, оптимальны по цене смены."),
  ("galichanin","Галичанин","Отечественные автокраны 25–100 тонн с длинной стрелой. Хорошее соотношение грузоподъёмности и цены, доступны вездеходные версии."),
  ("klincy","Клинцы","Автокраны 25–40 тонн Клинцовского завода на шасси КамАЗ, МАЗ, Урал. Надёжны в городских и полевых условиях, просты в обслуживании."),
  ("zoomlion","Zoomlion","Китайские автокраны 25–500 тонн. Современная гидравлика и большие вылеты при выгодной цене смены — часто берут на длительные проекты."),
  ("xcmg","XCMG","Автокраны XCMG от 25 до 500 тонн: широкий модельный ряд, мощные телескопические стрелы, хорошая доступность запчастей."),
  ("kato","Kato","Японские автокраны 25–160 тонн. Компактные, точные в управлении, ценятся на монтаже в городе и на ограниченных площадках."),
  ("grove","Grove","Автокраны Grove 40–300 тонн: американская школа, высокая устойчивость, надёжны на длительных монтажных работах."),
  ("terex","Terex","Автокраны Terex 40–500 тонн для промышленного и инфраструктурного монтажа. Большие вылеты, работа с гуськом."),
  ("sany","Sany","Автокраны Sany 25–500 тонн. Современная электроника, хорошие грузовысотные характеристики, выгодны на долгих проектах."),
]

# Страницы под задачи клиента
TASKS = [
  ("montazh-angara","Монтаж ангара","монтажа ангара",
   "Монтаж ангаров, складов и быстровозводимых зданий: подъём ферм, прогонов и сэндвич-панелей. Подбираем кран по массе секции, высоте и вылету, работаем со стропальщиками.",
   "автокран 25–50 т", 16300,
   [("Какой кран нужен для монтажа ангара?","Чаще всего достаточно автокрана 25–40 тонн: масса фермы обычно 1,5–4 тонны, но важен вылет — кран должен доставать до середины пролёта. Подберём по вашему чертежу."),
    ("Сколько смен занимает монтаж?","Каркас ангара 12×30 м обычно собирают за 2–4 смены крана. Точный расчёт сделаем по проекту."),
    ("Даёте стропальщиков?","Да, можем предоставить стропальщиков и такелажников вместе с краном.")]),
  ("ustanovka-bytovki","Установка бытовки","установки бытовки",
   "Разгрузка и установка бытовок, модульных зданий и постов охраны. Манипулятор привезёт и поставит бытовку за один рейс — это дешевле, чем кран плюс отдельная перевозка.",
   "манипулятор 7–8 т", 9900,
   [("Чем ставить бытовку — краном или манипулятором?","Стандартная бытовка 6×2,4 м весит 1,5–2,5 тонны — её привезёт и поставит манипулятор за один рейс. Кран нужен, если бытовку ставят через здание или на высоту."),
    ("Сколько стоит перевезти и поставить бытовку?","Смена манипулятора — от 9 900 ₽, обычно за смену перевозят 1–3 бытовки по Москве. Точную цену назовём по адресам."),
    ("Нужна ли подготовка площадки?","Желательны ровное основание и подъезд для техники. Блоки под бытовку можно выставить тем же манипулятором.")]),
  ("podem-na-kryshu","Подъём оборудования на крышу","подъёма оборудования на крышу",
   "Подъём кондиционеров, вентиляции, чиллеров и стройматериалов на кровлю зданий. Автокран или автовышка — в зависимости от массы груза, высоты и наличия подъезда.",
   "автокран 25 т / автовышка", 12900,
   [("Чем поднять кондиционер на крышу?","Для внешних блоков и сплит-систем обычно хватает автовышки или манипулятора. Для тяжёлых чиллеров и вентустановок нужен автокран 25–40 тонн — зависит от массы и вылета через здание."),
    ("Как считается вылет?","Вылет — расстояние от оси крана до груза. Если кран не может встать вплотную к зданию, вылет растёт, а грузоподъёмность падает. Пришлите фото площадки — подберём."),
    ("Работаете в выходные?","Да, работаем 24/7 — часто подъём на кровлю делают ночью или в выходные, чтобы не мешать работе здания.")]),
  ("razgruzka-fur","Разгрузка фур","разгрузки фур",
   "Разгрузка еврофур, контейнеров и негабаритных грузов на объекте и складе. Манипулятор или автокран с опытным оператором и стропальщиками, работа без простоя транспорта.",
   "манипулятор / автокран", 9900,
   [("Как быстро подадите технику под разгрузку?","По Москве обычно в течение 2 часов, приём заявок круглосуточно — фуру не придётся держать в простое."),
    ("Чем лучше разгружать?","До 7 тонн на подъём — манипулятор, он же перевезёт груз по площадке. Тяжелее или с большим вылетом — автокран."),
    ("Есть ли ночная разгрузка?","Да, работаем 24/7, ночная разгрузка — обычная практика для складов и магазинов.")]),
  ("montazh-metallokonstrukciy","Монтаж металлоконструкций","монтажа металлоконструкций",
   "Монтаж колонн, балок, ферм и площадок обслуживания. Подбираем кран по массе самого тяжёлого элемента и вылету, обеспечиваем такелаж и стропальщиков.",
   "автокран 25–100 т", 16300,
   [("Как подобрать кран под металлоконструкции?","Нужны три цифры: масса самого тяжёлого элемента, высота подъёма и вылет. По ним подберём кран так, чтобы был запас по грузовысотной характеристике."),
    ("Нужен ли ППР?","Для монтажа на действующем объекте обычно нужен проект производства работ. Поможем с требованиями к площадке и подготовим документы по крану."),
    ("Работаете на длительных проектах?","Да, на долгий монтаж выгоднее помесячная аренда — цена смены заметно ниже разовой.")]),
  ("ustanovka-septika","Установка септика и ёмкостей","установки септика",
   "Разгрузка и монтаж септиков, кессонов и резервуаров в котлован. Манипулятор или автокран аккуратно опустит ёмкость без повреждения корпуса.",
   "манипулятор 7 т", 9900,
   [("Чем опустить септик в котлован?","Ёмкости до 5 м³ ставит манипулятор, крупные резервуары — автокран 25 т и выше. Важно, чтобы техника могла подъехать к котловану."),
    ("Можно ли привезти и сразу поставить?","Да, манипулятор привезёт септик и опустит его в котлован за один выезд — это дешевле, чем отдельные машина и кран."),
    ("Работаете на участках с плохим подъездом?","Есть вездеходные манипуляторы и краны повышенной проходимости для загородных участков.")]),
  ("ustanovka-stolbov","Установка столбов и опор","установки столбов",
   "Бурение и установка опор освещения, ЛЭП, столбов ограждения и рекламных конструкций. Ямобур на базе крана-манипулятора бурит и сразу ставит опору.",
   "ямобур / манипулятор", 12900,
   [("Что входит в смену ямобура?","В стоимость смены входит 20 метров бурения глубиной до 5 метров. Метры сверх нормы считаются отдельно."),
    ("Какие диаметры бурите?","Шнеки от 150 до 1200 мм. Диаметр подбираем под сечение опоры и тип грунта."),
    ("Ставите опоры сразу после бурения?","Да, ямобур на базе крана-манипулятора бурит скважину и сразу устанавливает опору — за один выезд.")]),
  ("takelazhnye-raboty","Такелажные работы","такелажных работ",
   "Такелаж и перемещение тяжёлого оборудования: станки, трансформаторы, ёмкости, сейфы. Кран, такелажники и оснастка — под одну задачу.",
   "автокран + такелажники", 16300,
   [("Что относится к такелажным работам?","Перемещение тяжёлого и негабаритного оборудования: станки, трансформаторы, генераторы, сейфы, промышленные узлы — с использованием крана и специальной оснастки."),
    ("Даёте стропальщиков и оснастку?","Да, предоставляем стропальщиков, стропы, траверсы и другую такелажную оснастку под конкретный груз."),
    ("Страхуете груз?","Техника застрахована. По ценным грузам страхование обсуждаем отдельно до начала работ.")]),
  ("demontazh-zdaniy","Демонтаж зданий","демонтажа зданий",
   "Снос и демонтаж зданий, ангаров и промышленных сооружений. Экскаваторы с гидромолотом и крашером, вывоз строительного мусора самосвалами.",
   "экскаватор + самосвалы", 8100,
   [("Какая техника нужна для сноса?","Экскаватор с гидромолотом или крашером для разрушения, погрузчик для сбора и самосвалы для вывоза. Комплект подбираем по объёму объекта."),
    ("Вывозите мусор?","Да, вывозим строительный мусор самосвалами на лицензированные полигоны, с документами о размещении отходов."),
    ("Считаете объём заранее?","Да, по площади и материалу здания рассчитаем количество рейсов и итоговую стоимость до начала работ.")]),
  ("vyvoz-grunta","Вывоз грунта","вывоза грунта",
   "Разработка котлованов и вывоз грунта самосвалами на лицензированные полигоны. Экскаватор, самосвалы и документы на размещение — в одном заказе.",
   "экскаватор + самосвалы 20 м³", 10900,
   [("Как считается вывоз грунта?","По объёму в кубометрах и расстоянию до полигона. Самосвал 20 м³ вывозит примерно 12–14 тонн грунта за рейс."),
    ("Даёте документы на утилизацию?","Да, вывозим на лицензированные полигоны и предоставляем документы о размещении отходов."),
    ("Можно только самосвалы, без экскаватора?","Да, если у вас есть своя погрузочная техника — подадим только самосвалы.")]),
]

# (slug, предложный падеж, именительный, шоссе/направление, соседние населённые пункты, характер застройки)
GEO = [
  ("moskva","Москве","Москва","в пределах МКАД и в Новой Москве","ЦАО, ЮАО, САО, ВАО и все округа",
   "Работаем в плотной городской застройке: узкие дворы, ограниченный подъезд, ночные окна для работ. Подбираем компактные краны и согласуем время подачи так, чтобы не перекрывать движение."),
  ("odincovo","Одинцово","Одинцово","Можайское и Минское шоссе, запад области","Голицыно, Власиха, Немчиновка, Барвиха",
   "Западное направление — частный сектор, коттеджные посёлки и логистические комплексы. Часто нужны вездеходные краны и манипуляторы для участков без твёрдого подъезда."),
  ("himki","Химках","Химки","Ленинградское шоссе, север области","Куркино, Сходня, Долгопрудный, Лобня",
   "Химки — склады, логистика и активная жилая застройка. Чаще всего заказывают разгрузку фур манипуляторами и монтаж металлоконструкций автокранами 25–50 тонн."),
  ("balashiha","Балашихе","Балашиха","шоссе Энтузиастов, восток области","Реутов, Железнодорожный, Ногинск, Салтыковка",
   "Восточное направление — промзоны и новые жилые кварталы. Востребованы автокраны на монтаж и самосвалы под вывоз грунта с котлованов."),
  ("podolsk","Подольске","Подольск","Симферопольское и Варшавское шоссе, юг области","Климовск, Щербинка, Домодедово, Троицк",
   "Юг области — производственные площадки и индивидуальное строительство. Часто требуются ямобуры под опоры и манипуляторы для доставки бытовок и материалов."),
  ("mytishchi","Мытищах","Мытищи","Ярославское шоссе, северо-восток","Королёв, Пушкино, Медведково, Челобитьево",
   "Мытищи — жилые комплексы и торговые центры. Типовые задачи: подъём оборудования и вентиляции на кровлю, монтаж рекламных конструкций автовышками."),
  ("krasnogorsk","Красногорске","Красногорск","Волоколамское и Новорижское шоссе, северо-запад","Нахабино, Павшино, Опалиха, Дедовск",
   "Новорижское направление — активная стройка бизнес-центров и жилья. Берут автокраны 40–100 тонн на монтаж и тралы для перевозки техники между объектами."),
  ("lyubercy","Люберцах","Люберцы","Новорязанское шоссе, юго-восток","Котельники, Дзержинский, Жулебино, Малаховка",
   "Юго-восток — склады, автосервисы и жилые новостройки. Чаще всего заказывают разгрузку фур, установку модульных зданий и вывоз строительного мусора."),
  ("domodedovo","Домодедово","Домодедово","Каширское шоссе, аэропортовая зона","Видное, Подольск, Ям, Барыбино",
   "Зона аэропорта — логистические комплексы и ангары. Востребован монтаж ангаров и складов автокранами, работа по пропускному режиму согласуется заранее."),
  ("korolev","Королёве","Королёв","Ярославское шоссе, наукоград","Мытищи, Ивантеевка, Щёлково, Юбилейный",
   "Королёв — промышленные предприятия и научные площадки. Частые задачи: такелаж и перемещение оборудования, монтаж металлоконструкций в цехах."),
  ("reutov","Реутове","Реутов","шоссе Энтузиастов, ближнее Подмосковье","Балашиха, Новокосино, Железнодорожный, Никольское",
   "Реутов вплотную примыкает к МКАД — подача техники быстрая, обычно в течение часа-двух. Плотная застройка, много работ по подъёму материалов на высоту."),
  ("shchelkovo","Щёлково","Щёлково","Щёлковское шоссе, северо-восток","Фрязино, Монино, Лосино-Петровский, Чкаловский",
   "Щёлковское направление — производственные базы и частный сектор. Заказывают ямобуры под столбы и опоры, манипуляторы для доставки стройматериалов."),
  ("ramenskoe","Раменском","Раменское","Егорьевское и Новорязанское шоссе, юго-восток","Жуковский, Быково, Ильинский, Удельная",
   "Раменский район — коттеджная застройка и аэродромная зона Жуковского. Часто нужны манипуляторы для септиков и бытовок, автокраны на монтаж каркасов."),
  ("pushkino","Пушкино","Пушкино","Ярославское шоссе, север области","Ивантеевка, Правдинский, Софрино, Красноармейск",
   "Север области — дачные посёлки и небольшие производства. Востребованы вездеходные манипуляторы и краны для участков с грунтовым подъездом."),
]

def price_table_types(active=None):
    rows = ""
    for t in TYPES:
        cls = ' style="background:rgba(255,106,0,.06)"' if active==t["slug"] else ""
        rows += '<tr%s><td><a href="/%s/" style="color:var(--ink)">%s</a></td><td>%s</td><td><b>%s</b> <span style="color:var(--muted-2);font-size:.82rem">/ смена</span>%s</td></tr>' % (
            cls, t["slug"], esc(t["name"]), esc(t["meta"]), money(t["price"]), price_hour_html(t["price"]))
    return '<div class="ptable-wrap"><table class="ptable"><thead><tr><th>Техника</th><th>Параметры</th><th>Цена</th></tr></thead><tbody>%s</tbody></table></div>' % rows

def tonnage_table(active=None):
    rows = ""
    for t,p in AVTOKRAN:
        cls = ' style="background:rgba(255,106,0,.06)"' if active==t else ""
        rows += '<tr%s><td><a href="/avtokrany/%d-tonn/" style="color:var(--ink)">Автокран %d т</a></td><td>%s</td></tr>' % (
            cls, t, t, ('<b>%s</b> <span style="color:var(--muted-2);font-size:.82rem">/ смена</span>%s' % (money(p), price_hour_html(p))) if p else '<b>под запрос</b>')
    return '<div class="ptable-wrap"><table class="ptable"><thead><tr><th>Грузоподъёмность</th><th>Цена</th></tr></thead><tbody>%s</tbody></table></div>' % rows

def related_tonnages(active):
    links = "".join('<a href="/avtokrany/%d-tonn/"><b>%d</b> т</a>' % (t,t) for t,_ in AVTOKRAN if t!=active)
    return '<div class="related"><h3>Другие грузоподъёмности</h3><div class="related-grid">%s</div></div>' % links

def related_geo(active_slug=None):
    links = "".join('<a href="/geo/%s/">%s</a>' % (g[0], esc(g[2])) for g in GEO if g[0]!=active_slug)
    return '<div class="related"><h3>Аренда в других районах и городах</h3><div class="related-grid">%s</div></div>' % links

def param_table(items, base, unit, active=None):
    """Таблица по параметру: [(значение, цена)] → строки со ссылками."""
    rows = ""
    for it in items:
        v, p = it[0], it[1]
        cls = ' style="background:rgba(255,106,0,.06)"' if active == v else ""
        price = ('<b>%s</b> <span style="color:var(--muted-2);font-size:.82rem">/ смена</span>%s' % (money(p), price_hour_html(p))) if p else '<b>под запрос</b>'
        rows += '<tr%s><td><a href="%s%d-%s/" style="color:var(--ink)">%d %s</a></td><td>%s</td></tr>' % (
            cls, base, v, unit[1], v, unit[0], price)
    return '<div class="ptable-wrap"><table class="ptable"><thead><tr><th>Параметр</th><th>Цена</th></tr></thead><tbody>%s</tbody></table></div>' % rows

def related_param(items, base, unit, active, title):
    links = "".join('<a href="%s%d-%s/"><b>%d</b> %s</a>' % (base, it[0], unit[1], it[0], unit[0].split()[0]) for it in items if it[0] != active)
    return '<div class="related"><h3>%s</h3><div class="related-grid">%s</div></div>' % (title, links)

def related_marki(active=None):
    links = "".join('<a href="/avtokrany/marki/%s/">%s</a>' % (s, esc(n)) for s, n, _ in MARKI if s != active)
    return '<div class="related"><h3>Автокраны по маркам</h3><div class="related-grid">%s</div></div>' % links

def related_tasks(active=None):
    links = "".join('<a href="/uslugi/%s/">%s</a>' % (s, esc(n)) for s, n, _, _, _, _, _ in TASKS if s != active)
    return '<div class="related"><h3>Услуги под задачу</h3><div class="related-grid">%s</div></div>' % links

def related_types(active_slug=None):
    links = "".join('<a href="/%s/">%s</a>' % (t["slug"], esc(t["name"])) for t in TYPES if t["slug"]!=active_slug)
    return '<div class="related"><h3>Другая техника</h3><div class="related-grid">%s</div></div>' % links


def related_cats(active_slug=None, limit=None):
    """Перелинковка категорий спецтехники между собой.
    До этого на них вела единственная ссылка — с главной, из-за чего робот
    считал их второстепенными."""
    items = [c for c in CATS if c["slug"] != active_slug]
    if limit:
        items = items[:limit]
    links = "".join('<a href="/%s/">%s</a>' % (c["slug"], esc(c["name_nom"])) for c in items)
    return '<div class="related"><h3>Другая спецтехника</h3><div class="related-grid">%s</div></div>' % links


def related_blog(*keys, **kw):
    """Ссылки на статьи блога по теме страницы.

    Нужны не только читателю: до этого статьи лежали на глубине 3 клика
    от главной (главная -> /blog/ -> статья), теперь профильные разделы
    ведут на них напрямую.
    """
    limit = kw.get("limit", 3)
    picked, seen = [], set()
    for k in keys:
        for slug, title, lead, blocks in BLOG:
            if k in slug and slug not in seen:
                seen.add(slug)
                picked.append((slug, title))
            if len(picked) >= limit:
                break
        if len(picked) >= limit:
            break
    if not picked:
        return ""
    links = "".join('<a href="/blog/%s/">%s</a>' % (sl, esc(t)) for sl, t in picked)
    return '<div class="related"><h3>Статьи по теме</h3><div class="related-grid">%s</div></div>' % links


def related_geo_rf(active_slug=None, limit=10):
    """Перелинковка городов России между собой.

    related_geo() охватывает только Москву и область, поэтому на страницы
    30 регионов вела единственная ссылка — с главной.
    """
    # скользящее окно: каждая страница ведёт на СВОИХ соседей по списку,
    # иначе первые десять городов собирают все ссылки, а остальные — ни одной
    idx = next((i for i, g in enumerate(GEO_RF) if g[0] == active_slug), 0)
    rest = GEO_RF[idx + 1:] + GEO_RF[:idx]
    items = rest[:limit]
    links = "".join('<a href="/geo/%s/">%s</a>' % (g[0], esc(g[2])) for g in items)
    return '<div class="related"><h3>Другие города России</h3><div class="related-grid">%s</div></div>' % links

def hero(kicker, h1, lead, price, price_unit="/ смена"):
    badge = ""
    if price:
        badge = '<div class="price-badge"><b>%s</b><span>%s</span>%s</div>' % (money(price), price_unit, price_hour_html(price))
    return '''<section class="page-hero"><div class="wrap">
  <span class="eyebrow">%s</span><h1>%s</h1><p class="lead">%s</p>
  %s
  <div class="actions"><a class="btn btn--primary btn--lg" href="#order">Заказать <span class="arr">→</span></a>
  <a class="btn btn--ghost btn--lg" href="tel:%s">%s</a></div>
</div></section>''' % (esc(kicker), esc(h1), esc(lead), badge, PHONE_TEL, PHONE_DISP)

def body(prose_html, related_html):
    return '''<section style="padding-top:8px"><div class="wrap"><div class="page-cols">
  <div class="prose reveal">%s %s</div>
  %s
</div></div></section>''' % (prose_html, related_html, aside_form())


def spec_table(rows, headers):
    """Простая таблица характеристик из списка кортежей."""
    th = "".join("<th>%s</th>" % esc(h) for h in headers)
    tr = ""
    for row in rows:
        tr += "<tr>" + "".join("<td>%s</td>" % (c if c.startswith("<") else esc(c)) for c in row) + "</tr>"
    return '<div class="ptable-wrap"><table class="ptable"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, tr)


def tonnage_prose(tn, pr):
    """Уникальный текст страницы автокрана по грузоподъёмности."""
    d = TONNAGE[tn]
    h = ""
    for p in d["intro"]:
        h += "<p>%s</p>" % esc(p)

    h += "<h2>Какие машины выезжают на объект</h2>"
    h += "<p>Под заявку «автокран %d тонн» выходит одна из этих машин — конкретную назовём при подтверждении заказа, " \
         "исходя из вашей площадки и графика.</p>" % tn
    h += spec_table([(m[0], m[1], m[2], m[3]) for m in d["models"]],
                    ["Модель", "Шасси", "Стрела", "Особенности"])

    h += "<h2>Сколько реально поднимет автокран %d тонн</h2>" % tn
    h += "<p>%s Грузоподъёмность падает по мере того, как груз отдаляется от машины — " \
         "именно вылет, а не паспортный тоннаж, определяет, справится кран или нет.</p>" % esc(d["boom_note"])
    h += spec_table(d["reach"], ["Вылет стрелы", "Грузоподъёмность"])
    h += "<p><small>Значения ориентировочные: усреднены по типовым машинам класса при полном выносе опор " \
         "и полном противовесе. Точные цифры — по грузовысотной характеристике конкретного крана, " \
         "пришлём вместе с расчётом.</small></p>"

    h += "<h2>Что нужно на площадке</h2>"
    h += spec_table(d["site"], ["Параметр", "Требование"])

    h += "<h2>Стоимость аренды автокрана %d тонн</h2>" % tn
    h += "<p>%s</p>" % (
        ("Смена до 10 часов — %s, оператор и топливо включены. Подача считается отдельно, по адресу объекта."
         % money(pr).lower()) if pr else
        "Техника этого класса считается под объект: в смету входят смена, доставка крана и противовеса, "
        "спецразрешения и подготовка основания. Пришлите задачу — посчитаем в течение дня.")
    h += tonnage_table(active=tn)

    h += "<h2>Типовые задачи</h2><ul>%s</ul>" % "".join("<li>%s</li>" % esc(t) for t in d["tasks"])

    h += "<h2>Когда нужен другой тоннаж</h2><p>%s</p>" % d["compare"]

    h += "<h2>Частые вопросы</h2>%s" % faq_html(d["faqs"])
    return h


def strela_prose(m_, pr, tn):
    """Уникальный текст страницы по длине стрелы. Ось раскрытия — геометрия работы,
    чтобы не дублировать страницы по грузоподъёмности (это та же машина)."""
    d = STRELA_DATA[m_]
    h = ""
    for p in d["intro"]:
        h += "<p>%s</p>" % esc(p)

    h += "<h2>Что достанет стрела %d метров</h2>" % m_
    h += spec_table(d["geometry"], ["Параметр", "Значение"])
    h += "<p><small>Рабочая высота всегда меньше длины стрелы на 3–4 метра: этот запас уходит " \
         "на оголовок, крюковую подвеску, стропы и габарит самого груза.</small></p>"

    h += "<h2>Как посчитать вылет</h2>"
    h += "<p>Вылет — это расстояние по горизонтали от оси вращения крана до груза. " \
         "Считается просто: сложите расстояние от крана до препятствия, ширину препятствия " \
         "и расстояние от него до точки установки. Именно вылет, а не высота здания, " \
         "чаще всего определяет, справится машина или нет.</p>"
    h += "<h3>%s</h3><p>%s</p>" % (esc(d["example_title"]), esc(d["example"]))

    h += "<h2>Типовые работы</h2><ul>%s</ul>" % "".join("<li>%s</li>" % esc(s) for s in d["scenarios"])

    h += "<h2>Стоимость</h2>"
    h += "<p>%s Стрелу такой длины несут машины от %d тонн — цену считаем по массе груза, " \
         "высоте и вылету, потому что от них зависит, какая именно машина поедет.</p>" % (
         (("Смена крана с такой стрелой — %s, оператор и топливо включены." % money(pr).lower()) if pr
          else "Машины с такой стрелой — проектная техника, стоимость считаем под объект."), tn)
    h += param_table(STRELA, "/avtokrany/strela-", ("метров", "metrov"), active=m_)

    h += "<h2>Частые вопросы</h2>%s" % faq_html(d["faqs"])
    return h


def pros_cons(pros, cons):
    """Два списка рядом: сильные и слабые стороны. Честные минусы — часть ценности страницы."""
    li_p = "".join("<li>%s</li>" % esc(x) for x in pros)
    li_c = "".join("<li>%s</li>" % esc(x) for x in cons)
    return ('<div class="pc"><div class="pc__col pc__col--plus"><h3>Сильные стороны</h3><ul>%s</ul></div>'
            '<div class="pc__col pc__col--minus"><h3>Что учесть</h3><ul>%s</ul></div></div>') % (li_p, li_c)


def marka_prose(slug, name):
    """Уникальный текст страницы марки. Ось раскрытия — эксплуатация:
    модельный ряд в аренде, сильные и слабые стороны, сервис, кому подходит."""
    d = MARKI_DATA[slug]
    h = ""
    for p in d["intro"]:
        h += "<p>%s</p>" % esc(p)

    h += "<h2>Какие модели %s встречаются в аренде</h2>" % esc(name)
    h += spec_table([(m[0], m[1], m[2], m[3]) for m in d["lineup"]],
                    ["Модель", "Грузоподъёмность", "Стрела", "Где применяется"])

    h += "<h2>Плюсы и минусы в работе</h2>"
    h += pros_cons(d["pros"], d["cons"])

    h += "<h2>Обслуживание и запчасти</h2><p>%s</p>" % esc(d["service"])

    h += "<h2>Кому подходит</h2><p>%s</p>" % esc(d["who"])

    h += "<h2>Цены на аренду</h2>"
    h += ("<p>Ставка зависит от грузоподъёмности, а не от марки: смена крана %s стоит столько же, "
          "сколько смена любой другой машины того же класса. Разница возникает только на импортной технике "
          "на спецшасси — её мы озвучиваем отдельно при подтверждении.</p>" % esc(name))
    h += tonnage_table()

    h += "<h2>Как заказать именно эту марку</h2>"
    h += ("<p>Скажите при заявке, что нужна именно %s — проверим наличие на дату по своему парку и партнёрской сети. "
          "Если свободной машины не окажется, честно скажем об этом и предложим равноценную замену по тоннажу "
          "и длине стрелы, а не подставим что попало по факту приезда.</p>" % esc(name))

    h += "<h2>Частые вопросы</h2>%s" % faq_html(d["faqs"])
    return h


def vyshka_prose(h_, pr):
    """Уникальный текст страницы автовышки. Ось — работа человека на высоте."""
    d = VYSHKI_DATA[h_]
    out = ""
    for p in d["intro"]:
        out += "<p>%s</p>" % esc(p)

    out += "<h2>Характеристики вышки %d метров</h2>" % h_
    out += spec_table(d["specs"], ["Параметр", "Значение"])
    out += "<p><small>Высота и вылет связаны: полная высота достигается при работе почти вплотную "\
           "к объекту, а на максимальном боковом вылете фактическая точка работы оказывается ниже.</small></p>"

    out += "<h2>Для каких работ подходит</h2><ul>%s</ul>" % "".join("<li>%s</li>" % esc(x) for x in d["works"])

    out += "<h2>Что важно знать</h2><p>%s</p>" % d["note"]

    out += "<h2>Стоимость аренды автовышки %d м</h2>" % h_
    out += "<p>Смена до 10 часов — %s, работа оператора и топливо включены. " \
           "Подача рассчитывается по адресу объекта.</p>" % money(pr).lower()
    out += param_table(VYSHKI, "/avtovyshki/", ("метров", "metrov"), active=h_)

    out += "<h2>Частые вопросы</h2>%s" % faq_html(d["faqs"])
    return out


def manip_prose(t_, pr):
    """Уникальный текст страницы манипулятора. Ось — экономика одного рейса."""
    d = MANIP_DATA[t_]
    out = ""
    for p in d["intro"]:
        out += "<p>%s</p>" % esc(p)

    out += "<h2>Что может манипулятор %d тонн</h2>" % t_
    out += spec_table(d["specs"], ["Параметр", "Значение"])
    out += "<p><small>Борт всегда берёт больше, чем поднимает стрела: на платформу груз кладут погрузчиком, "\
           "а стрелой снимают по частям. Паспортная грузоподъёмность стрелы — это максимум у самой машины, "\
           "на полном вылете она в несколько раз меньше.</small></p>"

    out += "<h2>Что возят такой машиной</h2><ul>%s</ul>" % "".join("<li>%s</li>" % esc(x) for x in d["cargo"])

    out += "<h2>Когда это выгодно</h2><p>%s</p>" % d["economy"]

    out += "<h2>Стоимость аренды манипулятора %d т</h2>" % t_
    out += "<p>%s</p>" % (
        ("Смена до 10 часов — %s, оператор и топливо включены. Подача считается по адресу объекта."
         % money(pr).lower()) if pr else
        "Машины этого класса считаются под задачу: цена зависит от массы и габаритов груза, "
        "маршрута и времени работы на объекте.")
    out += param_table(MANIP, "/manipulyatory/", ("тонн", "tonn"), active=t_)

    out += "<h2>Частые вопросы</h2>%s" % faq_html(d["faqs"])
    return out


def zemlya_prose(group, slug, name, price, table):
    """Уникальный текст страниц экскаваторов и самосвалов."""
    d = (EKSK_DATA if group == "ekskavatory" else SAMOSVAL_DATA)[slug]
    out = ""
    for p in d["intro"]:
        out += "<p>%s</p>" % esc(p)

    if group == "ekskavatory":
        out += "<h2>Характеристики и производительность</h2>"
        out += spec_table(d["specs"], ["Параметр", "Значение"])
        out += "<p><small>Производительность указана для грунта II–III категории при нормальном подъезде "\
               "и достаточном числе самосвалов под погрузкой. Если самосвал один, реальная выработка "\
               "будет заметно ниже — машина простаивает между рейсами.</small></p>"
        out += "<h2>Для каких работ</h2><ul>%s</ul>" % "".join("<li>%s</li>" % esc(x) for x in d["works"])
        out += "<h2>По какому грунту работает</h2><p>%s</p>" % esc(d["ground"])
    else:
        out += "<h2>Что вмещает и что вывозит</h2>"
        out += spec_table(d["specs"], ["Параметр", "Значение"])
        out += "<p><small>Объём грунта «в плотном теле» — это сколько кубов вынутого котлована "\
               "помещается в кузов. Он меньше объёма кузова, потому что при выемке грунт разрыхляется "\
               "и занимает на 20–30 % больше места.</small></p>"
        out += "<h2>Что возим</h2><ul>%s</ul>" % "".join("<li>%s</li>" % esc(x) for x in d["cargo"])
        out += "<h2>Как считать вывоз</h2><p>%s</p>" % esc(d["logistics"])

    out += "<h2>Стоимость аренды</h2>"
    out += "<p>Смена до 10 часов — %s, оператор и топливо включены. Подача считается отдельно, "\
           "по расстоянию до объекта.</p>" % money(price).lower()
    out += table

    out += "<h2>Частые вопросы</h2>%s" % faq_html(d["faqs"])
    return out


def geo_mo_prose(slug, prep, neigh):
    """Уникальный текст гео-страницы по Москве и области.
    Ось — логистика подачи и то, что реально мешает работать именно здесь."""
    d = GEO_MO_DATA[slug]
    out = ""
    for p in d["intro"]:
        out += "<p>%s</p>" % esc(p)

    out += "<h2>Подача техники в %s</h2>" % esc(prep)
    out += spec_table(d["logistics"], ["Параметр", "Как обстоит"])

    out += "<h2>Что чаще всего заказывают</h2><ul>%s</ul>" % "".join("<li>%s</li>" % esc(x) for x in d["objects"])

    out += "<h2>Местная особенность</h2><p>%s</p>" % d["local"]

    out += "<h2>Техника и цены</h2>"
    out += "<p>Ставки одинаковые по всей зоне работы — меняется только стоимость подачи, "\
           "она считается по километражу до объекта. Оператор и топливо входят в смену.</p>"
    out += price_table_types()

    out += "<h2>Куда ещё выезжаем с этого направления</h2>"
    out += "<p>Кроме работ в %s обслуживаем ближние точки: %s. "\
           "Если объектов несколько, выгоднее объединить их в один выезд — подача оплачивается один раз.</p>" % (
           esc(prep), esc(neigh))

    out += "<h2>Частые вопросы</h2>%s" % faq_html(d["faqs"])
    return out


def geo_rf_prose(slug, prep, neigh):
    """Уникальный текст гео-страницы по городу России.
    Ось — региональная специфика: грунты, климат, отрасли, логистика.
    Модель работы (партнёрская сеть) проговаривается честно и явно."""
    d = GEO_RF_DATA[slug]
    out = ""
    for p in d["intro"]:
        out += "<p>%s</p>" % esc(p)

    out += "<h2>Что влияет на работу в регионе</h2>"
    out += spec_table(d["factors"], ["Фактор", "Как обстоит"])

    out += "<h2>Типовые объекты и задачи</h2><ul>%s</ul>" % "".join("<li>%s</li>" % esc(x) for x in d["objects"])

    out += "<h2>Местная особенность</h2><p>%s</p>" % d["local"]

    out += "<h2>Как мы работаем в %s</h2>" % esc(prep)
    out += ("<p>Своего парка в городе у нас нет, и мы говорим об этом прямо: технику подбираем "
            "через партнёрскую сеть в регионе, фиксируем условия договором и называем реальный срок. "
            "Работаем по направлениям: %s — логистика считается от базы партнёра, а не от Москвы. "
            "Набор доступных машин подтверждаем по фактическому наличию на дату.</p>" % esc(neigh))

    out += "<h2>Частые вопросы</h2>%s" % faq_html(d["faqs"])
    return out


def hub_prose(slug, lead):
    """Уникальный текст хаба техники, у которого нет собственной ветки с таблицей моделей."""
    d = HUBS_DATA[slug]
    out = ""
    for p in d["intro"]:
        out += "<p>%s</p>" % esc(p)

    out += "<h2>%s</h2>" % esc(d["table_title"])
    out += spec_table(d["table_rows"], d["table_head"])

    out += "<h2>%s</h2><p>%s</p>" % (esc(d["key_title"]), esc(d["key_text"]))

    out += "<h2>Типовые задачи</h2><ul>%s</ul>" % "".join("<li>%s</li>" % esc(x) for x in d["points"])

    out += "<h2>Что советуем перед заказом</h2><p>%s</p>" % d["advice"]

    out += "<h2>Сколько это стоит</h2>"
    out += ("<p>Технику этого класса не считают по прайсу: стоимость складывается из срока работ, "
            "доставки и подготовки площадки, и на разных объектах отличается кратно. "
            "Пришлите задачу — посчитаем и назовём сумму целиком, без сюрпризов в счёте. "
            "Цены на технику с посменной ставкой смотрите в разделах "
            '<a href="/avtokrany/">автокранов</a>, <a href="/avtovyshki/">автовышек</a> '
            'и <a href="/manipulyatory/">манипуляторов</a>.</p>')

    out += "<h2>Частые вопросы</h2>%s" % faq_html(d["faqs"])
    return out


def task_prose(slug, tech, faqs):
    """Уникальный текст страницы услуги. Ось — ход самой работы:
    этапы, что готовит заказчик, где ошибаются, из чего складывается цена."""
    d = TASKS_DATA[slug]
    out = ""
    for p in d["intro"]:
        out += "<p>%s</p>" % esc(p)

    out += "<h2>Как проходит работа</h2><ol>%s</ol>" % "".join("<li>%s</li>" % esc(x) for x in d["stages"])

    out += "<h2>Что нужно подготовить заказчику</h2><ul>%s</ul>" % "".join("<li>%s</li>" % esc(x) for x in d["need"])

    out += "<h2>Где чаще всего ошибаются</h2><p>%s</p>" % esc(d["mistake"])

    out += "<h2>Какая техника нужна</h2>"
    out += ("<p>Обычно для этой задачи подходит <b>%s</b>. Точный выбор зависит от массы груза, "
            "высоты подъёма и подъезда к объекту — подберём бесплатно по фото или чертежу.</p>" % esc(tech))

    out += "<h2>Из чего складывается цена</h2><p>%s</p>" % d["price"]

    out += "<h2>Частые вопросы</h2>%s" % faq_html(faqs)
    return out


def hub_extra_intro(slug):
    """Уникальный вводный блок хаба: два абзаца плюс практическое замечание."""
    d = HUB_EXTRA[slug]
    out = "".join("<p>%s</p>" % esc(p) for p in d["intro"])
    out += "<h2>Что важно учесть при выборе</h2><p>%s</p>" % esc(d["note"])
    return out


# ---------------------------------------------------------------- SEO: длины сниппета
TITLE_LIMIT = 62      # запас до 65: кириллица шире латиницы в пикселях
DESC_LIMIT  = 158     # запас до 165

BRAND = "КРАН365"


def _clean(s):
    """Схлопывает пробелы и убирает повтор гео, если он уже есть в основе."""
    return re.sub(r"\s+", " ", s).strip()



def lc_first(s):
    """Строчная только первая буква — чтобы «Москвы» внутри фразы не превращалось в «москвы»."""
    s = _clean(s)
    return s[:1].lower() + s[1:] if s else s

def seo_title(core, geo=None, extra=None):
    """Собирает title в пределах лимита выдачи.

    core  — обязательная основа («Аренда автокрана 25 тонн»)
    geo   — регион, присоединяется без тире и только если его ещё нет в основе
    extra — уточнение через тире («цена от 16 300 ₽»)

    Части, которые не помещаются, не добавляются вовсе — обрывов на полуслове нет.
    """
    out = _clean(core)
    tail = " | " + BRAND
    if len(out) > TITLE_LIMIT:                     # длинный заголовок статьи
        cut = out[:TITLE_LIMIT - 1]
        out = cut[:cut.rfind(" ")].rstrip(" ,;:—-") + "…"
        return out

    if geo:
        geo = _clean(geo)
        has_geo = ("Москв" in out) or ("Росси" in out)
        if not has_geo and len(out) + 1 + len(geo) + len(tail) <= TITLE_LIMIT:
            out = out + " " + geo

    if extra:
        extra = _clean(extra)
        if len(out) + 3 + len(extra) + len(tail) <= TITLE_LIMIT:
            out = out + " — " + extra

    if len(out) + len(tail) <= TITLE_LIMIT:
        out += tail
    return out


def seo_desc(*parts):
    """Собирает description из предложений, пока укладывается в лимит.
    Обрывов на полуслове не бывает: предложение либо входит целиком, либо нет."""
    out = ""
    for p in parts:
        if not p:
            continue
        p = _clean(p)
        if not p.endswith((".", "!", "?")):
            p += "."
        cand = (out + " " + p).strip()
        if len(cand) <= DESC_LIMIT:
            out = cand
        elif not out:                      # первое предложение длиннее лимита
            cut = p[:DESC_LIMIT]
            i = cut.rfind(" ")
            out = cut[:i].rstrip(" ,;:—-") + "…"
    return out


BLOG_FOR_TYPE = {
    "avtokrany":         ("avtokrana-50", "gruzovaya-harakteristika", "kak-vybrat-avtokran"),
    "avtovyshki":        ("avtovyshka", "stropalshik", "podgotovka-ploshchadki"),
    "manipulyatory":     ("manipulyatora", "kran-ili-manipulyator", "razgruzka-fury"),
    "ekskavatory":       ("ekskavatora", "vyvoz-grunta", "podgotovka-ploshchadki"),
    "samosvaly":         ("vyvoz-grunta", "arenda-na-mesyac", "dogovor-arendy"),
    "traly":             ("perevozka-negabarita", "arenda-gusenichnogo", "dogovor-arendy"),
    "gusenichnye-krany": ("arenda-gusenichnogo", "montazh-metallokonstrukciy", "ppr-na-kran"),
    "bashennye-krany":   ("bashennyy-kran", "ppr-na-kran", "razreshenie-na-rabotu"),
}

# ---------------------------------------------------------------- генерация
def build():
    pages = 0
    home = ("Главная","/")

    # --- хабы типов
    for t in TYPES:
        crumbs = [home, (t["name"], "/%s/" % t["slug"])]
        faqs = [
            ("Что входит в стоимость смены?", "В стоимость смены входят работа опытного оператора и топливо. Дополнительно оплачивается только подача до объекта и, при необходимости, переработка сверх смены."),
            ("Как быстро подадите технику?", "По Москве и ближней области подаём технику в день обращения, в среднем в течение 2 часов. Срочную подачу согласуем по телефону."),
            ("Работаете с юрлицами и по ЭДО?", "Да. Оформляем договор, счёт и закрывающие документы, работаем с НДС и по электронному документообороту."),
            ("Есть ли минимальный заказ?", "Минимальный заказ — одна смена. Точные условия зависят от типа техники и удалённости объекта."),
        ]
        if t["slug"]=="avtokrany":
            prose = ('<p>%s</p><h2>Аренда автокрана по грузоподъёмности</h2>'
                     '<p>Подберём автокран под массу и габариты груза, высоту и вылет. Ниже — цены по грузоподъёмности; нажмите на нужную, чтобы посмотреть характеристики и заказать.</p>%s'
                     '<h2>Аренда автокрана по длине стрелы</h2>'
                     '<p>Если важнее вылет и высота, а не тонны, — выбирайте по длине стрелы.</p>%s'
                     '<h2>Для каких задач</h2><ul><li>Монтаж металлоконструкций и оборудования</li><li>Разгрузка фур и подача материалов на высоту</li><li>Установка модульных зданий и бытовок</li><li>Подъём ЖБИ, плит, ферм, вентиляции на кровлю</li></ul>'
                     '<h2>Частые вопросы</h2>%s') % (esc(t["lead"]), tonnage_table(),
                     param_table(STRELA,"/avtokrany/strela-",("метров","metrov")), faq_html(faqs))
            rel = (related_tonnages(-1) + related_param(STRELA,"/avtokrany/strela-",("метров","metrov"),-1,"Длина стрелы")
                   + related_marki() + related_blog(*BLOG_FOR_TYPE["avtokrany"]) + related_tasks()
                   + related_geo() + related_types(t["slug"]))
        elif t["slug"] == "avtovyshki":
            prose = hub_extra_intro("avtovyshki") + ('<h2>Аренда автовышки по высоте подъёма</h2>'
                     '<p>Подберём автовышку по рабочей высоте и вылету. Цены «от», за смену, оператор и топливо включены.</p>%s'
                     '<h2>Для каких работ</h2><ul><li>Монтаж и обслуживание освещения</li><li>Работы на фасадах и остеклении</li><li>Установка вывесок и рекламных конструкций</li><li>Обрезка деревьев, клининг высотных объектов</li></ul>'
                     '<h2>Частые вопросы</h2>%s') % (param_table(VYSHKI,"/avtovyshki/",("метров","metrov")), faq_html(faqs))
            rel = (related_param(VYSHKI,"/avtovyshki/",("метров","metrov"),-1,"Высота подъёма")
                   + related_blog(*BLOG_FOR_TYPE["avtovyshki"]) + related_types(t["slug"]) + related_geo())
        elif t["slug"] == "manipulyatory":
            prose = hub_extra_intro("manipulyatory") + ('<h2>Аренда манипулятора по грузоподъёмности стрелы</h2>'
                     '<p>Кран-борт привезёт, разгрузит и установит груз за один выезд. Цены «от», за смену, с оператором и топливом.</p>%s'
                     '<h2>Что возят манипулятором</h2><ul><li>Бытовки, модульные здания, посты охраны</li><li>Ёмкости, септики, кессоны</li><li>Стройматериалы, ЖБИ, поддоны</li><li>Спецтехника и оборудование</li></ul>'
                     '<h2>Частые вопросы</h2>%s') % (param_table(MANIP,"/manipulyatory/",("тонн","tonn")), faq_html(faqs))
            rel = (related_param(MANIP,"/manipulyatory/",("тонн","tonn"),-1,"Грузоподъёмность стрелы")
                   + related_blog(*BLOG_FOR_TYPE["manipulyatory"]) + related_tasks() + related_types(t["slug"]) + related_geo())
        elif t["slug"] in ("ekskavatory", "samosvaly"):
            items = EKSK if t["slug"] == "ekskavatory" else SAMOSVAL
            base = "/%s/" % t["slug"]
            rows = "".join('<tr><td><a href="%s%s/" style="color:var(--ink)">%s</a></td><td>%s</td><td><b>%s</b> <span style="color:var(--muted-2);font-size:.82rem">/ смена</span></td></tr>' % (
                base, s2, esc(n2), esc(d2), money(p2)) for s2, n2, d2, p2 in items)
            tbl = '<div class="ptable-wrap"><table class="ptable"><thead><tr><th>Техника</th><th>Параметры</th><th>Цена</th></tr></thead><tbody>%s</tbody></table></div>' % rows
            prose = hub_extra_intro(t["slug"]) + ('<h2>Модели и цены</h2><p>Стоимость указана «от», за смену — включает работу оператора и топливо.</p>%s'
                     '<h2>Частые вопросы</h2>%s') % (
                     tbl, faq_html(faqs))
            rel = ('<div class="related"><h3>Модели</h3><div class="related-grid">%s</div></div>' %
                   "".join('<a href="%s%s/">%s</a>' % (base, s2, esc(n2)) for s2, n2, _, _ in items)) + related_blog(*BLOG_FOR_TYPE.get(t["slug"], ())) + related_tasks() + related_types(t["slug"]) + related_geo()
        elif t["slug"] in HUBS_DATA:
            prose = hub_prose(t["slug"], t["lead"])
            faqs = HUBS_DATA[t["slug"]]["faqs"]
            rel = related_blog(*BLOG_FOR_TYPE.get(t["slug"], ())) + related_types(t["slug"]) + related_tasks() + related_geo()
        else:
            prose = ('<p>%s</p><h2>Цены на аренду</h2><p>Стоимость указана «от», за смену — включает работу оператора и топливо. Точную цену под вашу задачу назовём по телефону.</p>%s'
                     '<h2>Частые вопросы</h2>%s') % (
                     esc(t["lead"]), price_table_types(t["slug"]), faq_html(faqs))
            rel = related_types(t["slug"]) + related_geo()
        rel += related_cats(limit=8)
        h1 = "Аренда %s в Москве и области" % t["one"]
        title = seo_title(h1, None, "цена %s" % money(t["price"]).lower())
        desc = seo_desc("Аренда %s в Москве и области: %s" % (t["one"], t["meta"]),
                        "Цена %s/смена, оператор и топливо включены" % money(t["price"]).lower(),
                        "Подача от 1 дня, договор и ЭДО")
        ld = [breadcrumb_ld(crumbs), service_ld("Аренда "+t["one"], t["lead"], t["price"]), faq_ld(faqs), local_business_ld()]
        page("%s/index.html" % t["slug"], title, desc, crumbs,
             hero("Аренда спецтехники", h1, t["lead"], t["price"]),
             body(prose, rel) + TRUST, ld)
        pages += 1

        # --- страницы автокранов по тоннажу
        if t["slug"]=="avtokrany":
            for tn, pr in AVTOKRAN:
                d = TONNAGE[tn]
                crumbs2 = [home, ("Автокраны","/avtokrany/"), ("%d тонн" % tn, "/avtokrany/%d-tonn/" % tn)]
                h1b = "Аренда автокрана %d тонн" % tn
                title2 = seo_title(h1b, "в Москве", "цена %s" % money(pr).lower())
                desc2 = seo_desc("Автокран %d тонн в Москве и области: %s" % (tn, lc_first(d["klass"])),
                                 ("Цена %s/смена" % money(pr).lower()) if pr else "Стоимость по расчёту",
                                 "Грузоподъёмность по вылету, требования к площадке")
                leadb = d["intro"][0]
                prose2 = tonnage_prose(tn, pr)
                rel2 = related_tonnages(tn) + related_geo()
                ld2 = [breadcrumb_ld(crumbs2), service_ld(h1b, leadb, pr), faq_ld(d["faqs"]), local_business_ld()]
                page("avtokrany/%d-tonn/index.html" % tn, title2, desc2, crumbs2,
                     hero("Автокраны · %d тонн" % tn, h1b, d["klass"], pr),
                     body(prose2, rel2), ld2)
                pages += 1

    # --- автовышки по высоте
    for h, pr in VYSHKI:
        d = VYSHKI_DATA[h]
        crumbs = [home, ("Автовышки","/avtovyshki/"), ("%d метров" % h, "/avtovyshki/%d-metrov/" % h)]
        h1 = "Аренда автовышки %d метров" % h
        lead = d["intro"][0]
        prose = vyshka_prose(h, pr)
        rel = related_param(VYSHKI,"/avtovyshki/",("метров","metrov"),h,"Другие высоты") + related_geo() + related_types("avtovyshki")
        ld = [breadcrumb_ld(crumbs), service_ld(h1, lead, pr), faq_ld(d["faqs"]), local_business_ld()]
        page("avtovyshki/%d-metrov/index.html" % h,
             seo_title(h1, "в Москве", "цена %s" % money(pr).lower()),
             seo_desc("Автовышка %d м в Москве и области: %s" % (h, lc_first(d["focus"])),
                      "Высота и боковой вылет, грузоподъёмность люльки",
                      "Цена %s/смена с оператором" % money(pr).lower()),
             crumbs, hero("Автовышки · %d м" % h, h1, d["focus"], pr), body(prose, rel), ld)
        pages += 1

    # --- манипуляторы по грузоподъёмности стрелы
    for t, pr in MANIP:
        d = MANIP_DATA[t]
        crumbs = [home, ("Манипуляторы","/manipulyatory/"), ("%d тонн" % t, "/manipulyatory/%d-tonn/" % t)]
        h1 = "Аренда манипулятора %d тонн" % t
        lead = d["intro"][0]
        prose = manip_prose(t, pr)
        rel = related_param(MANIP,"/manipulyatory/",("тонн","tonn"),t,"Другая грузоподъёмность") + related_tasks() + related_geo()
        ld = [breadcrumb_ld(crumbs), service_ld(h1, lead, pr), faq_ld(d["faqs"]), local_business_ld()]
        page("manipulyatory/%d-tonn/index.html" % t,
             seo_title(h1, "в Москве", "цена %s" % money(pr).lower()),
             seo_desc("Манипулятор %d тонн в Москве и области: вылет стрелы, грузоподъёмность борта" % t,
                      ("Цена %s/смена" % money(pr).lower()) if pr else "Стоимость по расчёту",
                      "Когда выгоднее автокрана"),
             crumbs, hero("Манипуляторы · %d т" % t, h1, d["focus"], pr), body(prose, rel), ld)
        pages += 1

    # --- марки автокранов
    for slug, name, txt in MARKI:
        d = MARKI_DATA[slug]
        crumbs = [home, ("Автокраны","/avtokrany/"), (name, "/avtokrany/marki/%s/" % slug)]
        h1 = "Аренда автокрана %s" % name
        lead = d["intro"][0]
        prose = marka_prose(slug, name)
        rel = related_marki(slug) + related_tonnages(-1) + related_geo()
        ld = [breadcrumb_ld(crumbs), service_ld(h1, lead, 16300), faq_ld(d["faqs"]), local_business_ld()]
        page("avtokrany/marki/%s/index.html" % slug,
             seo_title(h1, "в Москве", "модели и цены"),
             seo_desc("Автокраны %s в аренду: какие модели доступны, сильные и слабые стороны" % name,
                      "Запчасти и сервис, цены по тоннажу",
                      "Оператор в стоимости смены"),
             crumbs, hero("Автокраны · %s" % name, h1, d["focus"], 16300), body(prose, rel), ld)
        pages += 1

    # --- страницы под задачи клиента
    for slug, name, rod, lead, tech, pr, faqs in TASKS:
        crumbs = [home, ("Услуги","/uslugi/"), (name, "/uslugi/%s/" % slug)]
        h1 = name + " краном в Москве и области"
        prose = task_prose(slug, tech, faqs)
        rel = related_tasks(slug) + related_types() + related_geo()
        ld = [breadcrumb_ld(crumbs), service_ld(name, lead, pr), faq_ld(faqs), local_business_ld()]
        page("uslugi/%s/index.html" % slug,
             seo_title(name, "в Москве", "цена %s" % money(pr).lower()),
             seo_desc("%s в Москве и области: %s" % (name, lc_first(TASKS_DATA[slug]["angle"])),
                      "Как проходит работа и что подготовить",
                      "Оператор в стоимости, подача от 1 дня"),
             crumbs, hero("Услуги", h1, TASKS_DATA[slug]["angle"], pr), body(prose, rel) + TRUST, ld)
        pages += 1

    # --- хаб услуг
    crumbs = [home, ("Услуги","/uslugi/")]
    cards = "".join('<tr><td><a href="/uslugi/%s/" style="color:var(--ink)">%s</a></td><td>%s</td><td><b>%s</b></td></tr>' % (
        s, esc(n), esc(t), money(p)) for s, n, _, _, t, p, _ in TASKS)
    prose = (
        '<p>Заказчику редко нужен «автокран 32 тонны» — ему нужно поставить ангар, поднять оборудование '
        'на крышу или вывезти грунт. Поэтому мы берём задачу целиком: подбираем технику под конкретную работу, '
        'считаем стоимость и подаём машину на объект.</p>'
        '<p>Ниже — работы, которые выполняем чаще всего. На странице каждой расписано, как она проходит, '
        'что нужно подготовить с вашей стороны и где обычно ошибаются при планировании.</p>'
        '<div class="ptable-wrap"><table class="ptable"><thead><tr><th>Услуга</th><th>Техника</th><th>Цена от</th></tr></thead><tbody>%s</tbody></table></div>' % cards)
    prose += (
        '<h2>Что мы спрашиваем при заявке</h2>'
        '<p>Четыре вопроса, по ответам на которые техника подбирается за пару минут. '
        'Если ответов пока нет — присылайте фото площадки или чертёж, разберёмся сами.</p>'
        '<ul>'
        '<li><b>Что поднимаем или перевозим</b> — масса и габариты груза</li>'
        '<li><b>На какую высоту</b> — считая запас на стропы, а не высоту здания</li>'
        '<li><b>Откуда встанет техника</b> — расстояние до точки работ и что между ними</li>'
        '<li><b>Когда и на сколько</b> — дата, время и предполагаемая длительность</li>'
        '</ul>'
        '<h2>Три вещи, которые чаще всего срывают работы</h2>'
        '<p>По нашему опыту, техника простаивает не из-за поломок, а из-за неготовности объекта. '
        'Проверьте эти пункты до того, как машина выедет.</p>'
        '<ul>'
        '<li><b>Негде встать.</b> Опоры крана раскрываются на 4–8 метров в зависимости от класса. '
        'Освободите место заранее, особенно во дворах.</li>'
        '<li><b>Груз не готов.</b> Конструкции не разложены, ёмкость не привезена, котлован не выкопан — '
        'смена идёт, работа стоит.</li>'
        '<li><b>Нет ответственного.</b> Нужен человек, который встретит технику, покажет точки работ '
        'и примет груз. Без него крановщик ждёт.</li>'
        '</ul>'
        '<h2>Как считается стоимость</h2>'
        '<p>Минимальная единица — смена до 10 часов, в неё входят работа оператора и топливо. '
        'Отдельно считается подача по километражу до объекта. Для тяжёлой техники добавляются '
        'доставка противовеса и спецразрешения. От двух смен подряд ставка снижается: '
        'переезд и развёртывание оплачиваются один раз, а не каждый день.</p>')
    faqs_u = [("Как понять, какая техника нужна?","Опишите задачу — массу груза, высоту подъёма и откуда встанет машина. Инженер подберёт технику и назовёт цену за 5 минут, бесплатно. Если сомневаетесь в цифрах, пришлите фото площадки."),
              ("Что делать, если я не знаю точную массу груза?","Назовите, что это за груз и его габариты — по типовым конструкциям масса известна. Для нестандартного оборудования подойдёт паспорт или чертёж."),
              ("Работаете с частными лицами?","Да, работаем и с организациями, и с частными заказчиками. Для юрлиц — договор, счёт, закрывающие документы и ЭДО."),
              ("Есть ли работа в выходные и ночью?","Да, приём заявок круглосуточно. Ночные смены в городе — обычная практика: меньше трафика и проще перекрыть зону работ, ставка при этом не меняется."),
              ("Можно ли объединить несколько работ в один выезд?","Можно и нужно, особенно на дальних направлениях: подача оплачивается один раз. Скажите обо всех задачах сразу — соберём их в одну смену.")]
    prose += "<h2>Частые вопросы</h2>" + faq_html(faqs_u)
    ld = [breadcrumb_ld(crumbs), service_ld("Услуги спецтехники","Аренда спецтехники под конкретные задачи в Москве и области",16300), faq_ld(faqs_u), local_business_ld()]
    page("uslugi/index.html", "Услуги спецтехники в Москве — монтаж, подъём, вывоз | КРАН365",
         seo_desc("Монтаж ангаров и металлоконструкций, установка бытовок, подъём на крышу, разгрузка фур, вывоз грунта",
                  "Техника с оператором, подача в день заявки"),
         crumbs, hero("Услуги", "Услуги спецтехники под вашу задачу",
                      "Не нужно разбираться, какой кран заказать — опишите задачу, подберём технику и назовём точную цену. Работаем по Москве и всей области круглосуточно.", 16300),
         body(prose, related_tasks() + related_types()) + TRUST, ld)
    pages += 1

    # --- автокраны по длине стрелы
    for m_, pr, tn in STRELA:
        d = STRELA_DATA[m_]
        crumbs = [home, ("Автокраны","/avtokrany/"), ("стрела %d м" % m_, "/avtokrany/strela-%d-metrov/" % m_)]
        h1 = "Аренда автокрана со стрелой %d метров" % m_
        lead = d["intro"][0]
        prose = strela_prose(m_, pr, tn)
        rel = related_param(STRELA,"/avtokrany/strela-",("метров","metrov"),m_,"Другие длины стрелы") + related_tonnages(-1) + related_geo()
        ld = [breadcrumb_ld(crumbs), service_ld(h1, lead, pr), faq_ld(d["faqs"]), local_business_ld()]
        page("avtokrany/strela-%d-metrov/index.html" % m_,
             seo_title(h1, None, "цена %s" % money(pr).lower()),
             seo_desc("Автокран со стрелой %d м: %s" % (m_, lc_first(d["focus"])),
                      "Высота подъёма, вылет, расчёт геометрии",
                      ("Цена %s/смена" % money(pr).lower()) if pr else "Стоимость по расчёту"),
             crumbs, hero("Автокраны · стрела %d м" % m_, h1, d["focus"], pr), body(prose, rel), ld)
        pages += 1

    # --- экскаваторы и самосвалы по моделям/параметрам
    for group, items, base, parent, kicker in (
        ("ekskavatory", EKSK, "/ekskavatory/", "Экскаваторы", "Экскаваторы"),
        ("samosvaly", SAMOSVAL, "/samosvaly/", "Самосвалы", "Самосвалы")):
        rows = "".join('<tr><td><a href="%s%s/" style="color:var(--ink)">%s</a></td><td>%s</td><td><b>%s</b> <span style="color:var(--muted-2);font-size:.82rem">/ смена</span></td></tr>' % (
            base, s, esc(n), esc(d_), money(p)) for s, n, d_, p in items)
        table = '<div class="ptable-wrap"><table class="ptable"><thead><tr><th>Техника</th><th>Параметры</th><th>Цена</th></tr></thead><tbody>%s</tbody></table></div>' % rows
        data = EKSK_DATA if group == "ekskavatory" else SAMOSVAL_DATA
        for s, n, d_, p in items:
            dd = data[s]
            crumbs = [home, (parent, base), (n, base + s + "/")]
            h1 = "Аренда: %s" % n
            lead = dd["intro"][0]
            prose = zemlya_prose(group, s, n, p, table)
            rel = ('<div class="related"><h3>Другая техника этого класса</h3><div class="related-grid">%s</div></div>' %
                   "".join('<a href="%s%s/">%s</a>' % (base, s2, esc(n2)) for s2, n2, _, _ in items if s2 != s)) + related_tasks() + related_geo()
            ld = [breadcrumb_ld(crumbs), service_ld(n, lead, p), faq_ld(dd["faqs"]), local_business_ld()]
            page("%s/%s/index.html" % (group, s),
                 seo_title(n, "в Москве", "цена %s" % money(p).lower()),
                 seo_desc("%s в аренду в Москве и области: %s" % (n, d_),
                          dd["focus"],
                          "Цена %s/смена с оператором" % money(p).lower()),
                 crumbs, hero(kicker, h1, dd["focus"], p), body(prose, rel), ld)
            pages += 1

    # --- блог
    blog_links = "".join('<a href="/blog/%s/">%s</a>' % (s, esc(t)) for s, t, _, _ in BLOG)
    for s, t, lead, blocks in BLOG:
        crumbs = [home, ("Блог","/blog/"), (t, "/blog/%s/" % s)]
        parts = []
        for b in blocks:
            h_, txt = b[0], b[1]
            parts.append('<h2>%s</h2><p>%s</p>' % (esc(h_), esc(txt)))
            if len(b) > 2 and b[2]:
                parts.append(b[2])   # готовая разметка: таблица или список
        content = "".join(parts)
        # лид уже выведен в шапке страницы — в тексте его не повторяем
        prose = content
        prose += ('<h2>Нужна техника под вашу задачу?</h2><p>Опишите задачу — подберём машину и назовём точную цену за 5 минут. '
                  'Консультация бесплатна, приём заявок круглосуточно: <a href="tel:%s">%s</a>.</p>' % (PHONE_TEL, PHONE_DISP))
        rel = ('<div class="related"><h3>Другие статьи</h3><div class="related-grid">%s</div></div>' %
               "".join('<a href="/blog/%s/">%s</a>' % (s2, esc(t2)) for s2, t2, _, _ in BLOG if s2 != s)) + related_types() + related_tasks()
        ld = [breadcrumb_ld(crumbs),
              {"@context":"https://schema.org","@type":"Article","headline":t,"description":lead,
               "author":{"@type":"Organization","name":"КРАН365"},
               "publisher":{"@type":"Organization","name":"КРАН365"},
               "mainEntityOfPage":SITE+"/blog/%s/" % s},
              local_business_ld()]
        page("blog/%s/index.html" % s, seo_title(t), seo_desc(lead), crumbs,
             hero("Блог", t, lead, None), body(prose, rel), ld)
        pages += 1

    # --- хаб блога
    crumbs = [home, ("Блог","/blog/")]
    cards = "".join('<tr><td><a href="/blog/%s/" style="color:var(--ink)">%s</a></td><td style="color:var(--muted)">%s</td></tr>' % (
        s, esc(t), esc(l[:110].rsplit(" ",1)[0] + "…")) for s, t, l, _ in BLOG)
    prose = ('<p>Разбираем практические вопросы аренды спецтехники: как выбрать кран, из чего складывается цена, '
             'как подготовить площадку и не переплатить за вывоз грунта. Пишем по опыту своих объектов.</p>'
             '<div class="ptable-wrap"><table class="ptable"><thead><tr><th>Статья</th><th>О чём</th></tr></thead><tbody>%s</tbody></table></div>' % cards)
    ld = [breadcrumb_ld(crumbs), local_business_ld()]
    page("blog/index.html", "Блог о спецтехнике — как выбрать кран и не переплатить | КРАН365",
         "Практические статьи об аренде спецтехники: выбор автокрана, стоимость смены, кран или манипулятор, подготовка площадки, расчёт вывоза грунта.",
         crumbs, hero("Блог", "Блог о спецтехнике",
                      "Практические разборы для тех, кто заказывает технику: что спросить, как посчитать и на чём не стоит экономить.", None),
         body(prose, '<div class="related"><h3>Все статьи</h3><div class="related-grid">%s</div></div>' % blog_links + related_types()), ld)
    pages += 1

    # --- гео-страницы
    for slug, prep, nom, route, neigh, spec in GEO:
        d = GEO_MO_DATA[slug]
        crumbs = [home, ("Зона работы","/#geo"), ("Аренда в %s" % prep, "/geo/%s/" % slug)]
        h1 = "Аренда крана и спецтехники в %s" % prep
        title = seo_title(h1, None, "подача и сроки")
        desc = seo_desc("Аренда спецтехники в %s: %s" % (prep, lc_first(d["angle"])),
                        "Сроки подачи, что учесть на месте",
                        "Какую технику берут чаще всего")
        lead = d["intro"][0]
        prose = geo_mo_prose(slug, prep, neigh)
        rel = related_geo(slug) + related_tasks() + related_types()
        ld = [breadcrumb_ld(crumbs), service_ld("Аренда спецтехники в %s" % prep, lead, 16300), faq_ld(d["faqs"]), local_business_ld()]
        page("geo/%s/index.html" % slug, title, desc, crumbs,
             hero("Зона работы", h1, d["angle"], 16300), body(prose, rel) + TRUST, ld)
        pages += 1

    # --- гео-страницы по России (через партнёрскую сеть — честная рамка, без «свой парк/сегодня»)
    for slug, prep, nom, route, neigh, spec in GEO_RF:
        d = GEO_RF_DATA[slug]
        crumbs = [home, ("Зона работы","/#geo"), ("Аренда в %s" % prep, "/geo/%s/" % slug)]
        h1 = "Аренда крана и спецтехники в %s" % prep
        title = seo_title(h1, None, "условия и сроки")
        desc = seo_desc("Аренда спецтехники в %s: %s" % (prep, lc_first(d["angle"])),
                        "Подача через партнёрскую сеть в регионе",
                        "Договор и закрывающие документы")
        lead = d["intro"][0]
        prose = geo_rf_prose(slug, prep, neigh)
        rel = related_geo_rf(slug) + related_tasks() + related_types()
        ld = [breadcrumb_ld(crumbs), service_ld("Аренда спецтехники в %s" % prep, lead, None), faq_ld(d["faqs"]), local_business_ld()]
        page("geo/%s/index.html" % slug, title, desc, crumbs,
             hero("Зона работы", h1, d["angle"], None), body(prose, rel) + TRUST, ld)
        pages += 1

    # --- новые категории спецтехники (диспетчер, максимальный каталог)
    for c in CATS:
        crumbs = [home, (c["name_nom"], "/%s/" % c["slug"])]
        faqs = [(f[0], f[1]) for f in c["faqs"]]
        rows = ""
        for it in c["items"]:
            specs = " · ".join(esc(s) for s in it["specs"])
            rows += '<tr><td>%s</td><td>%s</td><td><b>%s</b>%s</td></tr>' % (esc(it["name"]), specs, money(it.get("price")), price_hour_html(it.get("price")))
        table = ('<div class="ptable-wrap"><table class="ptable"><thead><tr><th>Модель</th><th>Характеристики</th>'
                 '<th>Цена</th></tr></thead><tbody>%s</tbody></table></div>') % rows
        prose = ('<p>%s</p>'
                 '<h2>Модели и цены</h2>'
                 '<p>Ниже — варианты, которые подбираем под задачу. Цена «от», за смену; окончательную называем после уточнения объёма и площадки.</p>%s'
                 '<h2>Как мы работаем</h2><ul>'
                 '<li>Находим и подаём технику из проверенной сети — с оператором и ответственностью за сроки по договору</li>'
                 '<li>Подбираем класс машины под ваш объём, грунт и задачу</li>'
                 '<li>Договор, счёт, закрывающие документы, ЭДО для юрлиц</li>'
                 '<li>Работаем по Москве, области и регионам России</li></ul>'
                 '<h2>Частые вопросы</h2>%s') % (esc(c["intro"]), table, faq_html(faqs))
        rel = related_cats(c["slug"]) + related_types() + related_tasks()
        ld = [breadcrumb_ld(crumbs), service_ld(c["h1"], c["lead"], c.get("price_from")), faq_ld(faqs), local_business_ld()]
        title = seo_title(c["h1"], "в Москве", "цена %s" % money(c.get("price_from")).lower())
        desc = seo_desc("%s: подберём и подадим технику из проверенной сети" % c["h1"],
                        "Оператор и топливо в стоимости смены",
                        "Договор, счёт и закрывающие документы")
        page("%s/index.html" % c["slug"], title, desc, crumbs,
             hero("Спецтехника", c["h1"], c["lead"], c.get("price_from")), body(prose, rel) + TRUST, ld)
        pages += 1

    # --- sitemap.xml
    urls = ["/"]
    for t in TYPES:
        urls.append("/%s/" % t["slug"])
    for tn,_ in AVTOKRAN:
        urls.append("/avtokrany/%d-tonn/" % tn)
    for m_,_,_ in STRELA:
        urls.append("/avtokrany/strela-%d-metrov/" % m_)
    for h,_ in VYSHKI:
        urls.append("/avtovyshki/%d-metrov/" % h)
    for s,_,_,_ in EKSK:
        urls.append("/ekskavatory/%s/" % s)
    for s,_,_,_ in SAMOSVAL:
        urls.append("/samosvaly/%s/" % s)
    urls.append("/blog/")
    for s,_,_,_ in BLOG:
        urls.append("/blog/%s/" % s)
    for t,_ in MANIP:
        urls.append("/manipulyatory/%d-tonn/" % t)
    for s,_,_ in MARKI:
        urls.append("/avtokrany/marki/%s/" % s)
    urls.append("/uslugi/")
    for s,_,_,_,_,_,_ in TASKS:
        urls.append("/uslugi/%s/" % s)
    for g in GEO:
        urls.append("/geo/%s/" % g[0])
    for g in GEO_RF:
        urls.append("/geo/%s/" % g[0])
    for c in CATS:
        urls.append("/%s/" % c["slug"])
    # Страницы, которые этот генератор не собирает, но которые обязаны быть
    # в карте сайта: контакты и правовые документы (см. tools/make_legal_pages.py).
    urls += [CONTACTS_URL, POLICY_URL, CONSENT_URL]
    import datetime as _dt
    _today = _dt.date.today().isoformat()
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join('<url><loc>%s%s</loc><lastmod>%s</lastmod></url>\n' % (SITE, u, _today) for u in urls) + "</urlset>\n"
    with open(os.path.join(ROOT,"sitemap.xml"),"w",encoding="utf-8") as f: f.write(sm)
    with open(os.path.join(ROOT,"robots.txt"),"w",encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE)

    print("OK: %d страниц + sitemap.xml (%d URL) + robots.txt" % (pages, len(urls)))

if __name__ == "__main__":
    build()
