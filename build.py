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
SITE_URL = "https://cpl-site.vercel.app"
BASE_URL = SITE_URL  # backwards-compatible alias used across this module
SITE_NAME = "Clinical Performance Lab"
SITE_TAG = "Clinical reasoning platform for nursing students — master iHuman"

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
<meta property="og:image" content="{esc(SITE_URL)}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(full_title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:url" content="{esc(canonical)}">
<meta name="twitter:image" content="{esc(SITE_URL)}/og-image.png">
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
      <li><a href="/simulator/">Simulator</a></li>
      <li><a href="/free-resources/">Free Cheat Sheets</a></li>
      <li><a href="/cases/">Case Catalog</a></li>
      <li><a href="/faq/">FAQ</a></li>
      <li><a href="/about/">About</a></li>
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
      <p class="footer-tagline">Clinical reasoning platform for nursing students. Free simulator, free cheat sheets, complete iHuman case guides for purchase. Built on 200+ verified submissions across Chamberlain (NR509, NR511, NR602), Walden (NURS 6512, NRNP 6531, 6541, 6552, 6568), and other programs.</p>
      <p class="footer-tagline" style="margin-top:12px;">
        <a href="mailto:Tutorspot98@gmail.com">Tutorspot98@gmail.com</a>
      </p>
    </div>
    <div>
      <h4>Resources</h4>
      <ul>
        <li><a href="/simulator/">Case Simulator</a></li>
        <li><a href="/free-resources/">Free Cheat Sheets</a></li>
        <li><a href="/sample-guide/">Sample Guide</a></li>
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
    # Homepage shows only same-day cases — the ones with complete verified guides
    featured = by_lead_time("same-day")
    case_cards = "".join(case_card_html(c) for c in featured)

    total_cases = len(CASES)
    same_day_count = len(featured)
    build_count = total_cases - same_day_count

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
    <span class="hero-eyebrow" data-reveal><span class="dot"></span>Clinical Reasoning · Made Visible</span>
    <h1 data-reveal data-reveal-delay="80">Learn to think like a clinician.<br><span class="accent">Master iHuman.</span></h1>
    <p class="hero-sub" data-reveal data-reveal-delay="160">
      CPL teaches the clinical reasoning patterns iHuman scores — the question hierarchies, the must-not-miss diagnoses, the documentation language, the harmful-flag traps. Practice free with our simulator. Cheat sheets ship instant. Complete case guides delivered same day.
    </p>
    <div class="hero-ctas" data-reveal data-reveal-delay="240">
      <a href="/simulator/" class="btn btn-primary btn-lg">Try the free simulator →</a>
      <a href="/cases/" class="btn btn-ghost btn-lg">Browse {total_cases} cases</a>
    </div>
    <p class="hero-tertiary" data-reveal data-reveal-delay="280">
      Or <a href="/sample-guide/">see a sample case guide →</a>
    </p>
    <div class="hero-trust" data-reveal data-reveal-delay="320">
      <span><strong data-counter="200" data-counter-suffix="+">0</strong> verified submissions analyzed</span>
      <span><strong data-counter="{total_cases}">0</strong> cases catalogued</span>
      <span><strong data-counter="9">0</strong> courses supported</span>
      <span><strong>Same-day</strong> delivery</span>
    </div>
  </div>
</section>

<section class="section section-narrow">
  <div class="container">
    <div class="how-it-works-grid">

      <div class="how-step" data-reveal>
        <div class="how-step-num">01</div>
        <h3>Practice free with our simulator</h3>
        <p>
          Click through realistic iHuman case stages — history, PE, DDx, plan.
          See which choices score, which lose points, and why. Three cases
          available for free practice right now.
        </p>
        <a href="/simulator/" class="link-arrow">Open the simulator →</a>
      </div>

      <div class="how-step" data-reveal data-reveal-delay="80">
        <div class="how-step-num">02</div>
        <h3>Master the patterns with cheat sheets</h3>
        <p>
          Four PDF guides covering history, physical exam, differential
          diagnosis, and the management plan. The reasoning patterns that work
          across every case template iHuman uses.
        </p>
        <a href="#free-resources" class="link-arrow">Get the cheat sheets →</a>
      </div>

      <div class="how-step" data-reveal data-reveal-delay="160">
        <div class="how-step-num">03</div>
        <h3>Get your case guide when it counts</h3>
        <p>
          For the cases that count toward your grade — submission-ready guides
          with every history question, PE finding, DDx ranking, and management
          decision mapped to iHuman's scoring rubric. Same-day delivery.
        </p>
        <a href="/cases/" class="link-arrow">Browse {total_cases} cases →</a>
      </div>

    </div>
  </div>
</section>

<section class="section" id="free-resources" style="background:var(--cream-2);">
  <div class="container">
    <div class="section-title-block">
      <span class="eyebrow">Start free</span>
      <h2>Free clinical reasoning frameworks</h2>
      <p>Four PDFs covering the universal patterns CPL has identified across 200+ verified iHuman case submissions. The reasoning that transfers to every case template — yours and ours.</p>
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
      <h2>Case guides built from verified scoring data</h2>
      <p>Every CPL guide maps the actual iHuman scoring rubric: which history questions score, which PE items count, which DDx rankings are platform-verified, which management choices avoid harmful-flag deductions. {same_day_count} complete guides ship same day. {build_count} more available within 24–48h.</p>
    </div>
    <div class="case-grid">
      {case_cards}
    </div>
    <div class="text-center mt-4">
      <a href="/cases/" class="btn btn-ghost">See all {total_cases} cases →</a>
    </div>
  </div>
</section>

<section class="section" style="background:var(--cream-2);">
  <div class="container">
    <div class="section-title-block">
      <span class="eyebrow">Pricing</span>
      <h2>When you need the complete guide.</h2>
      <p>The simulator and cheat sheets are free forever. When a case counts toward your grade, our complete guides ship same day. Bundles are mix-and-match. New customer? Code <strong>CPLFIRST15</strong> takes 15% off your first single case.</p>
    </div>
    <div class="pricing-grid">
      {pricing_html}
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

    total = len(all_cases)
    same_day_n = sum(1 for c in all_cases if c.get("lead_time") == "same-day")
    fast_n = sum(1 for c in all_cases if c.get("lead_time") == "fast-build")
    request_n = sum(1 for c in all_cases if c.get("lead_time") == "on-request")

    body = f"""
<section class="hero">
  <div class="container">
    <span class="hero-eyebrow"><span class="dot"></span>Case Catalog</span>
    <h1><span data-counter="{total}" data-counter-suffix=" cases">0 cases</span>. <span class="accent">All available today.</span></h1>
    <p class="hero-sub">
      From verified scoring data across 200+ submissions. {same_day_n} ship same day. {total - same_day_n} more build within 24–48h on order. Across NR509, NR511, NR602, NURS 6512, NRNP 6531/6541/6552/6568, and Kaplan-platform programs.
    </p>
    <div class="hero-ctas">
      <button class="btn btn-primary btn-lg" onclick="document.getElementById('catalog-grid').scrollIntoView({{behavior:'smooth'}})">Browse cases ↓</button>
      <button class="btn btn-ghost btn-lg" onclick="document.getElementById('bundle-builder').scrollIntoView({{behavior:'smooth'}})">Build a bundle →</button>
    </div>
    <div class="hero-trust" style="margin-top:28px;">
      <span><strong data-counter="{same_day_n}">0</strong> same-day guides</span>
      <span><strong data-counter="{fast_n}">0</strong> fast-build (24–48h)</span>
      <span><strong data-counter="{request_n}">0</strong> on-request</span>
      <span><strong data-counter="9">0</strong> courses covered</span>
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
      <div class="pdf-lock-note">
        Want to see a full sample first? <a href="/sample-guide/">View a complete sample guide &rarr;</a>
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
      &middot; <a href="/sample-guide/">See a complete sample guide &rarr;</a>
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


# ─── PAGE: Simulator ──────────────────────────────────────────────
def build_simulator():
    """Build the interactive case simulator page (free clinical reasoning practice)."""
    import json as _json
    sim_data_json = _json.dumps(SIMULATOR_DATA)

    body = f'''
<section class="simulator-hero">
  <div class="container">
    <span class="hero-eyebrow"><span class="dot"></span>Free · Take a minute</span>
    <h1>Practice. Don't pay to learn.</h1>
    <p class="hero-sub">
      Three iHuman cases. Real scoring patterns. See which choices lose points
      and why. No signup, no payment — this is what free clinical reasoning
      education looks like.
    </p>
  </div>
</section>

<section class="simulator-section">
  <div class="container">

    <div class="sim-case-picker">
      <span class="sim-case-picker-label">Pick a case:</span>
      <button class="sim-case-btn is-active" data-case="harvey" onclick="loadCase('harvey', this)">Harvey Hoya — HTN</button>
      <button class="sim-case-btn" data-case="bebe" onclick="loadCase('bebe', this)">Bebe Babbitt — Migraine</button>
      <button class="sim-case-btn" data-case="kennedy" onclick="loadCase('kennedy', this)">Kennedy Poole — ADHD</button>
    </div>

    <div class="sim-container">
      <div class="sim-header">
        <div>
          <div class="sim-case-title" id="sim-case-title">Harvey Hoya — Hypertension Stage 2</div>
          <div class="sim-case-meta" id="sim-case-meta">57-year-old male · NR 509 / NR 511 Week 5 · Chamberlain</div>
        </div>
        <div class="sim-score-pill" id="sim-score-display">Score: 0%</div>
      </div>

      <div class="sim-progress">
        <div class="sim-prog-step" id="prog-1"></div>
        <div class="sim-prog-step" id="prog-2"></div>
        <div class="sim-prog-step" id="prog-3"></div>
        <div class="sim-prog-step" id="prog-4"></div>
      </div>

      <div class="sim-body" id="sim-body"></div>

      <div class="sim-footer">
        <span class="sim-stage-label" id="sim-stage-label">Stage 1 of 4 — History (free)</span>
        <button class="btn btn-primary btn-sm" id="sim-next-btn" onclick="nextQuestion()" style="display:none">Next question →</button>
      </div>
    </div>

    <div id="sim-unlock-section" style="display:none">
      <div class="sim-unlock">
        <h3>You've completed the free simulator.</h3>
        <p>
          The full reasoning map for any case — every history question, every PE
          finding, every DDx ranking, every harmful-flag trap — ships in a
          complete CPL guide. Same day, $150, or 15% off your first with code CPLFIRST15.
        </p>
        <div class="sim-unlock-ctas">
          <a href="/cases/" class="btn btn-lime">Browse complete case guides</a>
          <button class="btn btn-ghost" onclick="resetCurrentCase()">Try this case again</button>
        </div>
      </div>
    </div>

  </div>
</section>

<script>
const SIMULATOR_DATA = {sim_data_json};
let currentCase = 'harvey';
let currentQuestion = 0;
let score = 0;
let answered = [];

function loadCase(caseId, btn) {{
  currentCase = caseId;
  currentQuestion = 0;
  score = 0;
  answered = [];
  document.querySelectorAll('.sim-case-btn').forEach(b => b.classList.remove('is-active'));
  if (btn) btn.classList.add('is-active');
  const data = SIMULATOR_DATA[caseId];
  document.getElementById('sim-case-title').textContent = data.title;
  document.getElementById('sim-case-meta').textContent = data.meta;
  document.getElementById('sim-unlock-section').style.display = 'none';
  document.getElementById('sim-next-btn').style.display = 'none';
  updateScore();
  updateProgress();
  renderQuestion();
}}

function renderQuestion() {{
  const data = SIMULATOR_DATA[currentCase];
  const q = data.questions[currentQuestion];
  if (!q) {{ finishCase(); return; }}
  const body = document.getElementById('sim-body');
  body.innerHTML = `
    <div class="sim-question-stage">${{q.stage}}</div>
    <div class="sim-question">${{q.q}}</div>
    <div class="sim-options" id="sim-options"></div>
    <div class="sim-feedback" id="sim-feedback" style="display:none"></div>
  `;
  const opts = document.getElementById('sim-options');
  q.options.forEach((opt, idx) => {{
    const div = document.createElement('button');
    div.className = 'sim-option';
    div.textContent = opt;
    div.onclick = () => selectOption(idx);
    opts.appendChild(div);
  }});
  document.getElementById('sim-stage-label').textContent =
    `Stage ${{currentQuestion + 1}} of ${{data.questions.length}} — ${{q.stage}} (free)`;
  document.getElementById('sim-next-btn').style.display = 'none';
}}

function selectOption(idx) {{
  if (answered.includes(currentQuestion)) return;
  answered.push(currentQuestion);
  const q = SIMULATOR_DATA[currentCase].questions[currentQuestion];
  const correct = idx === q.correct;
  if (correct) score++;
  const opts = document.querySelectorAll('#sim-options .sim-option');
  opts.forEach((el, i) => {{
    el.classList.add('is-answered');
    if (i === q.correct) el.classList.add('is-correct');
    if (i === idx && !correct) el.classList.add('is-wrong');
  }});
  const fb = document.getElementById('sim-feedback');
  fb.className = correct ? 'sim-feedback is-correct' : 'sim-feedback is-wrong';
  fb.innerHTML = `<strong>${{correct ? '✓ Correct' : '✗ Not quite'}}</strong><br>${{q.feedback}}`;
  fb.style.display = 'block';
  updateScore();
  document.getElementById('sim-next-btn').style.display = '';
}}

function nextQuestion() {{
  currentQuestion++;
  updateProgress();
  renderQuestion();
}}

function updateScore() {{
  const data = SIMULATOR_DATA[currentCase];
  const pct = Math.round((score / data.questions.length) * 100);
  document.getElementById('sim-score-display').textContent = `Score: ${{pct}}%`;
}}

function updateProgress() {{
  for (let i = 1; i <= 4; i++) {{
    const el = document.getElementById(`prog-${{i}}`);
    if (!el) continue;
    el.className = 'sim-prog-step';
    if (i < currentQuestion + 1) el.classList.add('is-done');
    if (i === currentQuestion + 1) el.classList.add('is-active');
  }}
}}

function finishCase() {{
  const data = SIMULATOR_DATA[currentCase];
  const pct = Math.round((score / data.questions.length) * 100);
  document.getElementById('sim-body').innerHTML = `
    <div class="sim-finish">
      <div class="sim-finish-score">${{pct}}%</div>
      <div class="sim-finish-label">You got ${{score}} of ${{data.questions.length}} questions right.</div>
      <p class="sim-finish-note">
        That's just 4 of ~35 questions on this case. A complete CPL guide maps
        every scored question, every PE finding, every DDx ranking, and every
        management decision.
      </p>
    </div>
  `;
  document.getElementById('sim-next-btn').style.display = 'none';
  document.getElementById('sim-stage-label').textContent = 'Complete';
  document.getElementById('sim-unlock-section').style.display = '';
}}

function resetCurrentCase() {{
  loadCase(currentCase, document.querySelector(`.sim-case-btn[data-case="${{currentCase}}"]`));
}}

loadCase('harvey', document.querySelector('.sim-case-btn[data-case="harvey"]'));
</script>
'''

    write_page("simulator", body,
               title="Case Simulator",
               description="Practice clinical reasoning on real iHuman case patterns. Free simulator with three cases, scored feedback, no signup.",
               page_class="simulator")


# ─── PAGE: Sample guide (marketing demo of a full guide) ──────────
def build_sample_guide():
    """Build the /sample-guide/ page showing one full guide's anatomy."""
    total = len(CASES)
    same_day_n = sum(1 for c in CASES if c.get("lead_time") == "same-day")
    body = f'''
<section class="sample-hero">
  <div class="container">
    <span class="hero-eyebrow"><span class="dot"></span>Anatomy of a CPL guide</span>
    <h1>See exactly what you get.</h1>
    <p class="hero-sub">
      Below is the complete structure of a CPL case guide, with real pages from
      the Harvey Hoya HTN guide. Every CPL guide follows this same format with
      case-specific content.
    </p>
  </div>
</section>

<section class="sample-section">
  <div class="container sample-container">

    <div class="sample-page-block">
      <div class="sample-page-meta">
        <div class="sample-page-num">Page 1 · Cover &amp; Case Overview</div>
        <h2>Every guide opens with the case identity</h2>
        <p>
          Patient demographics, chief complaint, presenting context, and the
          verified diagnosis with associated must-not-miss conditions. This is
          the orientation page — you know exactly which case you're working on
          and what you're aiming for.
        </p>
      </div>
      <div class="sample-page-image">
        <img src="/sample-guide/page_1_cover.png" alt="Cover page of a CPL guide" loading="lazy">
      </div>
    </div>

    <div class="sample-page-block reversed">
      <div class="sample-page-meta">
        <div class="sample-page-num">Pages 2–8 · History Bank</div>
        <h2>Every scored history question, in iHuman order</h2>
        <p>
          The complete history bank with verbatim patient responses, organized
          into the OLDCARTS framework, past medical history, family history,
          social history, and review of systems. Each question is marked with
          its scoring weight and the pivotal communication questions are highlighted.
        </p>
        <p class="sample-fact">
          <strong>What this saves you:</strong> 30–45 minutes of fumbling through
          unhelpful "How are you today?" questions. You walk in knowing exactly
          which 35 questions iHuman counts.
        </p>
      </div>
      <div class="sample-page-image">
        <img src="/sample-guide/page_2_history.png" alt="History section page from a CPL guide" loading="lazy">
      </div>
    </div>

    <div class="sample-page-block">
      <div class="sample-page-meta">
        <div class="sample-page-num">Pages 9–14 · Physical Exam</div>
        <h2>Every scored PE item with documentation language</h2>
        <p>
          Each PE finding paired with the exact documentation phrase iHuman
          expects. Cardiac auscultation points, lung field locations, abdominal
          quadrant findings — all with the clinical language that scores instead
          of the lay language that loses points.
        </p>
        <p class="sample-fact">
          <strong>What this saves you:</strong> Knowing the difference between
          writing "AV nicking" (full credit) vs. "narrowing where the veins
          cross" (partial credit). Documentation language is 20% of the case score.
        </p>
      </div>
      <div class="sample-page-image">
        <img src="/sample-guide/page_3_pe.png" alt="Physical exam page from a CPL guide" loading="lazy">
      </div>
    </div>

    <div class="sample-page-block reversed">
      <div class="sample-page-meta">
        <div class="sample-page-num">Pages 15–24 · DDx, Tests, Management Plan, SOAP Note</div>
        <h2>The reasoning behind every grade-impacting decision</h2>
        <p>
          The ranked differential diagnosis list with the platform-verified order,
          the tests to order (and the harmful-flag tests to avoid), and the
          complete 6-part management plan with APA-formatted references. Plus a
          ready-to-submit SOAP note.
        </p>
        <p class="sample-fact">
          <strong>What this saves you:</strong> The harmful-flag traps alone can
          zero your Tests score. The DDx ranking can swing 15 points. We map
          every one — you don't guess.
        </p>
      </div>
      <div class="sample-page-image">
        <img src="/sample-guide/page_4_plan.png" alt="Management plan page from a CPL guide" loading="lazy">
      </div>
    </div>

  </div>
</section>

<section class="sample-cta-section">
  <div class="container">
    <div class="sample-cta-card">
      <h2>Your case follows this exact format.</h2>
      <p>
        {total} cases catalogued across NR509, NR511, NR602, NURS 6512,
        NRNP 6531, 6541, 6552, 6568 and Kaplan-platform programs.
        {same_day_n} ship same day. The rest build within 24–48h on order.
      </p>
      <div class="sample-cta-row">
        <a href="/cases/" class="btn btn-primary">Browse {total} case guides</a>
        <a href="mailto:Tutorspot98@gmail.com?subject=CPL%20Question" class="btn btn-ghost">Ask a question</a>
      </div>
      <p class="muted-small">
        Use code <strong>CPLFIRST15</strong> for 15% off your first single case.
        Bundles save up to $210.
      </p>
    </div>
  </div>
</section>
'''
    write_page("sample-guide", body,
               title="See a Sample CPL Case Guide",
               description="See exactly what a CPL iHuman case guide contains — full pages from the Harvey Hoya HTN guide, including history bank, physical exam, and management plan.",
               page_class="sample-guide")


# ─── PAGE: About ──────────────────────────────────────────────────
def build_about():
    body = """
<section class="hero">
  <div class="container container-narrow">
    <span class="hero-eyebrow"><span class="dot"></span>About</span>
    <h1>Clinical reasoning is the skill <span class="accent">iHuman is actually testing.</span></h1>
    <p class="hero-sub">
      iHuman simulates virtual patient encounters. It scores you on the exact same skills you'll be graded on as a practicing NP. The problem isn't that iHuman is hard — it's that the scoring logic is invisible. CPL makes it visible.
    </p>
  </div>
</section>

<section class="section">
  <div class="container container-narrow">
    <p>iHuman scores you on the same clinical judgment you'll use as a practicing NP:</p>
    <ul>
      <li>Which history questions to ask, in what order</li>
      <li>Which physical exam items are pertinent to this presentation</li>
      <li>How to rank differential diagnoses by probability and severity</li>
      <li>Which tests to order — and which trigger "harmful to patient"</li>
      <li>How to write documentation that matches clinical reality</li>
    </ul>
    <p>Most students never see <em>why</em> they lost 15 points on a case — only that they did.</p>

    <h2 class="mt-4">What CPL does</h2>
    <p>We make iHuman's invisible scoring logic visible.</p>
    <p><strong>For practice:</strong> Our case simulator walks you through real case patterns, scoring your choices and explaining the reasoning in real time. Free.</p>
    <p><strong>For mastery:</strong> Our four cheat sheet PDFs codify the universal patterns that score on every case template — history hierarchies, PE checklists, DDx ranking logic, and the harmful-flag traps. Free, email-delivered.</p>
    <p><strong>For graded submissions:</strong> Our complete case guides give you the verified scoring map for a specific case — every history question, every PE item, every DDx, every management decision, with the clinical reasoning behind each. $150 per case, same-day delivery, mix-and-match bundles.</p>

    <h2 class="mt-4">Where the data comes from</h2>
    <p>Every CPL guide is built from verified student submissions. We analyze 100% performance reports, client screenshots, and multi-submission pattern data to map what actually scores on the iHuman platform — not what should score in theory, what does score in practice.</p>
    <p>We've analyzed 200+ submissions across NR509, NR511, NR602, NURS 6512, NRNP 6531, 6541, 6552, and 6568. The patterns we identify get codified into the cheat sheets and simulator. The case-specific scoring maps get codified into the guides.</p>

    <h2 class="mt-4">Who we serve</h2>
    <p>Primarily nursing students at Chamberlain University and Walden University. Increasingly: PMHNP students at South University, Regis College, and others using the Kaplan Clinical Canvas platform. The reasoning patterns transfer across institutions — the case-specific scoring maps are institution-specific.</p>

    <h2 class="mt-4">What CPL is not</h2>
    <p>CPL is not a clinical reference. The medication dosing and management content in our guides reflects what the iHuman platform expects on those specific case templates. <strong>Verify all dosing with current Epocrates or UpToDate before any clinical application.</strong></p>
    <p>CPL is also not affiliated with iHuman, Kaplan, Chamberlain University, Walden University, or any other institution. We're an independent educational resource.</p>

    <h2 class="mt-4">Contact</h2>
    <p><a href="mailto:Tutorspot98@gmail.com">Tutorspot98@gmail.com</a> — for case orders, support, or partnership inquiries.</p>
  </div>
</section>
"""
    write_page("about", body,
               title="About",
               description="Clinical reasoning is the skill iHuman is actually testing. CPL makes the invisible scoring logic visible — free simulator, free cheat sheets, complete case guides.",
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
    <p class="text-center mt-4 muted">
      Want to see exactly what's inside a guide?
      <a href="/sample-guide/">View a complete sample guide →</a>
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
