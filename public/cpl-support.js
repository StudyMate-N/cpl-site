/* CPL — inbuilt messaging & AI support widget
   Floating launcher → chat panel. Answers via window.claude.complete,
   grounded in CPL context, with a canned fallback if the helper is absent. */
(function () {
  'use strict';

  var SYSTEM = [
    'You are the support assistant for Clinical Performance Lab (CPL), an independent clinical reasoning education resource for nursing students.',
    'Four free PDF resources cover history, physical examination, differential diagnosis, and management/SOAP. Email confirmation is required for delivery. The simulator is in development and only its waitlist is available.',
    'Prices in USD: single guide $150, three-case bundle $390, five-case bundle $540. CPLFIRST15 gives 15% off the first single guide.',
    'Ordering: request an invoice. CPL confirms the case version, content and delivery window before payment. Word and PDF guide delivery includes an access code. Availability varies: same-day, 24–48 hour build, or availability check.',
    'Patient names and aliases are search references. Do not assume findings or history responses transfer between versions. Direct students to the case library and the CPL team for version checks.',
    'Do not invent clinical findings, scoring targets, source verification, inventory availability or patient responses. Do not promise a live simulator or universal same-day delivery.',
    'Use plain language and keep replies under 90 words. Encourage students to follow their school policies. Support email: support@clinicalperformancelab.com.'
  ].join(' ');

  var GREETING = "Hi, I can explain ordering, free resources and how to match your case version. For specific case questions, email the CPL team.";
  var CHIPS = ['How does ordering work?', 'What\u2019s free?', 'Do you have my case?', 'Is this allowed?'];

  var history = [];

  var fab = document.createElement('button');
  fab.className = 'cpl-fab';
  fab.setAttribute('aria-label', 'Open support chat');
  fab.textContent = 'Need help?';
  document.body.appendChild(fab);

  var panel = document.createElement('div');
  panel.className = 'cpl-chat';
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-label', 'CPL support');
  panel.setAttribute('inert', '');
  panel.setAttribute('aria-hidden', 'true');
  panel.innerHTML = [
    '<div class="cpl-chat-head">',
    '  <div class="cpl-chat-id"><span class="cpl-chat-avatar">CPL</span><div><b>CPL Support</b><small><span class="cpl-dot"></span>Quick answers · email our team</small></div></div>',
    '  <button class="cpl-chat-close" aria-label="Close chat">×</button>',
    '</div>',
    '<div class="cpl-chat-body" data-chat-body role="log" aria-live="polite"></div>',
    '<div class="cpl-chat-chips" data-chat-chips></div>',
    '<form class="cpl-chat-input" data-chat-form>',
    '  <input type="text" aria-label="Your support question" placeholder="Ask about guides, resources, orders…" autocomplete="off" data-chat-text>',
    '  <button type="submit" aria-label="Send">↑</button>',
    '</form>',
    '<div class="cpl-chat-foot">Powered by CPL · or email <a href="mailto:support@clinicalperformancelab.com">support@clinicalperformancelab.com</a></div>'
  ].join('');
  document.body.appendChild(panel);

  var body = panel.querySelector('[data-chat-body]');
  var chips = panel.querySelector('[data-chat-chips]');
  var form = panel.querySelector('[data-chat-form]');
  var input = panel.querySelector('[data-chat-text]');
  var greeted = false;

  function scrollDown() { body.scrollTop = body.scrollHeight; }

  function addMsg(role, text) {
    var m = document.createElement('div');
    m.className = 'cpl-msg ' + role;
    m.textContent = text;
    body.appendChild(m);
    scrollDown();
    return m;
  }

  function renderChips() {
    chips.innerHTML = '';
    CHIPS.forEach(function (c) {
      var b = document.createElement('button');
      b.className = 'cpl-chip';
      b.textContent = c;
      b.addEventListener('click', function () { send(c); });
      chips.appendChild(b);
    });
  }

  function fallback(q) {
    var s = q.toLowerCase();
    if (s.indexOf('order') > -1 || s.indexOf('buy') > -1 || s.indexOf('pay') > -1)
      return "Request an invoice from a case page or a selected bundle. CPL confirms the case version, content and delivery window before payment. Your delivery email includes an access code for the Word and PDF guide. A single guide is $150 USD; CPLFIRST15 gives 15% off your first single guide.";
    if (s.indexOf('free') > -1 || s.indexOf('simulator') > -1)
      return "The four PDF resources cover history, physical examination, differential diagnosis, and management/SOAP. Choose your PDFs on the Free resources page, then confirm your email to receive them. The simulator is still in development; you can join its waitlist.";
    if (s.indexOf('allow') > -1 || s.indexOf('integrity') > -1 || s.indexOf('cheat') > -1)
      return "CPL supports personal study and practice. Complete your own encounter and documentation, and follow your school's academic policies. CPL is independent and is not affiliated with iHuman or any institution.";
    if (s.indexOf('case') > -1 || s.indexOf('have') > -1)
      return "Search the case library by patient name, presentation, course or school. Match the age and course details before ordering. Names alone do not confirm a version, and findings should not transfer between versions. Email support@clinicalperformancelab.com if you need a match checked.";
    return "For a specific answer, email support@clinicalperformancelab.com with your patient name, course and question. You can also find ordering, delivery and free resource details on the Questions & answers page.";
  }

  var pending = false;
  async function send(text) {
    if (pending || !text.trim()) return;
    pending = true;
    chips.innerHTML = '';
    addMsg('user', text);
    history.push({ role: 'user', content: text });
    var typing = document.createElement('div');
    typing.className = 'cpl-msg bot cpl-typing';
    typing.innerHTML = '<span></span><span></span><span></span>';
    body.appendChild(typing); scrollDown();

    var reply = '';
    try {
      if (window.claude && window.claude.complete) {
        var transcript = history.map(function (h) { return (h.role === 'user' ? 'Student' : 'Assistant') + ': ' + h.content; }).join('\n');
        var prompt = SYSTEM + '\n\nConversation so far:\n' + transcript + '\n\nWrite the Assistant\u2019s next reply only (no prefix):';
        reply = await window.claude.complete(prompt);
      }
    } catch (e) { reply = ''; }
    if (!reply || !reply.trim()) reply = fallback(text);

    typing.remove();
    addMsg('bot', reply.trim());
    history.push({ role: 'assistant', content: reply.trim() });
    pending = false;
  }

  function openChat() {
    panel.classList.add('open');
    panel.removeAttribute('inert');
    panel.setAttribute('aria-hidden', 'false');
    fab.setAttribute('aria-expanded', 'true');
    fab.classList.add('hidden');
    if (!greeted) { addMsg('bot', GREETING); renderChips(); greeted = true; }
    setTimeout(function () { input.focus(); }, 200);
  }
  function closeChat() { panel.classList.remove('open'); panel.setAttribute('inert', ''); panel.setAttribute('aria-hidden', 'true'); fab.classList.remove('hidden'); fab.setAttribute('aria-expanded', 'false'); fab.focus(); }
  panel.addEventListener('keydown', function (e) { if (e.key === 'Escape') { e.preventDefault(); closeChat(); } });

  fab.addEventListener('click', openChat);
  panel.querySelector('.cpl-chat-close').addEventListener('click', closeChat);
  form.addEventListener('submit', function (e) { e.preventDefault(); var v = input.value; input.value = ''; send(v); });
})();
