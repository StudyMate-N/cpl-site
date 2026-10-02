/* CPL public interactions. API endpoints retain their existing contracts. */
(function () {
  'use strict';
  var burger = document.querySelector('.nav-burger');
  var menu = document.querySelector('.mobile-menu');
  var backdrop = document.querySelector('.menu-backdrop');
  var lastMenuFocus;
  function focusables(root) {
    return Array.from(root.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),[tabindex="0"]')).filter(function (el) { return el.offsetParent !== null; });
  }
  function setMenu(open) {
    if (!menu) return;
    menu.classList.toggle('open', open);
    menu.inert = !open;
    menu.setAttribute('aria-hidden', String(!open));
    burger.setAttribute('aria-expanded', String(open));
    if (backdrop) backdrop.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
    document.body.classList.toggle('menu-open', open);
    if (open) { lastMenuFocus = document.activeElement; menu.querySelector('[data-menu-close]').focus(); }
    else if (lastMenuFocus) lastMenuFocus.focus();
  }
  if (burger) burger.addEventListener('click', function () { setMenu(!menu.classList.contains('open')); });
  document.querySelectorAll('[data-menu-close]').forEach(function (el) { el.addEventListener('click', function () { setMenu(false); }); });
  if (backdrop) backdrop.addEventListener('click', function () { setMenu(false); });
  document.addEventListener('keydown', function (ev) {
    if (!menu || !menu.classList.contains('open')) return;
    if (ev.key === 'Escape') setMenu(false);
    if (ev.key === 'Tab') {
      var all = focusables(menu), first = all[0], last = all[all.length - 1];
      if (ev.shiftKey && document.activeElement === first) { ev.preventDefault(); last.focus(); }
      else if (!ev.shiftKey && document.activeElement === last) { ev.preventDefault(); first.focus(); }
    }
  });
  document.querySelectorAll('.nav-links a,.mobile-menu>a').forEach(function (a) {
    if (a.pathname === location.pathname) a.setAttribute('aria-current', 'page');
  });

  /* Let native checkboxes handle both pointer and keyboard selection. */
  document.querySelectorAll('.resource-card').forEach(function (card) {
    var cb = card.querySelector('input[type=checkbox]');
    if (cb) cb.addEventListener('change', function () { card.classList.toggle('selected', cb.checked); });
  });
  function announce(box, message) {
    if (!box) return;
    box.hidden = false;
    box.style.display = 'block';
    box.textContent = message;
  }
  document.querySelectorAll('[data-capture]').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var box = form.querySelector('[data-capture-msg]');
      var email = form.querySelector('input[type=email]');
      if (!email || !email.checkValidity()) { announce(box, 'Please enter a valid email address.'); if (email) email.focus(); return; }
      var volumes = Array.from(form.querySelectorAll('input[name=volumes]:checked')).map(function (cb) { return cb.value; });
      if (form.querySelector('input[name=volumes]') && !volumes.length) { announce(box, 'Choose at least one resource to receive.'); return; }
      if (!volumes.length) volumes = ['history', 'physical-exam', 'ddx', 'plan'];
      var controls = form.querySelectorAll('input,button');
      var btn = form.querySelector('button[type=submit]'), original = btn.textContent;
      controls.forEach(function (c) { c.disabled = true; });
      btn.textContent = 'Sending…';
      if (box) box.hidden = true;
      fetch('/api/subscribe', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:email.value.trim(),volumes:volumes}) })
        .then(function (res) { return res.json().then(function (data) { if (!res.ok || !data.ok) throw new Error(data.error || 'We could not send your resources. Please try again.'); return data; }); })
        .then(function () { try { localStorage.setItem('cpl.formEmail', email.value.trim()); } catch (ignore) {} location.href = '/thank-you/'; })
        .catch(function (err) { controls.forEach(function (c) { c.disabled = false; }); btn.textContent = original; announce(box, err.message === 'Failed to fetch' ? 'Connection interrupted. Please try again.' : err.message); });
    });
  });

  /* Verbatim exchanges from the supplied Kristina Hart transcript. */
  var exchanges = [
    {q:'How can I help you today?',a:"I've been having some pain and burning when I urinate."},
    {q:'Do you have any other symptoms or concerns we should discuss?',a:"Yes, I'm also having some vaginal discharge. That's about it."}
  ];
  var tabs = Array.from(document.querySelectorAll('[data-excerpt]'));
  function selectExcerpt(index, moveFocus) {
    tabs.forEach(function (tab, n) { tab.setAttribute('aria-selected', String(n === index)); tab.tabIndex = n === index ? 0 : -1; });
    document.querySelector('[data-excerpt-question]').textContent = '“' + exchanges[index].q + '”';
    document.querySelector('[data-excerpt-response]').textContent = '“' + exchanges[index].a + '”';
    document.getElementById('excerptPanel').setAttribute('aria-labelledby', tabs[index].id);
    if (moveFocus) tabs[index].focus();
  }
  tabs.forEach(function (tab, n) {
    tab.addEventListener('click', function () { selectExcerpt(n, false); });
    tab.addEventListener('keydown', function (ev) {
      var index = n;
      if (ev.key === 'ArrowRight' || ev.key === 'ArrowLeft') index = (n + 1) % tabs.length;
      else if (ev.key === 'Home') index = 0;
      else if (ev.key === 'End') index = tabs.length - 1;
      else return;
      ev.preventDefault(); selectExcerpt(index, true);
    });
  });

  var waitlist = document.getElementById('waitlistForm');
  if (waitlist) waitlist.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var email = document.getElementById('wlEmail'), btn = document.getElementById('wlBtn'), box = document.getElementById('wlMsg');
    if (!email.checkValidity() || !email.value.trim()) { announce(box, 'Please enter a valid email address.'); email.focus(); return; }
    var original = btn.textContent;
    btn.disabled = true; email.disabled = true; btn.textContent = 'Joining…'; box.textContent = '';
    fetch('/api/waitlist', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:email.value.trim(),source:'simulator'})})
      .then(function (res) { return res.json().then(function (data) { if (!res.ok || !data.ok) throw new Error(data.error || 'Unable to join the list. Please try again.'); }); })
      .then(function () { announce(box, 'You are on the list. We will email you when the simulator launches.'); btn.textContent = 'You are on the list'; })
      .catch(function (err) { btn.disabled = false; email.disabled = false; btn.textContent = original; announce(box, err.message === 'Failed to fetch' ? 'Connection interrupted. Please try again.' : err.message); });
  });

  var triggers = document.querySelectorAll('[data-lightbox]');
  if (triggers.length) {
    var lightbox = document.createElement('div');
    lightbox.className = 'lightbox'; lightbox.setAttribute('role', 'dialog'); lightbox.setAttribute('aria-modal', 'true'); lightbox.setAttribute('aria-label', 'Guide page preview');
    lightbox.innerHTML = '<button class="lightbox-close" aria-label="Close preview">×</button><img alt="Guide page preview">';
    lightbox.inert = true; document.body.appendChild(lightbox);
    var opener;
    var close = function () { lightbox.classList.remove('open'); lightbox.inert = true; document.body.style.overflow = ''; if (opener) opener.focus(); };
    triggers.forEach(function (t) { t.addEventListener('click', function () {
      opener = t; var img = lightbox.querySelector('img'); img.src = t.getAttribute('data-lightbox'); img.alt = t.getAttribute('aria-label') || 'Guide page preview';
      lightbox.inert = false; lightbox.classList.add('open'); document.body.style.overflow = 'hidden'; lightbox.querySelector('button').focus();
    }); });
    lightbox.querySelector('button').addEventListener('click', close);
    lightbox.addEventListener('click', function (ev) { if (ev.target === lightbox) close(); });
    document.addEventListener('keydown', function (ev) {
      if (!lightbox.classList.contains('open')) return;
      if (ev.key === 'Escape') close();
      if (ev.key === 'Tab') { ev.preventDefault(); lightbox.querySelector('button').focus(); }
    });
  }
})();
