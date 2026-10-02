/* CPL homepage: live case search, "what's on your mind" chips and the school strip. */
(function () {
  'use strict';

  /* ── Case search ─────────────────────────────────────────────
     Reads /cases.json (the catalog manifest) on first use. Submitting the
     form still goes to the full library at /cases/?q=… */
  var catalog = null, loading = null;
  var leadLabels = { 'same-day': 'Same-day', 'fast-build': '24–48h', 'on-request': 'Check availability' };
  function loadCatalog() {
    if (catalog) return Promise.resolve(catalog);
    if (!loading) loading = fetch('/cases.json').then(function (r) { return r.json(); })
      .then(function (data) { catalog = data; return data; })
      .catch(function () { loading = null; return []; });
    return loading;
  }
  function norm(value) { return String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, ''); }
  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function initials(name) {
    return name.split(/\s+/).filter(Boolean).slice(0, 2).map(function (w) { return w[0]; }).join('').toUpperCase();
  }

  document.querySelectorAll('[data-case-search]').forEach(function (form) {
    var input = form.querySelector('input[type=search]');
    var panel = form.querySelector('.search-results');
    var list = panel.querySelector('[data-results-list]');
    var label = panel.querySelector('[data-results-label]');
    var requestLabel = panel.querySelector('[data-request-label]');
    var requestBtn = panel.querySelector('[data-request-case]');
    if (window.matchMedia('(max-width:640px)').matches) input.placeholder = 'Patient, course, week or school\u2026';

    function setOpen(open) {
      panel.hidden = !open;
      input.setAttribute('aria-expanded', String(open));
      form.classList.toggle('is-open', open);
    }
    function render() {
      var raw = input.value.trim(), q = norm(raw);
      loadCatalog().then(function (cases) {
        if (input.value.trim() !== raw) return;
        var matched = q
          ? cases.filter(function (c) { return norm([c.title, c.cc, c.school, c.course, c.alias].join(' ')).indexOf(q) !== -1; })
          : cases.filter(function (c) { return c.ready; });
        list.replaceChildren();
        matched.slice(0, 5).forEach(function (c) {
          var name = c.title.split('—')[0].trim(), focus = c.title.split('—').slice(1).join('—').trim();
          var row = el('a', 'result-row'); row.href = '/case/' + c.slug + '/';
          row.appendChild(el('span', 'result-initials', initials(name)));
          var text = el('span', 'result-text');
          text.appendChild(el('span', 'result-name', name + (focus ? ' — ' + focus : '')));
          text.appendChild(el('span', 'result-meta', [c.course, c.school].filter(Boolean).join(' · ')));
          row.appendChild(text);
          row.appendChild(el('span', 'tag' + (c.lead === 'same-day' ? ' tag-ok' : ''), leadLabels[c.lead] || (c.ready ? 'Same-day' : 'Check availability')));
          list.appendChild(row);
        });
        label.textContent = q ? (matched.length ? (matched.length > 5 ? 'Top matches · ' + matched.length + ' in the library' : 'Matching cases') : 'No published case matches yet') : 'Same-day guides';
        requestLabel.textContent = q && !matched.length ? 'Can’t find “' + raw + '”?' : 'Not listed yet?';
        requestBtn.setAttribute('data-order', raw ? 'Case request — ' + raw : 'Case request');
        requestBtn.setAttribute('data-alias', raw);
        setOpen(true);
      });
    }
    var debounce;
    input.addEventListener('focus', render);
    input.addEventListener('input', function () { clearTimeout(debounce); debounce = setTimeout(render, 100); });
    form.addEventListener('focusout', function () {
      setTimeout(function () { if (!form.contains(document.activeElement)) setOpen(false); }, 120);
    });
    document.addEventListener('pointerdown', function (ev) { if (!form.contains(ev.target)) setOpen(false); });
    form.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && !panel.hidden) { setOpen(false); input.focus(); return; }
      if (ev.key !== 'ArrowDown' && ev.key !== 'ArrowUp') return;
      var items = Array.from(panel.querySelectorAll('a.result-row, [data-request-case]'));
      if (panel.hidden || !items.length) return;
      ev.preventDefault();
      var i = items.indexOf(document.activeElement);
      if (ev.key === 'ArrowDown') items[Math.min(i + 1, items.length - 1)].focus();
      else if (i <= 0) input.focus();
      else items[i - 1].focus();
    });
  });

  /* ── What's on your mind ─────────────────────────────────── */
  var chips = Array.from(document.querySelectorAll('[data-intent]'));
  var result = document.querySelector('[data-intent-result]');
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      var on = chip.getAttribute('aria-pressed') !== 'true';
      chips.forEach(function (c) { c.setAttribute('aria-pressed', String(c === chip && on)); });
      result.hidden = !on;
      if (!on) return;
      result.href = chip.getAttribute('data-href');
      result.querySelector('[data-intent-dest]').textContent = chip.getAttribute('data-dest');
      result.querySelector('[data-intent-cta]').textContent = chip.getAttribute('data-cta');
    });
  });

  /* ── School strip ─────────────────────────────────────────
     The strip scrolls continuously (CSS); it pauses on hover, on focus and
     while a school's panel is open. */
  var strip = document.querySelector('.school-strip');
  if (strip) {
    var tiles = Array.from(strip.querySelectorAll('[data-school]'));
    var panels = Array.from(document.querySelectorAll('.school-panel'));
    var current = null;
    function select(index) {
      current = current === index ? null : index;
      tiles.forEach(function (t) {
        var on = t.getAttribute('data-school') === String(current);
        t.classList.toggle('is-selected', on);
        if (t.hasAttribute('aria-expanded')) t.setAttribute('aria-expanded', String(on));
      });
      panels.forEach(function (p) { p.hidden = p.id !== 'school-panel-' + current; });
      strip.classList.toggle('is-held', current !== null);
    }
    tiles.forEach(function (t) {
      t.addEventListener('click', function () { select(t.getAttribute('data-school')); });
    });
  }
})();
