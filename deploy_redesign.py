#!/usr/bin/env python3
"""
deploy_redesign.py
Takes each HTML file from _newdesign_extract/redesign/ verbatim,
patches all relative paths → absolute paths, fixes internal links
to pretty URLs, injects window.CPL_CASES for the catalog, and
writes the results to public/.

Run: python deploy_redesign.py
"""
import os
import json
import shutil
import sys

# ── Paths ────────────────────────────────────────────────────────────────────
BASE     = os.path.dirname(os.path.abspath(__file__))
REDESIGN = os.path.join(BASE, '_newdesign_extract', 'redesign')
PUB      = os.path.join(BASE, 'public')
SRC      = os.path.join(BASE, 'src')

# ── Link / asset substitutions (applied in order) ────────────────────────────
# More specific patterns come first to avoid double-substitution.
SUBS = [
    # ---- Internal links (.html → pretty URLs) --------------------------------
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
    # ---- Stylesheet ----------------------------------------------------------
    ('href="cpl.css"',             'href="/styles.css"'),
    # ---- JS assets -----------------------------------------------------------
    ('src="cpl.js"',               'src="/cpl.js"'),
    ('src="cpl-checkout.js"',      'src="/cpl-checkout.js"'),
    ('src="cpl-support.js"',       'src="/cpl-support.js"'),
    ('src="cpl-catalog.js"',       'src="/cpl-catalog.js"'),
    ('src="cpl-simulator.jsx"',    'src="/cpl-simulator.jsx"'),
    # ---- Image / preview paths -----------------------------------------------
    ('src="previews/',             'src="/previews/'),
    ('data-lightbox="previews/',   'data-lightbox="/previews/'),
    ('href="previews/',            'href="/previews/'),
]

# ── Helpers ──────────────────────────────────────────────────────────────────

def patch(html: str) -> str:
    """Apply all path / link substitutions to an HTML string."""
    for old, new in SUBS:
        html = html.replace(old, new)
    return html

def read_redesign(name: str) -> str:
    path = os.path.join(REDESIGN, name)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_pub(rel_path: str, html: str) -> None:
    dest = os.path.join(PUB, rel_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  OK  {rel_path}')

# ── Page deployers ────────────────────────────────────────────────────────────

def deploy_page(src_name: str, dest_rel: str) -> None:
    """Read, patch, and write a redesign page straight to public/."""
    html = read_redesign(src_name)
    html = patch(html)
    write_pub(dest_rel, html)

def _build_cases_json() -> str:
    """Build the window.CPL_CASES JSON array from cases_data.py."""
    if BASE not in sys.path:
        sys.path.insert(0, BASE)
    from cases_data import CASES  # noqa: E402

    out = []
    for c in CASES:
        # Build the school display name (cases_data uses 'school' as full name)
        school = c.get('school', '')
        # Some cases only have 'schools' list with short codes — skip those
        # (every current case has a 'school' key with the full name)
        out.append({
            't':      c['title'],
            'cc':     c['chief_complaint'],
            'dx':     c['diagnosis'],
            'sys':    c.get('tags', []),
            'school': school,
            'course': c.get('course', ''),
            'lead':   c.get('lead_time', 'on-request'),
            'href':   f'/case/{c["slug"]}/',
        })
    return json.dumps(out, ensure_ascii=False)

def deploy_catalog() -> None:
    """Deploy catalog.html with window.CPL_CASES injected for all 171 cases."""
    html = read_redesign('catalog.html')
    html = patch(html)

    # Inject window.CPL_CASES immediately before the catalog script tag
    cases_json = _build_cases_json()
    injection  = f'<script>window.CPL_CASES = {cases_json};</script>\n'
    marker     = '<script src="/cpl-catalog.js"'
    if marker in html:
        html = html.replace(marker, injection + marker, 1)
    else:
        # Fallback: inject before </body>
        html = html.replace('</body>', injection + '</body>', 1)

    write_pub('cases/index.html', html)

# ── Asset sync ────────────────────────────────────────────────────────────────

def sync_assets() -> None:
    """
    Ensure the redesign CSS is available as /styles.css (already the case
    from the previous build).  Also refresh all JS assets from src/.
    """
    # CSS — copy from redesign source to public/styles.css
    css_src  = os.path.join(REDESIGN, 'cpl.css')
    css_dest = os.path.join(PUB, 'styles.css')
    shutil.copy2(css_src, css_dest)
    print('  OK  styles.css (from redesign)')

    # JS — copy from src/ (already the redesign versions)
    for js_name in ('cpl.js', 'cpl-checkout.js', 'cpl-support.js',
                    'cpl-catalog.js', 'cpl-simulator.jsx'):
        js_src  = os.path.join(SRC, js_name)
        js_dest = os.path.join(PUB, js_name)
        if os.path.exists(js_src):
            shutil.copy2(js_src, js_dest)
            print(f'  OK  {js_name}')
        else:
            print(f'  WARN  {js_name} not found in src/ - skipping')

# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print('\n--- Syncing CSS + JS assets ---')
    sync_assets()

    print('\n--- Deploying redesign pages ---')
    deploy_page('index.html',          'index.html')
    deploy_catalog()                                   # catalog w/ 171 cases
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

    print('\n--- Done ---')
    print('  Main pages deployed from redesign zip verbatim.')
    print('  Individual case pages (/case/<slug>/) remain as generated.')
    print()

if __name__ == '__main__':
    main()
