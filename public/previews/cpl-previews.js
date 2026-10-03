/* CPL guide previews + direct requests.
   - "Look inside the guides" section: the first half of every guide, watermarked
   - "Look inside" pill on each library card, full-screen page viewer
   - Every request on the site goes straight to WhatsApp or email with the case
     details pre-filled (the app's multi-step request form is bypassed)
   Runs alongside the main app bundle and re-attaches if the app re-renders. */
(function () {
  'use strict';
  var WA_NUMBER = '12057279363';
  var EMAIL = 'support@unemployedproff.com';
  var SITE = 'https://www.clinicalperformancelab.com';
  var BASE = '/previews/';
  var SIX = ['At a glance', 'History', 'Physical exam', 'Case findings', 'Tests and differential', 'Problem statement'];
  function titles(shown, pe) {
    var t = ['Cover & contents', 'At a glance · OLD-CARTS', 'History · verbatim responses'];
    while (t.length < shown) t.push('History (cont.)');
    if (pe) t[shown - 1] = 'Physical exam';
    return t;
  }
  var CASES = [
    { slug: 'bebe-babbit', name: 'Bebe Babbit', label: 'Neurology · Case 01', dx: 'Migraine with aura', who: '26-year-old female with recurrent headaches', pages: 11, history: 28,
      sections: ['At a glance', 'History', 'Physical exam', 'Case findings', 'Diagnosis'], shown: titles(6) },
    { slug: 'marvin-webster', name: 'Marvin Webster', label: 'Respiratory · Case 02', dx: 'Influenza', who: '18-year-old male with fatigue and cough', pages: 10, history: 24, sections: SIX, shown: titles(5) },
    { slug: 'amanda-wheaton', name: 'Amanda Wheaton', label: 'ENT · Case 03', dx: 'Group A streptococcal pharyngitis', who: '23-year-old female with fever and sore throat', pages: 10, history: 42, sections: SIX, shown: titles(5) },
    { slug: 'krista-hampton', name: 'Krista Hampton', label: 'Dermatology · Case 04', dx: 'Allergic contact dermatitis', who: '25-year-old female with a new rash', pages: 11, history: 40, sections: SIX, shown: titles(6) },
    { slug: 'grady-turner', name: 'Grady Turner', label: 'Pediatrics · Case 05', dx: 'Bronchiolitis · Hospitalize', who: '18-month-old male with cough and fever', pages: 13, history: 33, sections: SIX, shown: titles(7, true) }
  ];
  var current = 0;

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function img(c, n, small) { return BASE + c.slug + '-' + (n + 1) + (small ? '-sm' : '') + '.webp'; }
  function caseByName(name) {
    var q = String(name || '').trim().toLowerCase();
    if (!q) return null;
    for (var i = 0; i < CASES.length; i++) if (CASES[i].name.toLowerCase() === q || q.indexOf(CASES[i].name.toLowerCase()) !== -1) return CASES[i];
    return null;
  }

  /* ── Direct request: WhatsApp or email, details pre-filled ─────────── */
  var chooser;
  function message(service, c, patient) {
    var lines = ['Hi CPL, I’d like to request: ' + (service || 'a case guide') + '.'];
    if (c) {
      lines.push('', 'Case: ' + c.name + ' — ' + c.label, 'Patient: ' + c.who, 'Diagnosis: ' + c.dx, 'Guide: ' + SITE + '/case/' + c.slug);
    } else {
      lines.push('', 'Case / patient name: ' + (patient || ''));
    }
    lines.push('', 'School / course / week (optional): ', 'Deadline (optional): ');
    return lines.join('\n');
  }
  function subject(service, c, patient) {
    return '[CPL] ' + (service || 'Case request') + (c ? ' · ' + c.name : patient ? ' · ' + patient : '');
  }
  function buildChooser() {
    chooser = el('dialog', 'cplp-send');
    chooser.setAttribute('aria-labelledby', 'cplp-send-title');
    chooser.innerHTML =
      '<button type="button" class="cplp-x" aria-label="Close">×</button>' +
      '<p class="cplp-eyebrow">Clinical Performance Lab · Direct request</p>' +
      '<h3 id="cplp-send-title">Send your request</h3>' +
      '<p class="cplp-send-sub">No forms. Your request is already written — pick WhatsApp or email and press send.</p>' +
      '<pre class="cplp-send-msg"></pre>' +
      '<div class="cplp-send-actions"><a class="cplp-wa" target="_blank" rel="noopener">WhatsApp us</a><a class="cplp-mail">Email us</a></div>' +
      '<button type="button" class="cplp-copy">Copy message</button>' +
      '<p class="cplp-send-fine">WhatsApp +1 (205) 727-9363 · ' + EMAIL + '<br>We confirm scope, timing and price before you pay.</p>';
    document.body.appendChild(chooser);
    chooser.querySelector('.cplp-x').onclick = function () { chooser.close(); };
    chooser.addEventListener('click', function (e) { if (e.target === chooser) chooser.close(); });
    chooser.querySelector('.cplp-copy').onclick = function () {
      var b = this, txt = chooser.querySelector('.cplp-send-msg').textContent;
      (navigator.clipboard ? navigator.clipboard.writeText(txt) : Promise.reject()).then(
        function () { b.textContent = 'Copied'; setTimeout(function () { b.textContent = 'Copy message'; }, 1600); },
        function () { b.textContent = 'Select the text above to copy'; });
    };
  }
  function openRequest(service, c, patient) {
    if (!chooser) buildChooser();
    var msg = message(service, c, patient);
    chooser.querySelector('.cplp-send-msg').textContent = msg;
    chooser.querySelector('.cplp-wa').href = 'https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(msg);
    chooser.querySelector('.cplp-mail').href = 'mailto:' + EMAIL + '?subject=' + encodeURIComponent(subject(service, c, patient)) + '&body=' + encodeURIComponent(msg);
    if (dlg && dlg.open) dlg.close();
    if (!chooser.open) chooser.showModal();
  }
  function openCasePageCase() {
    var m = location.pathname.match(/^\/case\/([a-z-]+)/);
    if (m) for (var i = 0; i < CASES.length; i++) if (CASES[i].slug === m[1]) return CASES[i];
    var h = document.querySelector('main h1');
    return h ? caseByName(h.textContent) : null;
  }
  /* The app's request dialog: read what it was opened for, close it, open the chooser. */
  function interceptAppDialog(d) {
    requestAnimationFrame(function () {
      var svc = d.querySelector('.service-selected strong');
      var service = svc ? svc.textContent.trim() : '';
      if (/existing/i.test(service) || /continue your request/i.test(d.textContent)) service = 'Follow-up on an existing request (CPL reference: )';
      var patientInput = Array.prototype.find.call(d.querySelectorAll('input'), function (i) {
        var l = i.closest('label'); return l && /patient|case name/i.test(l.textContent);
      });
      var patient = patientInput ? patientInput.value.trim() : '';
      var c = caseByName(patient) || openCasePageCase();
      d.close();
      openRequest(service || 'Complete case package', c, c ? '' : patient);
    });
  }

  /* ── Viewer ─────────────────────────────────────────── */
  var dlg, dlgImg, dlgCap, dlgCount, vCase = 0, vPage = 0;
  function buildViewer() {
    dlg = el('dialog', 'cplp-viewer');
    dlg.setAttribute('aria-label', 'Guide preview');
    dlg.innerHTML = '<div class="cplp-viewer-bar"><span class="cplp-viewer-cap"></span><span class="cplp-viewer-count"></span><button type="button" class="cplp-x" aria-label="Close preview">×</button></div>' +
      '<div class="cplp-viewer-stage"><button type="button" class="cplp-nav cplp-prev" aria-label="Previous page">‹</button><img alt=""><button type="button" class="cplp-nav cplp-next" aria-label="Next page">›</button></div>' +
      '<div class="cplp-viewer-foot"><span class="cplp-viewer-note"></span><button type="button" class="cplp-cta">Request this case</button></div>';
    document.body.appendChild(dlg);
    dlgImg = dlg.querySelector('img'); dlgCap = dlg.querySelector('.cplp-viewer-cap'); dlgCount = dlg.querySelector('.cplp-viewer-count');
    dlg.querySelector('.cplp-x').onclick = function () { dlg.close(); };
    dlg.querySelector('.cplp-prev').onclick = function () { show(vPage - 1); };
    dlg.querySelector('.cplp-next').onclick = function () { show(vPage + 1); };
    dlg.querySelector('.cplp-cta').onclick = function () { openRequest('Complete case package', CASES[vCase]); };
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') show(vPage + 1);
      if (e.key === 'ArrowLeft') show(vPage - 1);
    });
  }
  function show(p) {
    var c = CASES[vCase], total = c.shown.length;
    vPage = (p + total) % total;
    dlgImg.src = img(c, vPage, false);
    dlgImg.alt = c.name + ' guide, ' + c.shown[vPage] + ' (preview)';
    dlgCap.textContent = c.name + ' · ' + c.shown[vPage];
    dlgCount.textContent = 'Page ' + (vPage + 1) + ' of ' + c.pages;
    dlg.querySelector('.cplp-viewer-note').textContent = vPage === total - 1
      ? 'That’s the preview. The remaining ' + (c.pages - total) + ' pages come with the full guide.'
      : 'Previewing ' + total + ' of ' + c.pages + ' pages. Watermarked.';
  }
  function openViewer(ci, p) {
    if (!dlg) buildViewer();
    vCase = ci; show(p || 0);
    if (!dlg.open) dlg.showModal();
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
      '<div class="cplp-head"><div><p class="cplp-eyebrow">Look inside the guides</p><h2 id="cplp-title">Read half the guide before you request it.</h2>' +
      '<p class="cplp-lede">The first half of every current CPL case guide, page for page: every question with the patient\'s verbatim response, a clinic note beside it, and the reasoning behind each finding.</p></div>' +
      '<ul class="cplp-proof"><li><strong>50%</strong><span>of every guide open to preview</span></li><li><strong>167</strong><span>history entries across five guides</span></li><li><strong>v1.0</strong><span>versioned and dated</span></li></ul></div>' +
      '<div class="cplp-tabs" role="tablist" aria-label="Choose a case"></div>' +
      '<div class="cplp-body" role="tabpanel"><div class="cplp-pages"></div><aside class="cplp-side"></aside></div>' +
      '<p class="cplp-fine">Preview pages are watermarked. Request on WhatsApp or by email — no forms; we confirm your case version, scope and timing before payment.</p>';
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
    var pages = s.querySelector('.cplp-pages'); pages.replaceChildren(); pages.scrollLeft = 0;
    c.shown.forEach(function (title, n) {
      var b = el('button', 'cplp-page');
      b.type = 'button';
      b.setAttribute('aria-label', 'Open page ' + (n + 1) + ', ' + title + ', of the ' + c.name + ' guide');
      var frame = el('span', 'cplp-frame'), im = el('img');
      im.src = img(c, n, true); im.alt = ''; im.loading = 'lazy'; im.width = 420; im.height = 544;
      frame.appendChild(im); b.appendChild(frame);
      var cap = el('span', 'cplp-cap'); cap.appendChild(el('small', null, 'Page ' + (n + 1))); cap.appendChild(el('strong', null, title));
      b.appendChild(cap);
      b.onclick = function () { openViewer(i, n); };
      pages.appendChild(b);
    });
    var more = el('button', 'cplp-more'); more.type = 'button';
    more.appendChild(el('strong', null, '+' + (c.pages - c.shown.length)));
    more.appendChild(el('span', null, 'more pages in the full guide'));
    more.appendChild(el('em', null, 'Request it →'));
    more.onclick = function () { openRequest('Complete case package', c); };
    pages.appendChild(more);

    var side = s.querySelector('.cplp-side'); side.replaceChildren();
    side.appendChild(el('p', 'cplp-eyebrow', c.label));
    side.appendChild(el('h3', null, c.name));
    side.appendChild(el('p', 'cplp-who', c.who));
    var dx = el('p', 'cplp-dx'); dx.appendChild(el('small', null, 'Diagnosis')); dx.appendChild(el('span', null, c.dx)); side.appendChild(dx);
    var stats = el('dl', 'cplp-stats');
    [['Preview', c.shown.length + ' of ' + c.pages], ['Sections', c.sections.length], ['History entries', c.history]].forEach(function (r) {
      var d = el('div'); d.appendChild(el('dt', null, r[0])); d.appendChild(el('dd', null, String(r[1]))); stats.appendChild(d);
    });
    side.appendChild(stats);
    var ol = el('ol', 'cplp-sections');
    c.sections.forEach(function (name) { ol.appendChild(el('li', null, name)); });
    side.appendChild(ol);
    var row = el('div', 'cplp-actions');
    var wa = el('a', 'cplp-wa', 'Request on WhatsApp'); wa.target = '_blank'; wa.rel = 'noopener';
    wa.href = 'https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(message('Complete case package', c));
    var mail = el('a', 'cplp-mail', 'Request by email');
    mail.href = 'mailto:' + EMAIL + '?subject=' + encodeURIComponent(subject('Complete case package', c)) + '&body=' + encodeURIComponent(message('Complete case package', c));
    row.appendChild(wa); row.appendChild(mail); side.appendChild(row);
    var open = el('button', 'cplp-link', 'Open case →'); open.type = 'button'; open.onclick = function () { openCase(c); };
    side.appendChild(open);
  }

  /* ── Card pills ─────────────────────────────────────── */
  function decorateCards() {
    CASES.forEach(function (c, i) {
      var a = document.querySelector('.case-library-grid a[href="/case/' + c.slug + '"]');
      if (!a || a.querySelector('.cplp-pill')) return;
      var pill = el('span', 'cplp-pill', 'Look inside · ' + c.shown.length + ' pages');
      pill.setAttribute('role', 'button'); pill.tabIndex = 0;
      pill.setAttribute('aria-label', 'Preview ' + c.shown.length + ' pages from the ' + c.name + ' guide');
      function go(e) { e.preventDefault(); e.stopPropagation(); openViewer(i, 0); }
      pill.addEventListener('click', go);
      pill.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') go(e); });
      a.appendChild(pill);
    });
  }

  /* "Request a case" buttons the app doesn't route to its form (e.g. the "Can't find your case?" card). */
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('button');
    if (!b || b.closest('.cplp, .cplp-send, .cplp-viewer') || b.classList.contains('library-request-link')) return;
    if (!/^\s*Request a case\s*$/i.test(b.textContent)) return;
    e.preventDefault(); e.stopPropagation();
    openRequest('New case guide', null);
  }, true);

  function mount() {
    var lib = document.getElementById('cases');
    if (lib && !document.getElementById('look-inside')) lib.insertAdjacentElement('afterend', buildSection());
    decorateCards();
  }
  var queued = false;
  new MutationObserver(function (records) {
    for (var r = 0; r < records.length; r++) {
      var t = records[r].target;
      if (records[r].type === 'attributes' && t.tagName === 'DIALOG' && t.open && t.classList.contains('request-dialog')) interceptAppDialog(t);
    }
    if (queued) return; queued = true;
    requestAnimationFrame(function () { queued = false; mount(); });
  }).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['open'] });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
