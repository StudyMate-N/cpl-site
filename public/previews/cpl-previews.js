/* CPL guide previews: "Look inside the guides" section, card preview pills and a page viewer.
   Runs alongside the main app bundle and re-attaches if the app re-renders. */
(function () {
  'use strict';
  var CASES = [
    { slug: 'bebe-babbit', name: 'Bebe Babbit', label: 'Neurology · Case 01', dx: 'Migraine with aura', who: '26-year-old female with recurrent headaches', pages: 11, history: 28,
      sections: ['At a glance', 'History', 'Physical exam', 'Case findings', 'Diagnosis'] },
    { slug: 'marvin-webster', name: 'Marvin Webster', label: 'Respiratory · Case 02', dx: 'Influenza', who: '18-year-old male with fatigue and cough', pages: 10, history: 24,
      sections: ['At a glance', 'History', 'Physical exam', 'Case findings', 'Tests and differential', 'Problem statement'] },
    { slug: 'amanda-wheaton', name: 'Amanda Wheaton', label: 'ENT · Case 03', dx: 'Group A streptococcal pharyngitis', who: '23-year-old female with fever and sore throat', pages: 10, history: 42,
      sections: ['At a glance', 'History', 'Physical exam', 'Case findings', 'Tests and differential', 'Problem statement'] },
    { slug: 'krista-hampton', name: 'Krista Hampton', label: 'Dermatology · Case 04', dx: 'Allergic contact dermatitis', who: '25-year-old female with a new rash', pages: 11, history: 40,
      sections: ['At a glance', 'History', 'Physical exam', 'Case findings', 'Tests and differential', 'Problem statement'] },
    { slug: 'grady-turner', name: 'Grady Turner', label: 'Pediatrics · Case 05', dx: 'Bronchiolitis · Hospitalize', who: '18-month-old male with cough and fever', pages: 13, history: 33,
      sections: ['At a glance', 'History', 'Physical exam', 'Case findings', 'Tests and differential', 'Problem statement'] }
  ];
  var PAGES = [
    { n: 1, title: 'Cover & contents' },
    { n: 2, title: 'At a glance · OLD-CARTS' },
    { n: 3, title: 'History · verbatim responses' }
  ];
  var BASE = '/previews/';
  var current = 0;

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function img(c, p, small) { return BASE + c.slug + '-' + p.n + (small ? '-sm' : '') + '.webp'; }

  /* ── Viewer ─────────────────────────────────────────── */
  var dlg, dlgImg, dlgCap, dlgCount, vCase = 0, vPage = 0;
  function buildViewer() {
    dlg = el('dialog', 'cplp-viewer');
    dlg.setAttribute('aria-label', 'Guide preview');
    dlg.innerHTML = '<div class="cplp-viewer-bar"><span class="cplp-viewer-cap"></span><span class="cplp-viewer-count"></span><button type="button" class="cplp-x" aria-label="Close preview">×</button></div>' +
      '<div class="cplp-viewer-stage"><button type="button" class="cplp-nav cplp-prev" aria-label="Previous page">‹</button><img alt=""><button type="button" class="cplp-nav cplp-next" aria-label="Next page">›</button></div>' +
      '<div class="cplp-viewer-foot"><span>Preview pages are watermarked. The full guide is delivered once scope and timing are confirmed.</span><button type="button" class="cplp-cta">Request this case</button></div>';
    document.body.appendChild(dlg);
    dlgImg = dlg.querySelector('img'); dlgCap = dlg.querySelector('.cplp-viewer-cap'); dlgCount = dlg.querySelector('.cplp-viewer-count');
    dlg.querySelector('.cplp-x').onclick = function () { dlg.close(); };
    dlg.querySelector('.cplp-prev').onclick = function () { show(vPage - 1); };
    dlg.querySelector('.cplp-next').onclick = function () { show(vPage + 1); };
    dlg.querySelector('.cplp-cta').onclick = function () { dlg.close(); requestCase(); };
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') show(vPage + 1);
      if (e.key === 'ArrowLeft') show(vPage - 1);
    });
  }
  function show(p) {
    vPage = (p + PAGES.length) % PAGES.length;
    var c = CASES[vCase], pg = PAGES[vPage];
    dlgImg.src = img(c, pg, false);
    dlgImg.alt = c.name + ' guide, ' + pg.title + ' (preview)';
    dlgCap.textContent = c.name + ' · ' + pg.title;
    dlgCount.textContent = 'Page ' + pg.n + ' of ' + c.pages;
  }
  function openViewer(ci, p) {
    if (!dlg) buildViewer();
    vCase = ci; show(p || 0);
    if (!dlg.open) dlg.showModal();
  }
  function requestCase() {
    var b = document.querySelector('.library-request-link');
    if (b) b.click(); else location.hash = '#how-it-works';
  }
  function openCase(c) {
    var a = document.querySelector('.case-library-grid a[href="/case/' + c.slug + '"]');
    if (a) a.click(); else location.href = '/case/' + c.slug;
  }

  /* ── Section ────────────────────────────────────────── */
  function buildSection() {
    var s = el('section', 'cplp container');
    s.id = 'look-inside';
    s.setAttribute('aria-labelledby', 'cplp-title');
    s.innerHTML =
      '<div class="cplp-head"><div><p class="cplp-eyebrow">Look inside the guides</p><h2 id="cplp-title">See the work before you request it.</h2>' +
      '<p class="cplp-lede">Real pages from current CPL case guides: every question with the patient\'s verbatim response, a clinic note beside it, and the reasoning behind each finding.</p></div>' +
      '<ul class="cplp-proof"><li><strong>167</strong><span>history entries across these five guides</span></li><li><strong>5–6</strong><span>sections in every guide</span></li><li><strong>v1.0</strong><span>versioned and dated</span></li></ul></div>' +
      '<div class="cplp-tabs" role="tablist" aria-label="Choose a case"></div>' +
      '<div class="cplp-body" role="tabpanel"><div class="cplp-pages"></div><aside class="cplp-side"></aside></div>' +
      '<p class="cplp-fine">Previews are watermarked and the history page is cut short. Full guides are delivered after we confirm your case version, scope and timing.</p>';
    var tabs = s.querySelector('.cplp-tabs');
    CASES.forEach(function (c, i) {
      var t = el('button', 'cplp-tab');
      t.type = 'button'; t.setAttribute('role', 'tab');
      t.innerHTML = '<small></small><span></span>';
      t.querySelector('small').textContent = c.label;
      t.querySelector('span').textContent = c.name;
      t.onclick = function () { select(s, i); };
      t.onkeydown = function (e) {
        if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
        e.preventDefault();
        var n = (i + (e.key === 'ArrowRight' ? 1 : CASES.length - 1)) % CASES.length;
        select(s, n); tabs.children[n].focus();
      };
      tabs.appendChild(t);
    });
    select(s, current);
    return s;
  }
  function select(s, i) {
    current = i;
    var c = CASES[i];
    Array.prototype.forEach.call(s.querySelectorAll('.cplp-tab'), function (t, n) {
      t.setAttribute('aria-selected', String(n === i)); t.tabIndex = n === i ? 0 : -1;
    });
    var pages = s.querySelector('.cplp-pages'); pages.replaceChildren();
    PAGES.forEach(function (p, n) {
      var b = el('button', 'cplp-page' + (n === 2 ? ' is-teaser' : ''));
      b.type = 'button';
      b.setAttribute('aria-label', 'Open ' + p.title + ' preview of the ' + c.name + ' guide');
      var frame = el('span', 'cplp-frame'), im = el('img');
      im.src = img(c, p, true); im.alt = ''; im.loading = 'lazy'; im.width = 480; im.height = 621;
      frame.appendChild(im); b.appendChild(frame);
      var cap = el('span', 'cplp-cap'); cap.appendChild(el('small', null, 'Page ' + p.n)); cap.appendChild(el('strong', null, p.title));
      b.appendChild(cap);
      b.onclick = function () { openViewer(i, n); };
      pages.appendChild(b);
    });
    var more = el('div', 'cplp-more');
    more.appendChild(el('strong', null, '+' + (c.pages - PAGES.length)));
    more.appendChild(el('span', null, 'more pages in the full guide'));
    pages.appendChild(more);

    var side = s.querySelector('.cplp-side'); side.replaceChildren();
    side.appendChild(el('p', 'cplp-eyebrow', c.label));
    side.appendChild(el('h3', null, c.name));
    side.appendChild(el('p', 'cplp-who', c.who));
    var dx = el('p', 'cplp-dx'); dx.appendChild(el('small', null, 'Diagnosis')); dx.appendChild(el('span', null, c.dx)); side.appendChild(dx);
    var stats = el('dl', 'cplp-stats');
    [['Pages', c.pages], ['Sections', c.sections.length], ['History entries', c.history]].forEach(function (r) {
      var d = el('div'); d.appendChild(el('dt', null, r[0])); d.appendChild(el('dd', null, String(r[1]))); stats.appendChild(d);
    });
    side.appendChild(stats);
    var ol = el('ol', 'cplp-sections');
    c.sections.forEach(function (name) { ol.appendChild(el('li', null, name)); });
    side.appendChild(ol);
    var row = el('div', 'cplp-actions');
    var req = el('button', 'cplp-cta', 'Request this case'); req.type = 'button'; req.onclick = requestCase;
    var open = el('button', 'cplp-link', 'Open case →'); open.type = 'button'; open.onclick = function () { openCase(c); };
    row.appendChild(req); row.appendChild(open); side.appendChild(row);
  }

  /* ── Card pills ─────────────────────────────────────── */
  function decorateCards() {
    CASES.forEach(function (c, i) {
      var a = document.querySelector('.case-library-grid a[href="/case/' + c.slug + '"]');
      if (!a || a.querySelector('.cplp-pill')) return;
      var pill = el('span', 'cplp-pill', 'Look inside');
      pill.setAttribute('role', 'button'); pill.tabIndex = 0;
      pill.setAttribute('aria-label', 'Preview pages from the ' + c.name + ' guide');
      function go(e) { e.preventDefault(); e.stopPropagation(); openViewer(i, 0); }
      pill.addEventListener('click', go);
      pill.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') go(e); });
      a.appendChild(pill);
    });
  }

  function mount() {
    var lib = document.getElementById('cases');
    if (lib && !document.getElementById('look-inside')) lib.insertAdjacentElement('afterend', buildSection());
    decorateCards();
  }
  var queued = false;
  new MutationObserver(function () {
    if (queued) return; queued = true;
    requestAnimationFrame(function () { queued = false; mount(); });
  }).observe(document.body, { childList: true, subtree: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
