/* CPL Ops — auth gate (LIVE)
   ───────────────────────────────────────────────────────────────
   The /ops/ console boots only after a valid, signed httpOnly session
   cookie is present. The cookie is set by POST /api/ops/login and is
   NOT readable from JS, so on page load we confirm it with the server
   via GET /api/ops/session.
     • authenticate(passcode) → POST /api/ops/login {passcode}
         200 → server set the cookie → resolve(true) ; 401 → resolve(false)
     • signOut()              → POST /api/ops/logout, then reload
   The grant()/ops:authed contract that boots cpl-admin.js is unchanged. */
(function () {
  'use strict';
  var SESSION = 'cpl_ops_session';     // soft UX hint only; the server cookie is the source of truth
  var BASE = '/api/ops';

  function grant() {
    document.body.classList.add('ops-authed');
    document.documentElement.classList.remove('ops-authed-pre');
    try { localStorage.setItem(SESSION, '1'); } catch (e) {}
    document.dispatchEvent(new CustomEvent('ops:authed'));
  }

  function authenticate(passcode) {
    return fetch(BASE + '/login', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ passcode: passcode })
    }).then(function (r) { return r.ok; }).catch(function () { return false; });
  }

  function signOut() {
    try { localStorage.removeItem(SESSION); } catch (e) {}
    fetch(BASE + '/logout', { method: 'POST', credentials: 'include' })
      .then(function () { location.reload(); })
      .catch(function () { location.reload(); });
  }

  // Confirm an existing session server-side (the httpOnly cookie can't be read here).
  function checkSession() {
    return fetch(BASE + '/session', { credentials: 'include' })
      .then(function (r) { return r.ok; }).catch(function () { return false; });
  }

  function init() {
    var form = document.getElementById('opsLogin');
    var pass = document.getElementById('opsPass');
    var err = document.getElementById('opsErr');
    var signout = document.getElementById('admSignout');
    if (signout) signout.addEventListener('click', signOut);

    function focusPass() { if (pass) setTimeout(function () { pass.focus(); }, 60); }

    // If we think we're signed in, verify with the server before granting.
    var hint = false;
    try { hint = !!localStorage.getItem(SESSION); } catch (e) {}
    if (hint) {
      checkSession().then(function (ok) {
        if (ok) grant();
        else { try { localStorage.removeItem(SESSION); } catch (e) {} focusPass(); }
      });
    } else {
      focusPass();
    }

    if (form) form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (err) err.hidden = true;
      var go = document.getElementById('opsGo');
      if (go) go.disabled = true;
      authenticate(pass ? pass.value : '').then(function (ok) {
        if (go) go.disabled = false;
        if (!ok) { if (err) err.hidden = false; if (pass) { pass.value = ''; pass.focus(); } return; }
        grant();
      });
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
