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
# Single source of truth for the live domain. Update here only.
SITE_URL = "https://www.clinicalperformancelab.com"
BASE_URL = SITE_URL  # backwards-compatible alias used across this module
SITE_NAME = "Clinical Performance Lab"
SITE_TAG = "Clinical reasoning platform for nursing students — master iHuman"

# Role-based email addresses (single source of truth for the rebrand).
CONTACT_EMAIL = "hello@clinicalperformancelab.com"     # brand front door · footer/about/general
ORDER_EMAIL   = "orders@clinicalperformancelab.com"    # "Order this guide" requests · invoicing
SUPPORT_EMAIL = "support@clinicalperformancelab.com"   # delivery issues · refunds · "delete my data"

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")

CHEAT_SHEETS = [
    {"id": "history",       "vol": "I",   "title": "History Framework",        "pages": 8, "filename": "cpl-vol-1-history.pdf"},
    {"id": "physical-exam", "vol": "II",  "title": "Universal PE Checklist",   "pages": 9, "filename": "cpl-vol-2-physical-exam.pdf"},
    {"id": "ddx",           "vol": "III", "title": "DDx & Key Findings",       "pages": 8, "filename": "cpl-vol-3-ddx.pdf"},
    {"id": "plan",          "vol": "IV",  "title": "Management Plan & SOAP",   "pages": 9, "filename": "cpl-vol-4-plan.pdf"},
]

# Interactive case simulator content (free clinical-reasoning practice)
SIMULATOR_DATA = {
    "harvey": {
        "title": "Harvey Hoya — Hypertension Stage 2",
        "meta": "57-year-old male · NR 509 / NR 511 Week 5 · Chamberlain",
        "questions": [
            {
                "stage": "History",
                "q": "The patient says 'I was told my blood pressure was high at a health fair.' What is your first response?",
                "options": [
                    "How can I help you today?",
                    "Tell me your blood pressure number.",
                    "Have you taken medication for this before?",
                    "How long have you had hypertension?",
                ],
                "correct": 0,
                "feedback": "Correct. The patient-centered opener scores on pivotal communication. Always open with 'How can I help you today?' — never lead with a closed clinical question on iHuman.",
            },
            {
                "stage": "History",
                "q": "Patient confirms elevated BP readings. Which OLDCARTS element should you address next?",
                "options": [
                    "Onset — when did they first notice elevated BP?",
                    "Radiation — does the pain spread anywhere?",
                    "Severity — rate your headache 1–10",
                    "Duration — how long has this been a problem?",
                ],
                "correct": 0,
                "feedback": "Onset is always first in OLDCARTS. Establishing the timeline is foundational — iHuman scores you on systematic history-taking, not breadth-first questions.",
            },
            {
                "stage": "Physical Exam",
                "q": "You're starting the cardiac exam. Which auscultation point represents the MITRAL valve (also where you palpate for PMI)?",
                "options": [
                    "2nd ICS, right sternal border (Aortic)",
                    "4th ICS, left sternal border (Tricuspid)",
                    "5th ICS, midclavicular line",
                    "3rd ICS, left sternal border (Erb's point)",
                ],
                "correct": 2,
                "feedback": "Correct. 5th ICS, midclavicular line = Mitral/Apex. This is also where you check PMI — lateral displacement indicates LVH, a key target organ damage finding in HTN.",
            },
            {
                "stage": "Physical Exam",
                "q": "On fundoscopic exam you notice copper wire appearance with focal narrowing where arteries cross veins. What is the clinical term?",
                "options": [
                    "Papilledema",
                    "Arteriovenous nicking",
                    "Exudates",
                    "Cotton wool spots",
                ],
                "correct": 1,
                "feedback": "AV nicking = hypertensive retinopathy = target organ damage. This is a HIGH-YIELD scoring trap — missing it means missing the TOD diagnosis, which downgrades the case grade.",
            },
        ],
    },
    "bebe": {
        "title": "Bebe Babbitt — Migraine with Aura",
        "meta": "26-year-old female · NR 509 Week 6 · Chamberlain",
        "questions": [
            {
                "stage": "History",
                "q": "Patient presents with 'more frequent, severe headaches.' Which SNOOP4 red flag would indicate you should NOT manage this as a primary headache?",
                "options": [
                    "Photophobia and phonophobia",
                    "Sudden onset — 'worst headache of my life'",
                    "Unilateral throbbing pain",
                    "Nausea with the headache",
                ],
                "correct": 1,
                "feedback": "Thunderclap onset = subarachnoid hemorrhage until proven otherwise. This is the 'S' in SNOOP4. Immediate imaging is required for this red flag — the only situation where ordering CT is correct on a headache case.",
            },
            {
                "stage": "History",
                "q": "Patient describes 'zig-zaggy lights before the headache.' What is the correct clinical documentation term?",
                "options": [
                    "Visual aura",
                    "Scintillating scotomas",
                    "Photophobia",
                    "Optic neuritis",
                ],
                "correct": 1,
                "feedback": "Scintillating scotomas is the correct clinical term. 'Zig-zaggy lights' in lay language = scintillating scotomas in EHR documentation. Lay language loses points on the documentation rubric.",
            },
            {
                "stage": "Physical Exam",
                "q": "This is a clinical diagnosis — no red flags on SNOOP4 screen. What happens if you order a CT head?",
                "options": [
                    "It confirms the migraine diagnosis",
                    "It earns you extra points for thoroughness",
                    "It triggers the 'harmful to patient' flag — Tests score drops to 0%",
                    "It is required for any severe headache",
                ],
                "correct": 2,
                "feedback": "Critical trap. Ordering imaging on a classic migraine with normal exam and negative SNOOP4 = harmful flag. The iHuman platform will zero your Tests score for unnecessary radiation exposure.",
            },
            {
                "stage": "Physical Exam",
                "q": "Which medication is the correct acute treatment for this migraine case?",
                "options": [
                    "Ibuprofen 800mg PO TID",
                    "Sumatriptan 50mg PO at onset, may repeat ×1 after 2h",
                    "Acetaminophen 1g PO TID",
                    "Propranolol 40mg PO BID",
                ],
                "correct": 1,
                "feedback": "Sumatriptan 50mg is the correct iHuman answer for this case. Remember: max 200mg/day, ≤10 days/month, hold if pregnant. Propranolol is for prophylaxis, not acute.",
            },
        ],
    },
    "kennedy": {
        "title": "Kennedy Poole — ADHD, Predominantly Inattentive",
        "meta": "10-year-old female · NR 602 Week 4 · Chamberlain",
        "questions": [
            {
                "stage": "History",
                "q": "Patient is a 10-year-old child. Who should receive the history questions?",
                "options": [
                    "The child directly — she can answer for herself",
                    "Both child and parent equally",
                    "The parent — history questions for pediatric cases go to the caregiver",
                    "The school counselor",
                ],
                "correct": 2,
                "feedback": "Correct. For pediatric iHuman cases, history questions are directed to the parent/caregiver. The opener is 'How can I help her today?' — not 'How can I help you?' This is the pivotal communication question for pediatric cases.",
            },
            {
                "stage": "History",
                "q": "To meet DSM-5 criteria for ADHD inattentive, symptoms must be present in how many settings?",
                "options": [
                    "Only at school",
                    "At home only",
                    "At least 2 settings (home + school minimum)",
                    "All settings including social and recreational",
                ],
                "correct": 2,
                "feedback": "DSM-5 requires symptoms in ≥2 settings. Asking about both home AND school behavior is scored on this case. Single-setting attention problems point to environmental issues, not ADHD.",
            },
            {
                "stage": "Physical Exam",
                "q": "Before starting stimulant medication for ADHD, which test is required as baseline?",
                "options": [
                    "CBC and metabolic panel",
                    "Thyroid panel (TSH)",
                    "Electrocardiogram (ECG)",
                    "Brain MRI",
                ],
                "correct": 2,
                "feedback": "Baseline ECG is required before stimulant initiation. This is a scored item on the Kennedy Poole case — missing it costs management plan points. Stimulants can cause cardiac events in undiagnosed structural heart disease.",
            },
            {
                "stage": "Physical Exam",
                "q": "What is the correct starting dose of Methylphenidate ER for this 10-year-old?",
                "options": [
                    "5mg PO daily",
                    "18mg PO every morning",
                    "36mg PO every morning",
                    "10mg PO BID",
                ],
                "correct": 1,
                "feedback": "Methylphenidate ER 18mg every morning is the correct iHuman starting dose for this case. It is a Schedule II controlled substance — 0 refills on the prescription, parent must obtain new written script monthly.",
            },
        ],
    },
}


# ─── HTML helpers ─────────────────────────────────────────────────
def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def write_page(rel_path, body, title=None, description=None, page_class="", head_extra="", body_scripts=""):
    """Write a page to public/{rel_path}/index.html with the redesign shell.

    head_extra    — extra tags injected into <head> (e.g. page-specific data).
    body_scripts  — extra <script> tags injected before the core scripts
                    (e.g. React/Babel + the simulator .jsx on the sim page).
    """
    full_title = f"{title} · {SITE_NAME}" if title else f"{SITE_NAME} — Learn to think like a clinician"
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
<meta property="og:image" content="{esc(SITE_URL)}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(full_title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:url" content="{esc(canonical)}">
<meta name="twitter:image" content="{esc(SITE_URL)}/og-image.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,400;1,9..144,500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
{head_extra}
</head>
<body class="{esc(page_class)}">

{nav_html()}

{body}

{footer_html()}
{body_scripts}
<script src="/cpl.js" defer></script>
<script src="/cpl-checkout.js" defer></script>
<script src="/cpl-support.js" defer></script>

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


def footer_html():
    year = datetime.now(timezone.utc).year
    return f"""
<footer class="footer">
  <div class="footer-inner">
    <div>
      <div class="footer-brand">Clinical Performance Lab</div>
      <p class="footer-tagline">Learn to think like a clinician. Master iHuman. A clinical reasoning platform for nursing students — free simulator, free cheat sheets, and complete case guides built on 200+ verified submissions.</p>
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


def _lead_chip(lead_time):
    if lead_time == "same-day":
        return '<span class="case-tag lead-fast">⚡ Same-day</span>'
    if lead_time == "fast-build":
        return '<span class="case-tag">⌛ 24–48h</span>'
    return '<span class="case-tag">📋 On request</span>'


def case_card_html(case):
    """Render a case card (redesign markup) linking to the pretty case URL."""
    href = f"/case/{case['slug']}/"
    course = esc(case.get("course", ""))
    school = esc(case.get("school", ""))
    lead_time = case.get("lead_time", "same-day")
    # show up to two system tags, then the lead-time chip
    sys_tags = [t for t in case.get("tags", []) if t not in ("Adult",)][:2] or case.get("tags", [])[:2]
    tag_chips = "".join(f'<span class="case-tag">{esc(t)}</span>' for t in sys_tags)
    sub = " · ".join(p for p in [school, course] if p)
    return f"""
<a class="case-card" href="{href}" data-reveal>
  <h3>{esc(case['title'])}</h3>
  <p class="case-cc">{esc(case['chief_complaint'])}</p>
  <div class="case-meta">{tag_chips}{_lead_chip(lead_time)}</div>
  <p class="case-sub">{sub}</p>
  <div class="case-cta"><span>Preview case</span><span aria-hidden="true">→</span></div>
</a>
"""


# ─── PAGE: Home ───────────────────────────────────────────────────
def build_home():
    cheat_cards = "".join(cheat_sheet_card_html(cs) for cs in CHEAT_SHEETS)
    # Homepage shows only same-day cases — the ones with complete verified guides
    featured = by_lead_time("same-day")
    case_cards = "".join(case_card_html(c) for c in featured)

    total_cases = len(CASES)
    same_day_count = len(featured)
    build_count = total_cases - same_day_count

    # Pricing tiers shown on home (single / 3-bundle featured / 5-bundle)
    home_tiers = [
        ("Single guide", 150, "", "One complete case, delivered same day."),
        ("3-case bundle", 390, "Save $60", "Mix any 3 cases. Great for a busy mid-term."),
        ("5-case bundle", 540, "Save $210", "Best value for a full term of submissions."),
    ]
    pricing_html = ""
    for i, (label, price, saves, blurb) in enumerate(home_tiers):
        feat = " featured" if i == 1 else ""
        delay = f' data-reveal-delay="{i*90}"' if i else ""
        pricing_html += f"""
      <div class="tier{feat}" data-reveal{delay}>
        <div class="tier-label">{esc(label)}</div>
        <div class="tier-price"><span class="cur">$</span>{price}</div>
        <div class="tier-saves">{saves or '&nbsp;'}</div>
        <p class="tier-blurb">{esc(blurb)}</p>
        <a href="/cases/" class="btn btn-primary">Browse cases</a>
      </div>"""

    body = f"""
<section class="hero">
  <div class="container">
    <div class="hero-panel">
      <div class="hero-content">
        <span class="eyebrow on-dark" data-reveal><span class="dot"></span>Clinical reasoning · made visible</span>
        <h1 data-reveal data-reveal-delay="60">Learn to think like a clinician. <span class="italic-accent">Master iHuman.</span></h1>
        <p class="hero-sub" data-reveal data-reveal-delay="120">
          iHuman scores you against a rubric you never see. CPL makes that invisible logic visible and teachable — the question hierarchies, the must-not-miss diagnoses, the harmful-flag traps. Practice free. Master the patterns. Submit with confidence.
        </p>
        <div class="hero-ctas" data-reveal data-reveal-delay="180">
          <a href="/simulator/" class="btn btn-lime btn-lg">Try the free simulator →</a>
          <a href="/sample-guide/" class="btn btn-ghost-dark btn-lg">See a sample guide</a>
        </div>
        <p class="hero-tertiary" data-reveal data-reveal-delay="220">Free simulator and cheat sheets — <a href="#free">no card required →</a></p>
        <div class="hero-trust" data-reveal data-reveal-delay="280">
          <span class="t"><b><span data-counter="200" data-counter-suffix="+">0</span></b>verified submissions analyzed</span>
          <span class="t"><b><span data-counter="{total_cases}">0</span></b>cases catalogued</span>
          <span class="t"><b>Same-day</b>guide delivery</span>
        </div>
      </div>

      <div class="rubric" data-decode data-reveal data-reveal-delay="140">
        <div class="rubric-title"><span>iHuman scoring · reconstructed</span><span class="badge">DECODED</span></div>
        <div class="rubric-case">Bebe Babbitt — Migraine with aura</div>
        <div class="rubric-row"><div class="rubric-check">✓</div><div class="rubric-text">Screen for aura &amp; visual prodrome<small>Pivotal differentiator</small></div><div class="rubric-pts">+4</div></div>
        <div class="rubric-row"><div class="rubric-check">✓</div><div class="rubric-text">Rule out thunderclap onset<small>Must-not-miss: subarachnoid hemorrhage</small></div><div class="rubric-pts">+5</div></div>
        <div class="rubric-row locked"><div class="rubric-check">✓</div><div class="rubric-text">Photophobia &amp; phonophobia history<small>Supporting criteria</small></div><div class="rubric-pts">+2</div></div>
        <div class="rubric-row locked"><div class="rubric-check">✓</div><div class="rubric-text">Avoid opioid-first management<small>Harmful-flag trap</small></div><div class="rubric-pts">+3</div></div>
      </div>
    </div>
  </div>
</section>

<section class="section" id="how">
  <div class="container">
    <div class="section-head center" data-reveal>
      <span class="eyebrow"><span class="dot"></span>How CPL works</span>
      <h2>Learn the reasoning first. Buy a guide only when it counts.</h2>
      <p>Everything you need to <em>learn</em> is free. The graded submissions are where we help most — and where we earn our keep.</p>
    </div>
    <div class="steps">
      <div class="step" data-reveal>
        <div class="step-num">01</div><span class="step-free">Free</span>
        <h3>Practice with the simulator</h3>
        <p>Click through realistic iHuman stages — history, PE, DDx, plan. See which choices score, which lose points, and exactly why. Reasoning you can use on any case.</p>
        <a href="/simulator/" class="link-arrow">Open the simulator →</a>
      </div>
      <div class="step" data-reveal data-reveal-delay="90">
        <div class="step-num">02</div><span class="step-free">Free</span>
        <h3>Master the patterns with cheat sheets</h3>
        <p>Four PDFs — history, physical exam, differential diagnosis, and management plan. The universal patterns that transfer across every iHuman case template.</p>
        <a href="#free" class="link-arrow">Get the cheat sheets →</a>
      </div>
      <div class="step" data-reveal data-reveal-delay="180">
        <div class="step-num">03</div><span class="step-paid">Premium</span>
        <h3>Get the guide when it's graded</h3>
        <p>For the cases that count: submission-ready guides with every history question, PE finding, DDx ranking, and management call mapped to the rubric. Same-day delivery.</p>
        <a href="/cases/" class="link-arrow">Browse {total_cases} cases →</a>
      </div>
    </div>
  </div>
</section>

<section class="section bg-cream2" id="free">
  <div class="container">
    <div class="section-head" data-reveal>
      <span class="eyebrow"><span class="dot"></span>Start free</span>
      <h2>Free clinical reasoning frameworks</h2>
      <p>Four PDFs covering the universal patterns CPL identified across 200+ verified iHuman submissions — the reasoning that transfers to every case template, yours and ours.</p>
    </div>
    <form data-capture data-reveal data-reveal-delay="80">
      <div class="resource-grid">
        {cheat_cards}
      </div>
      <div class="capture">
        <div class="capture-inner">
          <div class="capture-eyebrow">Email-delivered · free</div>
          <h3>Where should we send your selections?</h3>
          <p>Pick at least one cheat sheet above. We'll confirm by email and send the PDFs — no spam, unsubscribe any time.</p>
          <div class="capture-row">
            <input type="email" name="email" placeholder="you@school.edu" required autocomplete="email">
            <button type="submit" class="btn btn-lime btn-lg">Send the PDFs →</button>
          </div>
          <p class="capture-fine">We use your email only to deliver requested resources and a short clinical-insight follow-up.</p>
          <p class="form-success" data-capture-msg style="display:none; margin-top:14px; color:var(--lime-400); font-size:.92rem;"></p>
        </div>
      </div>
    </form>
  </div>
</section>

<section class="section" id="cases">
  <div class="container">
    <div class="section-head" data-reveal>
      <span class="eyebrow"><span class="dot"></span>Case catalog</span>
      <h2>Guides built from verified scoring data</h2>
      <p>Every CPL guide maps the actual iHuman rubric — which history questions score, which PE items count, which DDx rankings are platform-verified, which management choices avoid harmful-flag deductions. {same_day_count} ship same day; {build_count} more build within 24–48h.</p>
    </div>
    <div class="case-grid">
      {case_cards}
    </div>
    <div style="text-align:center; margin-top:36px;" data-reveal>
      <a href="/cases/" class="btn btn-ghost">See all {total_cases} cases →</a>
    </div>
  </div>
</section>

<section class="section bg-cream2" id="pricing">
  <div class="container">
    <div class="section-head center" data-reveal>
      <span class="eyebrow"><span class="dot"></span>Pricing</span>
      <h2>When you need the complete guide</h2>
      <p>The simulator and cheat sheets are free forever. When a case counts toward your grade, complete guides ship same day. Bundles mix and match. New here? Code <strong>CPLFIRST15</strong> takes 15% off your first single case.</p>
    </div>
    <div class="pricing-grid">{pricing_html}
    </div>
  </div>
</section>
"""

    write_page("", body,
               title=None,
               description="Learn to think like a clinician and master iHuman. Free clinical reasoning simulator, free cheat sheets, and complete case guides built from verified student submissions.",
               page_class="home")


# ─── PAGE: Free Resources (dedicated lead magnet hub) ─────────────
def build_free_resources():
    # Cheat-sheet cards (preselected) for the redesign capture form
    def card(cs):
        return f'''
        <label class="resource-card selected" data-id="{esc(cs['id'])}">
          <input type="checkbox" name="volumes" value="{esc(cs['id'])}" style="display:none" checked>
          <span class="resource-stage">Vol {esc(cs['vol'])} · Stage {esc(cs['vol'])} of IV</span>
          <h3>{esc(cs['title'])}</h3>
          <p>{volume_description(cs['id'])}</p>
          <div class="resource-meta"><span>{cs['pages']} pages</span><span>·</span><span>~10 min</span></div>
        </label>'''
    cheat_cards = "".join(card(cs) for cs in CHEAT_SHEETS)

    body = f"""
<section class="hero">
  <div class="container">
    <div class="hero-panel" style="grid-template-columns:1fr;">
      <div class="hero-content" style="max-width:none;">
        <span class="eyebrow on-dark" data-reveal><span class="dot"></span>Free forever · no card</span>
        <h1 data-reveal data-reveal-delay="60">Four frameworks that work on <span class="italic-accent">every</span> case.</h1>
        <p class="hero-sub" data-reveal data-reveal-delay="120" style="max-width:60ch;">We analyzed 200+ verified iHuman submissions and pulled out the patterns that repeat across every case template — the questions that always score, the exam items that always count, the differentials faculty expect, and the management traps to avoid. It's yours, free.</p>
        <div class="hero-trust" data-reveal data-reveal-delay="200" style="border-top:none; padding-top:0; margin-top:8px;">
          <span class="t"><b>4</b>PDF volumes</span>
          <span class="t"><b>34</b>pages total</span>
          <span class="t"><b>~40 min</b>to read all four</span>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section" id="get" style="padding-top:56px;">
  <div class="container">
    <div class="section-head" data-reveal>
      <span class="eyebrow"><span class="dot"></span>Pick your volumes</span>
      <h2>Choose what you need — or grab all four</h2>
      <p>Each maps to one stage of the iHuman case. Select the ones you want and we'll email the PDFs after a quick confirmation.</p>
    </div>
    <form data-capture data-reveal data-reveal-delay="80">
      <div class="resource-grid">
        {cheat_cards}
      </div>
      <div class="capture">
        <div class="capture-inner">
          <div class="capture-eyebrow">Email-delivered · free</div>
          <h3>Where should we send them?</h3>
          <p>We'll send a one-click confirmation, then the PDFs. No spam — unsubscribe any time.</p>
          <div class="capture-row">
            <input type="email" name="email" placeholder="you@school.edu" required autocomplete="email">
            <button type="submit" class="btn btn-lime btn-lg">Send my cheat sheets →</button>
          </div>
          <p class="capture-fine">We use your email only to deliver requested resources and a short clinical-insight follow-up.</p>
          <p class="form-success" data-capture-msg style="display:none; margin-top:14px; color:var(--lime-400); font-size:.92rem;"></p>
        </div>
      </div>
    </form>
  </div>
</section>

<section class="section bg-cream2">
  <div class="container">
    <div class="steps">
      <div class="step" data-reveal>
        <div class="step-num">①</div>
        <h3>Because learning should be free</h3>
        <p>The reasoning patterns transfer to every case you'll ever see. We'd rather you learn them than gate them — that's the mission.</p>
      </div>
      <div class="step" data-reveal data-reveal-delay="90">
        <div class="step-num">②</div>
        <h3>Built from real scoring data</h3>
        <p>Every framework comes from 200+ verified submissions — not guesswork. You're learning what the platform actually rewards.</p>
      </div>
      <div class="step" data-reveal data-reveal-delay="180">
        <div class="step-num">③</div>
        <h3>The guides are there when it counts</h3>
        <p>When a specific case is graded and you're short on time, our complete case guides pick up where the frameworks leave off.</p>
        <a href="/cases/" class="link-arrow">Browse the catalog →</a>
      </div>
    </div>
  </div>
</section>
"""

    write_page("free-resources", body,
               title="Free Cheat Sheets",
               description="Four free PDFs covering the universal patterns that score on every iHuman case. Email-delivered, no card required.",
               page_class="free-resources")


# ─── PAGE: Cases catalog ──────────────────────────────────────────
def _short_course(course):
    """Compact a course string for catalog cards (e.g. 'NR 509 Week 6' → 'NR 509 · Wk 6')."""
    import re as _re
    c = (course or "").strip()
    c = _re.sub(r'\bWeek\s*(\d+)', r'Wk \1', c)
    return c


def build_catalog():
    import json as _json
    all_cases = CASES
    total = len(all_cases)
    same_day_n = sum(1 for c in all_cases if c.get("lead_time") == "same-day")

    # Full catalog injected for the client-side renderer (cpl-catalog.js).
    cases_js = _json.dumps([
        {
            "t": c["title"],
            "cc": c.get("chief_complaint", ""),
            "dx": c.get("diagnosis", ""),
            "sys": c.get("tags", []),
            "school": c.get("school", "") or "Multiple Institutions",
            "course": _short_course(c.get("course", "")),
            "lead": c.get("lead_time", "same-day"),
            "href": f"/case/{c['slug']}/",
        }
        for c in all_cases
    ], ensure_ascii=False)

    body = """
<section class="cat-hero">
  <div class="container">
    <div class="cat-hero-panel">
      <div class="cat-hero-inner">
        <span class="eyebrow on-dark"><span class="dot"></span>Case catalog</span>
        <h1>Find your case. <span class="italic-accent">See exactly what scores.</span></h1>
        <p>Every guide is built from verified scoring data and mapped to the iHuman rubric. Search by patient, diagnosis, or course — iHuman rotates names, so each guide covers every alias of its template.</p>
        <div class="cat-search-big">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" id="catSearch" placeholder="Search by name, diagnosis, or course…" autocomplete="off">
          <button class="cat-search-clear" id="catSearchClear" aria-label="Clear search" style="display:none;">×</button>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="cat-body" id="catalog">
  <div class="container">
    <div class="cat-filters">
      <div class="filter-group"><span class="filter-label">System</span><div class="filter-chips" id="fSystem"></div></div>
      <div class="filter-group"><span class="filter-label">School</span><div class="filter-chips" id="fSchool"></div></div>
      <div class="filter-group"><span class="filter-label">Lead time</span><div class="filter-chips" id="fLead"></div></div>
      <button class="filter-clear" id="filterClear">Clear filters ×</button>
    </div>
    <div class="cat-count" id="catCount">Showing all cases</div>
    <div class="case-grid" id="caseGrid"></div>
    <div class="cat-empty" id="catEmpty">
      <h3>No cases match those filters</h3>
      <p>Try removing a filter — or message support and we'll confirm whether your case is in the pipeline.</p>
    </div>
  </div>
</section>

<div class="bundle-bar" id="bundleBar">
  <div class="bundle-bar-inner">
    <div class="bundle-info">
      <span class="bc" data-bundle-count>0 cases</span>
      <span class="bt" data-bundle-total>$0</span>
      <span class="bs" data-bundle-save>&nbsp;</span>
    </div>
    <div class="bundle-list" data-bundle-list></div>
    <button class="btn btn-lime" data-bundle-order>Order this bundle →</button>
  </div>
</div>
"""

    body_scripts = (
        f'<script>window.CPL_CASES = {cases_js};</script>\n'
        f'<script src="/cpl-catalog.js" defer></script>'
    )

    write_page("cases", body,
               title="Case Catalog",
               description=(f"Browse {total} iHuman case guides across NR509, NR511, NR602, "
                            f"NURS 6512, NRNP 6531/6541/6552/6568 and Kaplan programs. "
                            f"{same_day_n} ship same day."),
               page_class="catalog",
               body_scripts=body_scripts)


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


def _render_preview_gallery(case, preview):
    """Render the redesign guide-preview panel (.gallery). Real previews show
    section pages (clear) + locked teasers; sample previews show watermarked
    format excerpts with an honest 'not your case' note. Both end in an
    unlock/order bar."""
    if not preview:
        return ''
    slug = case['slug']
    total = preview['total_pages']
    title = esc(case['title'])
    order_attr = esc(case['title'])

    if not preview['is_sample']:
        labels = preview['section_labels']
        clear_count = preview['clear_count']
        locked_count = preview['locked_count']
        gpages = ''
        for n in preview['clear_pages']:
            label = esc(labels.get(str(n), f"Page {n}"))
            gpages += f'''
            <div class="gpage clear" data-lightbox="/previews/{slug}/page_{n}.png">
              <div class="gpage-frame"><span class="gpage-tag sample">Sample</span><img src="/previews/{slug}/page_{n}.png" alt="Page {n} — {label}" loading="lazy"></div>
              <div class="gpage-label"><b>Page {n}</b>{label}</div>
            </div>'''
        for n in preview['stack_blurred']:
            gpages += f'''
            <div class="gpage locked">
              <div class="gpage-frame"><span class="gpage-tag locked">Locked</span><img src="/previews/{slug}/page_{n}_blurred.png" alt="Locked page" loading="lazy"></div>
              <div class="gpage-label"><b>Page {n}</b>Locked</div>
            </div>'''
        intro = (f"Actual pages from your {title} guide — one from each section. "
                 f"Click a sample to read it full size. The remaining {locked_count} "
                 f"unlock when you order.")
        return f'''
        <div class="panel" data-reveal style="padding-bottom:28px;">
          <div class="panel-eyebrow">Real guide preview</div>
          <h3>See the real pages. {clear_count} of {total} are on us.</h3>
          <p style="color:var(--muted); font-size:.95rem; margin:0 0 18px;">{intro}</p>
          <div class="gallery">{gpages}
          </div>
          <div class="unlock-bar">
            <div class="ub-text"><b>{locked_count} more pages — locked</b><small>Full history bank, PE checklist, ranked DDx, EHR docs, SOAP note &amp; 6-part management plan</small></div>
            <button class="btn btn-lime" data-order="{order_attr}" data-price="150">Unlock the complete guide — $150</button>
          </div>
        </div>'''

    # Sample preview — watermarked format excerpts from a different completed case
    source = preview['sample_source']
    source_title = esc(preview['source_title'])
    sample_labels = [(1, "Cover &amp; overview"), (2, "History bank"),
                     (3, "PE checklist"), (4, "Tests &amp; DDx")]
    gpages = ''
    for idx, label in sample_labels:
        gpages += f'''
            <div class="gpage clear" data-lightbox="/previews/_watermarked/{source}/sample_{idx}.png">
              <div class="gpage-frame"><span class="gpage-tag sample">Example</span><img src="/previews/_watermarked/{source}/sample_{idx}.png" alt="Example {label}" loading="lazy"></div>
              <div class="gpage-label"><b>Example</b>{label}</div>
            </div>'''
    return f'''
        <div class="panel" data-reveal style="padding-bottom:28px;">
          <div class="panel-eyebrow">Guide format preview</div>
          <h3>This isn't your case yet — here's our format</h3>
          <p style="color:var(--muted); font-size:.95rem; margin:0 0 18px;">We haven't built {title} yet. These are stamped excerpts from a completed guide ({source_title}) so you can see the exact structure. Your guide will be written specifically for {title} and follow this same format.</p>
          <div class="gallery">{gpages}
          </div>
          <div class="unlock-bar">
            <div class="ub-text"><b>Order {title} and get your own complete guide</b><small>Built specifically for {title} — history bank, PE checklist, ranked DDx, EHR docs, SOAP note &amp; management plan</small></div>
            <button class="btn btn-lime" data-order="{order_attr}" data-price="150">Order this guide — $150</button>
          </div>
        </div>'''


def build_case_preview(case):
    title = esc(case['title'])
    course = esc(case.get('course', ''))
    school = esc(case.get('school', ''))
    patient = esc(case.get('patient_short', ''))
    cc = esc(case.get('chief_complaint', ''))
    diagnosis = esc(case.get('diagnosis', ''))
    must_not_miss = esc(case.get('must_not_miss', '—'))
    tags = case.get('tags', [])
    primary_sys = esc(tags[0]) if tags else 'Clinical'
    patient_name = esc(case['title'].split('—')[0].split('-')[0].strip())
    lead_time = case.get('lead_time', 'same-day')
    badge = ('⚡ Same-day delivery' if lead_time == 'same-day'
             else '⌛ 24–48h build' if lead_time == 'fast-build'
             else '📋 On request')
    order_attr = esc(case['title'])
    order_subject = esc(f"CPL Order - {case['title']}").replace(' ', '%20')

    # Scoring traps
    traps_html = "".join(
        f'<div class="trap" data-reveal data-reveal-delay="{i*60}"><span class="trap-ico">⚠</span><div class="trap-body">{esc(t)}</div></div>'
        for i, t in enumerate(case.get('key_scoring_traps', []))
    ) or '<p style="color:var(--muted); font-size:.95rem; margin:0;">Full scoring strategy is mapped in the delivered guide.</p>'

    # Guide stats + contents (use real counts when present)
    preview = get_preview_data(case['slug'])
    total_pages = preview['total_pages'] if preview else None
    hpi = case.get('preview_hpi_count')
    pe = case.get('preview_pe_count')
    dx = case.get('preview_dx_count')
    stats = []
    if hpi: stats.append((hpi, 'History Qs'))
    if pe: stats.append((pe, 'PE items'))
    if dx: stats.append((dx, 'Ranked DDx'))
    if total_pages: stats.append((total_pages, 'Pages'))
    stats_html = "".join(
        f'<div class="gstat"><b>{v}</b><span>{esc(l)}</span></div>' for v, l in stats
    )
    stats_block = f'<div class="guide-stats">{stats_html}</div>' if stats_html else ''
    guide_heading = (f"{total_pages} pages, mapped to the rubric" if total_pages
                     else "Mapped to the iHuman rubric")
    if hpi and pe and dx:
        contents_top = (
            f'<li><span><b>{hpi}</b> history questions with verbatim patient responses</span></li>'
            f'<li><span><b>{pe}</b> physical exam items with documentation language</span></li>'
            f'<li><span><b>{dx}</b> ranked differentials (platform-verified names)</span></li>'
        )
    else:
        contents_top = (
            '<li><span>Full history question bank with verbatim patient responses</span></li>'
            '<li><span>Physical exam checklist with documentation language</span></li>'
            '<li><span>Ranked differentials with platform-verified names</span></li>'
        )

    gallery_html = _render_preview_gallery(case, preview)

    # Aliases panel
    aliases_html = ''
    if case.get('aliases') and len(case['aliases']) > 1:
        chips = "".join(f'<span class="alias-chip">{esc(a)}</span>' for a in case['aliases'])
        aliases_html = f'''
        <div class="panel" data-reveal style="margin-bottom:0;">
          <div class="panel-eyebrow">Same case, different patient name</div>
          <h3>This guide covers every alias</h3>
          <p style="color:var(--muted); font-size:.95rem; margin:0 0 6px;">iHuman rotates the patient name across course sections. This template's known aliases:</p>
          <div class="alias-chips">{chips}</div>
          <p style="color:var(--muted); font-size:.86rem; margin:0;">Tell us which alias you have at checkout — we customize the delivered guide to your exact patient.</p>
        </div>'''

    body = f"""
<section class="cp-hero">
  <div class="container">
    <div class="cp-hero-panel">
      <div class="cp-breadcrumb"><a href="/cases/">Case catalog</a> &nbsp;/&nbsp; {primary_sys} &nbsp;/&nbsp; {patient_name}</div>
      <div class="cp-eyebrow">
        <span class="course">Case preview · {course}</span>
        <span class="cp-badge">{badge}</span>
      </div>
      <h1 data-reveal>{title}</h1>
      <p class="cp-cc" data-reveal data-reveal-delay="80">"{cc}"</p>
      <div class="cp-meta" data-reveal data-reveal-delay="140">
        <span class="m">Patient<b>{patient or '—'}</b></span>
        <span class="m">Course<b>{course or '—'}</b></span>
        <span class="m">School<b>{school or '—'}</b></span>
        <span class="m">System<b>{primary_sys}</b></span>
      </div>
    </div>
  </div>
</section>

<section class="cp-body">
  <div class="container">
    <div class="cp-grid">
      <div class="cp-main">

        <div class="panel dx-row" data-reveal>
          <div>
            <div class="panel-eyebrow">Final diagnosis</div>
            <p class="dx-final">{diagnosis}</p>
          </div>
          <div>
            <div class="panel-eyebrow">Must-not-miss</div>
            <p style="margin:0; color:var(--ink-2); font-size:.95rem; line-height:1.45;">{must_not_miss}</p>
          </div>
        </div>

        <div class="panel" data-reveal>
          <div class="panel-eyebrow">What's in the guide</div>
          <h3>{guide_heading}</h3>
          {stats_block}
          <ul class="guide-contents">
            {contents_top}
            <li><span>Full EHR documentation — Subjective + Objective</span></li>
            <li><span>Tests Ordered, each with scoring rationale</span></li>
            <li><span>Complete 6-part management plan</span></li>
            <li><span>SOAP note, ready to submit</span></li>
            <li><span>APA-formatted scholarly references</span></li>
          </ul>
        </div>

        <div class="panel" data-reveal>
          <div class="panel-eyebrow">Scoring logic, decoded</div>
          <h3>The traps that quietly cost points</h3>
          <p style="color:var(--muted); font-size:.95rem; margin:0 0 18px;">These are the point-loss patterns iHuman never tells you about. We map every one for this case.</p>
          {traps_html}
        </div>

        {gallery_html}

        {aliases_html}
      </div>

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
        </div>

        <div class="side-free">
          <div class="panel-eyebrow">First time here?</div>
          <h4>Get the free cheat sheets first</h4>
          <p>Four PDFs that work across every iHuman case. Email-delivered, no card.</p>
          <form data-capture>
            <input type="email" name="email" placeholder="you@school.edu" required autocomplete="email" style="width:100%; padding:12px 16px; border-radius:999px; border:1.5px solid var(--border-strong); font-family:var(--font-body); font-size:.92rem; background:#fff; margin-bottom:9px;">
            <button type="submit" class="btn btn-primary" style="width:100%;">Get all 4 cheat sheets →</button>
            <p class="form-success" data-capture-msg style="display:none; margin:12px 0 0; color:var(--teal-700); font-size:.85rem;"></p>
          </form>
        </div>
      </aside>
    </div>
  </div>
</section>
"""

    write_page(f"case/{case['slug']}", body,
               title=case['title'],
               description=f"{case['title']} — {case['chief_complaint']}. iHuman case guide for {case.get('course','')}. Built from verified student submissions, mapped to the scoring rubric.",
               page_class="case-preview")


# ─── PAGE: Confirm (double opt-in landing) ────────────────────────
def build_confirm():
    body = """
<section class="status-page">
  <div class="container">
    <div class="status-card" data-reveal>
      <div class="status-badge" id="confirmBadge">…</div>
      <h1 id="confirmTitle">Confirming your email…</h1>
      <p id="confirmSub">Validating your confirmation link. This takes a few seconds.</p>
      <div id="confirmResult" class="status-ctas"></div>
    </div>
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
      var badge = document.getElementById('confirmBadge');
      if (badge) badge.textContent = '✓';
      titleEl.textContent = "Your PDFs are on the way!";
      subEl.textContent = "Check your inbox in a minute. We've also scheduled a short follow-up over the next week with a clinical insight you can use.";
      resultEl.innerHTML = '<a href="/cases/" class="btn btn-lime">Browse case catalog →</a><a href="/simulator/" class="btn btn-ghost">Open the simulator</a>';
    } else {
      titleEl.textContent = "Couldn't confirm";
      subEl.textContent = data.error || "This link is invalid or expired. Try requesting a new one from the free resources page.";
      resultEl.innerHTML = '<a href="/free-resources/" class="btn btn-primary">Get a new link</a>';
    }
  } catch (e) {
    titleEl.textContent = "Something went wrong";
    subEl.textContent = "We couldn't reach the confirmation service. Try again in a minute or email support@clinicalperformancelab.com.";
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
<section class="status-page">
  <div class="container">
    <div class="status-card" data-reveal>
      <div class="status-badge">✉</div>
      <h1>One quick step.</h1>
      <p>We've sent a confirmation link to your email. Click it within 24 hours and your PDFs land in your inbox immediately.</p>
      <p style="font-size:.9rem;">Don't see it? Check the spam folder — the sender is <strong>onboarding@resend.dev</strong>.</p>
      <div class="status-ctas">
        <a href="/simulator/" class="btn btn-lime">Try the simulator while you wait</a>
        <a href="/cases/" class="btn btn-ghost">Browse cases</a>
      </div>
    </div>
  </div>
</section>
"""
    write_page("thank-you", body,
               title="Check your inbox",
               description="Confirmation link sent. Click it to get your CPL cheat sheets.",
               page_class="thank-you")


# ─── PAGE: Simulator ──────────────────────────────────────────────
def build_simulator():
    """Build the interactive case simulator page (React app from cpl-simulator.jsx)."""
    body = '''
<section class="section-tight" style="padding-top:48px;">
  <div class="container-narrow" style="text-align:center;">
    <span class="eyebrow"><span class="dot"></span>Free · no sign-up</span>
    <h1 style="margin:16px 0 12px; font-size:clamp(2rem,4vw,3rem);">Practice the reasoning. <span class="italic-accent" style="color:var(--teal-700);">See every point.</span></h1>
    <p style="color:var(--muted); font-size:1.08rem; max-width:54ch; margin:0 auto;">Work a real iHuman case the way it's graded — history, exam, differential, and plan. Make your picks, then watch the scoring logic light up: what earns points, what's filler, and which choices are harmful-flag traps.</p>
  </div>
</section>

<section class="sim-wrap" style="padding-top:8px;">
  <div class="container">
    <div id="sim-root"></div>
    <p style="text-align:center; color:var(--muted); font-size:.85rem; margin-top:18px;">This is a teaching simulation built from verified scoring patterns — it's not affiliated with iHuman. Always follow your school's academic policies.</p>
  </div>
</section>
'''
    sim_scripts = (
        '<script src="https://unpkg.com/react@18.3.1/umd/react.development.js" crossorigin="anonymous"></script>\n'
        '<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" crossorigin="anonymous"></script>\n'
        '<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" crossorigin="anonymous"></script>\n'
        '<script type="text/babel" src="/cpl-simulator.jsx"></script>'
    )
    write_page("simulator", body,
               title="Case Simulator",
               description="Practice clinical reasoning on a real iHuman case pattern — free interactive simulator with scored feedback, no signup.",
               page_class="simulator",
               body_scripts=sim_scripts)
    return


# ─── PAGE: Sample guide (marketing demo of a full guide) ──────────
def build_sample_guide():
    """Build the /sample-guide/ page — anatomy of a complete guide (Bebe Babbitt)."""
    total = len(CASES)
    pv = "/previews/bebe-babbitt-migraine"
    body = f'''
<section class="cat-hero">
  <div class="container">
    <div class="cat-hero-panel">
      <div class="cat-hero-inner">
        <span class="eyebrow on-dark"><span class="dot"></span>Anatomy of a guide</span>
        <h1>What you actually <span class="italic-accent">get.</span></h1>
        <p>A complete CPL guide is a 25-page, submission-ready document — every history question, exam finding, differential, and management call mapped to how the case scores. Here's the full Bebe Babbitt guide, section by section.</p>
        <div class="hero-trust" style="border-top:none; padding-top:0; margin-top:4px;">
          <span class="t"><b>25</b>pages</span>
          <span class="t"><b>4</b>scored stages</span>
          <span class="t"><b>Word + PDF</b>same-day</span>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section" style="padding-top:48px;">
  <div class="container">
    <div class="section-head" data-reveal>
      <span class="eyebrow"><span class="dot"></span>Section by section</span>
      <h2>Every page earns its place</h2>
      <p>Click any page to read it full-size. These are real pages from a delivered guide.</p>
    </div>

    <div class="anatomy-row" data-reveal>
      <div class="anatomy-img" data-lightbox="{pv}/page_1.png">
        <div class="a-frame"><img src="{pv}/page_1.png" alt="Cover and case overview page"></div>
        <span class="a-page">Page 1</span>
      </div>
      <div class="anatomy-text">
        <span class="anatomy-num">01 · Cover &amp; overview</span>
        <h3>The case at a glance</h3>
        <p>Patient, chief complaint, course and week, the final diagnosis, and the must-not-miss conditions — so you know where the case is going before you start, and how the points are distributed across the four stages.</p>
        <div class="anatomy-scores"><span class="as">Diagnosis</span><span class="as">Must-not-miss</span><span class="as">Score map</span></div>
      </div>
    </div>

    <div class="anatomy-row" data-reveal>
      <div class="anatomy-img" data-lightbox="{pv}/page_6.png">
        <div class="a-frame"><img src="{pv}/page_6.png" alt="History question bank page"></div>
        <span class="a-page">Page 6</span>
      </div>
      <div class="anatomy-text">
        <span class="anatomy-num">02 · History — verbatim question bank</span>
        <h3>Every scored question, with the patient's exact words</h3>
        <p>32 history questions, each marked as performed, with the verbatim patient response and the clinical term to document. History is ~40% of your score — this is where most points are won or lost.</p>
        <div class="anatomy-scores"><span class="as">32 questions</span><span class="as">Verbatim responses</span><span class="as">~40% of score</span></div>
      </div>
    </div>

    <div class="anatomy-row" data-reveal>
      <div class="anatomy-img" data-lightbox="{pv}/page_10.png">
        <div class="a-frame"><img src="{pv}/page_10.png" alt="Physical exam checklist page"></div>
        <span class="a-page">Page 10</span>
      </div>
      <div class="anatomy-text">
        <span class="anatomy-num">03 · Physical exam — complete checklist</span>
        <h3>What to examine, and the words that score</h3>
        <p>24 exam items with the exact documentation language faculty look for. Includes the items that score on every case and the ones specific to this presentation — plus what <em>not</em> to do.</p>
        <div class="anatomy-scores"><span class="as">24 PE items</span><span class="as">Documentation language</span><span class="as">Trap warnings</span></div>
      </div>
    </div>

    <div class="anatomy-row" data-reveal>
      <div class="anatomy-img" data-lightbox="{pv}/page_17.png">
        <div class="a-frame"><img src="{pv}/page_17.png" alt="Tests and differentials page"></div>
        <span class="a-page">Page 17</span>
      </div>
      <div class="anatomy-text">
        <span class="anatomy-num">04 · Diagnosis — tests &amp; differentials</span>
        <h3>Ranked differentials and the tests that count</h3>
        <p>Platform-verified differential names in ranked order, the tests to order (and the ones that trigger harmful-flag deductions), and the 2–3 sentence problem statement faculty expect.</p>
        <div class="anatomy-scores"><span class="as">4 ranked DDx</span><span class="as">Tests + rationale</span><span class="as">Problem statement</span></div>
      </div>
    </div>
  </div>
</section>

<section class="section bg-cream2">
  <div class="container">
    <div class="section-head center" data-reveal>
      <span class="eyebrow"><span class="dot"></span>And the rest</span>
      <h2>Plus the parts that finish the submission</h2>
    </div>
    <div class="steps" data-reveal>
      <div class="step"><div class="step-num">EHR</div><h3>Full documentation</h3><p>Subjective + Objective sections, ready to paste into the iHuman EHR.</p></div>
      <div class="step"><div class="step-num">SOAP</div><h3>SOAP note</h3><p>A complete, submission-ready SOAP note in the structure faculty grade against.</p></div>
      <div class="step"><div class="step-num">APA</div><h3>Scholarly references</h3><p>APA-formatted references and the 6-part management plan, fully written out.</p></div>
    </div>
    <div style="text-align:center; margin-top:40px;" data-reveal>
      <a class="btn btn-primary btn-lg" data-order="Bebe Babbitt — Migraine with Aura" data-price="150">Get this guide — $150</a>
      <a class="btn btn-ghost btn-lg" href="/cases/" style="margin-left:10px;">Browse all {total} cases</a>
      <p style="color:var(--muted); font-size:.85rem; margin-top:14px;">Code <strong style="color:var(--teal-700);">CPLFIRST15</strong> takes 15% off your first single case.</p>
    </div>
  </div>
</section>
'''
    write_page("sample-guide", body,
               title="See a Sample CPL Case Guide",
               description="See exactly what a CPL iHuman case guide contains — real pages from the Bebe Babbitt migraine guide: history bank, physical exam, differentials, and management plan.",
               page_class="sample-guide")


# ─── PAGE: About ──────────────────────────────────────────────────
def build_about():
    body = """
<section class="hero">
  <div class="container">
    <div class="hero-panel" style="grid-template-columns:1fr;">
      <div class="hero-content" style="max-width:none;">
        <span class="eyebrow on-dark" data-reveal><span class="dot"></span>Our mission</span>
        <h1 data-reveal data-reveal-delay="60" style="max-width:20ch;">Make the invisible <span class="italic-accent">visible.</span></h1>
        <p class="hero-sub" data-reveal data-reveal-delay="120" style="max-width:60ch;">iHuman scores nursing students against a rubric they never see. That opacity breeds anxiety and rewards memorization over reasoning. CPL exists to change that — to turn a black-box assessment into something you can actually learn from.</p>
      </div>
    </div>
  </div>
</section>

<section class="section" style="padding-top:56px;">
  <div class="container">
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:48px; align-items:center;" class="about-split">
      <div data-reveal>
        <p class="mission-quote">A grade shouldn't depend on <span class="hl">guessing</span> what the software wants.</p>
      </div>
      <div data-reveal data-reveal-delay="90">
        <p style="font-size:1.05rem; color:var(--ink-2); line-height:1.65;">Nursing and NP students spend hours on iHuman cases with little feedback on <em>why</em> they lost points. The scoring logic — which questions are pivotal, which exam items count, which management choices trigger harmful-flag deductions — stays hidden.</p>
        <p style="font-size:1.05rem; color:var(--ink-2); line-height:1.65;">We analyzed 200+ verified submissions to reconstruct that logic, then turned it into something teachable: a free simulator and free cheat sheets to learn the patterns, and complete case guides for the submissions that count.</p>
      </div>
    </div>
  </div>
</section>

<section class="section-tight">
  <div class="container">
    <div class="statband" data-reveal>
      <div class="sb"><b><span data-counter="200" data-counter-suffix="+">0</span></b><span>Verified submissions analyzed</span></div>
      <div class="sb"><b><span data-counter="171">0</span></b><span>Cases catalogued</span></div>
      <div class="sb"><b><span data-counter="9">0</span></b><span>Courses supported</span></div>
      <div class="sb"><b>Same-day</b><span>Guide delivery</span></div>
    </div>
  </div>
</section>

<section class="section bg-cream2">
  <div class="container">
    <div class="section-head" data-reveal>
      <span class="eyebrow"><span class="dot"></span>The model</span>
      <h2>Lead with education. Monetize the moments that matter.</h2>
      <p>The vast majority of what CPL offers is free — because the mission is learning. Revenue comes from the high-stakes, time-pressured graded submissions, where a complete, rubric-mapped guide is worth real money to a stressed student.</p>
    </div>
    <div class="steps" data-reveal>
      <div class="step"><span class="step-free">Free</span><h3>The simulator</h3><p>Interactive, scored clinical-reasoning practice. The top of the funnel and the heart of the mission.</p></div>
      <div class="step"><span class="step-free">Free</span><h3>The cheat sheets</h3><p>Four frameworks that transfer to every case — and an email relationship built on genuine value.</p></div>
      <div class="step"><span class="step-paid">Premium</span><h3>The case guides</h3><p>$150 each, bundles to $540. Same-day, rubric-mapped, built from verified data. Where CPL earns.</p></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head" data-reveal>
      <span class="eyebrow"><span class="dot"></span>What we stand for</span>
      <h2>Principles that keep us honest</h2>
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:30px 48px;" class="about-principles" data-reveal>
      <div class="principle"><div class="pi">📘</div><div><h4>Education first</h4><p>Everything that teaches the reasoning is free. We gate convenience, never understanding.</p></div></div>
      <div class="principle"><div class="pi">🔍</div><div><h4>Verified, not invented</h4><p>Our frameworks and guides come from real, verified submissions — not guesswork or scraping.</p></div></div>
      <div class="principle"><div class="pi">🤍</div><div><h4>Calm over pressure</h4><p>Our audience is anxious and time-poor. We design to reduce stress, never manufacture it.</p></div></div>
      <div class="principle"><div class="pi">⚖️</div><div><h4>Integrity-aware</h4><p>CPL is a study resource. We're independent of iHuman and any school, and we point students to their own academic policies.</p></div></div>
    </div>
  </div>
</section>

<section class="section-tight" style="padding-bottom:80px;">
  <div class="container">
    <div class="capture" data-reveal style="text-align:center;">
      <div class="capture-inner">
        <div class="capture-eyebrow">Get in touch</div>
        <h3>Questions, partnerships, or press?</h3>
        <p style="max-width:50ch; margin-left:auto; margin-right:auto;">We're a small team building calmly and deliberately. We'd love to hear from you.</p>
        <a class="btn btn-lime btn-lg" href="mailto:hello@clinicalperformancelab.com">Email the team →</a>
      </div>
    </div>
  </div>
</section>
"""
    write_page("about", body,
               title="About",
               description="iHuman scores students against a rubric they never see. CPL makes the invisible visible — a clinical reasoning platform with a free simulator, free cheat sheets, and complete case guides.",
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
<section class="cat-hero">
  <div class="container">
    <div class="cat-hero-panel">
      <div class="cat-hero-inner">
        <span class="eyebrow on-dark"><span class="dot"></span>Questions, answered</span>
        <h1>Everything you might <span class="italic-accent">ask.</span></h1>
        <p>Delivery, formats, pricing, academic integrity, and how the guides line up with iHuman. Still unsure? The Support chat in the corner can help, or email us any time.</p>
      </div>
    </div>
  </div>
</section>

<section class="section" style="padding-top:48px;">
  <div class="container container-narrow">
    <div class="faq-list" data-reveal>
      {faq_html}
    </div>
    <p style="text-align:center; margin-top:36px; color:var(--muted);" data-reveal>
      Want to see exactly what's inside a guide?
      <a href="/sample-guide/">View the anatomy of a guide →</a>
    </p>
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
  <div class="container container-narrow"><div class="prose">
    <h1>Terms of Use</h1>
    <p class="updated">Last updated: May 2026</p>
    <h3>1. Educational use only</h3>
    <p>CPL materials are sold for personal study and academic preparation use. They are not clinical references. Medication dosing and management content reflect what specific iHuman case templates expect — not what should be prescribed in real clinical practice.</p>
    <h3>2. No clinical authority</h3>
    <p>CPL is not a medical authority. Verify all dosing, indications, and clinical decisions with current authoritative sources (Epocrates, UpToDate, IDSA/ACC/AHA guidelines) before any clinical application.</p>
    <h3>3. Independent of institutions</h3>
    <p>CPL is not affiliated with iHuman, Kaplan, Chamberlain University, Walden University, or any other institution. We are an independent educational resource.</p>
    <h3>4. Refund policy</h3>
    <p>Refunds available within 7 days of purchase for the wrong case delivered or substantive uncorrectable error. Contact support@clinicalperformancelab.com.</p>
    <h3>5. Email use</h3>
    <p>We use your email address solely to deliver requested resources and a short clinical-insight follow-up sequence. We do not sell, rent, or share email addresses. Unsubscribe at any time via the link in every email.</p>
  </div></div>
</section>
"""
    privacy_body = """
<section class="section">
  <div class="container container-narrow"><div class="prose">
    <h1>Privacy</h1>
    <p class="updated">Last updated: May 2026</p>
    <h3>What we collect</h3>
    <p>When you submit the free-resources form, we collect your email address and the IDs of the cheat sheets you selected. Nothing else.</p>
    <h3>What we do with it</h3>
    <p>We send a confirmation email immediately. After confirmation, we deliver the PDFs and schedule a four-email follow-up sequence over 7 days. After that, we send nothing further unless you reply or request more.</p>
    <h3>Where it's stored</h3>
    <p>Email addresses and the drip schedule are stored in Vercel KV (a Redis-backed service). The email sending platform is Resend.</p>
    <h3>What we don't do</h3>
    <p>We do not sell, rent, or share your email. We do not embed analytics tracking pixels in delivery emails. We do not use email to target advertising.</p>
    <h3>How to delete your data</h3>
    <p>Email support@clinicalperformancelab.com with the subject "Delete my data" and we'll remove your address from our records within 7 days.</p>
  </div></div>
</section>
"""
    write_page("terms", terms_body, title="Terms of Use", page_class="legal")
    write_page("privacy", privacy_body, title="Privacy", page_class="legal")


# ─── Sitemap + robots ─────────────────────────────────────────────
def build_sitemap():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = ["", "simulator", "sample-guide", "free-resources", "cases", "faq", "about", "terms", "privacy"]
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
    """Copy the redesign JS/JSX assets from src/ to public/."""
    assets = ["cpl.js", "cpl-checkout.js", "cpl-support.js",
              "cpl-catalog.js", "cpl-simulator.jsx"]
    for name in assets:
        src_path = os.path.join(ROOT, "src", name)
        if not os.path.exists(src_path):
            continue
        with open(src_path, "r", encoding="utf-8") as fr:
            content = fr.read()
        with open(os.path.join(PUBLIC, name), "w", encoding="utf-8") as fw:
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
    build_simulator()
    print("  ✓ simulator/")
    build_sample_guide()
    print("  ✓ sample-guide/")
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
