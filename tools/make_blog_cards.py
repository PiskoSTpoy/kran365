# -*- coding: utf-8 -*-
"""
Карточки-постеры для статей блога — по образцу partnerkin.com (заголовок
вшит прямо в картинку, категория-плашка сверху), а не сток-фото. Пользователь
прислал ссылку на iStock для картинок к статьям — покупать/тащить оттуда
не стал: чужой стоковый контент без лицензии на коммерческий сайт незаконен.
Вместо этого — тот же приём, что уже понравился на partnerkin: карточка
рисуется, а не фотографируется, и получается бренд-консистентной бесплатно
(фирменный тёмный фон + оранжевый акцент + собственный знак #i-mark, а не
случайное стоковое фото крана без прав на использование).

Категория берётся из content-style-guide.md-логики (тот же принцип, что
у профилей тона): не выдумана заново, а выведена из темы статьи.

Запуск (из kran365_site):
    python tools/make_blog_cards.py
"""
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets", "img", "blog-cards")

W, H = 800, 500
BG = (12, 17, 24)         # #0C1118 — тот же фон, что у аватарки/сайта
BG2 = (21, 26, 33)        # #151A21 — вторая тёмная, для градиентной плашки снизу
ORANGE = (245, 116, 28)   # #F5741C
ORANGE_DIM = (120, 60, 20)
WHITE = (255, 255, 255)
MUTED = (150, 158, 168)

FONT_DIR = "C:/Windows/Fonts"
F_HEAD = os.path.join(FONT_DIR, "segoeuib.ttf")   # заголовок — bold
F_TAG = os.path.join(FONT_DIR, "segoeuib.ttf")    # плашка категории — bold, мельче
F_MARK = os.path.join(FONT_DIR, "segoeuib.ttf")

# слаг → (заголовок карточки — короче h1, категория)
# Категории — та же логика, что в content-style-guide.md: документы (профиль А),
# выбор/цена (профиль Б, самый частый интент поиска), техника (карточка модели),
# на объекте (профиль В, кейсовый).
CARDS = {
    "kak-vybrat-avtokran": ("Как выбрать автокран: 3 цифры, которые решают всё", "ВЫБОР И ЦЕНА"),
    "skolko-stoit-arenda-krana": ("Сколько стоит аренда крана и из чего складывается цена", "ВЫБОР И ЦЕНА"),
    "kran-ili-manipulyator": ("Кран или манипулятор: что дешевле для вашей задачи", "ВЫБОР И ЦЕНА"),
    "podgotovka-ploshchadki": ("Как подготовить площадку к приезду крана", "НА ОБЪЕКТЕ"),
    "vyvoz-grunta-kak-schitat": ("Вывоз грунта: как посчитать объём и не переплатить", "НА ОБЪЕКТЕ"),
    "arenda-na-mesyac": ("Помесячная аренда: когда это выгоднее смен", "ВЫБОР И ЦЕНА"),
    "arenda-avtokrana-50-tonn": ("Аренда автокрана 50 тонн: когда он нужен", "ТЕХНИКА"),
    "razreshenie-na-rabotu-krana-moskva": ("Разрешение на работу крана в Москве: ППР и наряд-допуск", "ДОКУМЕНТЫ"),
    "ppr-na-kran-kto-sostavlyaet": ("Что такое ППР на кран и кто его составляет", "ДОКУМЕНТЫ"),
    "gruzovaya-harakteristika-avtokrana": ("Грузовая характеристика автокрана: как её читать", "ВЫБОР И ЦЕНА"),
    "arenda-krana-zimoy": ("Аренда крана зимой: на что смотреть в цене", "НА ОБЪЕКТЕ"),
    "stropalshik-i-takelazh": ("Стропальщик и такелаж: кто отвечает за строповку", "НА ОБЪЕКТЕ"),
    "montazh-metallokonstrukciy-avtokranom": ("Монтаж металлоконструкций автокраном", "НА ОБЪЕКТЕ"),
    "arenda-gusenichnogo-krana": ("Аренда гусеничного крана: когда выгоднее автокрана", "ТЕХНИКА"),
    "bashennyy-kran-arenda-montazh-demontazh": ("Башенный кран: монтаж, аренда и демонтаж", "ТЕХНИКА"),
    "avtovyshka-arenda-vysota-teleskop-ili-kolenchataya": ("Автовышка: телескоп или коленчатая — как выбрать", "ТЕХНИКА"),
    "yamobur-burilno-kranovaya-mashina-zadachi-raschet": ("Ямобур: для каких задач и как считать", "ТЕХНИКА"),
    "arenda-manipulyatora-gruzopodemnost-borta-i-strely": ("Манипулятор: грузоподъёмность борта и стрелы", "ТЕХНИКА"),
    "razgruzka-fury-manipulyatorom": ("Разгрузка фуры манипулятором: как заказать", "НА ОБЪЕКТЕ"),
    "perevozka-negabarita-tralom": ("Перевозка негабарита тралом", "ДОКУМЕНТЫ"),
    "arenda-ekskavatora-pogruzchika": ("Экскаватор-погрузчик: типовые задачи", "ТЕХНИКА"),
    "dogovor-arendy-spectehniki-s-ekipazhem": ("Договор аренды спецтехники с экипажем: что проверить", "ДОКУМЕНТЫ"),
    "kran-u-lep-ohrannaya-zona": ("Кран у ЛЭП: охранная зона и минимальные расстояния", "ДОКУМЕНТЫ"),
    "zayavki-na-tehniku-teryayutsya-v-chatah": ("Почему заявки на технику теряются в чатах", "НА ОБЪЕКТЕ"),
    "uchet-topliva-brigady-spectehniki": ("Кто теряет топливо, если бригаду никто не считает", "НА ОБЪЕКТЕ"),
}

# Фирменный знак сайта (#i-mark из index.html) — те же координаты, что в
# make_dzen_avatar.py, только меньше и в углу карточки, а не по центру.
MARK_LINES = [
    (13, 29, 13, 7, 2.6), (4.5, 7, 26.5, 7, 2.6),
    (13, 3.5, 24, 7, 1.7), (13, 3.5, 6.5, 7, 1.7), (13, 3.5, 13, 7, 1.7),
    (21.5, 7, 21.5, 12.5, 1.6), (19.6, 12.5, 23.4, 12.5, 2.2), (8.5, 29, 17.5, 29, 2.4),
]
MARK_RECT = (3.2, 5.4, 3.2 + 3.4, 5.4 + 3.2)


def draw_mark(dr, ox, oy, scale, color):
    def p(x, y):
        return (ox + x * scale, oy + y * scale)
    for x1, y1, x2, y2, w in MARK_LINES:
        dr.line([p(x1, y1), p(x2, y2)], fill=color, width=max(1, round(w * scale)))
        r = w * scale / 2
        for cx, cy in (p(x1, y1), p(x2, y2)):
            dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    rx0, ry0 = p(*MARK_RECT[:2]); rx1, ry1 = p(*MARK_RECT[2:])
    dr.rounded_rectangle([rx0, ry0, rx1, ry1], radius=max(1, (rx1 - rx0) * 0.2), fill=color)


def wrap_title(dr, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if dr.textlength(trial, font=font) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def make_card(slug, title, category):
    im = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(im)

    # Фоновая сетка — тонкие линии, как терминальный мотив в сети kran-network,
    # только едва заметная (это карточка КРАН365, не терминальный дизайн-код).
    for x in range(0, W, 40):
        dr.line([(x, 0), (x, H)], fill=(20, 26, 34), width=1)
    for y in range(0, H, 40):
        dr.line([(0, y), (W, y)], fill=(20, 26, 34), width=1)

    # Диагональная оранжевая полоса в углу — акцент без фото.
    dr.polygon([(W, 0), (W, 220), (W - 220, 0)], fill=(30, 22, 15))
    dr.line([(W - 220, 0), (W, 220)], fill=ORANGE_DIM, width=3)

    # Знак сайта — крупно, полупрозрачно, правый нижний угол (водяной знак).
    mark_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mdr = ImageDraw.Draw(mark_layer)
    draw_mark(mdr, W - 210, H - 260, 6.2, (245, 116, 28, 40))
    im.paste(mark_layer, (0, 0), mark_layer)

    # Плашка категории.
    f_tag = ImageFont.truetype(F_TAG, 22)
    tag_w = dr.textlength(category, font=f_tag) + 36
    dr.rounded_rectangle([48, 44, 48 + tag_w, 44 + 42], radius=21, fill=ORANGE)
    dr.text((48 + 18, 44 + 9), category, font=f_tag, fill=(20, 12, 4))

    # Заголовок, перенос по словам, крупно, снизу с отступом.
    f_head = ImageFont.truetype(F_HEAD, 46)
    max_w = W - 48 - 60
    lines = wrap_title(dr, title, f_head, max_w)
    if len(lines) > 4:
        lines = lines[:4]
    line_h = 58
    total_h = line_h * len(lines)
    y0 = H - 56 - total_h
    for i, ln in enumerate(lines):
        dr.text((50, y0 + i * line_h), ln, font=f_head, fill=WHITE)

    # Бренд-подпись снизу слева, мелко.
    f_brand = ImageFont.truetype(F_TAG, 18)
    draw_mark(dr, 50, H - 40, 0.9, MUTED)
    dr.text((78, H - 42), "КРАН365", font=f_brand, fill=MUTED)

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, slug + ".jpg")
    im.convert("RGB").save(out, "JPEG", quality=90)
    return out


if __name__ == "__main__":
    for slug, (title, cat) in CARDS.items():
        p = make_card(slug, title, cat)
        print("cards:", slug, "->", p)
    print("готово:", len(CARDS), "карточек в", OUT_DIR)
