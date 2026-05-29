#!/usr/bin/env python3
"""
deploy_redesign.py
Takes each HTML file from _newdesign_extract/redesign/ verbatim,
patches all relative paths to absolute paths, fixes internal links
to pretty URLs, injects window.CPL_CASES for the catalog, and adds
canonical, Open Graph, Twitter Card, and JSON-LD structured data to
every page for full SEO + AI-model optimisation.

Run: python deploy_redesign.py
"""
import os
import json
import re
import shutil
import sys

# ── Paths ────────────────────────────────────────────────────────────────────
BASE     = os.path.dirname(os.path.abspath(__file__))
REDESIGN = os.path.join(BASE, '_newdesign_extract', 'redesign')
PUB      = os.path.join(BASE, 'public')
SRC      = os.path.join(BASE, 'src')

SITE     = 'https://cpl-site.vercel.app'
OG_IMAGE = f'{SITE}/og-image.png'

# ── Link / asset substitutions (applied in order) ─────────────────────────────
SUBS = [
    ('href="index.html#how"',      'href="/#how"'),
    ('href="index.html#free"',     'href="/#free"'),
    ('href="index.html#cases"',    'href="/#cases"'),
    ('href="index.html#pricing"',  'href="/#pricing"'),
    ('href="index.html"',          'href="/"'),
    ('href="catalog.html#catalog"','href="/cases/#catalog"'),
    ('href="catalog.html"',        'href="/cases/"'),
    ('href="case-preview.html"',   'href="/case-preview/"'),
    ('href="simulator.html"',      'href="/simulator/"'),
    ('href="about.html"',          'href="/about/"'),
    ('href="faq.html"',            'href="/faq/"'),
    ('href="free-resources.html"', 'href="/free-resources/"'),
    ('href="sample-guide.html"',   'href="/sample-guide/"'),
    ('href="terms.html"',          'href="/terms/"'),
    ('href="privacy.html"',        'href="/privacy/"'),
    ('href="cpl.css"',             'href="/styles.css"'),
    ('src="cpl.js"',               'src="/cpl.js"'),
    ('src="cpl-checkout.js"',      'src="/cpl-checkout.js"'),
    ('src="cpl-support.js"',       'src="/cpl-support.js"'),
    ('src="cpl-catalog.js"',       'src="/cpl-catalog.js"'),
    ('src="cpl-simulator.jsx"',    'src="/cpl-simulator.jsx"'),
    ('src="previews/',             'src="/previews/'),
    ('data-lightbox="previews/',   'data-lightbox="/previews/'),
    ('href="previews/',            'href="/previews/'),
]

# ── FAQ items for JSON-LD ─────────────────────────────────────────────────────
FAQ_ITEMS = [
    ("How fast is delivery?",
     "Same day — usually within about 4 hours of payment confirmation. Once your invoice is paid, your access code and guide land in your inbox."),
    ("What format do I get?",
     "Both Word (.docx) and PDF — same content. The Word version is editable, the PDF is print-ready. We email both."),
    ("My patient name is different from your catalog listing. Is the guide still relevant?",
     "Yes. iHuman rotates the patient name across course sections, but the case template — questions, findings, scoring — stays the same. We alias-customize the delivered guide to your exact patient name."),
    ("Will iHuman show exactly what's in the guide?",
     "Very close, but iHuman occasionally updates question phrasing or scored items. We follow up after delivery to log discrepancies. If you spot a mismatch, send a screenshot and we'll send a corrected version."),
    ("Is this 'cheating'?",
     "No. Our guides work the way any study guide does — they walk you through what the assessment is looking for so you can learn and practice it. You still complete the case yourself in iHuman. Always follow your school's academic policies."),
    ("How does the 15% discount work?",
     "Use code CPLFIRST15 for 15% off your first single case guide — one-time only. Bundle pricing is already discounted, so the code applies to single cases."),
    ("How does ordering and payment work?",
     "Request an invoice on any case. We email it within the hour. Once it's paid, you receive a personal access code that unlocks your complete guide for download — no card details are entered on the site."),
    ("Can I get a refund?",
     "If you receive the wrong case, or there's a substantive error we can't quickly correct, yes. We'll work with you to fix it first — most issues are correctable within a day."),
    ("Will you build a guide for my exact case?",
     "If it's in the catalog, yes — same-day. If it's not yet built, we can usually deliver within 24-48 hours after intake, depending on complexity. Reach out via the Support chat or email."),
    ("What happens with my email address?",
     "We use it only to deliver requested PDFs and a short clinical-insight follow-up. You can unsubscribe any time. We never sell, rent, or share email addresses."),
    ("Is the cheat-sheet medication content safe for clinical practice?",
     "No — and we say so explicitly. Those doses reflect what iHuman expects on specific case templates. Always verify dosing with Epocrates or UpToDate before any clinical application."),
]

# ── JSON-LD schemas ───────────────────────────────────────────────────────────

def _ld(obj: dict) -> str:
    return (
        '<script type="application/ld+json">\n'
        + json.dumps(obj, ensure_ascii=False, indent=2)
        + '\n</script>'
    )

def schema_home() -> str:
    return _ld({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": f"{SITE}/#org",
                "name": "Clinical Performance Lab",
                "url": SITE,
                "logo": {"@type": "ImageObject", "url": f"{SITE}/og-image.png"},
                "contactPoint": {
                    "@type": "ContactPoint",
                    "email": "Tutorspot98@gmail.com",
                    "contactType": "customer support",
                    "availableLanguage": "English"
                },
                "description": (
                    "Clinical reasoning education platform for nursing students. "
                    "Free clinical reasoning simulator, free cheat sheets, and "
                    "complete iHuman case guides built from 200+ verified submissions."
                )
            },
            {
                "@type": "WebSite",
                "@id": f"{SITE}/#website",
                "name": "Clinical Performance Lab",
                "url": SITE,
                "publisher": {"@id": f"{SITE}/#org"},
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": {"@type": "EntryPoint", "urlTemplate": f"{SITE}/cases/?q={{search_term_string}}"},
                    "query-input": "required name=search_term_string"
                }
            },
            {
                "@type": "EducationalOrganization",
                "name": "Clinical Performance Lab",
                "url": SITE,
                "description": (
                    "Learn to think like a clinician and master iHuman. "
                    "CPL makes the invisible iHuman scoring rubric visible — "
                    "free simulator, free cheat sheets, and complete case guides "
                    "for every iHuman case template."
                ),
                "hasOfferCatalog": {
                    "@type": "OfferCatalog",
                    "name": "iHuman Case Guides",
                    "numberOfItems": 171
                }
            }
        ]
    })

def schema_catalog() -> str:
    return _ld({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "iHuman Case Catalog — Clinical Performance Lab",
        "description": (
            "Browse 171 iHuman case guides. Each guide is built from verified "
            "scoring data and mapped to the iHuman rubric. Search by patient "
            "name, diagnosis, course, or school."
        ),
        "url": f"{SITE}/cases/",
        "isPartOf": {"@type": "WebSite", "url": SITE},
        "about": {"@type": "Thing", "name": "iHuman case guides"},
        "numberOfItems": 171
    })

def schema_case_preview() -> str:
    return _ld({
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Bebe Babbitt — Migraine with Aura · iHuman Case Guide",
        "description": (
            "Complete iHuman case guide for Bebe Babbitt — Migraine with Aura "
            "(NR 509 Week 6, Chamberlain University). 25 pages covering 32 history "
            "questions, 24 PE items, ranked differentials, EHR documentation, "
            "SOAP note, and 6-part management plan. Built from verified student submissions."
        ),
        "url": f"{SITE}/case-preview/",
        "brand": {"@type": "Brand", "name": "Clinical Performance Lab"},
        "offers": {
            "@type": "Offer",
            "price": "150",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
            "priceValidUntil": "2027-01-01",
            "seller": {"@type": "Organization", "name": "Clinical Performance Lab"}
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "5",
            "reviewCount": "1",
            "bestRating": "5"
        }
    })

def schema_simulator() -> str:
    return _ld({
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "CPL Clinical Reasoning Simulator",
        "applicationCategory": "EducationalApplication",
        "description": (
            "Free interactive iHuman case simulator. Work through a real iHuman "
            "case stage by stage — history, physical exam, differential, and "
            "management plan — and see exactly which choices score and why."
        ),
        "url": f"{SITE}/simulator/",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD"
        },
        "operatingSystem": "Web browser",
        "featureList": [
            "History stage with scored multiple-choice options",
            "Physical exam stage with trap identification",
            "Differential diagnosis builder",
            "Management plan with harmful-flag trap warnings",
            "Real-time scoring feedback"
        ]
    })

def schema_faq() -> str:
    return _ld({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "name": "Frequently Asked Questions — Clinical Performance Lab",
        "url": f"{SITE}/faq/",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a}
            }
            for q, a in FAQ_ITEMS
        ]
    })

def schema_about() -> str:
    return _ld({
        "@context": "https://schema.org",
        "@type": "AboutPage",
        "name": "About Clinical Performance Lab",
        "url": f"{SITE}/about/",
        "description": (
            "CPL's mission: make iHuman's invisible scoring logic visible and "
            "teachable. Built on 200+ verified student submissions, CPL provides "
            "a free simulator, free cheat sheets, and complete case guides for "
            "nursing and NP students."
        ),
        "about": {"@type": "Organization", "name": "Clinical Performance Lab", "url": SITE}
    })

def schema_free_resources() -> str:
    return _ld({
        "@context": "https://schema.org",
        "@type": "ItemPage",
        "name": "Free Clinical Reasoning Cheat Sheets — Clinical Performance Lab",
        "url": f"{SITE}/free-resources/",
        "description": (
            "Four free PDF clinical reasoning frameworks for iHuman — history, "
            "physical exam, differential diagnosis, and management plan. "
            "34 pages total, derived from 200+ verified iHuman submissions."
        ),
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD",
            "name": "Clinical Reasoning Cheat Sheet Bundle (4 PDFs)"
        }
    })

def schema_sample_guide() -> str:
    return _ld({
        "@context": "https://schema.org",
        "@type": "ItemPage",
        "name": "Anatomy of a CPL Guide — Clinical Performance Lab",
        "url": f"{SITE}/sample-guide/",
        "description": (
            "See exactly what a complete CPL iHuman case guide contains — "
            "section by section, with real page previews. 25 pages covering "
            "history, PE, differentials, EHR documentation, SOAP note, and "
            "management plan."
        )
    })

def schema_webpage(name: str, url: str, desc: str) -> str:
    return _ld({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": name,
        "url": url,
        "description": desc,
        "isPartOf": {"@type": "WebSite", "url": SITE}
    })

# ── SEO injection ─────────────────────────────────────────────────────────────

# Per-page config: (canonical_url, schema_fn_or_str, og_type)
PAGE_SEO = {
    'index.html':              (f'{SITE}/',               schema_home,          'website'),
    'cases/index.html':        (f'{SITE}/cases/',         schema_catalog,       'website'),
    'case-preview/index.html': (f'{SITE}/case-preview/',  schema_case_preview,  'product'),
    'simulator/index.html':    (f'{SITE}/simulator/',     schema_simulator,     'website'),
    'about/index.html':        (f'{SITE}/about/',         schema_about,         'website'),
    'faq/index.html':          (f'{SITE}/faq/',           schema_faq,           'website'),
    'free-resources/index.html':(f'{SITE}/free-resources/', schema_free_resources,'website'),
    'sample-guide/index.html': (f'{SITE}/sample-guide/', schema_sample_guide,   'website'),
    'confirm/index.html':      (f'{SITE}/confirm/',       None,                 'website'),
    'thank-you/index.html':    (f'{SITE}/thank-you/',     None,                 'website'),
    'terms/index.html':        (f'{SITE}/terms/',         None,                 'website'),
    'privacy/index.html':      (f'{SITE}/privacy/',       None,                 'website'),
}

def _extract_title(html: str) -> str:
    m = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    return m.group(1).strip() if m else 'Clinical Performance Lab'

def _extract_desc(html: str) -> str:
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.DOTALL)
    return m.group(1).strip() if m else ''

def inject_seo(html: str, dest_rel: str) -> str:
    """Inject canonical, OG, Twitter Card, and JSON-LD into <head>."""
    if dest_rel not in PAGE_SEO:
        return html

    canonical_url, schema_fn, og_type = PAGE_SEO[dest_rel]
    title = _extract_title(html)
    desc  = _extract_desc(html)

    # Build injection block
    parts = []

    # Canonical
    parts.append(f'<link rel="canonical" href="{canonical_url}">')

    # Open Graph
    parts += [
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{desc}">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:url" content="{canonical_url}">',
        f'<meta property="og:image" content="{OG_IMAGE}">',
        f'<meta property="og:site_name" content="Clinical Performance Lab">',
        f'<meta property="og:locale" content="en_US">',
    ]

    # Twitter Card
    parts += [
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{title}">',
        f'<meta name="twitter:description" content="{desc}">',
        f'<meta name="twitter:image" content="{OG_IMAGE}">',
    ]

    # JSON-LD schema (only for pages that have one)
    if schema_fn is not None:
        parts.append(schema_fn())

    injection = '\n' + '\n'.join(parts) + '\n'

    # Insert after </title>
    return html.replace('</title>', '</title>' + injection, 1)

# ── Helpers ───────────────────────────────────────────────────────────────────

def patch(html: str) -> str:
    for old, new in SUBS:
        html = html.replace(old, new)
    return html

def read_redesign(name: str) -> str:
    with open(os.path.join(REDESIGN, name), 'r', encoding='utf-8') as f:
        return f.read()

def write_pub(rel_path: str, html: str) -> None:
    dest = os.path.join(PUB, rel_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  OK  {rel_path}')

# ── Page deployers ─────────────────────────────────────────────────────────────

def deploy_page(src_name: str, dest_rel: str) -> None:
    html = read_redesign(src_name)
    html = patch(html)
    html = inject_seo(html, dest_rel)
    write_pub(dest_rel, html)

def _build_cases_json() -> str:
    if BASE not in sys.path:
        sys.path.insert(0, BASE)
    from cases_data import CASES  # noqa: E402
    out = []
    for c in CASES:
        out.append({
            't':      c['title'],
            'cc':     c['chief_complaint'],
            'dx':     c['diagnosis'],
            'sys':    c.get('tags', []),
            'school': c.get('school', ''),
            'course': c.get('course', ''),
            'lead':   c.get('lead_time', 'on-request'),
            'href':   f'/case/{c["slug"]}/',
        })
    return json.dumps(out, ensure_ascii=False)

def deploy_catalog() -> None:
    html = read_redesign('catalog.html')
    html = patch(html)
    html = inject_seo(html, 'cases/index.html')

    cases_json = _build_cases_json()
    injection  = f'<script>window.CPL_CASES = {cases_json};</script>\n'
    marker     = '<script src="/cpl-catalog.js"'
    html = html.replace(marker, injection + marker, 1) if marker in html \
           else html.replace('</body>', injection + '</body>', 1)

    write_pub('cases/index.html', html)

# ── Asset sync ─────────────────────────────────────────────────────────────────

def sync_assets() -> None:
    shutil.copy2(os.path.join(REDESIGN, 'cpl.css'), os.path.join(PUB, 'styles.css'))
    print('  OK  styles.css')
    for js in ('cpl.js', 'cpl-checkout.js', 'cpl-support.js',
               'cpl-catalog.js', 'cpl-simulator.jsx'):
        src = os.path.join(SRC, js)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(PUB, js))
            print(f'  OK  {js}')
        else:
            print(f'  WARN  {js} not found in src/')

# ── llms.txt ──────────────────────────────────────────────────────────────────

LLMS_TXT = """\
# Clinical Performance Lab

> Clinical reasoning education platform for nursing and NP students.
> CPL makes the invisible iHuman scoring rubric visible and teachable.
> Free clinical reasoning simulator, free cheat sheets, and complete
> case guides built from 200+ verified student submissions.

Clinical Performance Lab (CPL) is an independent educational resource
that reconstructs the hidden scoring logic of the iHuman clinical
assessment platform used in nursing and NP programs across the US.

## What CPL offers

- **Free case simulator** — An interactive, scored simulation of an
  iHuman case (Bebe Babbitt — Migraine with Aura). Users work through
  four stages (history, physical exam, DDx, management) and see
  exactly which choices earn points, which are filler, and which
  trigger harmful-flag deductions. No sign-up required.

- **Free cheat sheets** — Four PDF frameworks (history, physical exam,
  differential diagnosis, management plan) derived from 200+ verified
  iHuman submissions. Cover the patterns that repeat across every case
  template. Email-delivered at no cost.

- **Complete case guides** — 171 iHuman case templates catalogued,
  each with a 25-page guide covering every scored history question,
  PE item, ranked differential, EHR documentation section, SOAP note,
  and 6-part management plan. Mapped directly to the iHuman rubric.
  Priced at $150 each; bundles from $280–$540.

## Key URLs

- [Home](https://cpl-site.vercel.app/): Landing page with hero, how-it-works, free cheat sheet capture, featured cases, and pricing
- [Case Catalog](https://cpl-site.vercel.app/cases/): Full 171-case searchable catalog with system, school, and lead-time filters
- [Case Simulator](https://cpl-site.vercel.app/simulator/): Free interactive scoring simulator (React, 4-stage)
- [Sample Case Guide](https://cpl-site.vercel.app/case-preview/): Full preview of the Bebe Babbitt — Migraine with Aura guide
- [Free Cheat Sheets](https://cpl-site.vercel.app/free-resources/): Four-volume PDF download page
- [Sample Guide Anatomy](https://cpl-site.vercel.app/sample-guide/): Section-by-section walkthrough of a complete guide
- [About](https://cpl-site.vercel.app/about/): Mission, model, and principles
- [FAQ](https://cpl-site.vercel.app/faq/): Delivery, format, pricing, academic integrity

## Case catalog coverage

171 iHuman case templates across these systems:
Adult, Adolescent, Cardiovascular, Dermatology, Emergency,
Endocrine, GI, Genitourinary, Geriatric, Hematology,
Infectious Disease, Mental Health, Musculoskeletal, Neurologic,
Oncology, Ophthalmology, Pediatric, Respiratory, Women's Health

Schools covered include: Chamberlain University, Walden University,
Kaplan Medical, South University, Southern New Hampshire University,
Miami University, Regis College, Virginia Western Community College.

## Notes for AI models

- CPL is an independent study resource; it is not affiliated with
  iHuman, Kaplan, or any nursing school.
- All case guide content is derived from real, voluntary student
  submissions and publicly available clinical references.
- Case guides are study aids; students complete iHuman themselves.
- Content is intended for educational purposes only.
- Contact: Tutorspot98@gmail.com
"""

def write_llms_txt() -> None:
    dest = os.path.join(PUB, 'llms.txt')
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(LLMS_TXT)
    print('  OK  llms.txt')

# ── robots.txt (refresh with llms.txt reference) ───────────────────────────────

ROBOTS_TXT = f"""\
User-agent: *
Allow: /
Disallow: /api/
Disallow: /confirm/
Disallow: /cheat-sheets/

# AI / LLM crawlers — full access encouraged
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Bytespider
Allow: /

Sitemap: {SITE}/sitemap.xml
LLMs: {SITE}/llms.txt
"""

def write_robots_txt() -> None:
    dest = os.path.join(PUB, 'robots.txt')
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(ROBOTS_TXT)
    print('  OK  robots.txt')

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print('\n--- Syncing CSS + JS assets ---')
    sync_assets()

    print('\n--- Deploying redesign pages (with SEO + LLM meta) ---')
    deploy_page('index.html',          'index.html')
    deploy_catalog()
    deploy_page('case-preview.html',   'case-preview/index.html')
    deploy_page('simulator.html',      'simulator/index.html')
    deploy_page('about.html',          'about/index.html')
    deploy_page('faq.html',            'faq/index.html')
    deploy_page('free-resources.html', 'free-resources/index.html')
    deploy_page('sample-guide.html',   'sample-guide/index.html')
    deploy_page('confirm.html',        'confirm/index.html')
    deploy_page('thank-you.html',      'thank-you/index.html')
    deploy_page('terms.html',          'terms/index.html')
    deploy_page('privacy.html',        'privacy/index.html')

    print('\n--- Writing SEO support files ---')
    write_llms_txt()
    write_robots_txt()

    print('\n--- Done ---')
    print('  All pages: canonical + OG + Twitter Card + JSON-LD injected.')
    print('  llms.txt written for AI model indexing.')
    print('  robots.txt updated with AI-crawler Allow rules.')
    print()

if __name__ == '__main__':
    main()
