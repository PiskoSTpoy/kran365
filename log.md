# Лог ежедневного конвейера статей блога

Одна строка на запуск: дата · слаг · статус.

- 2026-09-24 · rabochiy-lyulki-avtovyshki-udostoverenie · опубликовано (94a0c55 + bda0c9c), живая проверка https://kran365.ru/blog/rabochiy-lyulki-avtovyshki-udostoverenie/ — 200, контент на месте
- 2026-09-24 · kak-vybrat-avtobetononasos-dlina-strely · опубликовано (2-я статья дня, информационная; 70cd33e), живая проверка https://kran365.ru/blog/kak-vybrat-avtobetononasos-dlina-strely/ — 200, контент на месте
- 2026-09-24 · kolesnyy-ili-gusenichnyy-ekskavator · опубликовано (3-я статья дня, сравнительная; 70cd33e), живая проверка https://kran365.ru/blog/kolesnyy-ili-gusenichnyy-ekskavator/ — 200, контент на месте
- 2026-09-24 · итог дня: 3/3 — дневная норма выполнена (rabochiy-lyulki-avtovyshki-udostoverenie, kak-vybrat-avtobetononasos-dlina-strely, kolesnyy-ili-gusenichnyy-ekskavator). Попутно (ed1e150): fix_sitemap_lastmod.py больше не считает блок «Ещё статьи» содержимым статьи — полная пересборка ставила всем 50 старым статьям lastmod = дата новой
- 2026-09-25 · kak-vybrat-strop-dlya-krana · закоммичено (информационная; 2e35c34 + d4dd5dc), **НЕ задеплоено** — push на GitHub не прошёл: токен недействителен (`gh auth status`: token invalid, Git Credential Manager ждёт интерактивный вход). Живая проверка не выполнялась
- 2026-09-25 · mini-ekskavator-ili-ekskavator-pogruzchik · закоммичено (сравнительная; 2e35c34), **НЕ задеплоено** — та же причина
- 2026-09-25 · rabota-krana-nochyu-moskva · закоммичено (практическая/региональная, закон г. Москвы № 42 + ст. 3.13 КоАП Москвы; 2e35c34), **НЕ задеплоено** — та же причина
- 2026-09-25 · итог дня: 3/3 написано и собрано, geo_check — 0 FAIL на новых страницах (FAIL только у 3 служебных файлов верификации), WARN только «КРАН365 в <50% абзацев» — оставлено сознательно (сущность абзаца — техника/норматив, бренд в половине абзацев = спам). Первые статьи с FAQ + «Источники · проверено» + FAQPage (BLOG_EXTRA в build_pages.py). Попутно (1706688): «обновлено» в meta-row теперь по последней правке видимого текста, а не по любому коммиту — иначе ретрофит 23eb692 ставил всем 200 страницам «обновлено 25.09». ДЕЙСТВИЕ ВЛАДЕЛЬЦУ: `gh auth login -h github.com`, затем `git push origin main` из kran365_site — уйдут 4 коммита
