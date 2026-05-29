/* CPL — catalog: live search, filters, bundle cart */
(function () {
  'use strict';
  var grid = document.getElementById('caseGrid');
  if (!grid) return;

  // Full catalog injected by the build (window.CPL_CASES, all 171 cases with
  // per-case pretty-URL hrefs). Falls back to the curated demo list below.
  var CASES = (window.CPL_CASES && window.CPL_CASES.length) ? window.CPL_CASES : [
    { t:"Harvey Hoya — Hypertension Stage 2", cc:"High blood pressure noted at a community health fair", dx:"Primary hypertension, stage 2", sys:["Cardiovascular","Adult"], school:"Chamberlain University", course:"NR 509 / 511 · Wk 5", lead:"same-day" },
    { t:"Bebe Babbitt — Migraine with Aura", cc:"More frequent, more severe headaches", dx:"Migraine with aura", sys:["Neurologic","Adult"], school:"Chamberlain University", course:"NR 509 · Wk 6", lead:"same-day", href:"case-preview.html" },
    { t:"Cynthia Francis — Hyperlipidemia", cc:"Follow-up after an abnormal lipid panel", dx:"Mixed hyperlipidemia", sys:["Endocrine","Adult"], school:"Chamberlain University", course:"NR 509 / 511", lead:"same-day" },
    { t:"Samantha Graves — Viral Gastroenteritis", cc:"Vomiting and diarrhea ×2 days", dx:"Acute viral gastroenteritis", sys:["GI","Pediatric"], school:"Chamberlain University", course:"NR 602 · Wk 5", lead:"same-day" },
    { t:"Kennedy Poole — ADHD, Inattentive", cc:"Slipping grades and academic decline", dx:"ADHD, predominantly inattentive", sys:["Mental Health","Pediatric"], school:"Chamberlain University", course:"NR 602 · Wk 4", lead:"same-day" },
    { t:"Christine Smith — Pyelonephritis", cc:"Flank pain, fever, dysuria", dx:"Acute pyelonephritis", sys:["GU","Adult"], school:"Walden University", course:"NRNP 6531 · Wk 7", lead:"same-day" },
    { t:"Lori Jacobs — Urinary Tract Infection", cc:"Burning with urination ×3 days", dx:"Uncomplicated cystitis", sys:["GU","Adult"], school:"Walden University", course:"NRNP 6552", lead:"same-day" },
    { t:"Nick Roberts — Acute Otitis Media", cc:"Ear pain and fever in a toddler", dx:"Acute otitis media", sys:["ENT","Pediatric"], school:"Chamberlain University", course:"NR 602", lead:"same-day" },
    { t:"Danny Rivera — Pediatric Respiratory Infection", cc:"Cough and congestion in a child", dx:"Viral URI", sys:["Respiratory","Pediatric"], school:"Multiple Institutions", course:"NR 509 / Shadow Health", lead:"fast-build" },
    { t:"Tina Jones — Comprehensive Assessment", cc:"Shadow Health comprehensive exam", dx:"Comprehensive H&P", sys:["General","Adult","Shadow Health"], school:"Multiple Institutions", course:"NR 509", lead:"fast-build" },
    { t:"Ben Bundy — COPD Exacerbation", cc:"Worsening shortness of breath", dx:"COPD exacerbation", sys:["Respiratory","Adult"], school:"Walden University", course:"NRNP 6531 · Wk 4", lead:"fast-build" },
    { t:"Jacob Abraham — GERD", cc:"Burning chest pain after meals", dx:"Gastroesophageal reflux disease", sys:["GI","Adult"], school:"Kaplan Medical", course:"Kaplan", lead:"fast-build" },
    { t:"Evan Tyson — Diabetes Mellitus", cc:"Fatigue, thirst, frequent urination", dx:"Type 2 diabetes mellitus", sys:["Endocrine","Adult"], school:"Chamberlain University", course:"NR 509", lead:"fast-build" },
    { t:"Maria Ash — Hypothyroidism", cc:"Fatigue, weight gain, cold intolerance", dx:"Primary hypothyroidism", sys:["Endocrine","Adult"], school:"Kaplan Medical", course:"Kaplan", lead:"fast-build" },
    { t:"Chester Wilson — Gout", cc:"Acute great-toe pain and swelling", dx:"Acute gouty arthritis", sys:["Musculoskeletal","Adult"], school:"Kaplan Medical", course:"Kaplan", lead:"fast-build" },
    { t:"Krista Hampton — Contact Dermatitis", cc:"Itchy rash after new detergent", dx:"Allergic contact dermatitis", sys:["Dermatology","Adult"], school:"Kaplan Medical", course:"Kaplan", lead:"fast-build" },
    { t:"Jerome Cauthen — Acute Appendicitis", cc:"Migrating right-lower-quadrant pain", dx:"Acute appendicitis", sys:["GI","Surgery","Adult"], school:"Kaplan Medical", course:"Kaplan", lead:"fast-build" },
    { t:"Florence Blackman — Coronary Artery Disease", cc:"Exertional chest tightness", dx:"Stable coronary artery disease", sys:["Cardiovascular","Adult"], school:"Walden University", course:"NRNP 6531", lead:"fast-build" },
    { t:"Jacqueline Russell — Major Depressive Disorder", cc:"Low mood and anhedonia ×2 months", dx:"Major depressive disorder", sys:["Mental Health","Adult"], school:"Walden University", course:"NRNP 6568", lead:"fast-build" },
    { t:"Janet Riley — Alzheimer's Disease", cc:"Progressive memory loss", dx:"Alzheimer's dementia", sys:["Neurologic","Geriatric"], school:"Walden University", course:"NRNP 6568", lead:"fast-build" },
    { t:"Emma Ryan — Pediatric URI", cc:"Runny nose and mild cough", dx:"Upper respiratory infection", sys:["Respiratory","Pediatric"], school:"Chamberlain University", course:"NR 509", lead:"fast-build" },
    { t:"Elias Leon — Hypertension", cc:"Elevated BP at a routine visit", dx:"Essential hypertension", sys:["Cardiovascular","Adult"], school:"South University", course:"NR 509", lead:"fast-build" },
    { t:"Brad Banerjee — Ischemic Stroke", cc:"Sudden one-sided weakness", dx:"Acute ischemic stroke", sys:["Neurologic","Emergency","Adult"], school:"Kaplan Medical", course:"Kaplan", lead:"on-request" },
    { t:"Karen Simpson — Pulmonary Embolism", cc:"Sudden pleuritic chest pain, dyspnea", dx:"Pulmonary embolism", sys:["Respiratory","Emergency","Adult"], school:"Kaplan Medical", course:"Kaplan", lead:"on-request" },
    { t:"Jamie Feldman — Unstable Angina", cc:"Chest pain at rest", dx:"Unstable angina", sys:["Cardiovascular","Emergency","Adult"], school:"Kaplan Medical", course:"Kaplan", lead:"on-request" },
    { t:"John Quimby — STEMI", cc:"Crushing chest pain with diaphoresis", dx:"ST-elevation MI", sys:["Cardiovascular","Emergency","Adult"], school:"Multiple Institutions", course:"NRNP 6531", lead:"on-request" },
    { t:"Nancy Penn — Ectopic Pregnancy", cc:"Pelvic pain and spotting", dx:"Ectopic pregnancy", sys:["Women's Health","Emergency","Adult"], school:"Kaplan Medical", course:"Kaplan", lead:"on-request" },
    { t:"Caleb Metz — Testicular Torsion", cc:"Sudden severe scrotal pain", dx:"Testicular torsion", sys:["GU","Emergency","Adolescent"], school:"Kaplan Medical", course:"Kaplan", lead:"on-request" },
    { t:"Melissa Steward — Diabetic Ketoacidosis", cc:"Nausea, polyuria, confusion", dx:"Diabetic ketoacidosis", sys:["Endocrine","Emergency","Adult"], school:"Kaplan Medical", course:"Kaplan", lead:"on-request" },
    { t:"Miah Zavarro — Sickle Cell Anemia", cc:"Recurrent pain crises", dx:"Sickle cell disease", sys:["Hematology","Pediatric"], school:"Kaplan Medical", course:"Kaplan", lead:"on-request" },
    { t:"Jack Johnson — Schizophrenia", cc:"Auditory hallucinations, withdrawal", dx:"Schizophrenia", sys:["Mental Health","Adult"], school:"Kaplan Medical", course:"Kaplan", lead:"on-request" },
    { t:"Ella West — Alzheimer's Disease", cc:"Memory complaints in an older adult", dx:"Alzheimer's dementia", sys:["Neurologic","Geriatric"], school:"Kaplan Medical", course:"Kaplan", lead:"on-request" }
  ];
  var PRICE = 150;
  var LEAD_LABEL = { "same-day": "⚡ Same-day", "fast-build": "⌛ 24–48h", "on-request": "📋 On request" };

  // state
  var state = { q: "", sys: new Set(), school: new Set(), lead: new Set() };
  var bundle = new Set();

  // build filter chip rows
  var systems = {}, schools = {};
  CASES.forEach(function (c) { c.sys.forEach(function (s) { systems[s] = 1; }); schools[c.school] = 1; });
  function chipRow(id, values, type) {
    var wrap = document.getElementById(id);
    if (!wrap) return;
    values.forEach(function (v) {
      var b = document.createElement('button');
      b.className = 'filter-chip';
      b.type = 'button';
      b.textContent = (type === 'lead') ? LEAD_LABEL[v] : v;
      b.setAttribute('data-val', v);
      b.addEventListener('click', function () {
        b.classList.toggle('active');
        var set = state[type === 'lead' ? 'lead' : (type === 'school' ? 'school' : 'sys')];
        if (set.has(v)) set.delete(v); else set.add(v);
        render();
      });
      wrap.appendChild(b);
    });
  }
  chipRow('fSystem', Object.keys(systems).sort(), 'sys');
  chipRow('fSchool', Object.keys(schools).sort(), 'school');
  chipRow('fLead', ['same-day', 'fast-build', 'on-request'], 'lead');

  function matches(c) {
    if (state.sys.size && !c.sys.some(function (s) { return state.sys.has(s); })) return false;
    if (state.school.size && !state.school.has(c.school)) return false;
    if (state.lead.size && !state.lead.has(c.lead)) return false;
    if (state.q) {
      var hay = (c.t + ' ' + c.cc + ' ' + c.dx + ' ' + c.sys.join(' ') + ' ' + c.school + ' ' + c.course).toLowerCase();
      if (hay.indexOf(state.q.toLowerCase()) === -1) return false;
    }
    return true;
  }

  var countEl = document.getElementById('catCount');
  var clearEl = document.getElementById('filterClear');
  var emptyEl = document.getElementById('catEmpty');

  function render() {
    var shown = CASES.filter(matches);
    grid.innerHTML = '';
    shown.forEach(function (c) {
      var inB = bundle.has(c.t);
      var card = document.createElement('div');
      card.className = 'case-card cat-card';
      card.innerHTML =
        '<h3>' + c.t + '</h3>' +
        '<p class="case-cc">' + c.cc + '</p>' +
        '<div class="case-meta">' + c.sys.slice(0, 2).map(function (s) { return '<span class="case-tag">' + s + '</span>'; }).join('') +
          '<span class="case-tag ' + (c.lead === 'same-day' ? 'lead-fast' : '') + '">' + LEAD_LABEL[c.lead] + '</span></div>' +
        '<p class="case-sub">' + c.school + ' · ' + c.course + '</p>' +
        '<div class="cat-card-actions">' +
          '<a class="link-arrow" href="' + (c.href || '/cases/') + '">Preview case →</a>' +
          '<button class="bundle-add' + (inB ? ' added' : '') + '" data-add="' + c.t.replace(/"/g, '') + '">' + (inB ? '✓ In bundle' : '+ Bundle') + '</button>' +
        '</div>';
      grid.appendChild(card);
    });
    if (countEl) countEl.textContent = 'Showing ' + shown.length + ' of ' + CASES.length + ' cases';
    var active = state.sys.size + state.school.size + state.lead.size + (state.q ? 1 : 0);
    if (clearEl) clearEl.style.display = active ? 'inline-flex' : 'none';
    if (emptyEl) emptyEl.style.display = shown.length ? 'none' : 'block';
  }

  // add-to-bundle (delegated)
  grid.addEventListener('click', function (e) {
    var b = e.target.closest('[data-add]');
    if (!b) return;
    var name = b.getAttribute('data-add');
    if (bundle.has(name)) bundle.delete(name); else bundle.add(name);
    renderBundle();
    render();
  });

  // search
  var search = document.getElementById('catSearch');
  var searchClear = document.getElementById('catSearchClear');
  var deb;
  if (search) {
    search.addEventListener('input', function () {
      clearTimeout(deb);
      deb = setTimeout(function () { state.q = search.value; if (searchClear) searchClear.style.display = search.value ? 'block' : 'none'; render(); }, 110);
    });
  }
  if (searchClear) searchClear.addEventListener('click', function () { search.value = ''; state.q = ''; searchClear.style.display = 'none'; render(); });

  if (clearEl) clearEl.addEventListener('click', function () {
    state.sys.clear(); state.school.clear(); state.lead.clear(); state.q = '';
    if (search) search.value = ''; if (searchClear) searchClear.style.display = 'none';
    document.querySelectorAll('.filter-chip.active').forEach(function (c) { c.classList.remove('active'); });
    render();
  });

  // bundle cart
  var bar = document.getElementById('bundleBar');
  function priceFor(n) {
    if (n === 0) return 0;
    var tiers = { 1: 150, 2: 280, 3: 390, 4: 470, 5: 540 };
    if (tiers[n]) return tiers[n];
    return 540 + (n - 5) * 80;
  }
  function renderBundle() {
    if (!bar) return;
    var n = bundle.size;
    if (!n) { bar.classList.remove('open'); return; }
    bar.classList.add('open');
    var total = priceFor(n);
    var full = n * PRICE;
    var save = full - total;
    bar.querySelector('[data-bundle-count]').textContent = n + (n === 1 ? ' case' : ' cases');
    bar.querySelector('[data-bundle-total]').textContent = '$' + total;
    var saveEl = bar.querySelector('[data-bundle-save]');
    saveEl.textContent = save > 0 ? ('Save $' + save) : 'Add a 2nd case to save';
    saveEl.style.color = save > 0 ? 'var(--lime-400)' : 'var(--on-dark-2)';
    var list = bar.querySelector('[data-bundle-list]');
    list.innerHTML = '';
    bundle.forEach(function (name) {
      var chip = document.createElement('span');
      chip.className = 'bundle-chip';
      chip.innerHTML = name.split('—')[0].trim() + ' <button data-remove="' + name.replace(/"/g, '') + '" aria-label="Remove">×</button>';
      list.appendChild(chip);
    });
  }
  if (bar) {
    bar.addEventListener('click', function (e) {
      var r = e.target.closest('[data-remove]');
      if (r) { bundle.delete(r.getAttribute('data-remove')); renderBundle(); render(); return; }
      if (e.target.closest('[data-bundle-order]')) {
        var names = Array.from(bundle);
        var label = names.length === 1 ? names[0] : (names.length + '-case bundle');
        if (window.cplCheckout) window.cplCheckout.open('order');
        var titleEls = document.querySelectorAll('[data-case-title],[data-case-name]');
        titleEls.forEach(function (el) { el.textContent = label; });
        var priceEl = document.querySelector('[data-case-price]');
        if (priceEl) priceEl.textContent = priceFor(bundle.size);
      }
    });
  }

  render();
})();
