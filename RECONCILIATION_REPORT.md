# CPL Repo ↔ Design Workspace — Reconciliation Report

**Date:** 2026-05-30
**Scope:** Prove the deployed public site matches the design workspace's role-address mapping, close any gaps, and document the source-of-truth so the two stay byte-aligned.
**Constraints honored:** No flows / pricing / security / env-var changes. `CPL_TOKEN_SECRET` not rotated. Redeploy only for the one real gap (Step 4.1).

**Role-address mapping (authoritative):**

| Address | Used for |
|---|---|
| `hello@clinicalperformancelab.com` | footers, "Contact" nav, terms general contact, about "Email the team", confirmation sender |
| `orders@clinicalperformancelab.com` | case page "Order this guide →" mailto |
| `support@clinicalperformancelab.com` | privacy deletion/data, support-chat escalation |

---

## (1) STEP 1 — Page-chrome source from `build.py` (verbatim)

### The three role constants (build.py lines 40–42)
```python
CONTACT_EMAIL = "hello@clinicalperformancelab.com"     # brand front door · footer/about/general
ORDER_EMAIL   = "orders@clinicalperformancelab.com"    # "Order this guide" requests · invoicing
SUPPORT_EMAIL = "support@clinicalperformancelab.com"   # delivery issues · refunds · "delete my data"
```

### Header / nav (`nav_html()`, lines 286–318)
Plain string (no email in the nav itself; the "Contact" link lives in the footer).
```python
def nav_html():
    return """
<nav class="nav">
  <div class="nav-inner">
    <a href="/" class="nav-brand">
      <span class="nav-logo">CPL</span>
      <span>Clinical Performance Lab<small>iHuman case mastery</small></span>
    </a>
    <ul class="nav-links">
      <li><a href="/simulator/">Simulator</a></li>
      <li><a href="/free-resources/">Free cheat sheets</a></li>
      <li><a href="/cases/">Case catalog</a></li>
      <li><a href="/faq/">FAQ</a></li>
      <li><a href="/about/">About</a></li>
    </ul>
    <div class="nav-actions">
      <a href="/simulator/" class="btn btn-primary btn-sm nav-cta-desktop">Try the simulator</a>
      <button class="nav-burger" aria-label="Open menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</nav>

<div class="menu-backdrop"></div>
<div class="mobile-menu">
  <button class="mobile-menu-close" data-menu-close aria-label="Close menu">×</button>
  <a href="/simulator/" data-menu-close>Simulator</a>
  <a href="/free-resources/" data-menu-close>Free cheat sheets</a>
  <a href="/cases/" data-menu-close>Case catalog</a>
  <a href="/faq/" data-menu-close>FAQ</a>
  <a href="/about/" data-menu-close>About</a>
  <a href="/simulator/" class="btn btn-primary" data-menu-close>Try the simulator</a>
</div>
"""
```

### Global footer (`footer_html()`, lines 321–364)
f-string; tagline email link + "Contact" nav link both `{CONTACT_EMAIL}`.
```python
def footer_html():
    year = datetime.now(timezone.utc).year
    return f"""
<footer class="footer">
  <div class="footer-inner">
    <div>
      <div class="footer-brand">Clinical Performance Lab</div>
      <p class="footer-tagline">Clinical reasoning platform for nursing students. Free simulator, free cheat sheets, complete iHuman case guides for purchase. Built on 200+ verified submissions across Chamberlain (NR509, NR511, NR602), Walden (NURS 6512, NRNP 6531, 6541, 6552, 6568), and other programs.</p>
      <p class="footer-tagline" style="margin-top:12px;">
        <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
      </p>
    </div>
    <div>
      <h4>Learn</h4>
      <ul>
        <li><a href="/simulator/">Case Simulator</a></li>
        <li><a href="/free-resources/">Free Cheat Sheets</a></li>
        <li><a href="/sample-guide/">Sample Guide</a></li>
        <li><a href="/cases/">Case Catalog</a></li>
      </ul>
    </div>
    <div>
      <h4>Company</h4>
      <ul>
        <li><a href="/about/">About CPL</a></li>
        <li><a href="/faq/">FAQ</a></li>
        <li><a href="mailto:{CONTACT_EMAIL}">Contact</a></li>
      </ul>
    </div>
    <div>
      <h4>Legal</h4>
      <ul>
        <li><a href="/terms/">Terms of Use</a></li>
        <li><a href="/privacy/">Privacy</a></li>
      </ul>
    </div>
  </div>

  <div class="footer-bottom">
    <span>© {year} Clinical Performance Lab. For personal study use only.</span>
    <span>Independent educational resource · Not affiliated with iHuman or any institution</span>
  </div>
</footer>
"""
```

### Case-page "Order this guide →" block (`build_case_preview()`, lines 1035–1049)
```python
      <aside class="cp-aside">
        <div class="order-card" id="order">
          <div class="order-card-inner">
            <div class="order-eyebrow">{course or 'iHuman case'}</div>
            <h4>Get this case guide</h4>
            <div class="order-price"><span class="cur">$</span>150</div>
            <p class="sub">Word + PDF, delivered same day to your inbox.</p>
            <a href="mailto:{ORDER_EMAIL}?subject={order_subject}" class="btn btn-lime" data-order="{order_attr}" data-price="150">Order this guide →</a>
            <button class="btn btn-ghost-dark" data-access-code>I have an access code</button>
            <ul class="order-incl">
              <li>Same-day delivery</li>
              <li>Mapped to the scoring rubric</li>
              <li>Customized to your patient alias</li>
            </ul>
            <div class="order-code">Code <strong>CPLFIRST15</strong> — 15% off your first single case</div>
          </div>
```

> ⚠️ **Critical architecture note for byte-alignment.** `build.py`'s `nav_html()`/`footer_html()` render **only the 171 case pages**. The **main pages** (home, about, terms, privacy, faq, etc.) are rendered by **`deploy_redesign.py`**, which copies the design's redesign HTML and applies path + email substitutions. There are **two render paths** for page chrome — both route to the same role constants, but when diffing the design markup: diff **case pages against `build.py`**, and **main pages against the redesign HTML + `deploy_redesign.py` SUBS**.

---

## (2) STEP 2 — Front-end JS/CSS source of truth

| Asset | Canonical source | Copied to `public/` by |
|---|---|---|
| `cpl.js` | **`src/cpl.js`** | `build.py:build_js()` + `deploy_redesign.py:sync_assets()` |
| `cpl-checkout.js` | **`src/cpl-checkout.js`** | same |
| `cpl-support.js` | **`src/cpl-support.js`** | same |
| `cpl-catalog.js` | **`src/cpl-catalog.js`** | same |
| `cpl-simulator.jsx` | **`src/cpl-simulator.jsx`** | same |
| **`styles.css`** | ⚠️ **`_newdesign_extract/redesign/cpl.css` — which is `.gitignore`d** (no committed in-repo source) | `deploy_redesign.py:sync_assets()` |

- **JS = one clean source of truth: `src/`.** ✅
- **CSS = a drift risk.** The deployed `public/styles.css` is committed, but its *build source* (`cpl.css`) exists only in the gitignored design-extraction dir. There is **no canonical `cpl.css` in the repo's tracked tree** (`git ls-files | grep css` → only `public/styles.css`).

**Recommended direction:** Design workspace owns visual + content; the repo's `src/` is the canonical in-repo mirror. **Design edits → ported into `src/` (JS) and into `build.py`/`deploy_redesign.py` (chrome + addresses).** To close the CSS gap: **commit the canonical `cpl.css` into `src/cpl.css`** and point `deploy_redesign.py` at `src/cpl.css` (not the gitignored extract) so CSS has one tracked source like the JS.

---

## (3) STEP 3 — grep result + what was rebranded

```
$ grep -rn "Tutorspot98\|cpl-site.vercel.app" src/ public/ api/ emails/ build.py
(no output — clean)
```

Admin / support / email-preview equivalents:

| Design asset | In repo / deployed? | Action |
|---|---|---|
| `cpl-admin.js` (admin dashboard) | **No** | Design-only — no action |
| `cpl-support.js` (support chat) | **Yes** (`src/` + `public/`) | Already rebranded → `support@` only (grep clean). No further action |
| `cpl-emails.js` (in-app email preview) | **No** | Design-only — no action |

**Rebranded/rebuilt this session:** only the Step-4.1 terms gap (below). `deploy_redesign.py` SUBS updated → `python deploy_redesign.py` rebuilt main pages → committed `1c66dd1` → redeployed. Nothing from the grep itself (already clean).

---

## (4) STEP 4 — Judgment calls

1. **Terms page contact:** GENERAL contact ("Questions about these terms?") → ships as **`hello@`** ✅ *(was `support@`; fixed to match design and deployed — the one real gap).*
2. **Admin internal-ops address:** **No admin is deployed** (`cpl-admin.js` is design-only) → N/A in repo; if/when it ships, map internal ops → `orders@` per design.
3. **Support-chat escalation:** **`support@`** ✅ (deployed `cpl-support.js` resolves to `support@` only).
4. **Site links www vs apex:** Repo ships **`www`** (canonical — `SITE_URL`/`SITE` = `https://www.clinicalperformancelab.com`; apex 307-redirects to www). Design should align its apex `BASE` → **www**.

---

## (5) STEP 5 — Live-site ground truth (raw outputs)

```
homepage   grep -ic Tutorspot98 :  0
case page  grep -ic Tutorspot98 :  0
about      grep -ic Tutorspot98 :  0
terms      grep -ic Tutorspot98 :  0
privacy    grep -ic Tutorspot98 :  0

case /case/harvey-hoya-htn/  mailto sort -u:
  mailto:hello@clinicalperformancelab.com
  mailto:orders@clinicalperformancelab.com

terms/   mailto (post-fix):      3  mailto:hello@clinicalperformancelab.com
about/   mailto:                 3  mailto:hello@clinicalperformancelab.com   (incl. "Email the team")
privacy/ mailto:                 2  mailto:hello@clinicalperformancelab.com
                                 1  mailto:support@clinicalperformancelab.com   (deletion/data line)
cpl-support.js escalation:          support@clinicalperformancelab.com
```

**Rendered homepage footer HTML (view-source):**
```html
<footer class="footer">
  <div class="footer-inner">
    <div>
      <div class="footer-brand">Clinical Performance Lab</div>
      <p class="footer-tagline">Learn to think like a clinician. Master iHuman. A clinical reasoning platform for nursing students — free simulator, free cheat sheets, and complete case guides built on 200+ verified submissions.</p>
      <p class="footer-tagline"><a href="mailto:hello@clinicalperformancelab.com">hello@clinicalperformancelab.com</a></p>
      ...
        <li><a href="mailto:hello@clinicalperformancelab.com">Contact</a></li>
  <div class="footer-bottom">
```
*Note: the homepage footer copy differs slightly from `build.py`'s `footer_html()` tagline because the homepage is rendered by `deploy_redesign.py` from the design's redesign HTML (see the two-render-path note in §1). Both use `hello@`.*

---

## Bottom line

- **Deployed site matches the design role-mapping** on every public surface; **all five `Tutorspot98` counts = 0**.
- **One gap found & closed:** terms general-contact `support@` → **`hello@`** (deployed, verified — commit `1c66dd1`).
- **Two source-of-truth items for the design side to action:**
  1. Confirm the **two render paths** (case pages = `build.py`; main pages = redesign HTML via `deploy_redesign.py`) so chrome stays byte-aligned.
  2. **Commit a canonical `cpl.css` into `src/`** to remove the gitignored-CSS drift risk.
- No flows / pricing / security / env touched; `CPL_TOKEN_SECRET` not rotated.
