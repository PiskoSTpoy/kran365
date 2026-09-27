# -*- coding: utf-8 -*-
"""
Источники для статей блога, у которых в ТЕКСТЕ уже названа конкретная норма
(закон/ГОСТ/ФНП/постановление) с номером. Источник даёт факт и ссылку, не абзац
(правило №2/№8 скилла seo-2026-playbook). URL сверены WebSearch 28.09.2026 —
официальные КонсультантПлюс / docs.cntd.ru.

Формат совпадает с BLOG_EXTRA: {"checked": "YYYY-MM-DD", "sources": [(подпись, url), ...]}.
Подмешивается в BLOG_EXTRA поверх записей FAQ-бэкфилла (см. build_pages.py).
Только те статьи, где норма реально фигурирует в тексте; где проверяемой нормы
нет — источник НЕ добавляется.
"""

CHECKED = "2026-09-28"

# --- канонические ссылки (сверены поиском 28.09.2026) ---
U_GK_632   = "https://www.consultant.ru/document/cons_doc_LAW_9027/1ffe0cb622bfbe86c61d7d6df4c8c6011dfb45fe/"
U_GK_642   = "https://www.consultant.ru/document/cons_doc_LAW_9027/0980286733e45f8e2639d616606189838d3f3bcc/"
U_GK_PARA3 = "https://base.garant.ru/10164072/08b7d927fd863bb6a25ed3796d6629ee/"
U_PP_878   = "https://www.consultant.ru/document/cons_doc_LAW_29306/"
U_MAGISTR  = "https://www.consultant.ru/document/cons_doc_LAW_15847/cebcdba7ffea45125814d4120dcf2902c59567b6/"
U_PP_1507  = "https://www.consultant.ru/law/hotdocs/91005.html"
U_PP_160   = "https://www.consultant.ru/document/cons_doc_LAW_85368/"
U_FNP_461  = "https://www.consultant.ru/document/cons_doc_LAW_373321/"
U_MT_782N  = "https://www.consultant.ru/document/cons_doc_LAW_371453/"
U_PP_491   = "https://www.consultant.ru/document/cons_doc_LAW_62293/"
U_GOST_9818  = "https://docs.cntd.ru/document/1200122888"
U_GOST_52044 = "https://docs.cntd.ru/document/1200031478"
U_GOST_56195 = "https://docs.cntd.ru/document/1200114298"

BLOG_SOURCES_BACKFILL = {
    "dogovor-arendy-spectehniki-s-ekipazhem": {
        "checked": CHECKED,
        "sources": [
            ("ГК РФ, ст. 632 «Договор аренды транспортного средства с экипажем» — КонсультантПлюс", U_GK_632),
            ("ГК РФ, § 3 гл. 34 «Аренда транспортных средств», ст. 632–649 (в т.ч. ст. 640 об ответственности владельца) — Гарант", U_GK_PARA3),
        ],
    },
    "arenda-krana-bez-ekipazha": {
        "checked": CHECKED,
        "sources": [
            ("ГК РФ, ст. 642 «Договор аренды транспортного средства без экипажа» — КонсультантПлюс", U_GK_642),
            ("ГК РФ, § 3 гл. 34 «Аренда транспортных средств», ст. 632–649 — Гарант", U_GK_PARA3),
        ],
    },
    "ppr-na-kran-kto-sostavlyaet": {
        "checked": CHECKED,
        "sources": [
            ("ФНП «Правила безопасности ОПО, на которых используются подъёмные сооружения» — приказ Ростехнадзора от 26.11.2020 № 461, КонсультантПлюс", U_FNP_461),
        ],
    },
    "kran-u-gazoprovoda-ohrannaya-zona": {
        "checked": CHECKED,
        "sources": [
            ("Правила охраны газораспределительных сетей, п. 7 (охранная зона 2 м) — ПП РФ от 20.11.2000 № 878, КонсультантПлюс", U_PP_878),
            ("Правила охраны магистральных трубопроводов (охранная зона 25/100 м) — пост. Госгортехнадзора от 24.04.1992 № 9, КонсультантПлюс", U_MAGISTR),
        ],
    },
    "yamobur-u-gazoprovoda-ohrannaya-zona": {
        "checked": CHECKED,
        "sources": [
            ("Правила охраны газораспределительных сетей, п. 7 и пп. «з» п. 14 (глубина > 0,3 м) — ПП РФ от 20.11.2000 № 878, КонсультантПлюс", U_PP_878),
        ],
    },
    "kran-u-zheleznoy-dorogi-ohrannaya-zona": {
        "checked": CHECKED,
        "sources": [
            ("Положение об охранных зонах железных дорог — ПП РФ от 30.09.2025 № 1507 (в силе с 01.03.2026) — КонсультантПлюс", U_PP_1507),
        ],
    },
    "kran-u-lep-ohrannaya-zona": {
        "checked": CHECKED,
        "sources": [
            ("Правила установления охранных зон объектов электросетевого хозяйства — ПП РФ от 24.02.2009 № 160, КонсультантПлюс", U_PP_160),
            ("ФНП «Правила безопасности ОПО с подъёмными сооружениями» (минимальные расстояния до ЛЭП) — приказ Ростехнадзора от 26.11.2020 № 461, КонсультантПлюс", U_FNP_461),
        ],
    },
    "rabochiy-lyulki-avtovyshki-udostoverenie": {
        "checked": CHECKED,
        "sources": [
            ("ФНП по подъёмным сооружениям, п. 151 (назначение персонала) — приказ Ростехнадзора от 26.11.2020 № 461, КонсультантПлюс", U_FNP_461),
            ("Правила по охране труда при работе на высоте — приказ Минтруда России от 16.11.2020 № 782н, КонсультантПлюс", U_MT_782N),
        ],
    },
    "razreshenie-na-manipulyator-moskva": {
        "checked": CHECKED,
        "sources": [
            ("ФНП по подъёмным сооружениям — приказ Ростехнадзора от 26.11.2020 № 461 (с изм. приказом от 22.01.2024 № 16) — КонсультантПлюс", U_FNP_461),
        ],
    },
    "razreshenie-na-rabotu-krana-moskva": {
        "checked": CHECKED,
        "sources": [
            ("ФНП «Правила безопасности ОПО с подъёмными сооружениями» — приказ Ростехнадзора от 26.11.2020 № 461, КонсультантПлюс", U_FNP_461),
        ],
    },
    "montazh-lestnichnyh-marshey-kranom": {
        "checked": CHECKED,
        "sources": [
            ("ГОСТ 9818-2015 «Марши и площадки лестниц железобетонные» — docs.cntd.ru", U_GOST_9818),
        ],
    },
    "kran-dlya-ustanovki-bilborda": {
        "checked": CHECKED,
        "sources": [
            ("ГОСТ Р 52044-2003 «Наружная реклама на автомобильных дорогах и территориях городских и сельских поселений» — docs.cntd.ru", U_GOST_52044),
        ],
    },
    "uborka-snega-pogruzchikom-dvor": {
        "checked": CHECKED,
        "sources": [
            ("Правила содержания общего имущества в многоквартирном доме — ПП РФ от 13.08.2006 № 491, КонсультантПлюс", U_PP_491),
            ("ГОСТ Р 56195-2014 «Услуги содержания придомовой территории, сбора и вывоза бытовых отходов» — docs.cntd.ru", U_GOST_56195),
        ],
    },
}
