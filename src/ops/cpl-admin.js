/* CPL — Ops / Admin dashboard logic
   Order fulfillment state machine + live Resend email previews.
   States: new → invoiced → (ready: fulfilled | build: building → fulfilled)
   Human-in-the-loop = paste Payoneer link · confirm payment · upload guide.
   Everything else (emails, access codes, links) the system automates.
   Requires: cpl-emails.js (window.CPLEmails). Persists to localStorage. */
(function () {
  'use strict';

  /* ⇄ BACKEND SEAM ───────────────────────────────────────────────────
     This dashboard runs FULLY in the browser in demo mode: orders are
     seeded, persisted to localStorage, and all "emails / access links /
     uploads" are simulated. To ship for real, Claude Code swaps each
     marked block (search "⇄ LIVE:") for a fetch() to the noted endpoint —
     signatures + the Order shape stay identical. Full contract + data
     model + the 4 real integrations are in OPS-ADMIN-handoff.md.
       OPS.mode 'demo'  → localStorage (this file)
       OPS.mode 'live'  → GET/POST {OPS.base}/...  (server is source of truth)
     ─────────────────────────────────────────────────────────────────── */
  var OPS = { mode: 'live', base: '/api/ops' };

  var LS = 'cpl_admin_orders_v1';
  var BASE = 'https://www.clinicalperformancelab.com';
  var ADMIN_EMAIL = 'orders@clinicalperformancelab.com';
  var E = window.CPLEmails;

  /* ── live backend helpers ──────────────────────────────────────── */
  // fetch wrapper → { status, body } (body parsed JSON or null). Cookie auth.
  function api(path, opts) {
    opts = opts || {};
    opts.credentials = 'include';
    if (opts.body && !(opts.headers && opts.headers['Content-Type'])) {
      opts.headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
    }
    return fetch(OPS.base + path, opts).then(function (r) {
      return r.json().then(function (j) { return { status: r.status, body: j }; })
        .catch(function () { return { status: r.status, body: null }; });
    }).catch(function () { return { status: 0, body: null }; });
  }
  function fileToB64(file) {
    return new Promise(function (resolve, reject) {
      var fr = new FileReader();
      fr.onload = function () { resolve(String(fr.result).split(',')[1] || ''); };
      fr.onerror = reject;
      fr.readAsDataURL(file);
    });
  }
  function replaceOrder(updated) {
    if (!updated || !updated.id) return;
    for (var i = 0; i < orders.length; i++) {
      if (orders[i].id === updated.id) { orders[i] = updated; sel = updated.id; return; }
    }
    orders.unshift(updated); sel = updated.id;
  }
  function sessionLost() {
    try { localStorage.removeItem('cpl_ops_session'); } catch (e) {}
    document.body.classList.remove('ops-authed');
    toast('Session expired', 'Please sign in again.');
  }
  // Apply a server mutation response to the UI.
  function applyMutation(r, nextKey, msg, sub) {
    if (r.status === 401) { sessionLost(); return; }
    if (!r.body || (!r.body.ok && !r.body.order)) {
      toast('Something went wrong', (r.body && r.body.error) || 'Please try again.');
      render(); return;
    }
    if (r.body.order) replaceOrder(r.body.order);
    if (nextKey) mailKey = nextKey;
    if (r.body.error) toast('Saved, but email failed', r.body.error);
    else toast(msg, sub);
    flashStat(); render();
  }

  /* ── demo seed ─────────────────────────────────────────────── */
  var H = 3600e3, MIN = 60e3;
  function seed() {
    var now = Date.now();
    return [
      mk('CPL-1051', now - 6 * MIN, 'kayla.m.rivers@gmail.com', 'Bebe Babbitt — Migraine with Aura',
        'More frequent, more severe headaches', 150, true, 'Chamberlain', 'NR 509 · Wk 6', 'Bebe Babbitt', 'new'),
      mk('CPL-1050', now - 41 * MIN, 'dmwallace22@outlook.com', 'Ben Bundy — COPD Exacerbation',
        'Worsening shortness of breath', 150, false, 'Walden', 'NRNP 6531 · Wk 4', 'Ben Bundy', 'new'),
      mk('CPL-1049', now - 2.4 * H, 'priya.n.kapoor@yahoo.com', 'Christine Smith — Pyelonephritis',
        'Flank pain, fever, dysuria', 150, true, 'Walden', 'NRNP 6531 · Wk 7', 'Christine Smith', 'invoiced'),
      mk('CPL-1048', now - 5 * H, 'j.okeke.rn@gmail.com', 'Jacob Abraham — GERD',
        'Burning chest pain after meals', 150, false, 'Kaplan', '', 'Jacob Abraham', 'invoiced'),
      mk('CPL-1047', now - 9 * H, 'taylor.brooks.np@gmail.com', 'Maria Ash — Hypothyroidism',
        'Fatigue, weight gain, cold intolerance', 150, false, 'Kaplan', '', 'Maria Ash', 'building'),
      mk('CPL-1046', now - 26 * H, 'samanthalee.bsn@icloud.com', 'Harvey Hoya — Hypertension Stage 2',
        'High blood pressure at a health fair', 150, true, 'Chamberlain', 'NR 509', 'Harvey Hoya', 'fulfilled'),
      mk('CPL-1045', now - 30 * H, 'andre.coleman90@gmail.com', 'Lori Jacobs — Urinary Tract Infection',
        'Burning with urination ×3 days', 150, true, 'Walden', 'NRNP 6552', 'Lori Jacobs', 'fulfilled')
    ];
  }
  function mk(id, placedAt, email, kase, cc, price, ready, school, course, alias, status) {
    var o = { id: id, placedAt: placedAt, email: email, case: kase, cc: cc, price: price,
      amount: price, ready: ready, school: school, course: course, alias: alias, status: 'new',
      invoiceUrl: '', accessCode: '', accessUrl: '', events: [] };
    o.events.push(ev('placed', placedAt, 'Order placed', email));
    o.events.push(ev('mail', placedAt + 4e3, 'Sent', '“Order received” → ' + email, 'orderReceived'));
    o.events.push(ev('mail', placedAt + 5e3, 'Sent', '“New order” alert → ops', 'adminAlert'));
    // fast-forward to requested status
    if (status === 'invoiced' || status === 'building' || status === 'fulfilled') {
      o.invoiceUrl = 'https://pay.payoneer.com/inv/' + id.replace('CPL-', '8K3') + 'X';
      o.status = 'invoiced';
      o.events.push(ev('invoiced', placedAt + 30 * MIN, 'Invoice sent', E ? '' : '', 'invoice', 'Payoneer link · ' + fmtMoney(price)));
    }
    if (status === 'building') {
      o.status = 'building';
      o.events.push(ev('paid', placedAt + 3 * H, 'Payment confirmed', 'Marked paid by ops'));
      o.events.push(ev('mail', placedAt + 3 * H + 4e3, 'Sent', '“Building your guide” → ' + email, 'building'));
    }
    if (status === 'fulfilled') {
      o.status = 'fulfilled';
      o.accessCode = code();
      o.accessUrl = BASE + '/g/' + tok();
      o.events.push(ev('paid', placedAt + 1.5 * H, 'Payment confirmed', 'Marked paid by ops'));
      o.events.push(ev('fulfilled', placedAt + 1.5 * H + 3e3, 'Guide delivered', 'Auto-delivered (pre-built case)'));
      o.events.push(ev('mail', placedAt + 1.5 * H + 4e3, 'Sent', '“Your guide is ready” → ' + email, 'delivery'));
    }
    return o;
  }
  function ev(type, at, label, sub, mail, extra) {
    return { type: type, at: at, label: label, sub: extra || sub || '', mail: mail || '' };
  }
  function code() {
    var s = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789', r = '';
    for (var i = 0; i < 4; i++) r += s[Math.floor(Math.random() * s.length)];
    return 'CPL-' + r;
  }
  function tok() {
    var s = 'abcdefghijkmnpqrstuvwxyz0123456789', r = '';
    for (var i = 0; i < 14; i++) r += s[Math.floor(Math.random() * s.length)];
    return r;
  }

  /* ── state ─────────────────────────────────────────────────── */
  var orders, sel = null, filter = 'needs', mailKey = null;
  function load(cb) {
    if (OPS.mode === 'live') {
      // server is source of truth
      api('/orders').then(function (r) {
        if (r.status === 401) { sessionLost(); orders = orders || []; if (cb) cb(); return; }
        orders = (r.body && r.body.orders) || [];
        if (cb) cb();
      });
      return;
    }
    try { orders = JSON.parse(localStorage.getItem(LS)); } catch (e) { orders = null; }
    if (!orders || !orders.length) { orders = seed(); save(); }
    if (cb) cb();
  }
  // Background refresh in live mode — pick up inbound orders without disrupting edits.
  function refresh() {
    if (OPS.mode !== 'live') return;
    var editing = $detail && document.activeElement && $detail.contains(document.activeElement);
    if (editing) return; // don't yank an in-progress invoice/upload
    api('/orders').then(function (r) {
      if (r.status === 401) { sessionLost(); return; }
      if (!r.body || !r.body.orders) return;
      var before = JSON.stringify(orders.map(function (o) { return o.id + ':' + o.status; }));
      orders = r.body.orders;
      var after = JSON.stringify(orders.map(function (o) { return o.id + ':' + o.status; }));
      if (before !== after) render();
    });
  }
  function save() { try { localStorage.setItem(LS, JSON.stringify(orders)); } catch (e) {} }
  function find(id) { return orders.filter(function (o) { return o.id === id; })[0]; }

  /* ── helpers ───────────────────────────────────────────────── */
  function fmtMoney(n) { return '$' + Number(n).toLocaleString('en-US'); }
  function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  function ago(ts) {
    var s = Math.floor((Date.now() - ts) / 1000);
    if (s < 60) return 'just now';
    if (s < 3600) return Math.floor(s / 60) + 'm ago';
    if (s < 86400) return Math.floor(s / 3600) + 'h ago';
    return Math.floor(s / 86400) + 'd ago';
  }
  function needsAction(o) { return o.status === 'new' || o.status === 'building'; }
  var STATUS_LABEL = { new: 'New order', invoiced: 'Awaiting payment', building: 'Building', fulfilled: 'Fulfilled', cancelled: 'Cancelled' };

  /* ── email registry per order ──────────────────────────────── */
  function mailsFor(o) {
    var list = [];
    var sentOrder = true, sentAlert = true;
    list.push({ key: 'orderReceived', label: 'Order received', to: o.email, subject: 'We\u2019ve got your order \u2014 invoice on the way', sent: true });
    list.push({ key: 'adminAlert', label: 'Admin alert', to: ADMIN_EMAIL, subject: '\uD83D\uDD14 New order ' + o.id + ' \u2014 ' + shortCase(o), sent: true });
    list.push({ key: 'invoice', label: 'Invoice', to: o.email, subject: 'Your CPL invoice \u2014 ' + shortCase(o), sent: o.status !== 'new', queued: o.status === 'new' });
    if (!o.ready) {
      list.push({ key: 'building', label: 'Building notice', to: o.email, subject: 'Payment confirmed \u2014 building your guide', sent: o.status === 'building' || o.status === 'fulfilled', queued: o.status === 'invoiced' });
    }
    list.push({ key: 'delivery', label: 'Guide delivered', to: o.email, subject: 'Your guide is ready \u2014 open it now', sent: o.status === 'fulfilled', queued: o.status !== 'fulfilled' && (o.ready ? o.status === 'invoiced' : o.status === 'building') });
    return list;
  }
  function shortCase(o) { return o.case.split('\u2014')[0].trim(); }

  /* ── DOM refs ──────────────────────────────────────────────── */
  var $stats, $tabs, $list, $detail, _pollTimer = null;
  function init() {
    $stats = document.getElementById('admStats');
    $tabs = document.getElementById('admTabs');
    $list = document.getElementById('admList');
    $detail = document.getElementById('admDetail');

    var sim = document.getElementById('admSim');
    var env = document.getElementById('admEnv');
    if (OPS.mode === 'live') {
      // real orders arrive via the inbound webhook — no manual simulate
      if (sim) sim.style.display = 'none';
      if (env) { env.textContent = 'Live'; env.classList.add('live'); }
    } else if (sim) {
      sim.addEventListener('click', simulateOrder);
    }

    load(function () {
      // default selection = first action-needed order
      var first = orders.filter(needsAction)[0] || orders[0];
      if (first) sel = first.id;
      render();
      if (OPS.mode === 'live' && !_pollTimer) {
        _pollTimer = setInterval(refresh, 20000);
      }
    });
  }

  /* ── rendering ─────────────────────────────────────────────── */
  function counts() {
    var c = { needs: 0, all: orders.length, new: 0, invoiced: 0, building: 0, fulfilled: 0 };
    orders.forEach(function (o) { c[o.status]++; if (needsAction(o)) c.needs++; });
    return c;
  }
  function render() { renderStats(); renderTabs(); renderList(); renderDetail(); }

  function renderStats() {
    var c = counts();
    var paidToday = orders.filter(function (o) { return o.status === 'fulfilled' && (Date.now() - o.placedAt) < 36 * H; });
    var revenue = orders.filter(function (o) { return o.status === 'fulfilled'; }).reduce(function (s, o) { return s + (o.amount || o.price); }, 0);
    var awaiting = orders.filter(function (o) { return o.status === 'invoiced'; }).reduce(function (s, o) { return s + (o.amount || o.price); }, 0);
    var cards = [
      { v: c.needs, l: '<b>Action needed</b>', alert: true, f: 'needs', live: true },
      { v: c.invoiced, l: 'Awaiting payment · ' + fmtMoney(awaiting), f: 'invoiced' },
      { v: c.building, l: 'In build', f: 'building' },
      { v: paidToday.length, l: 'Fulfilled today', f: 'fulfilled' },
      { v: fmtMoney(revenue), l: 'Revenue · fulfilled', f: 'all' }
    ];
    $stats.innerHTML = cards.map(function (s) {
      return '<div class="adm-stat' + (s.live ? ' live' : '') + '" data-filter="' + s.f + '">' +
        '<div class="sv' + (s.alert && s.v ? ' alert' : '') + '">' + s.v + '</div>' +
        '<div class="sl">' + s.l + '</div></div>';
    }).join('');
    [].forEach.call($stats.querySelectorAll('.adm-stat'), function (el) {
      el.addEventListener('click', function () { filter = el.getAttribute('data-filter'); render(); });
    });
  }

  function renderTabs() {
    var c = counts();
    var tabs = [
      { k: 'needs', l: 'Action needed', n: c.needs, alert: true },
      { k: 'all', l: 'All', n: c.all },
      { k: 'new', l: 'New', n: c.new },
      { k: 'invoiced', l: 'Awaiting pay', n: c.invoiced },
      { k: 'building', l: 'Building', n: c.building },
      { k: 'fulfilled', l: 'Fulfilled', n: c.fulfilled }
    ];
    $tabs.innerHTML = tabs.map(function (t) {
      return '<button class="adm-tab' + (filter === t.k ? ' active' : '') + (t.alert && t.n ? ' alert' : '') + '" data-tab="' + t.k + '">' +
        t.l + '<span class="cnt">' + t.n + '</span></button>';
    }).join('');
    [].forEach.call($tabs.querySelectorAll('.adm-tab'), function (el) {
      el.addEventListener('click', function () { filter = el.getAttribute('data-tab'); render(); });
    });
  }

  function filtered() {
    var arr = orders.slice().sort(function (a, b) { return b.placedAt - a.placedAt; });
    if (filter === 'needs') return arr.filter(needsAction);
    if (filter === 'all') return arr;
    return arr.filter(function (o) { return o.status === filter; });
  }

  function renderList() {
    var arr = filtered();
    if (!arr.length) { $list.innerHTML = '<div style="padding:30px 14px;text-align:center;color:var(--muted);font-size:.88rem;">Nothing here right now.</div>'; return; }
    $list.innerHTML = arr.map(function (o) {
      return '<button class="adm-order' + (sel === o.id ? ' sel' : '') + (needsAction(o) ? ' needs' : '') + '" data-id="' + o.id + '">' +
        '<div class="adm-order-top"><span class="oid">' + o.id + '</span>' + pill(o) + '</div>' +
        '<div class="ocase">' + esc(o.case) + '</div>' +
        '<div class="oemail">' + esc(o.email) + '</div>' +
        '<div class="adm-order-bot"><span class="otime">' + ago(o.placedAt) + '</span>' +
        '<span style="font-family:var(--font-display);font-weight:600;color:var(--ink);">' + fmtMoney(o.amount || o.price) + '</span></div>' +
        '</button>';
    }).join('');
    [].forEach.call($list.querySelectorAll('.adm-order'), function (el) {
      el.addEventListener('click', function () { sel = el.getAttribute('data-id'); mailKey = null; render(); });
    });
  }

  function pill(o) {
    var dot = '<span class="pdot"></span>';
    return '<span class="pill ' + o.status + '">' + (o.status === 'fulfilled' ? '&#10003; ' : dot) + STATUS_LABEL[o.status] + '</span>';
  }

  function renderDetail() {
    var o = find(sel);
    if (!o) {
      $detail.innerHTML = '<div class="adm-empty"><div class="ico">\uD83D\uDCEC</div><h3>Select an order</h3><p>Pick an order from the queue to fulfill it and preview every email the system sends.</p></div>';
      return;
    }
    if (!mailKey) mailKey = defaultMailKey(o);
    var sub = [o.school, o.course].filter(Boolean).join(' · ') || '\u2014';
    $detail.innerHTML =
      '<div class="adm-detail-head">' +
        '<div class="adm-dh-top"><div><div class="oid">' + o.id + ' · placed ' + ago(o.placedAt) + '</div>' +
          '<h2>' + esc(o.case) + '</h2><p class="dcc">' + esc(o.cc) + '</p></div>' + pill(o) + '</div>' +
        '<div class="adm-meta-grid">' +
          meta('Customer', esc(o.email)) +
          meta('School · course', esc(sub)) +
          meta('Patient alias', esc(o.alias || '\u2014')) +
          meta('Price', fmtMoney(o.price)) +
        '</div>' +
        '<div style="margin-top:14px;">' + availBadge(o) + '</div>' +
      '</div>' +
      '<div class="adm-detail-body">' +
        '<div class="adm-actioncol">' + actionCard(o) + timeline(o) + '</div>' +
        '<div class="adm-mailcol">' + mailPane(o) + '</div>' +
      '</div>';
    wireDetail(o);
    paintMail(o);
  }
  function meta(l, v) { return '<div class="m"><span>' + l + '</span><b>' + v + '</b></div>'; }
  function availBadge(o) {
    return o.ready
      ? '<span class="adm-avail ready">\u26a1 Pre-built iHuman case \u2014 auto-delivers the instant payment is confirmed</span>'
      : '<span class="adm-avail build">\uD83D\uDD28 Not pre-built \u2014 you\u2019ll upload the guide after payment; student gets a build notice meanwhile</span>';
  }

  /* ── the staged action card (the human-in-the-loop) ────────── */
  function actionCard(o) {
    if (o.status === 'new') {
      return '<div class="action-card go">' +
        '<div class="action-eyebrow"><span class="step-n">1</span> Generate invoice</div>' +
        '<h3>Send the Payoneer invoice</h3>' +
        '<p class="ah">Create the invoice in Payoneer, then paste its link here. The system emails it to <b>' + esc(o.email) + '</b> automatically.</p>' +
        '<label class="adm-fld"><span>Payoneer invoice link</span>' +
          '<input type="url" id="invUrl" placeholder="https://pay.payoneer.com/\u2026" autocomplete="off"></label>' +
        '<label class="adm-fld"><span>Amount to bill <small>(pre-filled from order)</small></span>' +
          '<div class="adm-amount-wrap"><span class="cur">$</span><input type="number" id="invAmt" value="' + (o.amount || o.price) + '" min="0" step="1"></div></label>' +
        '<button class="btn btn-primary btn-lg btn-block" id="btnInvoice" disabled>Send invoice email \u2192</button>' +
        '</div>';
    }
    if (o.status === 'invoiced') {
      return '<div class="action-card go">' +
        '<div class="action-eyebrow"><span class="step-n">2</span> Confirm payment</div>' +
        '<h3>Mark payment confirmed</h3>' +
        '<p class="ah">Invoice sent for ' + fmtMoney(o.amount || o.price) + '. When Payoneer shows it paid, confirm below \u2014 the system takes the next step automatically.</p>' +
        '<div class="branch-note"><span class="bn-ico">' + (o.ready ? '\u26a1' : '\uD83D\uDD28') + '</span><div>' +
          (o.ready
            ? '<b>This case is pre-built.</b> On confirm, the system instantly generates an access code + magic link and emails the guide \u2014 no further action from you.'
            : '<b>This case isn\u2019t pre-built.</b> On confirm, the student gets a \u201cbuilding your guide\u201d notice and the order moves to your build queue to upload.') +
        '</div></div>' +
        '<button class="btn btn-primary btn-lg btn-block" id="btnPaid">Payment confirmed \u2014 ' + (o.ready ? 'deliver guide' : 'start build') + ' \u2192</button>' +
        '<button class="btn btn-ghost btn-sm btn-block" id="btnResend" style="margin-top:10px;">Resend invoice email</button>' +
        '</div>';
    }
    if (o.status === 'building') {
      return '<div class="action-card go">' +
        '<div class="action-eyebrow"><span class="step-n">3</span> Build &amp; deliver</div>' +
        '<h3>Upload the finished guide</h3>' +
        '<p class="ah">Paid &amp; in production. Drop the completed guide (Word + PDF) below \u2014 sending it auto-generates the access code &amp; magic link and emails <b>' + esc(o.email) + '</b>.</p>' +
        '<div class="dropzone" id="dz"><div class="dz-ico">\uD83D\uDCCe</div><b>Drop the guide here</b><span>or click to browse \u2014 .docx, .pdf, .zip</span></div>' +
        '<input type="file" id="dzInput" hidden multiple accept=".doc,.docx,.pdf,.zip">' +
        '<div id="dzFiles"></div>' +
        '<button class="btn btn-primary btn-lg btn-block" id="btnDeliver" disabled style="margin-top:12px;">Deliver guide \u2192</button>' +
        '</div>';
    }
    // fulfilled
    return '<div class="action-card">' +
      '<div class="action-done">' +
        '<div class="dbadge">\u2713</div><h3>Guide delivered</h3>' +
        '<p>Access was emailed to <b>' + esc(o.email) + '</b>. Magic link + backup code below.</p>' +
        '<div class="access-box">' +
          '<div class="row"><span class="lbl">Magic link</span><button class="copy-btn" data-copy="' + esc(o.accessUrl) + '">Copy</button></div>' +
          '<div class="row"><span class="lbl">Access code</span><span class="val">' + esc(o.accessCode) + '</span></div>' +
          '<div class="row"><span class="lbl">Link expires</span><span class="val" style="font-family:var(--font-body);">30 days</span></div>' +
        '</div>' +
        '<button class="btn btn-ghost btn-sm btn-block" id="btnResendDelivery">Resend delivery email</button>' +
      '</div></div>';
  }

  function timeline(o) {
    // build ordered milestone view
    var done = {};
    o.events.forEach(function (e) { done[e.type] = e; });
    var milestones = [
      { type: 'placed', tt: 'Order placed', sub: 'Email captured at checkout' },
      { type: 'invoiced', tt: 'Invoice sent', sub: 'Payoneer link emailed', mail: 'invoice' }
    ];
    if (!o.ready) milestones.push({ type: 'paid', tt: 'Payment confirmed', sub: 'Build started' });
    if (!o.ready) milestones.push({ type: 'building', tt: 'Building notice sent', sub: 'Student notified', mail: 'building', tieType: 'paid' });
    if (o.ready) milestones.push({ type: 'paid', tt: 'Payment confirmed', sub: 'Auto-delivery triggered' });
    milestones.push({ type: 'fulfilled', tt: 'Guide delivered', sub: 'Access link + code emailed', mail: 'delivery' });

    var order = ['placed', 'invoiced', 'paid', 'building', 'fulfilled'];
    function reached(t) {
      if (t === 'placed') return true;
      if (t === 'invoiced') return o.status !== 'new';
      if (t === 'paid') return o.status === 'building' || o.status === 'fulfilled';
      if (t === 'building') return (o.status === 'building' || o.status === 'fulfilled') && !o.ready;
      if (t === 'fulfilled') return o.status === 'fulfilled';
      return false;
    }
    // current step = first not reached
    var curType = null;
    for (var i = 0; i < milestones.length; i++) { if (!reached(milestones[i].type)) { curType = milestones[i].type; break; } }

    var lis = milestones.map(function (m) {
      var r = reached(m.type), cur = m.type === curType;
      var cls = r ? 'done' : (cur ? 'now' : 'pending');
      var mailLink = (m.mail && r) ? '<span class="tmail" data-mail="' + m.mail + '">View email \u2192</span>' : '';
      return '<li class="' + cls + '"><span class="tdot"></span><div class="tc">' +
        '<div class="tt">' + m.tt + '</div><div class="tsub">' + m.sub + '</div>' + mailLink + '</div></li>';
    }).join('');
    return '<h4 style="font-size:.74rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin:22px 0 0;">Fulfillment timeline</h4>' +
      '<ul class="timeline">' + lis + '</ul>';
  }

  /* ── email preview pane ────────────────────────────────────── */
  function defaultMailKey(o) {
    if (o.status === 'new') return 'invoice';
    if (o.status === 'invoiced') return o.ready ? 'delivery' : 'building';
    if (o.status === 'building') return 'delivery';
    return 'delivery';
  }
  function mailPane(o) {
    var mails = mailsFor(o);
    var sw = mails.map(function (m) {
      return '<button data-mailswitch="' + m.key + '"' + (mailKey === m.key ? ' class="active"' : '') + '>' + m.label + '</button>';
    }).join('');
    var cur = mails.filter(function (m) { return m.key === mailKey; })[0] || mails[0];
    var tag = cur.sent ? '<span class="mail-sent-tag">\u2713 Sent</span>' : (cur.queued ? '<span class="mail-queued-tag">Queued \u2014 sends on next step</span>' : '<span class="mail-queued-tag" style="background:var(--cream-3);color:var(--muted);">Not applicable yet</span>');
    return '<h4><span class="mlabel">\u2709 Email the system sends</span></h4>' +
      '<div class="mail-switch">' + sw + '</div>' +
      '<div class="mail-frame-wrap">' +
        '<div class="mail-meta">' +
          '<div class="mm-row"><span class="mm-k">To</span><span class="mm-v">' + esc(cur.to) + '</span><span style="margin-left:auto;">' + tag + '</span></div>' +
          '<div class="mm-row"><span class="mm-k">Subj</span><span class="mm-v">' + esc(cur.subject) + '</span></div>' +
        '</div>' +
        '<iframe class="mail-frame" id="mailFrame" title="Email preview"></iframe>' +
      '</div>' +
      '<p style="font-size:.74rem;color:var(--muted);margin:10px 2px 0;line-height:1.5;">Rendered from the same template Resend sends. Tokens like the invoice link and access code fill in as the order progresses.</p>';
  }
  function paintMail(o) {
    var frame = document.getElementById('mailFrame');
    if (!frame || !E || !E[mailKey]) return;
    try { frame.srcdoc = E[mailKey](o); } catch (e) { frame.srcdoc = '<p style="font-family:sans-serif;padding:20px;color:#888">Preview unavailable</p>'; }
  }

  /* ── wiring per detail render ──────────────────────────────── */
  function wireDetail(o) {
    // mail switcher
    [].forEach.call($detail.querySelectorAll('[data-mailswitch]'), function (b) {
      b.addEventListener('click', function () { mailKey = b.getAttribute('data-mailswitch'); renderDetail(); });
    });
    [].forEach.call($detail.querySelectorAll('[data-mail]'), function (b) {
      b.addEventListener('click', function () { mailKey = b.getAttribute('data-mail'); renderDetail(); });
    });
    [].forEach.call($detail.querySelectorAll('[data-copy]'), function (b) {
      b.addEventListener('click', function () {
        var v = b.getAttribute('data-copy');
        if (navigator.clipboard) navigator.clipboard.writeText(v);
        b.textContent = 'Copied'; b.classList.add('ok');
        setTimeout(function () { b.textContent = 'Copy'; b.classList.remove('ok'); }, 1400);
      });
    });

    // STEP 1 — invoice
    var invUrl = document.getElementById('invUrl'), invAmt = document.getElementById('invAmt'), btnInv = document.getElementById('btnInvoice');
    if (invUrl && btnInv) {
      function chk() { btnInv.disabled = !/^https?:\/\/.{6,}/i.test(invUrl.value.trim()); }
      invUrl.addEventListener('input', function () {
        chk();
        // live-refresh the invoice preview with the typed link
        o.invoiceUrl = invUrl.value.trim(); o.amount = Number(invAmt.value) || o.price;
        if (mailKey === 'invoice') paintMail(o);
      });
      invAmt.addEventListener('input', function () { o.amount = Number(invAmt.value) || o.price; if (mailKey === 'invoice') paintMail(o); });
      btnInv.addEventListener('click', function () {
        var url = invUrl.value.trim(), amount = Number(invAmt.value) || o.price;
        if (OPS.mode === 'live') {
          btnInv.disabled = true; btnInv.textContent = 'Sending…';
          api('/orders/' + o.id + '/invoice', { method: 'POST', body: JSON.stringify({ url: url, amount: amount }) })
            .then(function (r) { applyMutation(r, o.ready ? 'delivery' : 'building', 'Invoice emailed to ' + o.email, 'The student gets the Payoneer link now.'); });
          return;
        }
        // demo
        o.invoiceUrl = url;
        o.amount = amount;
        o.status = 'invoiced';
        o.events.push(ev('invoiced', Date.now(), 'Invoice sent', 'Payoneer link · ' + fmtMoney(o.amount), 'invoice'));
        o.events.push(ev('mail', Date.now() + 2e3, 'Sent', '“Invoice” → ' + o.email, 'invoice'));
        save(); mailKey = o.ready ? 'delivery' : 'building';
        toast('Invoice emailed to ' + o.email, 'The student gets the Payoneer link now.');
        flashStat(); render();
      });
    }

    // STEP 2 — confirm payment
    var btnPaid = document.getElementById('btnPaid');
    if (btnPaid) {
      btnPaid.addEventListener('click', function () {
        if (OPS.mode === 'live') {
          btnPaid.disabled = true; btnPaid.textContent = 'Working…';
          api('/orders/' + o.id + '/confirm-payment', { method: 'POST' })
            .then(function (r) {
              var ok = r.body && r.body.order;
              var built = ok && r.body.order.ready;
              applyMutation(r, built ? 'delivery' : 'building',
                built ? 'Access delivered automatically' : 'Payment confirmed — build started',
                built ? 'Pre-built case — code + magic link emailed.' : 'Student notified; upload when the guide is ready.');
            });
          return;
        }
        // demo
        if (o.ready) {
          o.accessCode = code(); o.accessUrl = BASE + '/g/' + tok();
          o.status = 'fulfilled';
          o.events.push(ev('paid', Date.now(), 'Payment confirmed', 'Marked paid by ops'));
          o.events.push(ev('fulfilled', Date.now() + 2e3, 'Guide delivered', 'Auto-delivered (pre-built case)'));
          o.events.push(ev('mail', Date.now() + 3e3, 'Sent', '“Your guide is ready” → ' + o.email, 'delivery'));
          save(); mailKey = 'delivery';
          toast('Access delivered automatically', 'Pre-built case — code + magic link emailed.');
        } else {
          o.status = 'building';
          o.events.push(ev('paid', Date.now(), 'Payment confirmed', 'Build started'));
          o.events.push(ev('mail', Date.now() + 2e3, 'Sent', '“Building your guide” → ' + o.email, 'building'));
          save(); mailKey = 'building';
          toast('Payment confirmed — build started', 'Student notified; upload when the guide is ready.');
        }
        flashStat(); render();
      });
    }
    var btnResend = document.getElementById('btnResend');
    if (btnResend) btnResend.addEventListener('click', function () {
      if (OPS.mode === 'live') {
        btnResend.disabled = true;
        api('/orders/' + o.id + '/resend', { method: 'POST', body: JSON.stringify({ which: 'invoice' }) })
          .then(function (r) {
            btnResend.disabled = false;
            if (r.status === 401) { sessionLost(); return; }
            if (r.body && r.body.ok) { if (r.body.order) replaceOrder(r.body.order); toast('Invoice email re-sent', 'Same Payoneer link to ' + o.email + '.'); }
            else toast('Resend failed', (r.body && r.body.error) || 'Please try again.');
          });
        return;
      }
      toast('Invoice email re-sent', 'Same Payoneer link to ' + o.email + '.');
    });

    // STEP 3 — upload & deliver
    var dz = document.getElementById('dz'), dzInput = document.getElementById('dzInput'), dzFiles = document.getElementById('dzFiles'), btnDeliver = document.getElementById('btnDeliver');
    var picked = [];
    if (dz) {
      function renderFiles() {
        dzFiles.innerHTML = picked.map(function (f, i) {
          var ext = (f.name.split('.').pop() || '').toUpperCase().slice(0, 4);
          return '<div class="dz-file"><span class="fi">' + esc(ext) + '</span><span class="fn">' + esc(f.name) + '</span><button class="fx" data-rm="' + i + '">\u00d7</button></div>';
        }).join('');
        [].forEach.call(dzFiles.querySelectorAll('[data-rm]'), function (b) {
          b.addEventListener('click', function () { picked.splice(+b.getAttribute('data-rm'), 1); renderFiles(); });
        });
        btnDeliver.disabled = !picked.length;
      }
      dz.addEventListener('click', function () { dzInput.click(); });
      dzInput.addEventListener('change', function () { picked = picked.concat([].slice.call(dzInput.files)); renderFiles(); });
      ['dragover', 'dragenter'].forEach(function (e) { dz.addEventListener(e, function (ev2) { ev2.preventDefault(); dz.classList.add('drag'); }); });
      ['dragleave', 'drop'].forEach(function (e) { dz.addEventListener(e, function (ev2) { ev2.preventDefault(); dz.classList.remove('drag'); }); });
      dz.addEventListener('drop', function (ev2) { picked = picked.concat([].slice.call(ev2.dataTransfer.files)); renderFiles(); });
      btnDeliver.addEventListener('click', function () {
        if (OPS.mode === 'live') {
          btnDeliver.disabled = true; btnDeliver.textContent = 'Uploading…';
          Promise.all(picked.map(function (f) {
            return fileToB64(f).then(function (data) { return { name: f.name, type: f.type, data: data }; });
          })).then(function (files) {
            return api('/orders/' + o.id + '/deliver', { method: 'POST', body: JSON.stringify({ files: files }) });
          }).then(function (r) {
            applyMutation(r, 'delivery', 'Guide delivered to ' + o.email, 'Access code + magic link emailed.');
          }).catch(function () {
            btnDeliver.disabled = false; btnDeliver.textContent = 'Deliver guide →';
            toast('Upload failed', 'Could not read the files. Please try again.');
          });
          return;
        }
        // demo
        o.accessCode = code(); o.accessUrl = BASE + '/g/' + tok();
        o.status = 'fulfilled';
        o.events.push(ev('fulfilled', Date.now(), 'Guide delivered', 'Uploaded by ops · ' + picked.length + ' file' + (picked.length > 1 ? 's' : '')));
        o.events.push(ev('mail', Date.now() + 2e3, 'Sent', '“Your guide is ready” → ' + o.email, 'delivery'));
        save(); mailKey = 'delivery';
        toast('Guide delivered to ' + o.email, 'Access code + magic link emailed.');
        flashStat(); render();
      });
    }
    var btnRd = document.getElementById('btnResendDelivery');
    if (btnRd) btnRd.addEventListener('click', function () {
      if (OPS.mode === 'live') {
        btnRd.disabled = true;
        api('/orders/' + o.id + '/resend', { method: 'POST', body: JSON.stringify({ which: 'delivery' }) })
          .then(function (r) {
            btnRd.disabled = false;
            if (r.status === 401) { sessionLost(); return; }
            if (r.body && r.body.ok) { if (r.body.order) replaceOrder(r.body.order); toast('Delivery email re-sent', 'Magic link + code to ' + o.email + '.'); }
            else toast('Resend failed', (r.body && r.body.error) || 'Please try again.');
          });
        return;
      }
      toast('Delivery email re-sent', 'Magic link + code to ' + o.email + '.');
    });
  }

  /* ── simulate inbound order ────────────────────────────────── */
  var POOL = [
    ['Samantha Graves — Viral Gastroenteritis', 'Vomiting and diarrhea ×2 days', true, 'Chamberlain', 'NR 602 · Wk 3', 'Samantha Graves'],
    ['Kennedy Poole — ADHD, Inattentive', 'Slipping grades and academic decline', true, 'Chamberlain', 'NR 603', 'Kennedy Poole'],
    ['Chester Wilson — Gout', 'Acute great-toe pain and swelling', false, 'Kaplan', '', 'Chester Wilson'],
    ['Jerome Cauthen — Acute Appendicitis', 'Migrating right-lower-quadrant pain', false, 'Kaplan', '', 'Jerome Cauthen'],
    ['Florence Blackman — Coronary Artery Disease', 'Exertional chest tightness', false, 'Walden', 'NRNP 6531', 'Florence Blackman'],
    ['Nick Roberts — Acute Otitis Media', 'Ear pain and fever in a toddler', true, 'Chamberlain', 'NR 602', 'Nick Roberts']
  ];
  var NAMES = ['morgan.t.ellis', 'devon.castillo.rn', 'aisha.k.bello', 'liam.farrell90', 'noor.s.haddad', 'tyler.j.maddox'];
  var DOMS = ['gmail.com', 'outlook.com', 'yahoo.com', 'icloud.com'];
  var simN = 1052;
  // DEMO ONLY. ⇄ LIVE: real orders arrive on their own — the “Order this guide” email hits
  // Resend Inbound → webhook POST {OPS.base}/inbound parses it → new Order pushed to the queue
  // (poll GET {OPS.base}/orders or subscribe to an SSE stream). This button is hidden in live mode.
  function simulateOrder() {
    var p = POOL[Math.floor(Math.random() * POOL.length)];
    var em = NAMES[Math.floor(Math.random() * NAMES.length)] + '@' + DOMS[Math.floor(Math.random() * DOMS.length)];
    var o = mk('CPL-' + (simN++), Date.now(), em, p[0], p[1], 150, p[2], p[3], p[4], p[5], 'new');
    orders.unshift(o); save();
    filter = 'needs'; sel = o.id; mailKey = null;
    toast('New order from ' + em, 'Order received + admin alert emails sent.');
    flashStat(); render();
  }

  /* ── toast ─────────────────────────────────────────────────── */
  var toastWrap;
  function toast(msg, sub) {
    if (!toastWrap) { toastWrap = document.createElement('div'); toastWrap.className = 'adm-toast-wrap'; document.body.appendChild(toastWrap); }
    var t = document.createElement('div');
    t.className = 'adm-toast';
    t.innerHTML = '<span class="tk">\u2713</span><div>' + esc(msg) + (sub ? '<br><b style="font-weight:400;color:var(--on-dark-2);font-size:.8rem;">' + esc(sub) + '</b>' : '') + '</div>';
    toastWrap.appendChild(t);
    requestAnimationFrame(function () { t.classList.add('show'); });
    setTimeout(function () { t.classList.remove('show'); setTimeout(function () { t.remove(); }, 320); }, 3200);
  }
  function flashStat() {
    var s = $stats && $stats.querySelector('.adm-stat.live');
    if (s) { s.classList.remove('flash'); void s.offsetWidth; s.classList.add('flash'); }
  }

  // expose for debugging / reset
  window.cplAdmin = { reset: function () { localStorage.removeItem(LS); load(); sel = (orders[0] || {}).id; render(); }, orders: function () { return orders; } };

  // Boot only once the ops gate has authenticated (cpl-admin-auth.js).
  function boot() {
    if (document.body.classList.contains('ops-authed')) init();
    else document.addEventListener('ops:authed', init, { once: true });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
