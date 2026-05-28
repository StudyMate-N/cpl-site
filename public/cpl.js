/* ═══════════════════════════════════════════════════════════════════
   CPL — Front-end behaviors
   ═══════════════════════════════════════════════════════════════════
   Modules:
     - reveal:    scroll-triggered animations (data-reveal attributes)
     - counters:  animated number counting (data-counter attributes)
     - catalog:   live filtering + search on the /cases/ grid
     - bundle:    interactive bundle builder with live pricing
     - recent:    recently-viewed case tracking (localStorage)
     - popup:     engagement-scored email capture popup
     - exitIntent: exit-intent trigger on case-preview pages
     - forms:     lead-magnet form submission
     - sticky:    scroll-aware sticky-sidebar adjustments
   ═══════════════════════════════════════════════════════════════════ */
(function() {
  'use strict';

  /* ─── Storage helpers & session/visitor flags ───────────────── */
  const STORAGE_KEYS = {
    subscribed:    'cpl.subscribed',
    popupShown:    'cpl.popupShown',
    popupClosed:   'cpl.popupClosed',
    visitedCount:  'cpl.visitedCount',
    visitorReturn: 'cpl.visitorReturn',
    recentCases:   'cpl.recentCases',
    formEmail:     'cpl.formEmail',
    bundleState:   'cpl.bundleState',
  };
  const RECENT_CASES_MAX = 4;
  const SUBSCRIBED_TTL_DAYS = 30;

  function lsGet(key, fallback = null) {
    try {
      const raw = localStorage.getItem(key);
      if (raw == null) return fallback;
      try { return JSON.parse(raw); } catch { return raw; }
    } catch { return fallback; }
  }
  function lsSet(key, val) {
    try { localStorage.setItem(key, typeof val === 'string' ? val : JSON.stringify(val)); } catch {}
  }
  function ssGet(key, fallback = null) {
    try {
      const raw = sessionStorage.getItem(key);
      if (raw == null) return fallback;
      try { return JSON.parse(raw); } catch { return raw; }
    } catch { return fallback; }
  }
  function ssSet(key, val) {
    try { sessionStorage.setItem(key, typeof val === 'string' ? val : JSON.stringify(val)); } catch {}
  }

  function isSubscribed() {
    const ts = lsGet(STORAGE_KEYS.subscribed);
    if (!ts) return false;
    const ageDays = (Date.now() - Number(ts)) / (1000 * 60 * 60 * 24);
    return ageDays < SUBSCRIBED_TTL_DAYS;
  }
  function markSubscribed() { lsSet(STORAGE_KEYS.subscribed, Date.now()); }

  function isReturningVisitor() {
    const flag = lsGet(STORAGE_KEYS.visitorReturn);
    if (flag) return true;
    lsSet(STORAGE_KEYS.visitorReturn, Date.now());
    return false;
  }
  const returningVisitor = isReturningVisitor();

  (function bumpVisitedCount() {
    const n = (ssGet(STORAGE_KEYS.visitedCount, 0) || 0) + 1;
    ssSet(STORAGE_KEYS.visitedCount, n);
  })();
  function visitedThisSession() { return ssGet(STORAGE_KEYS.visitedCount, 1); }

  function escapeHtml(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
  }

  /* ─── REVEAL ──────────────────────────────────────────────── */
  const reveal = (function() {
    function init() {
      const targets = document.querySelectorAll('[data-reveal]');
      if (!targets.length) return;
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        targets.forEach(el => el.classList.add('is-revealed'));
        return;
      }
      if (typeof IntersectionObserver !== 'function') {
        targets.forEach(el => el.classList.add('is-revealed'));
        return;
      }
      const io = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const delay = parseInt(entry.target.getAttribute('data-reveal-delay') || '0', 10);
            setTimeout(() => entry.target.classList.add('is-revealed'), delay);
            io.unobserve(entry.target);
          }
        });
      }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
      targets.forEach(el => io.observe(el));
    }
    return { init };
  })();

  /* ─── COUNTERS ────────────────────────────────────────────── */
  const counters = (function() {
    function animate(el, target, suffix, duration = 1200) {
      const start = performance.now();
      function frame(now) {
        const t = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - t, 3);
        const v = Math.round(target * eased);
        el.textContent = v + suffix;
        if (t < 1) requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    }
    function init() {
      const targets = document.querySelectorAll('[data-counter]');
      if (!targets.length || typeof IntersectionObserver !== 'function') return;
      const io = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const el = entry.target;
            const target = parseInt(el.getAttribute('data-counter'), 10);
            const suffix = el.getAttribute('data-counter-suffix') || '';
            if (!isFinite(target) || target <= 0) {
              // Invalid or zero target — render a static final value, no animation
              el.textContent = (isFinite(target) ? target : 0) + suffix;
            } else {
              animate(el, target, suffix);
            }
            io.unobserve(el);
          }
        });
      }, { threshold: 0.5 });
      targets.forEach(el => io.observe(el));
    }
    return { init };
  })();

  /* ─── CATALOG ─────────────────────────────────────────────── */
  const catalog = (function() {
    let activeFilters = { school: null, tag: null, 'lead-time': null };
    let searchTerm = '';
    let allCards = [];

    function hasActiveFilter() {
      return !!(activeFilters.school || activeFilters.tag || activeFilters['lead-time']);
    }

    function applyFilters() {
      const grid = document.getElementById('caseGrid');
      const empty = document.getElementById('catalogEmpty');
      const countEl = document.getElementById('catalogResultCount');
      const clearBtn = document.getElementById('filterClear');
      if (!grid) return;

      let visibleCount = 0;
      const totalCount = allCards.length;
      const term = searchTerm.trim().toLowerCase();

      allCards.forEach(card => {
        let visible = true;
        if (activeFilters.school) {
          const cardSchool = card.getAttribute('data-school') || '';
          if (!cardSchool.split(',').includes(activeFilters.school)) visible = false;
        }
        if (visible && activeFilters.tag) {
          const cardTags = (card.getAttribute('data-tags') || '').split(',');
          if (!cardTags.includes(activeFilters.tag)) visible = false;
        }
        if (visible && activeFilters['lead-time']) {
          const lt = card.getAttribute('data-lead-time') || '';
          if (lt !== activeFilters['lead-time']) visible = false;
        }
        if (visible && term) {
          const blob = card.getAttribute('data-search') || '';
          if (!blob.includes(term)) visible = false;
        }
        card.style.display = visible ? '' : 'none';
        if (visible) visibleCount++;
      });

      if (empty) empty.style.display = visibleCount === 0 ? '' : 'none';
      if (grid) grid.style.display = visibleCount === 0 ? 'none' : '';
      if (countEl) {
        if (visibleCount === totalCount && !term && !hasActiveFilter()) {
          countEl.textContent = `Showing all ${totalCount} cases`;
        } else {
          countEl.textContent = `Showing ${visibleCount} of ${totalCount} cases`;
        }
      }
      if (clearBtn) {
        clearBtn.style.display = (hasActiveFilter() || term) ? '' : 'none';
      }
    }

    function toggleFilter(type, value, button) {
      if (activeFilters[type] === value) {
        activeFilters[type] = null;
        button.classList.remove('is-active');
      } else {
        document.querySelectorAll(`.filter-chip[data-filter="${type}"]`).forEach(b => b.classList.remove('is-active'));
        activeFilters[type] = value;
        button.classList.add('is-active');
      }
      applyFilters();
    }

    function clearAll() {
      activeFilters = { school: null, tag: null, 'lead-time': null };
      searchTerm = '';
      document.querySelectorAll('.filter-chip.is-active').forEach(b => b.classList.remove('is-active'));
      const input = document.getElementById('catalogSearch');
      if (input) input.value = '';
      const clearX = document.getElementById('catalogSearchClear');
      if (clearX) clearX.style.display = 'none';
      applyFilters();
    }

    function init() {
      const grid = document.getElementById('caseGrid');
      if (!grid) return;
      allCards = Array.from(grid.querySelectorAll('.case-card'));

      document.querySelectorAll('.filter-chip').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          toggleFilter(btn.getAttribute('data-filter'), btn.getAttribute('data-value'), btn);
        });
      });

      const search = document.getElementById('catalogSearch');
      const searchClear = document.getElementById('catalogSearchClear');
      if (search) {
        let timer;
        search.addEventListener('input', () => {
          clearTimeout(timer);
          timer = setTimeout(() => {
            searchTerm = search.value;
            if (searchClear) searchClear.style.display = search.value ? '' : 'none';
            applyFilters();
          }, 100);
        });
      }
      if (searchClear) {
        searchClear.addEventListener('click', () => {
          if (search) { search.value = ''; search.focus(); }
          searchTerm = '';
          searchClear.style.display = 'none';
          applyFilters();
        });
      }
      const clearBtn = document.getElementById('filterClear');
      if (clearBtn) clearBtn.addEventListener('click', clearAll);
    }

    return { init, clearAll };
  })();

  /* ─── BUNDLE BUILDER ──────────────────────────────────────── */
  const bundle = (function() {
    const TIERS = {
      1: { price: 150, label: 'Single guide',          saves: 0 },
      2: { price: 280, label: '2-case bundle',         saves: 20 },
      3: { price: 390, label: '3-case bundle',         saves: 60 },
      4: { price: 470, label: '4-case bundle',         saves: 130 },
      5: { price: 540, label: '5-case bundle',         saves: 210 },
    };
    const SINGLE = 150;

    let selected = new Set();
    let allCases = [];

    function priceFor(count) {
      if (count === 0) return null;
      if (count <= 5) return TIERS[count];
      return {
        price: 540 + (count - 5) * 80,
        label: `${count}-case order`,
        saves: 210 + (count - 5) * 70,
      };
    }

    function render() {
      const pool = document.getElementById('bundlePool');
      const cartItems = document.getElementById('bundleCartItems');
      const pricing = document.getElementById('bundlePricing');
      if (!pool || !cartItems) return;

      pool.innerHTML = '';
      allCases.forEach(c => {
        const isSelected = selected.has(c.slug);
        const chip = document.createElement('button');
        chip.className = 'bundle-pool-item' + (isSelected ? ' is-selected' : '');
        chip.setAttribute('data-slug', c.slug);
        chip.type = 'button';
        const tagsHtml = (c.tags || []).map(t => `<span class="case-tag">${escapeHtml(t)}</span>`).join('');
        chip.innerHTML = `
          <div class="bundle-pool-item-main">
            <div class="bundle-pool-item-title">${escapeHtml(c.title)}</div>
            <div class="bundle-pool-item-meta">${tagsHtml}</div>
          </div>
          <div class="bundle-pool-item-action">${isSelected ? '✓ Added' : '+ Add'}</div>
        `;
        chip.addEventListener('click', () => toggle(c.slug));
        pool.appendChild(chip);
      });

      cartItems.innerHTML = '';
      if (selected.size === 0) {
        cartItems.innerHTML = '<p class="muted" style="text-align:center; padding:32px 0;">No cases selected yet.<br>Click a case on the left to add it.</p>';
        if (pricing) pricing.style.display = 'none';
      } else {
        const list = document.createElement('div');
        list.className = 'bundle-cart-list';
        selected.forEach(slug => {
          const c = allCases.find(x => x.slug === slug);
          if (!c) return;
          const item = document.createElement('div');
          item.className = 'bundle-cart-item';
          item.innerHTML = `
            <div>
              <div class="bundle-cart-item-title">${escapeHtml(c.title)}</div>
              <div class="bundle-cart-item-meta">${c.lead_time === 'same-day' ? '⚡ Same-day' : '⌛ 24–48h'}</div>
            </div>
            <button class="bundle-cart-remove" type="button" aria-label="Remove">×</button>
          `;
          item.querySelector('.bundle-cart-remove').addEventListener('click', () => toggle(slug));
          list.appendChild(item);
        });
        cartItems.appendChild(list);
        if (pricing) pricing.style.display = '';

        const tier = priceFor(selected.size);
        const originalTotal = selected.size * SINGLE;

        const labelEl = document.getElementById('bundleTierLabel');
        const savesEl = document.getElementById('bundleTierSaves');
        const finalEl = document.getElementById('bundlePriceFinal');
        const origEl = document.getElementById('bundlePriceOriginal');
        const savingsEl = document.getElementById('bundlePriceSavings');
        const orderBtn = document.getElementById('bundleOrder');

        if (labelEl) labelEl.textContent = tier.label;
        if (savesEl) {
          if (tier.saves > 0) {
            savesEl.textContent = `Save $${tier.saves}`;
            savesEl.style.display = '';
          } else {
            savesEl.style.display = 'none';
          }
        }
        if (finalEl) finalEl.textContent = `$${tier.price}`;
        if (origEl) {
          if (tier.saves > 0) {
            origEl.textContent = `$${originalTotal}`;
            origEl.style.display = '';
          } else {
            origEl.style.display = 'none';
          }
        }
        if (savingsEl) {
          if (tier.saves > 0) {
            savingsEl.textContent = `You save $${tier.saves}`;
            savingsEl.style.display = '';
          } else {
            savingsEl.style.display = 'none';
          }
        }

        if (orderBtn) {
          const slugs = Array.from(selected);
          const titles = slugs.map(s => allCases.find(c => c.slug === s)?.title || s);
          const subject = `CPL ${tier.label} — ${titles.length} case${titles.length > 1 ? 's' : ''}`;
          const bodyLines = [
            `Hi CPL team,`,
            ``,
            `I'd like to order this bundle:`,
            ...titles.map(t => `  • ${t}`),
            ``,
            `Total: $${tier.price}${tier.saves > 0 ? ` (saving $${tier.saves})` : ''}`,
            ``,
            `For each case, my patient name on the iHuman platform is:`,
            ...titles.map(t => `  • ${t}: ____________`),
            ``,
            `Please confirm before charging. Thanks!`,
          ];
          orderBtn.onclick = () => {
            window.location.href = `mailto:Tutorspot98@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(bodyLines.join('\n'))}`;
          };
        }
      }

      lsSet(STORAGE_KEYS.bundleState, Array.from(selected));
    }

    function toggle(slug) {
      if (selected.has(slug)) selected.delete(slug);
      else selected.add(slug);
      render();
    }

    function init() {
      const root = document.querySelector('.bundle-builder');
      if (!root) return;
      try {
        allCases = JSON.parse(root.getAttribute('data-cases') || '[]');
      } catch (e) {
        allCases = [];
        return;
      }
      const saved = lsGet(STORAGE_KEYS.bundleState, []);
      if (Array.isArray(saved)) {
        saved.forEach(slug => {
          if (allCases.find(c => c.slug === slug)) selected.add(slug);
        });
      }
      render();
    }

    function addCaseBySlug(slug) {
      if (allCases.find(c => c.slug === slug)) {
        selected.add(slug);
        render();
      }
    }

    return { init, toggle, addCaseBySlug };
  })();

  /* ─── RECENT CASES ────────────────────────────────────────── */
  const recent = (function() {
    function trackCurrentPage() {
      const match = window.location.pathname.match(/^\/case\/([a-z0-9-]+)\/?$/);
      if (!match) return;
      const slug = match[1];
      const h1 = document.querySelector('.preview-hero h1');
      if (!h1) return;
      const title = h1.textContent.trim();

      let list = lsGet(STORAGE_KEYS.recentCases, []) || [];
      list = list.filter(x => x.slug !== slug);
      list.unshift({ slug, title, ts: Date.now() });
      list = list.slice(0, RECENT_CASES_MAX);
      lsSet(STORAGE_KEYS.recentCases, list);
    }

    function render() {
      const targets = document.querySelectorAll('[data-render="recent-cases"]');
      if (!targets.length) return;

      const list = lsGet(STORAGE_KEYS.recentCases, []) || [];
      const currentSlug = (window.location.pathname.match(/^\/case\/([a-z0-9-]+)/) || [])[1];
      const filtered = list.filter(x => x.slug !== currentSlug);

      if (filtered.length === 0) {
        targets.forEach(t => { t.style.display = 'none'; });
        return;
      }
      targets.forEach(target => {
        target.style.display = '';
        const inner = target.querySelector('[data-recent-list]') || target;
        inner.innerHTML = filtered.slice(0, 3).map(x => `
          <a class="recent-case-item" href="/case/${escapeHtml(x.slug)}/">
            <span class="recent-case-arrow">↩</span>
            <span class="recent-case-title">${escapeHtml(x.title)}</span>
          </a>
        `).join('');
      });
    }

    function init() {
      trackCurrentPage();
      render();
    }

    return { init };
  })();

  /* ─── POPUP ───────────────────────────────────────────────── */
  const popup = (function() {
    let pageEnterTime = Date.now();
    let maxScrollDepth = 0;
    let clickedCaseCard = false;
    let firedThisSession = false;
    const FIRE_THRESHOLD = 6;
    const MIN_TIME_ON_PAGE = 5000;

    function calculateScore() {
      let s = 0;
      const timeOnPage = Date.now() - pageEnterTime;
      if (timeOnPage >= 15000) s += 1;
      if (maxScrollDepth >= 0.4) s += 2;
      if (maxScrollDepth >= 0.75) s += 3;
      if (visitedThisSession() >= 2) s += 3;
      if (clickedCaseCard) s += 5;
      if (returningVisitor) s += 2;
      return s;
    }

    function shouldFire() {
      if (firedThisSession) return false;
      if (isSubscribed()) return false;
      if (ssGet(STORAGE_KEYS.popupShown)) return false;
      if (ssGet(STORAGE_KEYS.popupClosed)) return false;
      const timeOnPage = Date.now() - pageEnterTime;
      if (timeOnPage < MIN_TIME_ON_PAGE) return false;
      return calculateScore() >= FIRE_THRESHOLD;
    }

    function fire(reason) {
      const overlay = document.getElementById('cplPopup');
      if (!overlay) return;
      if (firedThisSession) return;
      firedThisSession = true;
      ssSet(STORAGE_KEYS.popupShown, Date.now());
      overlay.classList.add('open');

      const lastEmail = lsGet(STORAGE_KEYS.formEmail);
      if (lastEmail) {
        const input = overlay.querySelector('input[type="email"]');
        if (input && !input.value) input.value = lastEmail;
      }
      setTimeout(() => {
        const input = overlay.querySelector('input[type="email"]');
        if (input) input.focus();
      }, 250);
    }

    function close() {
      const overlay = document.getElementById('cplPopup');
      if (!overlay) return;
      overlay.classList.remove('open');
      ssSet(STORAGE_KEYS.popupClosed, Date.now());
    }

    function setupScrollTracking() {
      function update() {
        const docHeight = Math.max(
          document.body.scrollHeight,
          document.documentElement.scrollHeight
        ) - window.innerHeight;
        if (docHeight <= 0) return;
        const depth = Math.min(window.scrollY / docHeight, 1);
        if (depth > maxScrollDepth) maxScrollDepth = depth;
      }
      window.addEventListener('scroll', () => {
        update();
        if (shouldFire()) fire('scroll-score');
      }, { passive: true });
      setInterval(() => {
        if (shouldFire()) fire('time-score');
      }, 3000);
    }

    function trackCaseCardClicks() {
      document.querySelectorAll('.case-card').forEach(card => {
        card.addEventListener('click', () => { clickedCaseCard = true; });
      });
    }

    function init() {
      const overlay = document.getElementById('cplPopup');
      if (!overlay) return;

      window.cplClosePopup = close;
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close();
      });
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay.classList.contains('open')) close();
      });

      const form = overlay.querySelector('form');
      if (form) {
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const emailInput = form.querySelector('input[type="email"]');
          const email = (emailInput.value || '').trim();
          if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            emailInput.focus();
            return;
          }
          const btn = form.querySelector('button[type="submit"]');
          const originalLabel = btn.textContent;
          btn.disabled = true;
          btn.textContent = 'Sending…';
          try {
            const res = await fetch('/api/subscribe', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email, volumes: ['history', 'physical-exam', 'ddx', 'plan'] }),
            });
            const data = await res.json();
            if (res.ok && data.ok) {
              markSubscribed();
              lsSet(STORAGE_KEYS.formEmail, email);
              window.location.href = '/thank-you/';
            } else {
              btn.disabled = false;
              btn.textContent = originalLabel;
              alert(data.error || 'Something went wrong. Try again.');
            }
          } catch (err) {
            btn.disabled = false;
            btn.textContent = originalLabel;
            alert('Could not reach the server. Try again in a minute.');
          }
        });
      }

      setupScrollTracking();
      trackCaseCardClicks();
    }

    return { init, fire, close };
  })();

  /* ─── EXIT INTENT ─────────────────────────────────────────── */
  const exitIntent = (function() {
    function init() {
      if (!window.location.pathname.match(/^\/case\//)) return;
      if (isSubscribed()) return;

      let armed = false;
      setTimeout(() => { armed = true; }, 8000);

      document.addEventListener('mouseleave', (e) => {
        if (!armed) return;
        if (e.clientY > 5) return;
        if (ssGet(STORAGE_KEYS.popupShown)) return;
        popup.fire('exit-intent');
        armed = false;
      });
    }
    return { init };
  })();

  /* ─── FORMS ───────────────────────────────────────────────── */
  const forms = (function() {
    function showError(form, msg) {
      let existing = form.querySelector('.form-error');
      if (existing) existing.remove();
      const div = document.createElement('div');
      div.className = 'form-error';
      div.textContent = msg;
      form.appendChild(div);
    }
    function clearError(form) {
      const existing = form.querySelector('.form-error');
      if (existing) existing.remove();
    }

    function init() {
      document.querySelectorAll('.resource-card').forEach(card => {
        card.addEventListener('click', (e) => {
          if (e.target.tagName === 'A') return;
          e.preventDefault();
          const input = card.querySelector('input[type="checkbox"]');
          if (input) {
            input.checked = !input.checked;
            card.classList.toggle('selected', input.checked);
          }
        });
      });

      document.querySelectorAll('form[data-form="leadmagnet"]').forEach(form => {
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const emailInput = form.querySelector('input[type="email"]');
          const email = (emailInput.value || '').trim();
          if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            showError(form, 'Please enter a valid email address.');
            emailInput.focus();
            return;
          }
          const checkboxes = form.querySelectorAll('input[name="volumes"]:checked');
          const hiddenVolumes = form.querySelector('input[type="hidden"][name="volumes"]');
          let volumes = [];
          if (checkboxes.length > 0) {
            checkboxes.forEach(cb => volumes.push(cb.value));
          } else if (hiddenVolumes) {
            volumes = hiddenVolumes.value.split(',').map(s => s.trim()).filter(Boolean);
          }
          if (volumes.length === 0) {
            showError(form, 'Please select at least one cheat sheet.');
            return;
          }

          const btn = form.querySelector('button[type="submit"]');
          const originalText = btn.textContent;
          btn.disabled = true;
          btn.textContent = 'Sending…';
          clearError(form);

          try {
            const res = await fetch('/api/subscribe', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email, volumes }),
            });
            const data = await res.json();
            if (res.ok && data.ok) {
              markSubscribed();
              lsSet(STORAGE_KEYS.formEmail, email);
              window.location.href = '/thank-you/';
            } else {
              showError(form, data.error || 'Something went wrong. Try again or email Tutorspot98@gmail.com.');
              btn.disabled = false;
              btn.textContent = originalText;
            }
          } catch (err) {
            showError(form, 'Could not reach the server. Try again in a minute.');
            btn.disabled = false;
            btn.textContent = originalText;
          }
        });
      });
    }

    return { init };
  })();

  /* ─── STICKY ─────────────────────────────────────────────── */
  const sticky = (function() {
    function init() {
      const sidebar = document.querySelector('.preview-side-cta');
      if (!sidebar) return;
      window.addEventListener('scroll', () => {
        sidebar.classList.toggle('scrolled', window.scrollY > 200);
      }, { passive: true });
    }
    return { init };
  })();

  /* ─── BOOT ────────────────────────────────────────────────── */
  function boot() {
    reveal.init();
    counters.init();
    catalog.init();
    bundle.init();
    recent.init();
    popup.init();
    exitIntent.init();
    forms.init();
    sticky.init();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  window.cpl = {
    catalog, bundle, popup, recent, reveal, counters,
    isSubscribed, visitedThisSession,
  };

})();
