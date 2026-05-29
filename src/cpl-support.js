/* CPL — inbuilt messaging & AI support widget
   Floating launcher → chat panel. Answers via window.claude.complete,
   grounded in CPL context, with a canned fallback if the helper is absent. */
(function () {
  'use strict';

  var SYSTEM = [
    'You are the support assistant for Clinical Performance Lab (CPL), a clinical-reasoning education platform that helps nursing and NP students master iHuman virtual-patient cases.',
    'Mission: make iHuman\u2019s invisible scoring logic visible and teachable. Lead with education.',
    'Free forever: the case simulator and four cheat-sheet PDFs (history, physical exam, DDx, management/SOAP).',
    'Premium: complete case guides built from 200+ verified submissions and mapped to the scoring rubric. Pricing: single guide $150; 3-case bundle $390 (save $60); 5-case bundle $540 (save $210). New customers: code CPLFIRST15 = 15% off first single case.',
    'Ordering: the student requests an invoice; CPL emails it; once paid the student receives a personal access code that unlocks the complete guide for download. Same-day delivery, Word + PDF.',
    'Catalog: 171 cases across Chamberlain (NR509/NR511/NR602), Walden (NURS6512, NRNP6531/6541/6552/6568) and others. iHuman rotates patient names, so each guide covers all aliases of a case template.',
    'Tone: warm, calm, confident, concise \u2014 the audience is stressed students, often on mobile, anxious about grades. Reduce anxiety. On academic-integrity questions: CPL is a study and learning resource (like a tutor or answer-explanation guide); encourage students to follow their school\u2019s policies and use guides to learn the reasoning. Never claim affiliation with iHuman or any school.',
    'Keep replies under ~90 words. Use plain language. If unsure or it needs a human, offer to pass it to the CPL team at support@clinicalperformancelab.com.'
  ].join(' ');

  var GREETING = "Hi! I'm the CPL assistant 👋 I can help with how ordering works, what's free, whether we have your case, or scoring questions. What's on your mind?";
  var CHIPS = ['How does ordering work?', 'What\u2019s free?', 'Do you have my case?', 'Is this allowed?'];

  var history = [];

  var fab = document.createElement('button');
  fab.className = 'cpl-fab';
  fab.setAttribute('aria-label', 'Open support chat');
  fab.innerHTML = '<span class="cpl-fab-ico">💬</span><span class="cpl-fab-label">Support</span>';
  document.body.appendChild(fab);

  var panel = document.createElement('div');
  panel.className = 'cpl-chat';
  panel.innerHTML = [
    '<div class="cpl-chat-head">',
    '  <div class="cpl-chat-id"><span class="cpl-chat-avatar">CPL</span><div><b>CPL Support</b><small><span class="cpl-dot"></span>AI assistant · real humans on standby</small></div></div>',
    '  <button class="cpl-chat-close" aria-label="Close chat">×</button>',
    '</div>',
    '<div class="cpl-chat-body" data-chat-body></div>',
    '<div class="cpl-chat-chips" data-chat-chips></div>',
    '<form class="cpl-chat-input" data-chat-form>',
    '  <input type="text" placeholder="Ask about cases, scoring, orders…" autocomplete="off" data-chat-text>',
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
      return "Easy: request an invoice on any case, we email it within the hour, and once it\u2019s paid you get an access code that unlocks the complete guide (Word + PDF, same day). Single guide is $150 — code CPLFIRST15 takes 15% off your first.";
    if (s.indexOf('free') > -1)
      return "The case simulator and all four cheat-sheet PDFs — history, physical exam, DDx, and management/SOAP — are free forever. No card needed. Grab them from the Free Cheat Sheets section.";
    if (s.indexOf('allow') > -1 || s.indexOf('integrity') > -1 || s.indexOf('cheat') > -1)
      return "CPL is a study resource — it teaches the clinical reasoning iHuman rewards so you learn it, like a tutor or answer-explanation guide. Always follow your school\u2019s academic policies. We\u2019re not affiliated with iHuman.";
    if (s.indexOf('case') > -1 || s.indexOf('have') > -1)
      return "Most likely! We catalog 171 cases across Chamberlain and Walden programs. Tell me the patient name or diagnosis and I\u2019ll point you to it — and remember iHuman rotates names, so guides cover every alias.";
    return "Great question — for anything specific, the CPL team can help directly at support@clinicalperformancelab.com. In the meantime: the simulator and cheat sheets are free, and complete guides are $150 with same-day delivery.";
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
    fab.classList.add('hidden');
    if (!greeted) { addMsg('bot', GREETING); renderChips(); greeted = true; }
    setTimeout(function () { input.focus(); }, 200);
  }
  function closeChat() { panel.classList.remove('open'); fab.classList.remove('hidden'); }

  fab.addEventListener('click', openChat);
  panel.querySelector('.cpl-chat-close').addEventListener('click', closeChat);
  form.addEventListener('submit', function (e) { e.preventDefault(); var v = input.value; input.value = ''; send(v); });
})();
