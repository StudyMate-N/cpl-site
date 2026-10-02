/* CPL library: search, version references, filters, pagination and bundle cart. */
(function () {
  'use strict';
  var grid = document.getElementById('caseGrid');
  if (!grid) return;
  var cases = window.CPL_CASES || [];
  var search = document.getElementById('catSearch');
  var clearSearch = document.getElementById('catSearchClear');
  var reset = document.getElementById('filterClear');
  var systems = document.getElementById('fSystem');
  var schools = document.getElementById('fSchool');
  var lead = document.getElementById('fLead');
  var more = document.getElementById('catLoadMore');
  var count = document.getElementById('catCount');
  var empty = document.getElementById('catEmpty');
  var pageSize = 24, limit = pageSize;
  var bundle = new Set();
  var leadLabels = {'same-day':'Same-day guide','fast-build':'24–48h build','on-request':'Confirm availability'};
  function norm(value) { return String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, ''); }
  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function options(select, values) {
    Array.from(new Set(values)).filter(Boolean).sort().forEach(function (value) { var option = el('option', '', value); option.value = value; select.appendChild(option); });
  }
  options(systems, cases.reduce(function (all, c) { return all.concat(c.sys || []); }, []));
  options(schools, cases.map(function (c) { return c.school; }));
  var queryParams = new URLSearchParams(location.search);
  search.value = queryParams.get('q') || '';
  [systems, schools, lead].forEach(function (select, n) {
    var value = queryParams.get(['system','school','availability'][n]);
    if (value && Array.from(select.options).some(function (o) { return o.value === value; })) select.value = value;
  });
  function matches(c) {
    if (systems.value && (c.sys || []).indexOf(systems.value) === -1) return false;
    if (schools.value && schools.value !== c.school) return false;
    if (lead.value && lead.value !== c.lead) return false;
    var query = search.value.trim().toLowerCase();
    if (!query) return true;
    var hay = [c.t,c.cc,c.dx,c.school,c.course,c.patient].concat(c.sys || [], c.aliases || []).join(' ');
    return norm(hay).indexOf(norm(query)) !== -1;
  }
  function updateUrl() {
    var p = new URLSearchParams();
    if (search.value.trim()) p.set('q', search.value.trim());
    if (systems.value) p.set('system', systems.value);
    if (schools.value) p.set('school', schools.value);
    if (lead.value) p.set('availability', lead.value);
    var url = location.pathname + (p.toString() ? '?' + p.toString() : '') + location.hash;
    try { history.replaceState(null, '', url); } catch (ignore) {}
  }
  function render() {
    var matched = cases.filter(matches), visible = matched.slice(0, limit);
    grid.replaceChildren();
    visible.forEach(function (c) {
      var name = c.t.split('—')[0].trim(), focus = c.t.indexOf('—') === -1 ? c.dx : c.t.split('—').slice(1).join('—').trim();
      var card = el('article', 'case-card cat-card');
      var top = el('div','card-top');
      top.appendChild(el('span','system-label', (c.sys || []).filter(function (s) { return s !== 'Adult'; })[0] || 'Clinical'));
      top.appendChild(el('span','availability' + (c.lead === 'same-day' ? ' ready' : ''),leadLabels[c.lead] || 'Confirm availability'));
      card.appendChild(top);
      var h = el('h3'), titleLink = el('a','',name); titleLink.href = c.href; h.appendChild(titleLink); card.appendChild(h);
      card.appendChild(el('p','case-focus',focus));
      card.appendChild(el('p','case-cc',c.cc));
      var course = el('div','card-course',c.course || 'Course to confirm');
      course.appendChild(el('span','',c.school)); card.appendChild(course);
      var actions = el('div','cat-card-actions'), link = el('a','','View case'); link.href = c.href; actions.appendChild(link);
      var selected = bundle.has(c.t), button = el('button','bundle-add' + (selected ? ' added' : ''),selected ? 'Selected' : '+ Bundle');
      button.type = 'button'; button.setAttribute('data-add',c.t); button.setAttribute('aria-pressed',String(selected)); button.setAttribute('aria-label',(selected ? 'Remove ' : 'Add ') + name + (selected ? ' from bundle' : ' to bundle'));
      actions.appendChild(button); card.appendChild(actions); grid.appendChild(card);
    });
    count.textContent = matched.length ? visible.length + ' of ' + matched.length + ' matching cases' : '0 matching cases';
    clearSearch.hidden = !search.value;
    reset.hidden = !(search.value || systems.value || schools.value || lead.value);
    empty.hidden = matched.length > 0;
    more.hidden = visible.length >= matched.length;
    more.textContent = 'Show more cases (' + (matched.length - visible.length) + ' remaining)';
    updateUrl();
  }
  function priceFor(n) {
    var tiers = {0:0,1:150,2:280,3:390,4:470,5:540};
    return tiers[n] !== undefined ? tiers[n] : 540 + (n - 5) * 80;
  }
  var bar = document.getElementById('bundleBar');
  function sizeBundleBar() { document.body.style.setProperty('--bundle-height', bar.getBoundingClientRect().height + 'px'); }
  if (window.ResizeObserver) new ResizeObserver(sizeBundleBar).observe(bar);
  function renderBundle() {
    var n = bundle.size, total = priceFor(n), save = n * 150 - total;
    bar.classList.toggle('open',n > 0); bar.inert = n === 0;
    bar.querySelector('[data-bundle-count]').textContent = n + (n === 1 ? ' case' : ' cases');
    bar.querySelector('[data-bundle-total]').textContent = '$' + total;
    bar.querySelector('[data-bundle-save]').textContent = save ? 'Save $' + save : '';
    var list = bar.querySelector('[data-bundle-list]'); list.replaceChildren();
    bundle.forEach(function (name) {
      var chip = el('span','bundle-chip',name.split('—')[0].trim()), button = el('button','','×');
      button.type = 'button'; button.setAttribute('data-remove',name); button.setAttribute('aria-label','Remove ' + name + ' from bundle');
      chip.appendChild(button); list.appendChild(chip);
    });
    document.body.classList.toggle('has-bundle',n > 0);
    sizeBundleBar();
  }
  grid.addEventListener('click',function (ev) {
    var b = ev.target.closest('[data-add]'); if (!b) return;
    var name = b.getAttribute('data-add');
    if (bundle.has(name)) bundle.delete(name); else bundle.add(name);
    var selected = bundle.has(name);
    b.classList.toggle('added',selected); b.textContent = selected ? 'Selected' : '+ Bundle'; b.setAttribute('aria-pressed',String(selected));
    b.setAttribute('aria-label',(selected ? 'Remove ' : 'Add ') + name.split('—')[0].trim() + (selected ? ' from bundle' : ' to bundle'));
    renderBundle();
  });
  bar.addEventListener('click',function (ev) {
    var remove = ev.target.closest('[data-remove]');
    if (remove) { bundle.delete(remove.getAttribute('data-remove')); renderBundle(); render(); return; }
    if (ev.target.closest('[data-bundle-order]') && bundle.size && window.cplCheckout) {
      var names = Array.from(bundle), label = names.length === 1 ? names[0] : names.length + '-case bundle: ' + names.join('; ');
      window.cplCheckout.open('order');
      document.querySelector('[data-case-title]').textContent = names.length === 1 ? names[0] : names.length + '-case bundle';
      document.querySelector('[data-case-name]').textContent = label;
      document.querySelector('[data-case-price]').textContent = priceFor(bundle.size);
      var delivery = document.querySelector('[data-case-delivery]'); if (delivery) delivery.textContent = 'Case versions and delivery windows confirmed before payment';
      var alias = document.querySelector('.modal input[name=alias]'); if (alias) alias.value = '';
    }
  });
  var debounce;
  search.addEventListener('input',function () { clearTimeout(debounce); debounce = setTimeout(function () { limit = pageSize; render(); },120); });
  clearSearch.addEventListener('click',function () { search.value = ''; limit = pageSize; render(); search.focus(); });
  [systems,schools,lead].forEach(function (select) { select.addEventListener('change',function () { limit = pageSize; render(); }); });
  function resetAll() { search.value = ''; systems.value = ''; schools.value = ''; lead.value = ''; limit = pageSize; render(); search.focus(); }
  reset.addEventListener('click',resetAll);
  document.querySelector('[data-reset-catalog]').addEventListener('click',resetAll);
  more.addEventListener('click',function () { limit += pageSize; render(); });
  window.addEventListener('popstate',function () {
    var p = new URLSearchParams(location.search); search.value = p.get('q') || '';
    systems.value = p.get('system') || ''; schools.value = p.get('school') || ''; lead.value = p.get('availability') || '';
    limit = pageSize; render();
  });
  render();
})();
