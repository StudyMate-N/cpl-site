/* CPL redesign — lightweight interactions */
(function () {
  'use strict';
  document.documentElement.classList.add('js');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── scroll reveal ── */
  var reveals = document.querySelectorAll('[data-reveal]');
  var revealAll = function () { reveals.forEach(function (el) { el.classList.add('is-revealed'); }); };
  if (reduce) {
    revealAll();
  } else if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          var d = parseInt(e.target.getAttribute('data-reveal-delay') || '0', 10);
          setTimeout(function () { e.target.classList.add('is-revealed'); }, d);
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    reveals.forEach(function (el) { io.observe(el); });
    /* safety net: if IO never delivers (flaky networks, restrictive envs),
       never leave content permanently hidden */
    setTimeout(revealAll, 1500);
  } else {
    revealAll();
  }

  /* ── decoded rubric reveal (the signature device) ── */
  var rubric = document.querySelector('.rubric[data-decode]');
  if (rubric) {
    var trigger = function () { rubric.classList.add('revealed'); };
    if (reduce) { trigger(); }
    else { setTimeout(trigger, 1100); }
  }

  /* ── animated counters ── */
  var counters = document.querySelectorAll('[data-counter]');
  var animateCount = function (el) {
    var target = parseFloat(el.getAttribute('data-counter'));
    var suffix = el.getAttribute('data-counter-suffix') || '';
    if (reduce) { el.textContent = target + suffix; return; }
    var start = null, dur = 1300;
    var tick = function (ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };
  if ('IntersectionObserver' in window) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { animateCount(e.target); cio.unobserve(e.target); } });
    }, { threshold: 0.5 });
    counters.forEach(function (el) { cio.observe(el); });
    setTimeout(function () { counters.forEach(function (el) { if (el.textContent === '0') animateCount(el); }); }, 1500);
  } else {
    counters.forEach(animateCount);
  }

  /* ── mobile menu ── */
  var burger = document.querySelector('.nav-burger');
  var menu = document.querySelector('.mobile-menu');
  var backdrop = document.querySelector('.menu-backdrop');
  var setMenu = function (open) {
    if (!menu) return;
    menu.classList.toggle('open', open);
    if (backdrop) backdrop.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
  };
  if (burger) burger.addEventListener('click', function () { setMenu(true); });
  document.querySelectorAll('[data-menu-close]').forEach(function (el) {
    el.addEventListener('click', function () { setMenu(false); });
  });
  if (backdrop) backdrop.addEventListener('click', function () { setMenu(false); });

  /* ── cheat-sheet card selection ── */
  document.querySelectorAll('.resource-card').forEach(function (card) {
    var cb = card.querySelector('input[type=checkbox]');
    card.addEventListener('click', function (ev) {
      if (ev.target.tagName === 'A') return;
      if (cb) { cb.checked = !cb.checked; card.classList.toggle('selected', cb.checked); }
    });
  });

  /* ── capture form (real backend: /api/subscribe) ── */
  document.querySelectorAll('[data-capture]').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var box = form.querySelector('[data-capture-msg]');
      var email = form.querySelector('input[type=email]');
      if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test((email.value || '').trim())) {
        if (box) { box.textContent = 'Please enter a valid email address.'; box.style.display = 'block'; }
        if (email) email.focus();
        return;
      }
      // Collect selected cheat-sheet volumes; default to all four if none picked
      var volumes = Array.prototype.map.call(
        form.querySelectorAll('input[name="volumes"]:checked'),
        function (cb) { return cb.value; }
      );
      if (!volumes.length) volumes = ['history', 'physical-exam', 'ddx', 'plan'];

      var controls = form.querySelectorAll('input,button');
      controls.forEach(function (i) { i.disabled = true; });
      var btn = form.querySelector('button[type=submit]');
      var orig = btn ? btn.textContent : '';
      if (btn) btn.textContent = 'Sending…';

      fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.value.trim(), volumes: volumes })
      }).then(function (res) { return res.json().then(function (d) { return { ok: res.ok && d.ok, d: d }; }); })
        .then(function (r) {
          if (r.ok) {
            try { localStorage.setItem('cpl.formEmail', email.value.trim()); } catch (e) {}
            window.location.href = '/thank-you/';
          } else {
            controls.forEach(function (i) { i.disabled = false; });
            if (btn) btn.textContent = orig;
            if (box) { box.textContent = (r.d && r.d.error) || 'Something went wrong. Please try again.'; box.style.display = 'block'; }
          }
        }).catch(function () {
          controls.forEach(function (i) { i.disabled = false; });
          if (btn) btn.textContent = orig;
          if (box) { box.textContent = 'Network error — please try again.'; box.style.display = 'block'; }
        });
    });
  });

  /* ── lightbox for guide preview pages ── */
  var lbTriggers = document.querySelectorAll('[data-lightbox]');
  if (lbTriggers.length) {
    var lb = document.createElement('div');
    lb.className = 'lightbox';
    lb.innerHTML = '<button class="lightbox-close" aria-label="Close">×</button><img alt="Guide page">';
    document.body.appendChild(lb);
    var lbImg = lb.querySelector('img');
    var closeLb = function () { lb.classList.remove('open'); document.body.style.overflow = ''; };
    lbTriggers.forEach(function (t) {
      t.addEventListener('click', function () {
        lbImg.src = t.getAttribute('data-lightbox');
        lb.classList.add('open');
        document.body.style.overflow = 'hidden';
      });
    });
    lb.querySelector('.lightbox-close').addEventListener('click', closeLb);
    lb.addEventListener('click', function (e) { if (e.target === lb) closeLb(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && lb.classList.contains('open')) closeLb(); });
  }
})();
