/* CPL — checkout & access-code flow (invoice model)
   Order → request invoice (paid externally) → receive access code → unlock.
   Injects a single modal; any [data-order] button opens it; [data-access-code]
   jumps straight to code entry. Demo access code: CPL-2026 */
(function () {
  'use strict';
  var DEMO_CODE = 'CPL-2026';

  var overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.innerHTML = [
    '<div class="modal">',
    '  <button class="modal-close" aria-label="Close">×</button>',
    '  <div class="modal-steps">',
    // step 1 — order
    '    <div data-step="order">',
    '      <div class="modal-eyebrow">Order a case guide</div>',
    '      <h3 class="modal-title" data-case-title>Case guide</h3>',
    '      <div class="order-summary">',
    '        <div><span data-case-name>Case guide</span><small>Word + PDF · same-day delivery</small></div>',
    '        <div class="os-price"><span class="cur">$</span><span data-case-price>150</span></div>',
    '      </div>',
    '      <div class="invoice-note"><b>How ordering works:</b> request an invoice below. We email it within the hour. Once it\u2019s paid, you\u2019ll receive a personal <b>access code</b> that unlocks your complete guide for download.</div>',
    '      <form data-order-form>',
    '        <label class="fld"><span>Your email</span><input type="email" name="email" placeholder="you@school.edu" required autocomplete="email"></label>',
    '        <div class="fld-row">',
    '          <label class="fld"><span>School</span><input type="text" name="school" placeholder="e.g. Chamberlain"></label>',
    '          <label class="fld"><span>Course / week</span><input type="text" name="course" placeholder="e.g. NR 509 Wk 6"></label>',
    '        </div>',
    '        <label class="fld"><span>Your patient alias <small>(so we customize the guide)</small></span><input type="text" name="alias" placeholder="e.g. Bebe Babbitt"></label>',
    '        <button type="submit" class="btn btn-primary btn-lg" style="width:100%;margin-top:6px;">Request my invoice →</button>',
    '      </form>',
    '      <button class="modal-link" data-goto="code">Already have an access code? Enter it →</button>',
    '    </div>',
    // step 2 — invoice sent
    '    <div data-step="sent" hidden>',
    '      <div class="modal-badge">📧</div>',
    '      <h3 class="modal-title">Invoice on its way</h3>',
    '      <p class="modal-sub">We\u2019ve sent an invoice to <b data-sent-email>your email</b>. As soon as it\u2019s paid, your access code lands in the same inbox \u2014 usually within the hour.</p>',
    '      <div class="code-entry">',
    '        <div class="modal-eyebrow">Got your code?</div>',
    '        <form data-code-form>',
    '          <input type="text" name="code" placeholder="CPL-XXXX" autocomplete="off" spellcheck="false">',
    '          <button type="submit" class="btn btn-primary">Unlock</button>',
    '        </form>',
    '        <p class="code-error" data-code-error hidden>That code didn\u2019t match. Check the email we sent, or message support.</p>',
    '        <p class="code-hint">Prototype tip: use <b>' + DEMO_CODE + '</b> to see the unlocked state.</p>',
    '      </div>',
    '    </div>',
    // step 3 — code entry (direct)
    '    <div data-step="code" hidden>',
    '      <div class="modal-eyebrow">Unlock your guide</div>',
    '      <h3 class="modal-title">Enter your access code</h3>',
    '      <p class="modal-sub">Paste the code from your delivery email to unlock the complete guide.</p>',
    '      <form data-code-form2>',
    '        <input type="text" name="code" placeholder="CPL-XXXX" autocomplete="off" spellcheck="false" class="code-input-lg">',
    '        <button type="submit" class="btn btn-primary btn-lg" style="width:100%;margin-top:10px;">Unlock guide →</button>',
    '      </form>',
    '      <p class="code-error" data-code-error2 hidden>That code didn\u2019t match. Double-check your email or message support.</p>',
    '      <p class="code-hint">Prototype tip: use <b>' + DEMO_CODE + '</b>.</p>',
    '    </div>',
    // step 4 — unlocked
    '    <div data-step="done" hidden>',
    '      <div class="modal-badge success">✓</div>',
    '      <h3 class="modal-title">Guide unlocked</h3>',
    '      <p class="modal-sub">Your complete <b data-done-case>case guide</b> is ready. We\u2019ve also emailed you a permanent copy.</p>',
    '      <a href="#" class="btn btn-lime btn-lg" style="width:100%;" data-download>Download guide (Word + PDF) →</a>',
    '      <button class="modal-link" data-modal-dismiss>Back to the case</button>',
    '    </div>',
    '  </div>',
    '</div>'
  ].join('');
  document.body.appendChild(overlay);

  var modal = overlay.querySelector('.modal');
  var steps = overlay.querySelectorAll('[data-step]');
  var current = 'order';

  function show(step) {
    current = step;
    steps.forEach(function (s) { s.hidden = s.getAttribute('data-step') !== step; });
  }
  function open(step) {
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
    show(step || 'order');
  }
  function close() {
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }
  function setCase(name, price) {
    overlay.querySelectorAll('[data-case-title]').forEach(function (e) { e.textContent = name; });
    overlay.querySelectorAll('[data-case-name]').forEach(function (e) { e.textContent = name; });
    overlay.querySelectorAll('[data-done-case]').forEach(function (e) { e.textContent = name; });
    if (price) overlay.querySelector('[data-case-price]').textContent = price;
    var alias = overlay.querySelector('input[name=alias]');
    if (alias) alias.value = name.split('—')[0].trim();
  }

  // open triggers
  document.addEventListener('click', function (ev) {
    var orderBtn = ev.target.closest('[data-order]');
    if (orderBtn) {
      ev.preventDefault();
      setCase(orderBtn.getAttribute('data-order') || 'Case guide', orderBtn.getAttribute('data-price'));
      open('order');
      return;
    }
    var codeBtn = ev.target.closest('[data-access-code]');
    if (codeBtn) { ev.preventDefault(); open('code'); return; }
  });

  overlay.querySelector('.modal-close').addEventListener('click', close);
  overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && overlay.classList.contains('open')) close(); });
  overlay.querySelectorAll('[data-modal-dismiss]').forEach(function (b) { b.addEventListener('click', close); });
  overlay.querySelector('[data-goto="code"]').addEventListener('click', function () { show('code'); });

  // order → invoice sent
  overlay.querySelector('[data-order-form]').addEventListener('submit', function (e) {
    e.preventDefault();
    var email = this.querySelector('input[name=email]').value;
    overlay.querySelector('[data-sent-email]').textContent = email;
    show('sent');
  });

  function tryUnlock(value, errEl) {
    if (value.trim().toUpperCase() === DEMO_CODE) {
      if (errEl) errEl.hidden = true;
      // reflect unlocked state on the page if a guide gallery exists
      document.querySelectorAll('.gpage.locked .gpage-frame .gpage-tag').forEach(function (t) {
        t.textContent = 'Unlocked'; t.classList.remove('locked'); t.classList.add('sample');
      });
      document.querySelectorAll('.gpage.locked').forEach(function (g) { g.classList.remove('locked'); });
      show('done');
      return true;
    }
    if (errEl) errEl.hidden = false;
    return false;
  }
  overlay.querySelector('[data-code-form]').addEventListener('submit', function (e) {
    e.preventDefault();
    tryUnlock(this.querySelector('input[name=code]').value, overlay.querySelector('[data-code-error]'));
  });
  overlay.querySelector('[data-code-form2]').addEventListener('submit', function (e) {
    e.preventDefault();
    tryUnlock(this.querySelector('input[name=code]').value, overlay.querySelector('[data-code-error2]'));
  });
  overlay.querySelector('[data-download]').addEventListener('click', function (e) { e.preventDefault(); close(); });

  window.cplCheckout = { open: open, close: close };
})();
