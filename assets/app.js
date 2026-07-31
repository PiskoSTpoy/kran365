/* КРАН365 — интерактив главной. Без зависимостей. */
(function () {
  'use strict';

  /* ---------- Навбар: класс scrolled ---------- */
  var nav = document.getElementById('nav');
  function onScroll() {
    if (window.scrollY > 40) nav.classList.add('scrolled');
    else nav.classList.remove('scrolled');
  }
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  /* ---------- Бургер-меню (моб.) ---------- */
  var burger = document.getElementById('burger');
  var menu = document.getElementById('menu');
  if (burger && menu) {
    burger.addEventListener('click', function () {
      menu.classList.toggle('open');
    });
    menu.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') menu.classList.remove('open');
    });
  }

  /* ---------- Живой парк: рендер из park.json (сюда пишет выгрузка из 1С) ---------- */
  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
  }); }
  var liveGrid = document.getElementById('liveGrid');
  if (liveGrid && liveGrid.dataset.park && 'fetch' in window) {
    var STATUS = { free: ['s--free', 't--free'], part: ['s--part', 't--part'], busy: ['s--busy', 't--busy'] };
    fetch(liveGrid.dataset.park, { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (data) {
        if (!data || !Array.isArray(data.machines) || !data.machines.length) return;
        liveGrid.innerHTML = data.machines.map(function (m) {
          var st = STATUS[m.status] || STATUS.free;
          var specs = (m.specs || []).map(function (s) { return '<span>' + esc(s) + '</span>'; }).join('');
          var price = m.unit ? '<b>' + esc(m.price) + '</b> <span>' + esc(m.unit) + '</span>' : '<b>' + esc(m.price) + '</b>';
          return '<article class="mach reveal in">' +
              '<div class="mach__ph">' +
                (m.img ? '<img class="mach__img" src="' + esc(m.img) + '" alt="' + esc(m.name) + '" loading="lazy">'
                       : '<svg><use href="#' + esc(m.icon || 'i-crane') + '"/></svg>') +
                '<span class="mach__tag">' + esc(m.type) + '</span></div>' +
              '<div class="mach__body">' +
                '<h3>' + esc(m.name) + '</h3>' +
                '<div class="mach__specs">' + specs + '</div>' +
                '<div class="mach__status"><span class="s ' + st[0] + '"></span><span class="' + st[1] + '">' + esc(m.status_text) + '</span></div>' +
                '<div class="mach__foot"><span class="mach__price">' + price + '</span><a class="mach__btn" href="#order">' + esc(m.cta || 'Забронировать') + '</a></div>' +
              '</div>' +
            '</article>';
        }).join('');
      })
      .catch(function () { /* park.json недоступен — остаются демо-карточки из HTML */ });
  }

  /* ---------- Reveal-on-scroll ---------- */
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add('in');
          io.unobserve(en.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('in'); });
  }
  // Подстраховка: элементы, уже попавшие во вьюпорт при загрузке или переходе по #якорю
  // (deep-link из поиска, клик по меню), показываем сразу — без ожидания скролла.
  function revealInView() {
    var vh = window.innerHeight || document.documentElement.clientHeight;
    reveals.forEach(function (el) {
      if (el.classList.contains('in')) return;
      if (el.getBoundingClientRect().top < vh * 0.98) el.classList.add('in');
    });
  }
  window.addEventListener('scroll', revealInView, { passive: true });
  window.addEventListener('load', revealInView);
  window.addEventListener('hashchange', function () { setTimeout(revealInView, 60); });
  // несколько попыток — поймать позицию после перехода по #якорю на свежей загрузке
  [100, 400, 800, 1400].forEach(function (t) { setTimeout(revealInView, t); });

  /* ---------- Ленивая загрузка hero-видео ----------
     Грузим mp4 только на десктопе, при быстрой сети и без reduce-motion.
     Пока файла нет / условия не выполнены — остаётся SVG-постер с Ken Burns. */
  var video = document.querySelector('.hero__video');
  function heroVideo() {
    if (!video || !video.dataset.src) return;
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var conn = navigator.connection || {};
    var saveData = conn.saveData === true;
    var slow = /(2g|slow-2g)/.test(conn.effectiveType || '');
    var small = window.matchMedia('(max-width: 640px)').matches;
    if (reduce || saveData || slow || small) return;

    video.src = video.dataset.src;
    video.load();
    var show = function () { video.classList.add('is-playing'); };
    var tryPlay = function () { var p = video.play(); if (p && p.catch) p.catch(function () {}); };
    // как только появились кадры — показываем видео (даже если автоплей стартует чуть позже)
    video.addEventListener('loadeddata', function () { show(); tryPlay(); });
    video.addEventListener('playing', show);
    // если файл не найден/не декодируется — тихо остаёмся на SVG-постере
    video.addEventListener('error', function () { video.classList.remove('is-playing'); }, { once: true });
    tryPlay();
    // если политика автоплея заблокировала — запустить при первом действии пользователя
    var kick = function () {
      tryPlay();
      window.removeEventListener('scroll', kick);
      window.removeEventListener('pointerdown', kick);
      window.removeEventListener('touchstart', kick);
    };
    window.addEventListener('scroll', kick, { passive: true });
    window.addEventListener('pointerdown', kick);
    window.addEventListener('touchstart', kick);
  }
  if ('requestIdleCallback' in window) requestIdleCallback(heroVideo, { timeout: 2500 });
  else setTimeout(heroVideo, 1200);

  /* ---------- Валидация и демо-отправка формы ---------- */
  var form = document.getElementById('orderForm');
  if (form) {
    var phone = document.getElementById('f-phone');
    var ok = document.getElementById('formOk');

    // мягкая маска телефона
    phone.addEventListener('input', function () {
      var d = phone.value.replace(/\D/g, '');
      if (d[0] === '8') d = '7' + d.slice(1);
      if (d[0] !== '7') d = '7' + d;
      d = d.slice(0, 11);
      var out = '+7';
      if (d.length > 1) out += ' (' + d.slice(1, 4);
      if (d.length >= 4) out += ') ' + d.slice(4, 7);
      if (d.length >= 7) out += '-' + d.slice(7, 9);
      if (d.length >= 9) out += '-' + d.slice(9, 11);
      phone.value = out;
      phone.classList.remove('err');
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var digits = phone.value.replace(/\D/g, '');
      if (digits.length < 11) {
        phone.classList.add('err');
        phone.focus();
        return;
      }
      // ДЕМО: здесь на боевом сайте — отправка на бэкенд / CRM / Telegram.
      form.querySelectorAll('.field, .btn, small').forEach(function (el) { el.style.display = 'none'; });
      ok.style.display = 'block';
    });
  }

  /* ---------- Анимация счётчиков в герое ---------- */
  var counters = document.querySelectorAll('[data-count]');
  function krCount(el) {
    var target = parseFloat(el.getAttribute('data-count'));
    var suffix = el.getAttribute('data-suffix') || '';
    var dur = 1200, t0 = null;
    function step(ts) {
      if (t0 === null) t0 = ts;
      var p = Math.min((ts - t0) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased) + suffix;
      if (p < 1) requestAnimationFrame(step);
      else el.textContent = target + suffix;
    }
    requestAnimationFrame(step);
  }
  if (counters.length && 'IntersectionObserver' in window &&
      !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var cio = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { krCount(e.target); cio.unobserve(e.target); } });
    }, { threshold: 0.6 });
    counters.forEach(function (c) { cio.observe(c); });
  }

  /* ---------- Параллакс фона героя ---------- */
  var heroBg = document.querySelector('.hero__bg');
  if (heroBg && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var pTicking = false;
    window.addEventListener('scroll', function () {
      if (pTicking) return;
      pTicking = true;
      requestAnimationFrame(function () {
        var y = window.scrollY || window.pageYOffset || 0;
        if (y < 900) heroBg.style.transform = 'translate3d(0,' + (-y * 0.14) + 'px,0)';
        pTicking = false;
      });
    }, { passive: true });
  }

  /* ---------- Интерактивный подбор техники ---------- */
  var pkLoad = document.getElementById('pk-load');
  if (pkLoad) {
    var pkHeight = document.getElementById('pk-height'),
        pkTerm = document.getElementById('pk-term'),
        pkResult = document.getElementById('pk-result'),
        pkHint = document.getElementById('pk-hint'),
        pkName = document.getElementById('pk-name'),
        pkPrice = document.getElementById('pk-price');
    var pkRecommend = function () {
      var l = parseInt(pkLoad.value, 10) || 0,
          h = parseInt(pkHeight.value, 10) || 0,
          t = pkTerm.value;
      if (!l || !h || !t) { pkResult.hidden = true; if (pkHint) pkHint.hidden = false; return; }
      var lvl = Math.max(l, h), name, from;
      if (l <= 1 && h <= 1) { name = 'Автокран 25 тонн'; from = 16300; }
      else if (lvl <= 2) { name = 'Автокран 32–40 тонн'; from = 19900; }
      else if (lvl <= 3) { name = 'Автокран 50–70 тонн'; from = 34900; }
      else { name = 'Автокран 90+ тонн или гусеничный кран'; from = 0; }
      var price = from === 0 ? 'цена под запрос' : 'ориентир от ' + from.toLocaleString('ru-RU') + ' ₽ / смена';
      if (t === 'month' && from !== 0) price += ' · помесячно выгоднее';
      pkName.textContent = name;
      pkPrice.textContent = price;
      pkResult.hidden = false;
      if (pkHint) pkHint.hidden = true;
    };
    [pkLoad, pkHeight, pkTerm].forEach(function (el) { el.addEventListener('change', pkRecommend); });
  }

  /* ---------- Год в футере при необходимости ---------- */
})();
