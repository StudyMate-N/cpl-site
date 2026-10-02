"""
CPL static site generator.

Produces every HTML page in public/ from the case catalog and the page
templates in web/. After running this, also runs the cheat sheet generator to
refresh the PDFs.

Usage:
    python3 build.py              # pages + assets + PDFs
    python3 build.py --skip-pdfs  # pages + assets only

Layout:
    build.py          orchestrator, site config, data manifests, ops console
    web/layout.py     page shell: <head>, header, footer
    web/components.py shared UI pieces (logo, icons, case cards, resources)
    web/pages.py      one builder per public page
    src/site.css      design system (tokens → base → components → pages)
    src/*.js          front-end behaviour (API contracts unchanged)
    src/img/          optimized site imagery
"""

import os
import json
import shutil
from datetime import datetime, timezone

from cases_data import CASES, PRICING

# ─── Configuration ────────────────────────────────────────────────
# Single source of truth for the live domain. Update here only.
SITE_URL = "https://www.clinicalperformancelab.com"
SITE_NAME = "Clinical Performance Lab"
SITE_TAG = "iHuman case guides, exam preparation and real human support for nursing students."

# Role-based email addresses.
CONTACT_EMAIL = "hello@clinicalperformancelab.com"     # brand front door · footer/about/general
ORDER_EMAIL   = "orders@clinicalperformancelab.com"    # "Order this guide" requests · invoicing
SUPPORT_EMAIL = "support@clinicalperformancelab.com"   # delivery issues · refunds · "delete my data"

# Bump when src/ assets change so browsers pick up the new files.
ASSET_VERSION = "20261002-v2"

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")
SRC = os.path.join(ROOT, "src")

CHEAT_SHEETS = [
    {"id": "history",       "vol": "I",   "title": "History Framework",        "pages": 8, "filename": "cpl-vol-1-history.pdf"},
    {"id": "physical-exam", "vol": "II",  "title": "Universal PE Checklist",   "pages": 9, "filename": "cpl-vol-2-physical-exam.pdf"},
    {"id": "ddx",           "vol": "III", "title": "DDx & Key Findings",       "pages": 8, "filename": "cpl-vol-3-ddx.pdf"},
    {"id": "plan",          "vol": "IV",  "title": "Management Plan & SOAP",   "pages": 9, "filename": "cpl-vol-4-plan.pdf"},
]


# ─── Case preview metadata ────────────────────────────────────────
def get_preview_data(slug):
    """
    Read the preview meta.json for a case and return a normalized dict, or
    None if no preview exists.

    Real previews (is_sample=False) carry clear_pages (one per section),
    section_labels, and stack_blurred (3 teaser pages for the locked stack).

    Sample previews (is_sample=True) carry sample_source + source_title and
    are rendered from watermarked source pages in /previews/_watermarked/.
    """
    meta_path = os.path.join(PUBLIC, 'previews', slug, 'meta.json')
    if not os.path.isfile(meta_path):
        return None
    try:
        with open(meta_path, encoding='utf-8') as f:
            meta = json.load(f)
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


# ─── Sitemap + robots ─────────────────────────────────────────────
def build_sitemap():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = ["", "simulator", "sample-guide", "free-resources", "cases", "faq", "about", "terms", "privacy"]
    urls += [f"case/{c['slug']}" for c in CASES]

    entries = "\n".join(
        f"""  <url>
    <loc>{SITE_URL}/{u + '/' if u else ''}</loc>
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

Sitemap: {SITE_URL}/sitemap.xml
"""
    with open(os.path.join(PUBLIC, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)


# ─── Favicon (ring mark) ──────────────────────────────────────────
def build_favicon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60" fill="none">
  <circle cx="30" cy="30" r="30" fill="#fff"/>
  <circle cx="30" cy="30" r="25" stroke="#74A01F" stroke-width="5"/>
  <path d="M4 32H20L24 24L29 40L34 16L38 36L41 32H56" stroke="#262A25" stroke-width="4.4" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""
    with open(os.path.join(PUBLIC, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(svg)


# ─── Front-end assets ─────────────────────────────────────────────
def build_assets():
    """Copy the front-end CSS, JS and images from src/ to public/."""
    for name in ["cpl.js", "cpl-home.js", "cpl-checkout.js", "cpl-support.js", "cpl-catalog.js"]:
        shutil.copyfile(os.path.join(SRC, name), os.path.join(PUBLIC, name))
    # Public presentation is separate from the private operations stylesheet.
    shutil.copyfile(os.path.join(SRC, "site.css"), os.path.join(PUBLIC, "styles.css"))
    img_out = os.path.join(PUBLIC, "img")
    os.makedirs(img_out, exist_ok=True)
    for name in os.listdir(os.path.join(SRC, "img")):
        shutil.copyfile(os.path.join(SRC, "img", name), os.path.join(img_out, name))


def build_cases_manifest():
    """Emit public/cases.json — the catalog the ops inbound webhook reads to
    set each order's `ready` (pre-built → auto-deliver) flag + price. The
    homepage search reads it too."""
    single_price = PRICING.get("single", {}).get("price", 150)
    manifest = []
    for c in CASES:
        aliases = c.get("aliases") or []
        manifest.append({
            "slug": c.get("slug", ""),
            "title": c.get("title", ""),
            "cc": c.get("chief_complaint", ""),
            "ready": c.get("lead_time") == "same-day",
            "price": single_price,
            "school": c.get("school", ""),
            "course": c.get("course", ""),
            "alias": aliases[0] if aliases else "",
            "lead": c.get("lead_time", "on-request"),
        })
    with open(os.path.join(PUBLIC, "cases.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))


def build_ops():
    """Mount the ops console at /ops/ from src/ops/ (source of truth).
    admin.html → public/ops/index.html; assets copied alongside; the shared
    design-system CSS is copied in as cpl.css (admin.html links it relatively)."""
    src_ops = os.path.join(SRC, "ops")
    if not os.path.isdir(src_ops):
        return
    out = os.path.join(PUBLIC, "ops")
    os.makedirs(out, exist_ok=True)
    copies = [
        ("admin.html", "index.html"),
        ("admin.css", "admin.css"),
        ("cpl-admin.js", "cpl-admin.js"),
        ("cpl-admin-auth.js", "cpl-admin-auth.js"),
        ("cpl-emails.js", "cpl-emails.js"),
    ]
    for src_name, dst_name in copies:
        sp = os.path.join(src_ops, src_name)
        if os.path.exists(sp):
            shutil.copyfile(sp, os.path.join(out, dst_name))
    # shared design-system CSS (admin.html links href="cpl.css")
    css_src = os.path.join(SRC, "cpl.css")
    if os.path.exists(css_src):
        shutil.copyfile(css_src, os.path.join(out, "cpl.css"))


# ─── Orchestrator ────────────────────────────────────────────────
def build_all(rebuild_pdfs=True):
    from web import pages

    print(f"Building CPL static site → {PUBLIC}/")
    pages.build_pages()
    build_sitemap()
    print("  ✓ sitemap.xml + robots.txt")
    build_favicon()
    print("  ✓ favicon.svg")
    build_assets()
    print("  ✓ styles.css, scripts, img/")
    build_cases_manifest()
    print("  ✓ cases.json (ops catalog manifest)")
    build_ops()
    print("  ✓ ops/ (operations console)")

    if rebuild_pdfs:
        print("\nRebuilding cheat sheet PDFs...")
        import subprocess
        res = subprocess.run(
            ["python3", os.path.join(ROOT, "generate_cheat_sheets.py")],
            capture_output=True, text=True
        )
        print(res.stdout)
        if res.returncode != 0:
            raise RuntimeError(f"Cheat sheet build failed:\n{res.stderr}")

    print(f"\n✓ Site built in {PUBLIC}/")


if __name__ == "__main__":
    import sys
    build_all(rebuild_pdfs="--skip-pdfs" not in sys.argv)
