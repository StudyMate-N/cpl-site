"""
CPL static site generator.

Produces every HTML page in public/ from the case catalog and content modules.
After running this, also runs the cheat sheet generator to refresh the PDFs.

Usage:
    python3 build.py

Output:
    public/
      index.html
      free-resources/index.html
      cases/index.html
      case/{slug}/index.html        (one per case)
      confirm/index.html            (token validator landing)
      thank-you/index.html
      about/index.html
      faq/index.html
      cheat-sheets/*.pdf            (from generate_cheat_sheets.py)
      sitemap.xml
      robots.txt
"""

import os
import html
import json
from datetime import datetime, timezone

from cases_data import CASES, PRICING, by_lead_time, by_slug, COURSES

# ─── Configuration ────────────────────────────────────────────────
BASE_URL = "https://clinicalperformancelab.vercel.app"
SITE_NAME = "Clinical Performance Lab"
SITE_TAG = "Submission-ready clinical reasoning for nursing students"

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")

CHEAT_SHEETS = [
    {"id": "history",       "vol": "I",   "title": "History Framework",        "pages": 8, "filename": "cpl-vol-1-history.pdf"},
    {"id": "physical-exam", "vol": "II",  "title": "Universal PE Checklist",   "pages": 9, "filename": "cpl-vol-2-physical-exam.pdf"},
    {"id": "ddx",           "vol": "III", "title": "DDx & Key Findings",       "pages": 8, "filename": "cpl-vol-3-ddx.pdf"},
    {"id": "plan",          "vol": "IV",  "title": "Management Plan & SOAP",   "pages": 9, "filename": "cpl-vol-4-plan.pdf"},
]


# ─── HTML helpers ─────────────────────────────────────────────────
def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def write_page(rel_path, body, title=None, description=None, page_class=""):
    """Write a page to public/{rel_path}/index.html with the base shell."""
    full_title = f"{title} · {SITE_NAME}" if title else SITE_NAME
    desc = description or SITE_TAG
    full_path = os.path.join(PUBLIC, rel_path, "index.html") if rel_path else os.path.join(PUBLIC, "index.html")
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    canonical = f"{BASE_URL}/{rel_path}/" if rel_path else f"{BASE_URL}/"

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
</head>
<body class="{esc(page_class)}">

{nav_html()}

{body}

{footer_html()}

{popup_html()}

<script src="/cpl.js" defer></script>

</body>
</html>
"""
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(html_doc)


# ─── Reusable HTML chunks ─────────────────────────────────────────
def nav_html():
    return """
<nav class="nav">
  <div class="nav-inner">
    <a href="/" class="nav-brand">
      <span class="nav-logo">CPL</span>
      <span>Clinical Performance Lab
        <small>iHuman case mastery</small>
      </span>
    </a>
    <ul class="nav-links">
      <li><a href="/free-resources/">Free Cheat Sheets</a></li>
      <li><a href="/cases/">Case Catalog</a></li>
      <li><a href="/faq/">FAQ</a></li>
      <li><a href="/about/">About</a></li>
      <li><a href="/cases/" class="btn btn-primary btn-sm">Get a Guide</a></li>
    </ul>
  </div>
</nav>
"""


def footer_html():
    year = datetime.now(timezone.utc).year
    return f"""
<footer class="footer">
  <div class="footer-inner">
    <div>
      <div class="footer-brand">Clinical Performance Lab</div>
      <p class="footer-tagline">Submission-ready iHuman case guides built from verified student submissions. Used by NR509, NR511, NR602, NURS 6512, NRNP 6541 students.</p>
      <p class="footer-tagline" style="margin-top:12px;">
        <a href="mailto:Tutorspot98@gmail.com">Tutorspot98@gmail.com</a>
      </p>
    </div>
    <div>
      <h4>Resources</h4>
      <ul>
        <li><a href="/free-resources/">Free Cheat Sheets</a></li>
        <li><a href="/cases/">Case Catalog</a></li>
        <li><a href="/faq/">FAQ</a></li>
      </ul>
    </div>
    <div>
      <h4>Company</h4>
      <ul>
        <li><a href="/about/">About CPL</a></li>
        <li><a href="mailto:Tutorspot98@gmail.com">Contact</a></li>
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
    <span>clinicalperformancelab.vercel.app</span>
  </div>
</footer>
"""


def popup_html():
    """Engagement-triggered popup (Phase 3 will wire the JS triggers)."""
    return """
<div class="popup-overlay" id="cplPopup" role="dialog" aria-modal="true" aria-labelledby="popupTitle">
  <div class="popup">
    <button class="popup-close" aria-label="Close" onclick="cplClosePopup()">×</button>
    <span class="resource-stage">Free · Take a minute</span>
    <h3 id="popupTitle">Cheat sheets for every case stage.</h3>
    <p>Four free PDFs — history, PE, DDx, plan/SOAP. Email-delivered. No spam.</p>
    <form class="popup-form" onsubmit="cplSubmitPopup(event)">
      <input type="email" name="email" placeholder="you@school.edu" required autocomplete="email">
      <button type="submit" class="btn btn-primary btn-lg">Get the cheat sheets →</button>
    </form>
    <p class="popup-fine">We'll send a confirmation link. Unsubscribe any time.</p>
  </div>
</div>
"""


# ─── Cheat sheet card (used on home + free-resources pages) ───────
def cheat_sheet_card_html(cs, selected=False):
    sel = " selected" if selected else ""
    return f"""
<label class="resource-card{sel}" data-id="{esc(cs['id'])}">
  <input type="checkbox" name="volumes" value="{esc(cs['id'])}" style="display:none" {'checked' if selected else ''}>
  <span class="resource-stage">Vol {esc(cs['vol'])} · Stage {esc(cs['vol'])} of IV</span>
  <h3>{esc(cs['title'])}</h3>
  <p>{volume_description(cs['id'])}</p>
  <div class="resource-meta">
    <span>{cs['pages']} pages</span>
    <span>·</span>
    <span>~10 min read</span>
  </div>
</label>
"""


def volume_description(vol_id):
    return {
        "history":       "Universal questions that score on every case. OLDCARTS, ROS, the pivotal communication question, and the lay-to-clinical translation table.",
        "physical-exam": "PE items that score on every case — cardiac auscultation, lung fields, abdominal quadrants. Diagrams for each.",
        "ddx":           "How iHuman ranks differentials, the must-not-miss framework, and the 2–3 sentence problem statement structure faculty look for.",
        "plan":          "The harmful-flag trap, 6-part management plan, medication answers by case template, SOAP note. The faculty-scored 20%.",
    }.get(vol_id, "")


def case_card_html(case):
    """Render a case card with data attributes the filter JS reads."""
    href = f"/case/{case['slug']}/"
    course = esc(case.get("course", ""))
    school = esc(case.get("school", ""))
    lead_time = case.get("lead_time", "same-day")

    # Filter data attributes (lowercase, no spaces, comma-separated for multi-value)
    tag_slugs = ",".join(t.lower().replace(" ", "-") for t in case.get("tags", []))
    school_slug = school.lower().replace(" ", "-").replace("university", "u").strip("-")
    # Course code extraction (e.g. "NR 509 / NR 511 Week 5" → "nr-509,nr-511")
    course_codes = []
    import re as _re
    for m in _re.findall(r'(NR|NRNP|NURS)\s*(\d+)', case.get("course", "")):
        course_codes.append(f"{m[0].lower()}-{m[1]}")
    course_slug = ",".join(course_codes)

    # Searchable string for the JS search box
    search_blob = " ".join([
        case.get("title", ""), case.get("chief_complaint", ""), case.get("diagnosis", ""),
        case.get("course", ""), case.get("school", ""),
        " ".join(case.get("tags", [])),
        " ".join(case.get("aliases", [])),
    ]).lower()

    # Tag chips
    tag_chips = "".join(f'<span class="case-tag">{esc(t)}</span>' for t in case.get("tags", []))

    # Lead-time chip
    if lead_time == "same-day":
        lead_chip = '<span class="case-tag lead-fast">⚡ Same-day</span>'
    elif lead_time == "fast-build":
        lead_chip = '<span class="case-tag lead-build">⌛ 24–48h</span>'
    else:
        lead_chip = '<span class="case-tag lead-request">📋 On request</span>'

    return f"""
<a class="case-card" href="{href}"
   data-slug="{esc(case['slug'])}"
   data-tags="{esc(tag_slugs)}"
   data-school="{esc(school_slug)}"
   data-courses="{esc(course_slug)}"
   data-lead-time="{esc(lead_time)}"
   data-search="{esc(search_blob)}">
  <h3>{esc(case['title'])}</h3>
  <p class="case-cc">{esc(case['chief_complaint'])}</p>
  <div class="case-meta">{tag_chips}{lead_chip}</div>
  <p class="muted" style="font-size:0.85rem; margin:8px 0 0;">{course}</p>
  <div class="case-cta">
    <span>Preview case →</span>
    <span aria-hidden="true">→</span>
  </div>
</a>
"""


# ─── PAGE: Home ───────────────────────────────────────────────────
def build_home():
    cheat_cards = "".join(cheat_sheet_card_html(cs) for cs in CHEAT_SHEETS)
    # Homepage shows only same-day cases — the 9 with complete verified guides
    featured = by_lead_time("same-day")
    case_cards = "".join(case_card_html(c) for c in featured)

    pricing_html = ""
    for k, p in PRICING.items():
        featured_class = " featured" if k == "bundle3" else ""
        saves = f"Save ${p['saves']}" if p['saves'] else "&nbsp;"
        pricing_html += f"""
<div class="tier{featured_class}">
  <div class="tier-label">{esc(p['label'])}</div>
  <div class="tier-price"><span class="currency">$</span>{p['price']}</div>
  <div class="tier-saves">{saves}</div>
  <p class="tier-blurb">{esc(p['blurb'])}</p>
  <a href="/cases/" class="btn btn-primary">Browse cases</a>
</div>
"""

    body = f"""
<section class="hero">
  <div class="container">
    <span class="hero-eyebrow" data-reveal><span class="dot"></span>iHuman case mastery</span>
    <h1 data-reveal data-reveal-delay="80">Walk into your case with <span class="accent">the answer key.</span></h1>
    <p class="hero-sub" data-reveal data-reveal-delay="160">
      Submission-ready iHuman case guides built from verified student submissions across NR509, NR511, NR602, NURS 6512, and NRNP 6541. Every section walked through. Every scoring trap mapped. Word + PDF, delivered same day.
    </p>
    <div class="hero-ctas" data-reveal data-reveal-delay="240">
      <a href="/cases/" class="btn btn-primary btn-lg">Browse case catalog</a>
      <a href="#free-resources" class="btn btn-ghost btn-lg">Get free cheat sheets</a>
    </div>
    <div class="hero-trust" data-reveal data-reveal-delay="320">
      <span><strong data-counter="200" data-counter-suffix="+">0</strong> verified student submissions</span>
      <span><strong data-counter="38">0</strong> cases in catalog</span>
      <span><strong>Same-day</strong> delivery</span>
    </div>
  </div>
</section>

<section class="section" id="free-resources" style="background:var(--cream-2);">
  <div class="container">
    <div class="section-title-block">
      <span class="eyebrow">Start free</span>
      <h2>The CPL Cheat Sheet Library</h2>
      <p>Four free PDFs covering the universal patterns that score on every iHuman case. Pick which to download.</p>
    </div>

    <form id="leadMagnetForm" data-form="leadmagnet">
      <div class="resource-grid">
        {cheat_cards}
      </div>

      <div class="capture inline mt-4">
        <div class="capture-eyebrow">Email-delivered</div>
        <h3>Where should we send your selections?</h3>
        <p>Pick at least one cheat sheet above. We'll confirm via email and send the PDFs.</p>
        <div class="capture-row">
          <input type="email" name="email" placeholder="you@school.edu" required autocomplete="email">
          <button type="submit" class="btn btn-lime btn-lg">Send the PDFs →</button>
        </div>
        <p class="capture-fine">No spam. Unsubscribe any time. We use email only to deliver requested resources and a short clinical-insight follow-up.</p>
      </div>
    </form>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-title-block">
      <span class="eyebrow">Case Catalog</span>
      <h2>Ready-to-submit case guides</h2>
      <p>Each guide is the full answer key for one iHuman case — every history question, every PE finding, every test, every EHR phrase, every management decision.</p>
    </div>
    <div class="case-grid">
      {case_cards}
    </div>
    <div class="text-center mt-4">
      <a href="/cases/" class="btn btn-ghost">See all {len(CASES)} cases →</a>
    </div>
  </div>
</section>

<section class="section" style="background:var(--cream-2);">
  <div class="container">
    <div class="section-title-block">
      <span class="eyebrow">Pricing</span>
      <h2>Pick a single case or a bundle.</h2>
      <p>Bundles are mix-and-match. Use code <strong>CPLFIRST15</strong> for 15% off your first single case.</p>
    </div>
    <div class="pricing-grid">
      {pricing_html}
    </div>
  </div>
</section>
"""

    write_page("", body,
               title=None,
               description="iHuman case guides built from verified student submissions. Walk into your case with the answer key.",
               page_class="home")


# ─── PAGE: Free Resources (dedicated lead magnet hub) ─────────────
def build_free_resources():
    cheat_cards = "".join(cheat_sheet_card_html(cs) for cs in CHEAT_SHEETS)

    body = f"""
<section class="hero">
  <div class="container">
    <span class="hero-eyebrow"><span class="dot"></span>Free Resource</span>
    <h1>The CPL Cheat Sheet Library</h1>
    <p class="hero-sub">
      Four free PDFs — one per iHuman case stage. The universal patterns that score on every case, no matter what the chief complaint is. Premium typography. Verified content. Email-delivered.
    </p>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-title-block">
      <span class="eyebrow">Pick your sheets</span>
      <h2>Which ones do you need?</h2>
      <p>Pick one, two, or all four. We'll send a confirmation link, then deliver your PDFs immediately.</p>
    </div>

    <form id="leadMagnetForm" data-form="leadmagnet">
      <div class="resource-grid">
        {cheat_cards}
      </div>

      <div class="capture mt-4">
        <div class="capture-eyebrow">Email-delivered · No spam</div>
        <h3>Where should we send them?</h3>
        <p>You'll get a confirmation link in under a minute. Click it and your PDFs are in your inbox.</p>
        <div class="capture-row">
          <input type="email" name="email" placeholder="you@school.edu" required autocomplete="email">
          <button type="submit" class="btn btn-lime btn-lg">Send the PDFs →</button>
        </div>
        <p class="capture-fine">We use email only to deliver requested resources and a short clinical-insight follow-up. Unsubscribe any time. Powered by Resend.</p>
      </div>
    </form>
  </div>
</section>

<section class="section" style="background:var(--cream-2);">
  <div class="container">
    <div class="section-title-block">
      <span class="eyebrow">After the cheat sheets</span>
      <h2>When you need the full answer key.</h2>
      <p>The cheat sheets cover universal patterns. For your <em>specific case</em> — verbatim history questions, exact PE findings, the platform's preferred diagnosis names, complete management plans — that's what the CPL case guides are for.</p>
    </div>
    <div class="text-center">
      <a href="/cases/" class="btn btn-primary btn-lg">Browse the case catalog →</a>
    </div>
  </div>
</section>
"""

    write_page("free-resources", body,
               title="Free Cheat Sheets",
               description="Four free PDFs covering the universal patterns that score on every iHuman case. Email-delivered.",
               page_class="free-resources")


# ─── PAGE: Cases catalog ──────────────────────────────────────────
def build_catalog():
    # Build a structured catalog data blob the JS can use for bundle pricing
    all_cases = CASES
    all_cards = "".join(case_card_html(c) for c in all_cases)

    # Collect unique filter options from data
    schools = sorted({c.get("school", "") for c in all_cases if c.get("school")})
    tags = sorted({t for c in all_cases for t in c.get("tags", [])})
    courses = sorted({c.get("course", "").split(" Week")[0].strip() for c in all_cases if c.get("course")})

    school_filters = "".join(
        f'<button class="filter-chip" data-filter="school" data-value="{esc(s.lower().replace(" ", "-").replace("university", "u").strip("-"))}">{esc(s)}</button>'
        for s in schools
    )
    tag_filters = "".join(
        f'<button class="filter-chip" data-filter="tag" data-value="{esc(t.lower().replace(" ", "-"))}">{esc(t)}</button>'
        for t in tags
    )

    # Compact case data blob for bundle builder (just slug + title + price)
    import json as _json
    bundle_data = _json.dumps([
        {"slug": c["slug"], "title": c["title"], "tags": c.get("tags", []), "lead_time": c.get("lead_time", "same-day")}
        for c in all_cases
    ])

    body = f"""
<section class="hero">
  <div class="container">
    <span class="hero-eyebrow"><span class="dot"></span>Case Catalog</span>
    <h1><span data-counter="{len(all_cases)}" data-counter-suffix=" cases">0 cases</span>. <span class="accent">All orderable today.</span></h1>
    <p class="hero-sub">
      9 complete guides deliver same-day. 9 more build within 24–48h. 20 available on request across NR509, NR511, NR602, NURS 6512, NRNP 6531, 6541, 6542, 6552, and 6568. Use code <strong>CPLFIRST15</strong> for 15% off your first.
    </p>
    <div class="hero-ctas">
      <button class="btn btn-primary btn-lg" onclick="document.getElementById('catalog-grid').scrollIntoView({{behavior:'smooth'}})">Browse cases ↓</button>
      <button class="btn btn-ghost btn-lg" onclick="document.getElementById('bundle-builder').scrollIntoView({{behavior:'smooth'}})">Build a bundle →</button>
    </div>
    <div class="hero-trust" style="margin-top:28px;">
      <span><strong>9</strong> same-day guides</span>
      <span><strong>9</strong> fast-build (24–48h)</span>
      <span><strong>20</strong> on-request (48–72h)</span>
      <span><strong>9</strong> courses covered</span>
    </div>
  </div>
</section>

<section class="section catalog-section" id="catalog-grid">
  <div class="container">

    <!-- Toolbar: search + active filter readout -->
    <div class="catalog-toolbar">
      <div class="catalog-search">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input type="text" id="catalogSearch" placeholder="Search by name, course, diagnosis…" autocomplete="off">
        <button class="catalog-search-clear" id="catalogSearchClear" aria-label="Clear search" style="display:none;">×</button>
      </div>
      <div class="catalog-result-count" id="catalogResultCount" aria-live="polite">
        Showing all {len(all_cases)} cases
      </div>
    </div>

    <!-- Filter rail -->
    <div class="catalog-filters">
      <div class="filter-group">
        <span class="filter-label">School</span>
        {school_filters}
      </div>
      <div class="filter-group">
        <span class="filter-label">System</span>
        {tag_filters}
      </div>
      <div class="filter-group">
        <span class="filter-label">Lead time</span>
        <button class="filter-chip" data-filter="lead-time" data-value="same-day">⚡ Same-day</button>
        <button class="filter-chip" data-filter="lead-time" data-value="fast-build">⌛ 24–48h</button>
        <button class="filter-chip" data-filter="lead-time" data-value="on-request">📋 On request</button>
      </div>
      <button class="filter-clear" id="filterClear" style="display:none;">Clear filters ×</button>
    </div>

    <!-- Unified case grid -->
    <div class="case-grid" id="caseGrid">
      {all_cards}
    </div>

    <!-- Empty state -->
    <div class="catalog-empty" id="catalogEmpty" style="display:none;">
      <p>No cases match those filters.</p>
      <button class="btn btn-ghost" onclick="window.cpl.catalog.clearAll()">Show all cases</button>
    </div>
  </div>
</section>

<!-- Bundle builder section -->
<section class="section" id="bundle-builder" style="background:var(--cream-2);">
  <div class="container">
    <div class="section-title-block">
      <span class="eyebrow">Bundle Builder</span>
      <h2>Pick your cases. <span style="color:var(--teal-700); font-style:italic;">Save more.</span></h2>
      <p>Pick 1, 3, or 5 cases. Price updates live. Mix any cases — single price for any combination.</p>
    </div>

    <div class="bundle-builder" data-cases='{esc(bundle_data)}'>
      <div class="bundle-pool">
        <h3 class="bundle-section-title">Available cases <span class="muted" style="font-weight:400; font-size:0.85rem;">— click to add</span></h3>
        <div class="bundle-pool-grid" id="bundlePool"></div>
      </div>

      <div class="bundle-summary">
        <div class="bundle-cart" id="bundleCart">
          <h3 class="bundle-section-title">Your bundle</h3>
          <div class="bundle-cart-items" id="bundleCartItems">
            <p class="muted" style="text-align:center; padding:32px 0;">No cases selected yet.<br>Click a case on the left to add it.</p>
          </div>

          <div class="bundle-pricing" id="bundlePricing" style="display:none;">
            <div class="bundle-tier-row" id="bundleTierRow">
              <span class="bundle-tier-label" id="bundleTierLabel">—</span>
              <span class="bundle-tier-saves" id="bundleTierSaves"></span>
            </div>
            <div class="bundle-price-row">
              <div>
                <span class="bundle-price-original" id="bundlePriceOriginal"></span>
                <span class="bundle-price-final" id="bundlePriceFinal">$0</span>
              </div>
              <div class="bundle-price-savings" id="bundlePriceSavings"></div>
            </div>
            <button class="btn btn-primary btn-lg" id="bundleOrder" style="width:100%;">Order this bundle →</button>
            <p class="muted bundle-disclaimer">We'll confirm via email or WhatsApp before charging. Use code <strong>CPLFIRST15</strong> for 15% off if this is your first single case.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
"""

    write_page("cases", body,
               title="Case Catalog",
               description="Browse 16 iHuman case guides. Same-day delivery on most cases. Built from verified student submissions.",
               page_class="catalog")


# ─── PAGE: Individual case preview ────────────────────────────────
def get_preview_data(slug):
    """
    Read the preview meta.json for a case and return a normalized dict, or
    None if no preview exists.

    Real previews (is_sample=False) carry clear_pages (one per section),
    section_labels, and stack_blurred (3 teaser pages for the locked stack).

    Sample previews (is_sample=True) carry sample_source + source_title and
    are rendered from watermarked source pages in /previews/_watermarked/.
    """
    import json as _json
    preview_dir = os.path.join(PUBLIC, 'previews', slug)
    meta_path = os.path.join(preview_dir, 'meta.json')
    if not os.path.isfile(meta_path):
        return None
    try:
        with open(meta_path, encoding='utf-8') as f:
            meta = _json.load(f)
    except Exception:
        return None

    is_sample = meta.get('is_sample', True)
    total_pages = meta.get('total_pages', 24)

    if not is_sample:
        clear_pages = meta.get('clear_pages', [1])
        return {
            'slug': slug,
            'is_sample': False,
            'total_pages': total_pages,
            'clear_pages': clear_pages,
            'stack_blurred': meta.get('stack_blurred', []),
            'section_labels': meta.get('section_labels', {}),
            'clear_count': len(clear_pages),
            'locked_count': max(total_pages - len(clear_pages), 0),
        }

    return {
        'slug': slug,
        'is_sample': True,
        'total_pages': total_pages,
        'sample_source': meta.get('sample_source'),
        'source_title': meta.get('source_title', 'a completed CPL case'),
        'sample_label': meta.get('sample_label', ''),
    }


def _render_preview_section(case, preview):
    """Render the PDF preview block. Two tracks: real (section pages + locked
    stack) and sample (watermarked format excerpts + honest warning + CTA)."""
    if not preview:
        return ''

    slug = case['slug']
    total = preview['total_pages']
    order_subject = esc(f"CPL Order - {case['title']}").replace(' ', '%20')
    title = esc(case['title'])

    # Counts for the value copy (fall back to generic phrasing)
    q_count = case.get('preview_hpi_count')
    pe_count = case.get('preview_pe_count')
    dx_count = case.get('preview_dx_count')
    if q_count and pe_count and dx_count:
        value_line = (f"{q_count} scored history questions, {pe_count} physical "
                      f"exam items, {dx_count} ranked differentials")
    else:
        value_line = ("the full history bank, scored PE checklist, ranked "
                      "differentials")

    # ── Real preview ───────────────────────────────────────────────
    if not preview['is_sample']:
        clear_pages = preview['clear_pages']
        labels = preview['section_labels']
        clear_count = preview['clear_count']
        locked_count = preview['locked_count']

        clear_html = ''
        for n in clear_pages:
            label = labels.get(str(n), f"Page {n}")
            clear_html += f'''
        <div class="pdf-page pdf-page-clear">
          <div class="pdf-page-num">Page {n} of {total} &mdash; {esc(label)}</div>
          <img src="/previews/{slug}/page_{n}.png"
               alt="{title} guide &mdash; {esc(label)}"
               loading="lazy" class="pdf-page-img">
        </div>'''

        stack_html = ''
        for i, n in enumerate(preview['stack_blurred']):
            stack_html += f'''
          <div class="pdf-page pdf-page-blurred" style="z-index:{10-i}">
            <div class="pdf-page-num">Page {n} of {total} &mdash; Locked</div>
            <img src="/previews/{slug}/page_{n}_blurred.png"
                 alt="Locked guide page" loading="lazy"
                 class="pdf-page-img blurred-img">
          </div>'''

        return f'''
<div class="pdf-preview-section" data-reveal>
  <div class="pdf-preview-label">
    <span class="pdf-real-badge">&#9889; Guide Preview</span>
    <span class="pdf-real-note">{clear_count} sample pages from your actual {title} guide &mdash; one from each section</span>
  </div>
  {clear_html}
  <div class="pdf-locked-stack">
    {stack_html}
    <div class="pdf-unlock-overlay">
      <div class="pdf-lock-icon">&#128274;</div>
      <div class="pdf-lock-title">{locked_count} more pages &mdash; locked</div>
      <div class="pdf-lock-sub">
        Full history bank ({value_line}), complete PE checklist, ranked DDx,
        EHR documentation, SOAP note, and management plan with APA references.
      </div>
      <a href="mailto:Tutorspot98@gmail.com?subject={order_subject}" class="btn btn-primary">
        Get the complete {title} guide &mdash; $150
      </a>
      <div class="pdf-lock-note">
        Word + PDF &middot; Same-day delivery &middot;
        Use code <strong>CPLFIRST15</strong> for 15% off your first
      </div>
    </div>
  </div>
</div>'''

    # ── Sample preview ─────────────────────────────────────────────
    source = preview['sample_source']
    source_title = esc(preview['source_title'])
    return f'''
<div class="pdf-preview-section is-sample" data-reveal>
  <div class="pdf-sample-warning">
    <div class="pdf-sample-warning-icon">&#9888;&#65039;</div>
    <div class="pdf-sample-warning-text">
      <strong>This isn't your case preview.</strong>
      We haven't built {title} yet &mdash; these images are stamped excerpts
      from one of our completed guides ({source_title}). They show our format.
      Your guide will be written specifically for {title} and follow this same structure.
    </div>
  </div>

  <div class="pdf-page pdf-page-sample">
    <div class="pdf-page-num">Example &mdash; Cover &amp; case overview format</div>
    <img src="/previews/_watermarked/{source}/sample_1.png"
         alt="Example cover format" loading="lazy" class="pdf-page-img">
  </div>

  <div class="pdf-page pdf-page-sample">
    <div class="pdf-page-num">Example &mdash; History section format</div>
    <img src="/previews/_watermarked/{source}/sample_2.png"
         alt="Example history section format" loading="lazy" class="pdf-page-img">
  </div>

  <div class="pdf-sample-cta">
    <div class="pdf-sample-cta-title">Order {title} and get your own complete guide</div>
    <div class="pdf-sample-cta-sub">
      Word + PDF, built specifically for {title}. {total}+ pages of
      patient-specific content covering {value_line}, EHR documentation,
      SOAP note, and management plan.
    </div>
    <a href="mailto:Tutorspot98@gmail.com?subject={order_subject}" class="btn btn-primary">
      Order this guide &mdash; $150
    </a>
    <div class="pdf-sample-cta-note">
      Use code <strong>CPLFIRST15</strong> for 15% off your first single case.
    </div>
  </div>
</div>'''


def build_case_preview(case):
    traps_html = "".join(
        f'<div class="trap-callout" data-reveal data-reveal-delay="{i*80}"><div class="trap-callout-title">⚠ Scoring Trap</div><div>{esc(t)}</div></div>'
        for i, t in enumerate(case.get("key_scoring_traps", []))
    )

    lead_time = case.get("lead_time", "same-day")
    if lead_time == "same-day":
        cta_label = "Get this case guide"
        cta_blurb = "Word + PDF, delivered same day to your inbox."
        lead_badge = '<span class="lead-badge lead-badge-fast">⚡ Same-day delivery</span>'
    else:
        cta_label = "Order this case guide"
        cta_blurb = "Word + PDF, built and delivered within 24–48 hours."
        lead_badge = '<span class="lead-badge lead-badge-build">⌛ 24–48h build</span>'

    counts = ""
    if case.get("preview_hpi_count"):
        counts = f"""
<ul>
  <li><strong>{case['preview_hpi_count']}</strong> history questions with verbatim patient responses</li>
  <li><strong>{case['preview_pe_count']}</strong> physical exam items with documentation language</li>
  <li><strong>{case['preview_dx_count']}</strong> ranked differential diagnoses (platform-verified names)</li>
  <li>Full EHR documentation (Subjective + Objective sections)</li>
  <li>Tests Ordered list with rationale for each</li>
  <li>Complete Management Plan in 6-part structure</li>
  <li>SOAP Note ready to submit</li>
  <li>APA-formatted scholarly references</li>
</ul>
"""
    else:
        counts = """
<ul>
  <li>Full history question bank with verbatim patient responses</li>
  <li>Physical exam checklist with documentation language</li>
  <li>Ranked differential diagnoses with platform-verified names</li>
  <li>Complete EHR + SOAP Note</li>
  <li>Tests Ordered list with rationale</li>
  <li>Management Plan with APA references</li>
</ul>
"""

    aliases_html = ""
    if case.get("aliases") and len(case["aliases"]) > 1:
        chips = "".join(f'<span class="case-tag">{esc(a)}</span>' for a in case["aliases"])
        aliases_html = f"""
<div class="preview-section">
  <h3>Same case, different patient name</h3>
  <p>iHuman rotates the patient name across course sections. This guide covers all aliases of this case template:</p>
  <div class="case-meta">{chips}</div>
  <p class="muted mt-2" style="font-size:0.88rem;">Tell us which alias you have at checkout — we customize the delivered guide to your exact patient.</p>
</div>
"""

    # ── PDF Preview Section ──────────────────────────────────────
    preview = get_preview_data(case['slug'])
    pdf_preview_html = _render_preview_section(case, preview)

    course_chip = f'<span class="case-tag">{esc(case.get("course",""))}</span>'
    school_chip = f'<span class="case-tag">{esc(case.get("school",""))}</span>'
    tag_chips = "".join(f'<span class="case-tag">{esc(t)}</span>' for t in case.get("tags", []))

    body = f"""
<section class="preview-hero">
  <div class="container">
    <div class="preview-eyebrow">Case Preview · {esc(case.get('course',''))} {lead_badge}</div>
    <h1 data-reveal>{esc(case['title'])}</h1>
    <p class="preview-cc" data-reveal data-reveal-delay="100">"{esc(case['chief_complaint'])}"</p>
    <div class="preview-meta" data-reveal data-reveal-delay="200">
      <span>Patient: <strong>{esc(case['patient_short'])}</strong></span>
      <span>Course: <strong>{esc(case.get('course','—'))}</strong></span>
      <span>School: <strong>{esc(case.get('school','—'))}</strong></span>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="preview-grid">
      <div>
        <div class="preview-section">
          <h3>Final diagnosis</h3>
          <p style="font-family:var(--font-display); font-size:1.3rem; color:var(--teal-800); margin:0;">
            {esc(case['diagnosis'])}
          </p>
        </div>

        <div class="preview-section">
          <h3>Must-not-miss</h3>
          <p>{esc(case.get('must_not_miss', '—'))}</p>
        </div>

        <div class="preview-section">
          <h3>What's in the guide</h3>
          {counts}
        </div>

        {pdf_preview_html}

        <div class="preview-section">
          <h3>Scoring traps this case</h3>
          <p>The point-loss patterns we map for you:</p>
          {traps_html}
        </div>

        {aliases_html}
      </div>

      <aside>
        <div class="preview-side-cta">
          <span class="resource-stage">{esc(case.get('course','iHuman Case'))}</span>
          <h4>{esc(cta_label)}</h4>
          <div class="side-price">$150</div>
          <p class="muted" style="font-size:0.88rem;">{esc(cta_blurb)}</p>
          <a href="mailto:Tutorspot98@gmail.com?subject=CPL%20Order%20-%20{esc(case['title'])}" class="btn btn-primary" style="width:100%; margin-top:8px;">Order via email</a>
          <a href="https://wa.me/" class="btn btn-ghost" style="width:100%; margin-top:8px;">WhatsApp DM</a>
          <p class="muted mt-3" style="font-size:0.78rem; text-align:center;">Use code <strong>CPLFIRST15</strong> for 15% off your first single case.</p>
        </div>

        <div class="capture inline" style="margin-top:20px;">
          <div class="capture-eyebrow">First time here?</div>
          <h3 style="font-size:1.1rem;">Get the free cheat sheets first.</h3>
          <p>Four PDFs that work across every iHuman case. Email-delivered.</p>
          <form data-form="leadmagnet">
            <input type="hidden" name="volumes" value="history,physical-exam,ddx,plan">
            <div class="capture-row" style="margin-top:8px;">
              <input type="email" name="email" placeholder="you@school.edu" required autocomplete="email">
            </div>
            <button type="submit" class="btn btn-lime" style="width:100%; margin-top:8px;">Get all 4 cheat sheets →</button>
          </form>
        </div>

        <!-- Recently viewed cases (rendered dynamically by cpl.js) -->
        <div class="recent-cases-block" data-render="recent-cases" style="display:none;">
          <div class="recent-label">Recently viewed</div>
          <div data-recent-list></div>
        </div>
      </aside>
    </div>
  </div>
</section>
"""

    write_page(f"case/{case['slug']}", body,
               title=case['title'],
               description=f"{case['title']} — {case['chief_complaint']}. iHuman case guide for {case.get('course','')}. Built from verified student submissions.",
               page_class="case-preview")


# ─── PAGE: Confirm (double opt-in landing) ────────────────────────
def build_confirm():
    body = """
<section class="hero">
  <div class="container container-narrow text-center">
    <span class="hero-eyebrow"><span class="dot"></span>Almost there</span>
    <h1 id="confirmTitle">Confirming your email…</h1>
    <p class="hero-sub" id="confirmSub">
      Validating your confirmation link. This takes a few seconds.
    </p>
    <div id="confirmResult"></div>
  </div>
</section>

<script>
(async function() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get('t');
  const titleEl = document.getElementById('confirmTitle');
  const subEl = document.getElementById('confirmSub');
  const resultEl = document.getElementById('confirmResult');

  if (!token) {
    titleEl.textContent = "Missing confirmation token";
    subEl.textContent = "This link is incomplete. If you got it via email, try clicking it directly rather than copy-pasting.";
    return;
  }

  try {
    const res = await fetch('/api/confirm?t=' + encodeURIComponent(token));
    const data = await res.json();
    if (res.ok && data.ok) {
      titleEl.textContent = "Your PDFs are on the way!";
      subEl.textContent = "Check your inbox in a minute. We've also scheduled a short follow-up over the next week with a clinical insight you can use.";
      resultEl.innerHTML = '<div class="form-success">Email confirmed: ' + data.email + '. Volumes: ' + (data.volumes || []).join(', ') + '</div><div style="margin-top:24px;"><a href="/cases/" class="btn btn-primary btn-lg">Browse case catalog →</a></div>';
    } else {
      titleEl.textContent = "Couldn't confirm";
      subEl.textContent = data.error || "This link is invalid or expired. Try requesting a new one from the free resources page.";
      resultEl.innerHTML = '<a href="/free-resources/" class="btn btn-primary">Get a new link</a>';
    }
  } catch (e) {
    titleEl.textContent = "Something went wrong";
    subEl.textContent = "We couldn't reach the confirmation service. Try again in a minute or email Tutorspot98@gmail.com.";
  }
})();
</script>
"""
    write_page("confirm", body,
               title="Confirm your email",
               description="Confirm your email and get your CPL cheat sheets.",
               page_class="confirm")


# ─── PAGE: Thank you (post-form-submission) ───────────────────────
def build_thankyou():
    body = """
<section class="hero">
  <div class="container container-narrow text-center">
    <span class="hero-eyebrow"><span class="dot"></span>Check your inbox</span>
    <h1>One quick step.</h1>
    <p class="hero-sub">
      We've sent a confirmation link to your email. Click it (in the next 24 hours) and your PDFs land in your inbox immediately.
    </p>
    <p class="muted">
      Don't see it? Check the spam folder. The sender is <strong>onboarding@resend.dev</strong>.
    </p>
    <div class="mt-4">
      <a href="/cases/" class="btn btn-primary btn-lg">Browse cases while you wait →</a>
    </div>
  </div>
</section>
"""
    write_page("thank-you", body,
               title="Check your inbox",
               description="Confirmation link sent. Click it to get your CPL cheat sheets.",
               page_class="thank-you")


# ─── PAGE: About ──────────────────────────────────────────────────
def build_about():
    body = """
<section class="hero">
  <div class="container container-narrow">
    <span class="hero-eyebrow"><span class="dot"></span>About</span>
    <h1>Built by clinicians. <span class="accent">Verified by students.</span></h1>
    <p class="hero-sub">
      CPL exists for one reason: nursing students deserve clinical reasoning resources that match the way iHuman actually scores them. Every guide is reverse-engineered from real student submissions, real platform feedback, real faculty markups.
    </p>
  </div>
</section>

<section class="section">
  <div class="container container-narrow">
    <h2>What CPL is.</h2>
    <p>Clinical Performance Lab makes submission-ready iHuman case guides for nursing students. Each guide walks through every section a student must complete — history, physical exam, key findings, differential, tests, EHR documentation, management plan, SOAP note — and maps the specific scoring patterns that iHuman and faculty look for.</p>

    <h2 class="mt-4">What CPL is not.</h2>
    <p>CPL is not a clinical reference. The medication dosing and management content in our guides reflects what the iHuman platform expects on those specific case templates. <strong>Verify all dosing with current Epocrates or UpToDate before any clinical application.</strong> We're explicit about this on every page that mentions a medication.</p>
    <p>CPL is also not affiliated with iHuman, Kaplan, Chamberlain University, Walden University, or any other institution. We're an independent educational resource.</p>

    <h2 class="mt-4">How a guide is built.</h2>
    <p>Each guide starts with an intake — patient name, school, course, and any screenshots the student has of their case so far. From there:</p>
    <ol>
      <li>We search verified student-submitted research across Docsity, Studocu, CourseHero, NursingHero, and several other platforms.</li>
      <li>We cross-reference against iHuman performance reports (especially 100% submissions) to confirm scored item counts.</li>
      <li>We layer in our own clinical knowledge base (200+ submissions across NR509, NR511, NR602, NURS 6512, NRNP 6541).</li>
      <li>We build the guide in Word and convert to PDF, then validate via a pre-delivery checklist of 12 items.</li>
      <li>We follow up post-delivery to log any platform discrepancies and refine the next iteration.</li>
    </ol>

    <h2 class="mt-4">The team.</h2>
    <p>CPL is run by Nurb, an educator and former tutor who built the first iHuman case guide in 2024 after watching too many students lose points to the same handful of patterns.</p>
    <p>Contact: <a href="mailto:Tutorspot98@gmail.com">Tutorspot98@gmail.com</a></p>
  </div>
</section>
"""
    write_page("about", body,
               title="About",
               description="About Clinical Performance Lab — built by clinicians, verified by students.",
               page_class="about")


# ─── PAGE: FAQ ────────────────────────────────────────────────────
def build_faq():
    faqs = [
        ("How fast is delivery?", "Same day, usually within 4 hours of payment confirmation. WhatsApp orders typically deliver fastest because we can clarify intake details in real time."),
        ("What format do I get?", "Both Word (.docx) and PDF — same content. The Word version is editable, the PDF is print-ready. We email both as attachments."),
        ("My patient name is different from your catalog listing. Is the guide still relevant?", "Yes. iHuman rotates the patient name across course sections, but the case template (questions, findings, scoring) stays the same. We alias-customize the delivered guide to your exact patient name."),
        ("Will the iHuman platform show exactly what's in the guide?", "Very close, but iHuman occasionally updates question phrasing or scored items. We follow up after delivery to log any discrepancies and update the guide for future students. If you spot a mismatch, send us a screenshot and we'll send you a corrected version."),
        ("Is this 'cheating'?", "No. Our guides function the way any study guide does — they walk you through what the assessment is looking for so you can practice it. You still complete the case yourself in iHuman. Many programs explicitly recommend external study resources alongside iHuman."),
        ("How does the 15% discount work?", "Use code CPLFIRST15 at checkout for 15% off your first single case guide. One-time only. Bundle pricing is already discounted, so the code applies only to single cases."),
        ("Can I get a refund?", "If you receive the wrong case or there's a substantive error we can't quickly correct, yes. We'll work with you to fix it first — most issues are correctable within a day."),
        ("Will you build a guide for my exact case?", "If it's in the catalog, yes — same-day. If it's not yet built, we can usually deliver within 24–48 hours after intake, depending on complexity. Get in touch via WhatsApp or email."),
        ("What happens with my email address?", "We use it only to deliver requested PDFs and a short clinical insight follow-up (4 emails over 7 days). You can unsubscribe at any time. We do not sell, rent, or share email addresses."),
        ("Is the cheat sheet medication content safe to use in clinical practice?", "No — and we say so explicitly on the dosing reference page. Those doses reflect what iHuman expects on specific case templates. Verify all dosing with Epocrates or UpToDate before any clinical application."),
    ]
    faq_html = "".join(
        f"""<details class="faq-item"><summary>{esc(q)}</summary><div class="faq-item-body">{esc(a)}</div></details>"""
        for q, a in faqs
    )

    body = f"""
<section class="hero">
  <div class="container container-narrow">
    <span class="hero-eyebrow"><span class="dot"></span>FAQ</span>
    <h1>Common questions, <span class="accent">honest answers.</span></h1>
    <p class="hero-sub">If you don't see your question here, email <a href="mailto:Tutorspot98@gmail.com">Tutorspot98@gmail.com</a>.</p>
  </div>
</section>

<section class="section">
  <div class="container container-narrow">
    <div class="faq-list">
      {faq_html}
    </div>
  </div>
</section>
"""
    write_page("faq", body,
               title="FAQ",
               description="Frequently asked questions about CPL case guides, pricing, delivery, and refunds.",
               page_class="faq")


# ─── PAGE: Terms + Privacy (lightweight legal) ────────────────────
def build_legal():
    terms_body = """
<section class="section">
  <div class="container container-narrow">
    <h1>Terms of Use</h1>
    <p class="muted">Last updated: May 2026</p>
    <h3>1. Educational use only</h3>
    <p>CPL materials are sold for personal study and academic preparation use. They are not clinical references. Medication dosing and management content reflect what specific iHuman case templates expect — not what should be prescribed in real clinical practice.</p>
    <h3>2. No clinical authority</h3>
    <p>CPL is not a medical authority. Verify all dosing, indications, and clinical decisions with current authoritative sources (Epocrates, UpToDate, IDSA/ACC/AHA guidelines) before any clinical application.</p>
    <h3>3. Independent of institutions</h3>
    <p>CPL is not affiliated with iHuman, Kaplan, Chamberlain University, Walden University, or any other institution. We are an independent educational resource.</p>
    <h3>4. Refund policy</h3>
    <p>Refunds available within 7 days of purchase for the wrong case delivered or substantive uncorrectable error. Contact Tutorspot98@gmail.com.</p>
    <h3>5. Email use</h3>
    <p>We use your email address solely to deliver requested resources and a short clinical-insight follow-up sequence. We do not sell, rent, or share email addresses. Unsubscribe at any time via the link in every email.</p>
  </div>
</section>
"""
    privacy_body = """
<section class="section">
  <div class="container container-narrow">
    <h1>Privacy</h1>
    <p class="muted">Last updated: May 2026</p>
    <h3>What we collect</h3>
    <p>When you submit the free-resources form, we collect your email address and the IDs of the cheat sheets you selected. Nothing else.</p>
    <h3>What we do with it</h3>
    <p>We send a confirmation email immediately. After confirmation, we deliver the PDFs and schedule a four-email follow-up sequence over 7 days. After that, we send nothing further unless you reply or request more.</p>
    <h3>Where it's stored</h3>
    <p>Email addresses and the drip schedule are stored in Vercel KV (a Redis-backed service). The email sending platform is Resend.</p>
    <h3>What we don't do</h3>
    <p>We do not sell, rent, or share your email. We do not embed analytics tracking pixels in delivery emails. We do not use email to target advertising.</p>
    <h3>How to delete your data</h3>
    <p>Email Tutorspot98@gmail.com with the subject "Delete my data" and we'll remove your address from our records within 7 days.</p>
  </div>
</section>
"""
    write_page("terms", terms_body, title="Terms of Use", page_class="legal")
    write_page("privacy", privacy_body, title="Privacy", page_class="legal")


# ─── Sitemap + robots ─────────────────────────────────────────────
def build_sitemap():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = ["", "free-resources", "cases", "faq", "about", "terms", "privacy"]
    urls += [f"case/{c['slug']}" for c in CASES]

    entries = "\n".join(
        f"""  <url>
    <loc>{BASE_URL}/{u + '/' if u else ''}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{'weekly' if u in ['', 'cases'] else 'monthly'}</changefreq>
  </url>""" for u in urls
    )

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>
"""
    with open(os.path.join(PUBLIC, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)

    robots = f"""User-agent: *
Allow: /
Disallow: /api/
Disallow: /confirm/
Disallow: /cheat-sheets/

Sitemap: {BASE_URL}/sitemap.xml
"""
    with open(os.path.join(PUBLIC, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)


# ─── Favicon (simple SVG) ─────────────────────────────────────────
def build_favicon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="32" fill="#0B1F1B"/>
  <circle cx="32" cy="32" r="22" fill="#B7E04E"/>
  <text x="32" y="40" text-anchor="middle" font-family="Inter, sans-serif" font-size="22" font-weight="700" fill="#0B1F1B">CPL</text>
</svg>
"""
    with open(os.path.join(PUBLIC, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(svg)


# ─── Front-end JS ────────────────────────────────────────────────
def build_js():
    """Copy the source JS from src/cpl.js to public/cpl.js."""
    src_path = os.path.join(ROOT, "src", "cpl.js")
    dst_path = os.path.join(PUBLIC, "cpl.js")
    with open(src_path, "r", encoding="utf-8") as fr:
        content = fr.read()
    with open(dst_path, "w", encoding="utf-8") as fw:
        fw.write(content)

# ─── Orchestrator ────────────────────────────────────────────────
def build_all():
    print(f"Building CPL static site → {PUBLIC}/")
    build_home()
    print("  ✓ index.html")
    build_free_resources()
    print("  ✓ free-resources/")
    build_catalog()
    print("  ✓ cases/")
    for c in CASES:
        build_case_preview(c)
    print(f"  ✓ case/* ({len(CASES)} pages)")
    build_confirm()
    print("  ✓ confirm/")
    build_thankyou()
    print("  ✓ thank-you/")
    build_about()
    print("  ✓ about/")
    build_faq()
    print("  ✓ faq/")
    build_legal()
    print("  ✓ terms/ + privacy/")
    build_sitemap()
    print("  ✓ sitemap.xml + robots.txt")
    build_favicon()
    print("  ✓ favicon.svg")
    build_js()
    print("  ✓ cpl.js")

    # Now build cheat sheets via the existing module
    print("\nRebuilding cheat sheet PDFs...")
    import subprocess
    res = subprocess.run(
        ["python3", os.path.join(ROOT, "generate_cheat_sheets.py")],
        capture_output=True, text=True
    )
    print(res.stdout)
    if res.returncode != 0:
        print(f"  ⚠ Cheat sheet build failed:\n{res.stderr}")

    print(f"\n✓ Site built in {PUBLIC}/")


if __name__ == "__main__":
    build_all()
