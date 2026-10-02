"""Page shell: <head>, site header, mobile menu and footer."""
import os
from datetime import datetime, timezone

import build
from web.components import e, icon, logo_mark, dot

# Primary navigation, in the order of the homepage v2 header.
NAV = [
    ("iHuman", "/cases/"),
    ("Exams", "/#exam-path"),
    ("Coursework", "/#support"),
    ("ATI/HESI", "/#ati"),
    ("NCLEX", "/#nclex"),
    ("TEAS", "/#teas"),
]

FONTS = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400"
         "&family=IBM+Plex+Mono:wght@400;500&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap")


def brand(size=34):
    return (f'<a href="/" class="brand" aria-label="{e(build.SITE_NAME)} home">{logo_mark(size)}'
            '<span class="brand-name">Clinical Performance<span> Lab</span></span></a>')


def header_html():
    strong = ' class="nav-strong"'
    links = "".join(f'<li><a href="{href}"{strong if label == "iHuman" else ""}>{label}</a></li>' for label, href in NAV)
    mobile = "".join(f'<a href="{href}" data-menu-close>{label}</a>' for label, href in NAV)
    return f"""
<a class="skip-link" href="#main-content">Skip to content</a>
<header class="site-header"><div class="header-inner">
  {brand()}
  <nav aria-label="Main navigation"><ul class="nav-links">{links}<li><a href="/#support" class="nav-support">{dot()}Human Support</a></li></ul></nav>
  <div class="header-actions"><button class="header-signin" data-access-code>Access my guide</button><a class="btn btn-lime btn-sm" href="/cases/">Find My Case</a><button class="nav-burger" aria-label="Open menu" aria-expanded="false" aria-controls="mobileMenu">{icon('menu', 24)}</button></div>
</div></header>
<div class="menu-backdrop"></div>
<nav class="mobile-menu" id="mobileMenu" aria-label="Mobile navigation" aria-hidden="true" inert>
  <div class="mobile-menu-head"><span class="eyebrow">Menu</span><button class="mobile-menu-close" data-menu-close aria-label="Close menu">×</button></div>
  {mobile}<a href="/#support" data-menu-close>Human Support</a><a href="/free-resources/" data-menu-close>Free resources</a><a href="/sample-guide/" data-menu-close>Sample guide</a><a href="/faq/" data-menu-close>Questions &amp; answers</a>
  <a class="btn btn-lime" href="/cases/" data-menu-close>Find My Case</a><button class="btn btn-ghost" data-access-code data-menu-close>{icon('lock', 16)} Access my guide</button>
</nav>"""


def footer_html():
    year = datetime.now(timezone.utc).year
    return f"""
<footer class="site-footer"><div class="container">
  <div class="footer-top">
    <div class="footer-intro">{brand(30)}<p>Resources when you can handle it yourself. Real human support when you need more than a resource.</p><a href="mailto:{build.CONTACT_EMAIL}">{build.CONTACT_EMAIL}</a></div>
    <div><h2>Study</h2><a href="/cases/">iHuman cases</a><a href="/sample-guide/">Sample guide</a><a href="/free-resources/">Free resources</a><a href="/simulator/">Simulator waitlist</a></div>
    <div><h2>Get help</h2><a href="/#support">Human support</a><a href="/faq/">Questions &amp; answers</a><a href="/about/">About CPL</a><a href="mailto:{build.SUPPORT_EMAIL}">Contact support</a><button data-access-code>Access my guide</button></div>
    <div><h2>The details</h2><a href="/about/#integrity">Academic integrity</a><a href="/terms/">Terms of use</a><a href="/privacy/">Privacy</a></div>
  </div>
  <div class="footer-bottom"><span>© {year} Clinical Performance Lab · clinicalperformancelab.com</span><span>Independent educational resource. Not affiliated with or endorsed by iHuman, Kaplan or any institution.</span></div>
</div></footer>"""


def write_page(rel_path, body, title=None, description=None, page_class="", head_extra="", body_scripts="", after_footer=""):
    """Write public/{rel_path}/index.html wrapped in the site shell."""
    full_title = f"{title} · {build.SITE_NAME}" if title else f"{build.SITE_NAME} — iHuman cases, exams and human support"
    desc = description or build.SITE_TAG
    if rel_path:
        full_path = os.path.join(build.PUBLIC, rel_path, "index.html")
        canonical = f"{build.SITE_URL}/{rel_path}/"
    else:
        full_path = os.path.join(build.PUBLIC, "index.html")
        canonical = f"{build.SITE_URL}/"
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    v = build.ASSET_VERSION

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#F6FBE7">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(build.SITE_NAME)}">
<meta property="og:image" content="{e(build.SITE_URL)}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(full_title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{e(build.SITE_URL)}/og-image.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="/styles.css?v={v}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
{head_extra}
</head>
<body class="{e(page_class)}">
{header_html()}
<main id="main-content">
{body}
</main>
{footer_html()}
{after_footer}
{body_scripts}
<script src="/cpl.js?v={v}" defer></script>
<script src="/cpl-checkout.js?v={v}" defer></script>
<script src="/cpl-support.js?v={v}" defer></script>
</body>
</html>
"""
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(doc)
