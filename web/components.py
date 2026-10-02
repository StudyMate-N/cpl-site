"""Shared UI pieces used across public pages."""
import html
from urllib.parse import urlencode, quote

import build

LEAD = {"same-day": "Same-day guide", "fast-build": "24–48h build", "on-request": "Confirm availability"}

# Schools shown in the homepage strip. Colors are each institution's primary
# brand color; names are used only to organize resources (see disclaimer).
# `match` is the text searched for in the catalog's school field.
SCHOOLS = [
    {"name": "Chamberlain", "sub": "University", "full": "Chamberlain University", "mono": "C", "c1": "#013A81", "c2": "#FFFFFF", "match": "Chamberlain"},
    {"name": "Walden", "sub": "University", "full": "Walden University", "mono": "W", "c1": "#00467F", "c2": "#FFFFFF", "match": "Walden"},
    {"name": "Capella", "sub": "University", "full": "Capella University", "mono": "C", "c1": "#7A1F35", "c2": "#FFFFFF", "match": "Capella"},
    {"name": "Purdue Global", "sub": "Purdue University", "full": "Purdue University Global", "mono": "P", "c1": "#000000", "c2": "#CEB888", "match": "Purdue"},
]


def e(value):
    return html.escape(str(value or ""), quote=True)


def search_url(query):
    return "/cases/?" + urlencode({"q": query})


def mailto(subject, address=None):
    return f"mailto:{address or build.CONTACT_EMAIL}?subject={quote(subject)}"


def icon(name, size=20):
    paths = {
        "search": '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5 21 21"/>',
        "book": '<path d="M12 5.5C8 3 4 4 3 4.5v15c3-1 6-1 9 1 3-2 6-2 9-1v-15c-3-1-6-1-9 1Z"/><path d="M12 5.5v15"/>',
        "lock": '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/><path d="M12 14v3"/>',
        "layers": '<path d="m12 3 10 5-10 5L2 8l10-5Z"/><path d="m2 12 10 5 10-5M2 16l10 5 10-5"/>',
        "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
        "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    }
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg>'


def logo_mark(size=34):
    """Ring mark (logo option 2b): lime ring, ink pulse line."""
    return (f'<svg class="logo-mark" width="{size}" height="{size}" viewBox="0 0 60 60" fill="none" aria-hidden="true">'
            '<circle cx="30" cy="30" r="26" stroke="#74A01F" stroke-width="4"/>'
            '<path d="M4 32H20L24 24L29 40L34 16L38 36L41 32H56" stroke="#262A25" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def pulse_line():
    return ('<svg class="pulse-line" viewBox="0 0 400 22" preserveAspectRatio="none" fill="none" aria-hidden="true">'
            '<path d="M0 14H250L258 6L266 20L274 1L282 18L288 14H400" stroke="#74A01F" stroke-width="2" stroke-linejoin="round" vector-effect="non-scaling-stroke"/></svg>')


def dot(kind="ok"):
    return f'<span class="dot dot-{kind}" aria-hidden="true"></span>'


def split_title(case):
    name, _, focus = case["title"].partition("—")
    return name.strip(), (focus.strip() or case.get("diagnosis", ""))


def topic(case):
    tags = [t for t in case.get("tags", []) if t not in ("Adult",)]
    return tags[0] if tags else "Clinical"


def lead_badge(lead):
    return f'<span class="availability {"ready" if lead == "same-day" else ""}">{e(LEAD.get(lead, LEAD["on-request"]))}</span>'


def case_card_html(case):
    """Catalog card. Mirrors the markup cpl-catalog.js renders client-side."""
    name, focus = split_title(case)
    lead = case.get("lead_time", "on-request")
    return f"""
<article class="case-card cat-card">
  <div class="card-top"><span class="system-label">{e(topic(case))}</span>{lead_badge(lead)}</div>
  <h3><a href="/case/{e(case['slug'])}/">{e(name)}</a></h3><p class="case-focus">{e(focus)}</p><p class="case-cc">{e(case.get('chief_complaint'))}</p>
  <div class="card-course">{e(case.get('course') or 'Course to confirm')}<span>{e(case.get('school') or 'Institution to confirm')}</span></div>
  <div class="cat-card-actions"><a href="/case/{e(case['slug'])}/">View case</a></div>
</article>"""


def feature_case_html(case):
    """Homepage case card: tinted header with the patient name."""
    name, focus = split_title(case)
    lead = case.get("lead_time", "on-request")
    return f"""
<a class="feature-case" href="/case/{e(case['slug'])}/">
  <span class="feature-case-head"><span class="eyebrow-sm">{e(topic(case))} · {e(case.get('course') or 'Course to confirm')}</span><span class="feature-case-name">{e(name)}</span></span>
  <span class="feature-case-body"><span class="feature-case-meta">{e(case.get('patient_short'))} · {e(focus)}</span>
  <span class="tag-row">{lead_badge(lead)}<span class="tag">Word + PDF</span></span>
  <span class="link-arrow">Open case →</span></span>
</a>"""


RESOURCE_TEXT = {
    "history": "Build a focused interview with OLDCARTS, a relevant review of systems, and clear clinical language.",
    "physical-exam": "Organize the examination around the presentation and document the findings clearly.",
    "ddx": "Connect key findings to a problem statement and a reasoned differential.",
    "plan": "Structure management, patient education, follow-up and SOAP documentation.",
}


def resource_card(cs, selected=False):
    return f"""
<label class="resource-card {'selected' if selected else ''}" data-id="{e(cs['id'])}">
  <input type="checkbox" name="volumes" value="{e(cs['id'])}" {'checked' if selected else ''}>
  <span class="resource-stage">Volume {e(cs['vol'])} <span>PDF</span></span><span class="resource-title">{e(cs['title'])}</span><span class="resource-description">{e(RESOURCE_TEXT[cs['id']])}</span><span class="resource-meta">{cs['pages']} pages · Free resource</span>
</label>"""


def capture_html(selected=True):
    cards = "".join(resource_card(cs, selected) for cs in build.CHEAT_SHEETS)
    return f"""
<form data-capture class="resource-form"><div class="resource-grid">{cards}</div>
<div class="capture"><div class="capture-copy"><h3>Send these to my inbox.</h3><p>Choose your PDFs. Confirm your email. Start studying.</p></div><div class="capture-fields"><label class="sr-only" for="resourceEmail">Your email address</label><div class="capture-row"><input type="email" id="resourceEmail" name="email" placeholder="Your email address" required autocomplete="email"><button type="submit" class="btn btn-lime">Send my resources</button></div><p class="capture-fine">Includes a short clinical-insight follow-up. Unsubscribe any time.</p><p data-capture-msg role="status" aria-live="polite" hidden></p></div></div></form>"""


def page_intro(eyebrow, title_html, lede):
    return f'<section class="page-intro"><div class="container intro-row"><div><span class="eyebrow">{eyebrow}</span><h1>{title_html}</h1></div><p>{lede}</p></div></section>'


def closing_cta(title_html, text, primary_href, primary_label, secondary_href=None, secondary_label=None):
    second = f'<a class="text-link" href="{e(secondary_href)}">{secondary_label}</a>' if secondary_href else ""
    return f'<section class="closing"><div class="container"><div class="closing-panel"><h2>{title_html}</h2><p>{text}</p><div class="btn-row"><a class="btn btn-lime" href="{e(primary_href)}">{primary_label}</a>{second}</div></div></div></section>'
