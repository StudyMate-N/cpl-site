"""One builder per public page. Data comes from cases_data; API contracts are unchanged."""
import json

import build
from cases_data import CASES, PRICING
from web.components import (
    LEAD, SCHOOLS, e, search_url, mailto, icon, dot, pulse_line, split_title, topic, lead_badge,
    case_card_html, feature_case_html, capture_html, page_intro, closing_cta,
)
from web.layout import write_page

V = build.ASSET_VERSION
HUMAN_REVIEW = mailto("Human review request")
EXAM_PREP = mailto("Exam preparation request")

WORKFLOW = [
    ("History", "Questions asked and the patient's responses."),
    ("Physical examination", "Examination choices and documented findings."),
    ("Key findings", "The relevant positives and negatives."),
    ("Problem statement", "A focused summary of the presentation."),
    ("Differential diagnosis", "Compare and prioritize possible explanations."),
    ("Tests and results", "Connect investigations to the clinical question."),
    ("Diagnosis", "Explain how the evidence supports the assessment."),
    ("Management", "Review treatment, education and follow-up."),
    ("Documentation", "Organize the required case notes and course deliverables."),
]

# "Or start from what's on your mind" chips: label, destination, CTA, link.
INTENTS = [
    ("I have an iHuman due.", "iHuman case reconstructions", "Find My Case", "/cases/"),
    ("My midterm is Friday.", "Midterms & Finals", "Prepare for an Exam", "#exam-path"),
    ("I need someone to look over my SOAP note.", "Human SOAP review", "Talk to a reviewer", HUMAN_REVIEW),
    ("My professor left feedback. What do I fix?", "Professor-feedback review", "Talk to a reviewer", HUMAN_REVIEW),
    ("ATI is coming.", "ATI & HESI", "Explore ATI & HESI", "#ati"),
    ("I need to start NCLEX prep.", "NCLEX", "Explore NCLEX", "#nclex"),
]

REVIEW_WORK = ["SOAP note review", "Concept maps", "Care plans", "Case studies", "Clinical reflections", "Clinical journals",
               "Health assessments", "Discussion posts", "EBP papers", "PICOT assignments", "Research papers", "Presentations",
               "APA 7 & references", "Professor-feedback revisions", "Originality review", "Final proofreading"]

EXAM_PATH = [
    ("exams", "Midterms & Finals", "Study resources → Practice set → Weak-area review → Exam-prep support", True),
    ("ati", "ATI & HESI", "Free sample → Prep product → Readiness check → Coaching", False),
    ("teas", "TEAS", "Free sample → Prep product → Readiness check → Coaching", False),
    ("nclex", "NCLEX", "Free diagnostic → Study plan → Readiness assessment → Coaching", False),
]

FEATURED = ["bebe-babbitt-migraine", "harvey-hoya-htn", "christine-smith-pyelonephritis"]


def case_search(field_id, label, big=False):
    """Hero/closing search. Submits to the library; cpl-home.js adds live results."""
    return f"""
<form action="/cases/" method="get" role="search" id="{field_id}Form" class="case-search{' case-search-lg' if big else ''}" data-case-search>
  <label class="sr-only" for="{field_id}">{label}</label>
  <div class="search-field">{icon('search', 18)}<input id="{field_id}" type="search" name="q" placeholder="Search patient, course, week or school…" autocomplete="off" aria-controls="{field_id}-results" aria-expanded="false"></div>
  <div class="search-results" id="{field_id}-results" hidden>
    <div class="search-results-label" data-results-label>Published cases</div>
    <div data-results-list></div>
    <div class="search-results-foot"><span data-request-label>Not listed yet?</span><button type="button" class="link-btn" data-order="Case request" data-alias="" data-price="150" data-delivery="availability confirmed before payment" data-request-case>Request a case →</button></div>
  </div>
  {'<button class="btn btn-lime btn-bordered" type="submit">Find My Case</button>' if big else ''}
</form>"""


def hero_visual():
    rows = [("CC Sx", "How can I help you today?"), ("Location", "Where more precisely is the pain?"),
            ("Timing", "Any warning symptoms beforehand?"), ("Severity", "How severe (1–10) is your headache?")]
    q_rows = "".join(f'<div class="mini-row"><span>{dot()}</span><span class="muted">{a}</span><span>{q}</span></div>' for a, q in rows)
    findings = ["Preceding blurry bilateral vision", "Photophobia / phonophobia", "Normal neurological examination"]
    f_rows = "".join(f'<div class="mini-row mini-row-2"><span>{dot()}</span><span>{f}</span></div>' for f in findings)
    return f"""
<div class="hero-visual" aria-hidden="true">
  <div class="sheet sheet-back"><span class="eyebrow-sm">04 · Case findings</span><div class="mini-table"><div class="mini-row mini-row-2 mini-head"><span>Key</span><span>Finding</span></div>{f_rows}</div></div>
  <div class="sheet sheet-front">
    <div class="sheet-top"><span class="eyebrow-sm muted">Neurology · NR 509 Week 6</span><span class="tag tag-ok">Same-day guide</span></div>
    <div class="sheet-cover"><span class="sheet-name">Bebe Babbitt</span><span class="sheet-sub">26-year-old female with recurrent headaches</span>{pulse_line()}</div>
    <div class="mini-table"><div class="mini-row mini-head"><span></span><span>Approach</span><span>Question</span></div>{q_rows}</div>
    <div class="tag-row sheet-tags"><span class="tag">History</span><span class="tag">Physical exam</span><span class="tag">Key findings</span><span class="tag">Diagnosis</span></div>
  </div>
</div>"""


def schools_section():
    def tile(i, s, clone):
        attrs = ' tabindex="-1" aria-hidden="true"' if clone else f' aria-controls="school-panel-{i}" aria-expanded="false"'
        return (f'<button type="button" class="school-tile" data-school="{i}"{attrs} style="--c1:{s["c1"]};--c2:{s["c2"]}">'
                f'<span class="school-mono">{e(s["mono"])}</span><span class="school-word"><span>{e(s["name"])}</span><small>{e(s["sub"])}</small></span></button>')

    entries = SCHOOLS + [{"name": "Your school", "sub": "Request it", "full": "", "mono": "+", "c1": "#4A6914", "c2": "#FFFFFF", "match": None}]
    first = "".join(tile(i, s, False) for i, s in enumerate(entries))
    clones = "".join(tile(i, s, True) for _ in range(3) for i, s in enumerate(entries))

    panels = ""
    for i, s in enumerate(entries):
        if s["match"]:
            n = sum(1 for c in CASES if s["match"].lower() in (c.get("school") or "").lower())
            cases_cell = (f'<a href="{e(search_url(s["match"]))}"><small>iHuman cases</small><strong>{n} in the library →</strong></a>' if n else
                          f'<a href="{e(mailto("Case request · " + s["full"]))}"><small>iHuman cases</small><strong>Request your course\'s cases →</strong></a>')
            panels += (f'<div class="school-panel" id="school-panel-{i}" role="region" aria-label="Resources for {e(s["full"])}" hidden>'
                       f'<div class="school-panel-lead"><small>Showing resources for</small><strong>{e(s["full"])}</strong></div>{cases_cell}'
                       f'<a href="#exam-path"><small>Exams</small><strong>Midterm and final packs →</strong></a>'
                       f'<a href="#support"><small>Coursework</small><strong>Rubric-aligned review →</strong></a></div>')
        else:
            panels += (f'<div class="school-panel" id="school-panel-{i}" role="region" aria-label="Request your school" hidden>'
                       '<div class="school-panel-lead"><small>Don\'t see your school?</small><strong>Tell us where you study</strong></div>'
                       f'<a href="{e(mailto("Add my school"))}"><small>Request</small><strong>Add my school →</strong></a>'
                       f'<a href="/cases/"><small>Or search</small><strong>All {len(CASES)} case records →</strong></a>'
                       '<a href="#support"><small>Coursework</small><strong>Human support →</strong></a></div>')

    return f"""
<section class="schools" id="schools"><div class="container">
  <div class="section-head"><div><h2 class="h2-sm">Find resources for your school</h2><p>Choose your school to see cases and course resources organized by course and week.</p></div><a class="link-arrow" href="/cases/#fSchool">See all schools →</a></div>
</div>
<div class="school-strip"><div class="school-track">{first}{clones}</div></div>
<div class="container">{panels}<p class="fine">School names are used only to organize resources. Clinical Performance Lab is independent and not affiliated with or endorsed by any institution or by iHuman.</p></div>
</section>"""


def build_home():
    by = {c["slug"]: c for c in CASES}
    featured = "".join(feature_case_html(by[s]) for s in FEATURED if s in by)
    intents = "".join(f'<button type="button" class="chip" aria-pressed="false" data-intent data-dest="{e(dest)}" data-cta="{e(cta)}" data-href="{e(href)}">{e(label)}</button>' for label, dest, cta, href in INTENTS)
    review = "".join(f'<li>{e(w)}</li>' for w in REVIEW_WORK)
    path_rows = "".join(
        f'<div class="path-row" id="{pid}">{dot("ok" if now else "open")}<span class="path-name">{e(name)}</span><span class="path-steps">{e(steps)}</span>'
        f'<span class="path-status{" now" if now else ""}">{"Now" if now else "Growing"}</span></div>'
        for pid, name, steps, now in EXAM_PATH)

    body = f"""
<section class="hero"><div class="container hero-grid">
  <div class="hero-copy">
    <h1>Whatever nursing school puts in front of you, start here.</h1>
    <p class="hero-lede">From iHuman cases and clinical coursework to midterms, finals, ATI, TEAS and NCLEX — find the resources, preparation and real human support you need to move forward.</p>
    <div class="search-card">
      <span class="search-card-title">Working on an iHuman case?</span>
      {case_search("heroSearch", "Search patient, course, week or school")}
      <div class="btn-row"><button type="submit" form="heroSearchForm" class="btn btn-lime">Find My Case</button><a class="btn btn-ghost" href="#services">See Everything We Help With</a></div>
      <div class="intents"><span class="intents-label">Or start from what's on your mind</span><div class="chip-row">{intents}</div>
        <a class="intent-result" data-intent-result hidden href="#"><span><span class="muted">Start with </span><strong data-intent-dest></strong></span><span class="link-arrow"><span data-intent-cta></span> →</span></a></div>
    </div>
    <div class="hero-assure"><span class="avatar-stack" aria-hidden="true"><span></span><span></span><span></span></span><span>Resources when you can handle it yourself. Real human support when you need more than a resource.</span></div>
  </div>
  {hero_visual()}
</div></section>

{schools_section()}

<section class="section" id="ihuman"><div class="container">
  <div class="section-head"><div class="section-title"><span class="eyebrow">iHuman case reconstructions</span><h2>Every case, rebuilt section by section.</h2><p>History, physical exam, key findings, differential, tests, diagnosis and management — with the gaps students most often miss marked clearly.</p></div>
    <div class="chip-row"><a class="chip chip-on" href="#schools">By school</a><a class="chip" href="/cases/#catSearch">By course</a><a class="chip" href="/cases/#fSystem">By system</a></div></div>
  <div class="feature-grid">{featured}
    <div class="feature-request"><span class="feature-request-title">Can't find your case?</span><span>Tell us the patient, course and week. We'll tell you when it's ready.</span><button type="button" class="btn btn-ghost btn-sm" data-order="Case request" data-alias="" data-price="150" data-delivery="availability confirmed before payment">Request a case</button></div>
  </div>
  <ol class="steps-row">
    <li><span class="mono">01</span><strong>Full reconstruction</strong><span>Every required question and exam</span></li>
    <li><span class="mono">02</span><strong>Compare my attempt</strong><span>See exactly where points were lost</span></li>
    <li><span class="mono">03</span><strong>SOAP and management review</strong><span>A person checks your write-up</span></li>
    <li><span class="mono">04</span><strong>Weekly course support</strong><span>Stay ahead of every case in the term</span></li>
  </ol>
</div></section>

<section class="section section-grey" id="services"><div class="container">
  <div class="section-title"><span class="eyebrow">What are you working on?</span><h2>Start with what's due next.</h2></div>
  <div class="service-grid">
    <a class="service service-flagship" href="/cases/"><span class="service-top"><span class="mono">01</span><span class="flag">Flagship</span></span><span class="service-title">iHuman &amp; Simulations</span><span class="service-text">Complete iHuman case reconstructions, performance-gap review, history, physical exam, key findings, DDx, tests, diagnosis and management.</span><span class="btn btn-ink">Find an iHuman Case</span></a>
    <a class="service service-wide" href="#support"><span class="service-top"><span class="mono">06</span><span class="human-label">{dot()}Human support</span></span><span class="service-title">Coursework &amp; Writing</span><span class="service-text">SOAP notes, concept maps, care plans, case studies, reflections, discussion posts, EBP, PICOT, papers, APA and more.</span><span class="link-arrow">Get Coursework Support →</span></a>
    <a class="service" href="#exam-path"><span class="mono">02</span><span class="service-name">Midterms &amp; Finals</span><span class="service-text">Study guides, topic reviews, practice questions, custom exam packs.</span><span class="link-arrow">Prepare for an Exam →</span></a>
    <a class="service" href="#ati"><span class="service-top"><span class="mono">03</span><span class="growing">Growing</span></span><span class="service-name">ATI &amp; HESI</span><span class="service-text">Content mastery, predictor and exit prep, remediation.</span><span class="link-arrow">Explore ATI &amp; HESI →</span></a>
    <a class="service" href="#nclex"><span class="service-top"><span class="mono">04</span><span class="growing">Growing</span></span><span class="service-name">NCLEX</span><span class="service-text">NGN questions, CATs, readiness assessments, study plans.</span><span class="link-arrow">Explore NCLEX →</span></a>
    <a class="service" href="#teas"><span class="service-top"><span class="mono">05</span><span class="growing">Growing</span></span><span class="service-name">TEAS &amp; Admissions</span><span class="service-text">TEAS prep, prerequisite review, admission-exam resources.</span><span class="link-arrow">Explore TEAS →</span></a>
  </div>
</div></section>

<section class="section" id="support"><div class="container">
  <div class="section-title"><span class="eyebrow">Two ways to move forward</span><h2>Sometimes you need a resource. Sometimes you need a person.</h2></div>
  <div class="ways">
    <div class="way"><img src="/img/self-study.webp" alt="A student's desk with a laptop showing a case guide, an open notebook and a stethoscope" width="1600" height="541" loading="lazy"><div class="way-body"><span class="eyebrow-sm muted">Do it yourself</span><p class="way-text">Case reconstructions, study guides, practice questions, exam packs and course resources.</p><a class="btn btn-ghost" href="/cases/">Browse resources</a></div></div>
    <div class="way way-human"><img src="/img/human-review.webp" alt="A reviewer marking up a printed SOAP note with a pen" width="1600" height="541" loading="lazy"><div class="way-body"><span class="eyebrow-sm human-label">{dot()}Get human support</span><p class="way-text">Paper editing, SOAP review, concept-map review, case review, exam preparation, professor-feedback review and ongoing course support.</p><a class="btn btn-lime" href="{e(HUMAN_REVIEW)}">Talk to a reviewer</a></div></div>
  </div>
  <div class="review-split">
    <div><h3 class="h-small">The work we review</h3><ul class="review-list">{review}</ul></div>
    <div class="paper-review"><span class="eyebrow">Human Nursing Paper Review</span><span class="paper-title">Your writing. Reviewed by a real person.</span><p>Clarity and structure · Grammar and academic tone · APA 7 · References and citations · Rubric alignment · Originality review · Final proofread</p><p class="paper-note">You remain the author. We review, strengthen and explain your work. We never write or submit it for you.</p></div>
  </div>
</div></section>

<section class="section section-lime" id="exam-path"><div class="container split">
  <div class="split-side"><span class="eyebrow">Exam path</span><h2>From this week's midterm to licensure.</h2><p>Course exams are ready now. ATI, HESI, TEAS and NCLEX preparation is being added, one area at a time.</p><img class="exam-img" src="/img/exam-prep.webp" alt="Practice question printouts, a lime highlighter and flashcards on a light desk" width="1200" height="600" loading="lazy"><a class="link-arrow" href="{e(EXAM_PREP)}">Ask about exam prep →</a></div>
  <div class="path-list">{path_rows}</div>
</div></section>

<section class="section" id="rigor"><div class="container split">
  <div class="split-side"><span class="eyebrow">How we build cases</span><h2>Rigor you can check.</h2></div>
  <div class="rigor-grid">
    <div><strong>Evidence-led</strong><p>Built from the case itself. Questions, responses and feedback are kept word for word.</p></div>
    <div><strong>Version-controlled</strong><p>Every guide carries a version and date, and is updated when a case changes.</p></div>
    <div><strong>Clearly marked</strong><p>Anything not confirmed by the case is labelled, never filled in.</p><span class="tag-row"><span class="tag tag-ok">Verified</span><span class="tag tag-warn">Unresolved</span></span></div>
  </div>
</div></section>

<section class="final-cta"><div class="container"><div class="final-panel">
  <h2>Whatever is in front of you, start here.</h2>
  {case_search("finalSearch", "Search patient, course, week or school", big=True)}
  <p>or <a href="{e(HUMAN_REVIEW)}">talk to a real person</a> about your coursework</p>
</div></div></section>"""

    dock = f'<div class="m-dock" aria-label="Quick actions"><a class="btn btn-lime" href="/cases/">Find My Case</a><a class="btn btn-plain" href="#support">{dot()}Human Support</a></div>'
    schema = json.dumps({"@context": "https://schema.org", "@type": "Organization", "name": build.SITE_NAME, "url": build.SITE_URL + "/",
                         "logo": build.SITE_URL + "/favicon.svg", "email": build.CONTACT_EMAIL})
    write_page("", body, description="iHuman case reconstructions, midterm and final prep, ATI, TEAS and NCLEX resources, and real human review for nursing coursework.",
               page_class="home", head_extra=f'<script type="application/ld+json">{schema}</script>',
               after_footer=dock, body_scripts=f'<script src="/cpl-home.js?v={V}" defer></script>')


# ─── Case library ─────────────────────────────────────────────────
def build_catalog():
    data = [{"t": c["title"], "cc": c.get("chief_complaint", ""), "dx": c.get("diagnosis", ""), "sys": c.get("tags", []), "school": c.get("school") or "Institution to confirm", "course": c.get("course", ""), "aliases": c.get("aliases", []), "patient": c.get("patient_short", ""), "lead": c.get("lead_time", "on-request"), "href": f"/case/{c['slug']}/"} for c in CASES]
    initial = "".join(case_card_html(c) for c in CASES[:24])
    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    body = f"""
<section class="page-intro library-intro"><div class="container"><div class="intro-row"><div><span class="eyebrow">iHuman case library</span><h1>Find the case in front of you.</h1></div><p>Search by patient, presentation, school or course. Check the age and clinical details before choosing a guide.</p></div>
<div class="library-search" role="search">{icon('search', 22)}<label class="sr-only" for="catSearch">Search the case library</label><input type="search" id="catSearch" placeholder="Search a patient, condition, course or school" autocomplete="off"><button id="catSearchClear" aria-label="Clear search" hidden>×</button><span class="search-records">{len(data)} records</span></div></div></section>
<section class="library-body" id="catalog"><div class="container"><div class="catalog-toolbar">
  <label class="filter-field"><span>Clinical topic</span><select id="fSystem"><option value="">All topics</option></select></label><label class="filter-field"><span>Institution</span><select id="fSchool"><option value="">All institutions</option></select></label><label class="filter-field"><span>Availability</span><select id="fLead"><option value="">All availability</option><option value="same-day">Same-day guide</option><option value="fast-build">24–48h build</option><option value="on-request">Confirm availability</option></select></label><button class="filter-clear" id="filterClear" hidden>Reset filters</button>
</div><div class="catalog-results-head"><p id="catCount" role="status" aria-live="polite">{len(data)} cases in the library</p><span>Preview a guide before requesting it.</span></div><div class="case-grid" id="caseGrid">{initial}</div><div class="cat-empty" id="catEmpty" hidden>{icon('search', 30)}<h2>No matching cases yet.</h2><p>Try a patient surname, another course code, or fewer filters.</p><div class="btn-row"><button class="btn btn-lime" data-reset-catalog>Reset my search</button><button class="btn btn-ghost" data-order="Case request" data-alias="" data-price="150" data-delivery="availability confirmed before payment">Request a case</button></div></div><div class="load-more-wrap"><button id="catLoadMore" class="btn btn-ghost">Show more cases</button></div>
<noscript><p>JavaScript enables search and bundle selection. The complete list is available below.</p><div class="case-grid">{''.join(case_card_html(c) for c in CASES[24:])}</div></noscript>
</div></section><div class="bundle-bar" id="bundleBar" role="region" aria-label="Selected case bundle" aria-live="polite" inert><div class="bundle-bar-inner"><div class="bundle-info"><span data-bundle-count>0 cases</span><span data-bundle-total>$0</span><span data-bundle-save></span></div><div class="bundle-list" data-bundle-list></div><button class="btn btn-lime" data-bundle-order>Request bundle invoice</button></div></div>"""
    write_page("cases", body, title="Case Library", description=f"Search {len(data)} CPL catalog records by patient, condition, school or course. Preview guide pages and confirm your case version.", page_class="catalog", body_scripts=f'<script>window.CPL_CASES={data_json};</script><script src="/cpl-catalog.js?v={V}" defer></script>')


# ─── Case pages ───────────────────────────────────────────────────
def gallery_html(case, preview):
    if not preview:
        return '<div class="preview-notice"><h3>Case-specific preview pending.</h3><p>Contact CPL to confirm the available material for this case before requesting an invoice.</p><a class="link-arrow" href="/sample-guide/">Explore the sample guide format →</a></div>'
    pages = []
    if not preview["is_sample"]:
        label = "Pages from this case guide"
        description = f"Selected pages from {case['title']}. Open a page to read it at full size."
        for n in preview["clear_pages"]:
            pages.append((f"/previews/{case['slug']}/page_{n}.png", preview["section_labels"].get(str(n), f"Page {n}"), f"Page {n}"))
    else:
        source = preview.get("sample_source")
        if not source:
            return gallery_html(case, None)
        label = "Guide format example"
        description = f"These format samples are from {preview['source_title']}. We confirm the content and version for {case['title']} before invoicing."
        for n, title in [(1, "Case overview"), (2, "History"), (3, "Physical examination"), (4, "Tests & differentials")]:
            pages.append((f"/previews/_watermarked/{source}/sample_{n}.png", title, "Format sample"))
    cards = "".join(f'<button type="button" class="gpage" data-lightbox="{e(path)}" aria-label="Open {e(title)} preview"><span class="gpage-frame"><img src="{e(path)}" alt="{e(title)} — {e(tag)}" loading="lazy"></span><span class="gpage-label"><small>{e(tag)}</small><strong>{e(title)}</strong><span>Open preview</span></span></button>' for path, title, tag in pages)
    return f'<div class="preview-heading"><span class="eyebrow">{e(label)}</span><h2>Look inside the guide.</h2><p>{e(description)}</p></div><div class="gallery">{cards}</div>'


def build_case_preview(case):
    name, focus = split_title(case)
    lead = case.get("lead_time", "on-request")
    preview = build.get_preview_data(case["slug"])
    tp = topic(case)
    metadata = "".join(f'<div><dt>{e(label)}</dt><dd>{e(value or "To confirm")}</dd></div>' for label, value in [("Patient", case.get("patient_short")), ("Course", case.get("course")), ("Institution", case.get("school")), ("Clinical topic", tp)])
    workflow = "".join(f'<li><span class="mono">{i:02}</span><div><h3>{e(title)}</h3><p>{e(description)}</p></div></li>' for i, (title, description) in enumerate(WORKFLOW, 1))
    source_note = case.get("source_note", "Confirm the patient age, presentation and course against your current assignment. Patient names alone do not establish a case match.")
    transcript = ""
    if case.get("history_excerpt"):
        rows = "".join(f'<div class="transcript-row"><span class="eyebrow-sm">Question asked</span><h3>{e(q)}</h3><span class="eyebrow-sm">Patient response</span><p>“{e(a)}”</p></div>' for q, a in case["history_excerpt"])
        transcript = f'<section class="case-section" id="history"><span class="eyebrow">Source excerpt · History</span><h2>The recorded interview.</h2><div class="transcript-list">{rows}</div></section>'
    price = PRICING["single"]["price"]
    body = f"""
<section class="case-intro"><div class="container"><nav class="breadcrumb" aria-label="Breadcrumb"><a href="/cases/">Case library</a><span>/</span><span>{e(tp)}</span><span>/</span><span>{e(name)}</span></nav><div class="case-intro-grid"><div><span class="eyebrow">Case guide preview</span><h1>{e(name)}</h1><p class="case-condition">{e(focus)}</p><p class="case-presenting">{e(case.get('chief_complaint'))}</p></div><div class="case-version-note"><span class="eyebrow-sm">Check the version</span><p>{e(source_note)}</p><a href="{e(mailto('Help me confirm my case · ' + case['title']))}">Help me confirm my case →</a></div></div><dl class="case-metadata">{metadata}</dl></div></section>
<section class="case-detail"><div class="container case-detail-grid"><div class="case-main"><nav class="case-stage-nav" aria-label="On this page"><a href="#overview">Overview</a>{'<a href="#history">History excerpt</a>' if transcript else ''}<a href="#guide-preview">Guide preview</a><a href="#case-workflow">Case workflow</a></nav>
<section class="case-section" id="overview"><span class="eyebrow">The case at a glance</span><h2>Start with the presentation.</h2><div class="case-overview-grid"><div><span class="eyebrow-sm">Reason for encounter</span><p>{e(case.get('chief_complaint'))}</p></div><div><span class="eyebrow-sm">Listed assessment</span><p>{e(case.get('diagnosis'))}</p></div></div></section>{transcript}
<section class="case-section" id="guide-preview">{gallery_html(case, preview)}</section><section class="case-section" id="case-workflow"><span class="eyebrow">From encounter to documentation</span><h2>A connected case workflow.</h2><p class="section-description">This is the structure we use to organize case material. The required sections and available evidence are confirmed for your version and course.</p><ol class="workflow-list">{workflow}</ol></section></div>
<aside class="case-aside"><div class="order-card" id="order"><span class="eyebrow-sm">Your case guide</span><h2>Study this encounter.</h2><div class="order-price"><span>$</span>{price}<small>USD</small></div>{lead_badge(lead)}<p>Word + PDF. Confirm the case match and delivery window before payment.</p><button class="btn btn-lime" data-order="{e(case['title'])}" data-price="{price}" data-delivery="{e(LEAD[lead])}">Request an invoice</button><button class="btn btn-ghost" data-access-code>{icon('lock', 16)} Enter my access code</button><ol class="order-steps"><li>Tell us your case and course.</li><li>Confirm scope and payment.</li><li>Receive access to your guide.</li></ol><p class="order-discount">First single guide: <b>CPLFIRST15</b> takes 15% off.</p></div><div class="aside-resource"><span class="human-label eyebrow-sm">{dot()}Need a person?</span><h3>Get your write-up reviewed.</h3><p>SOAP and management review by a real person. You remain the author.</p><a class="link-arrow" href="{e(HUMAN_REVIEW)}">Talk to a reviewer →</a></div></aside></div></section>"""
    write_page(f"case/{case['slug']}", body, title=case["title"], description=f"{case['title']}. {case.get('chief_complaint', '')} Explore the guide format and confirm your case version.", page_class="case-preview")


def build_sample_guide():
    case = next(c for c in CASES if c["slug"] == "bebe-babbitt-migraine")
    preview = build.get_preview_data(case["slug"])
    body = f"""{page_intro("A sample CPL guide", "See the structure. <em>Read the actual pages.</em>", "Explore selected pages from the Bebe Babbitt migraine guide: case overview, history, physical examination, and diagnostic reasoning.")}<section class="section sample-body"><div class="container">{gallery_html(case, preview)}<div class="sample-bottom"><div><h2>Make sure the guide matches your encounter.</h2><p>Use the patient details, presentation and course to check the version.</p></div><a class="btn btn-lime" href="/case/{case['slug']}/">View the Bebe Babbitt case</a></div></div></section>"""
    write_page("sample-guide", body, title="Sample Guide", description="Read selected pages from a CPL case guide: overview, history, examination and diagnostic reasoning.", page_class="sample-guide")
    write_page("case-preview", body, title="Sample Guide", description="Explore the CPL case guide format.", page_class="sample-guide")


# ─── Free resources, simulator ────────────────────────────────────
def build_free_resources():
    body = f"""{page_intro("Free clinical learning resources", "Build your method. <em>Keep it close.</em>", "Four practical PDF frameworks, from the patient interview to the management plan. Choose a single volume or keep the full set.")}
<section class="section"><div class="container">{capture_html()}<ol class="steps-row steps-row-3"><li><span class="mono">01 · Choose</span><strong>Pick your focus.</strong><span>Select the stages you want to review.</span></li><li><span class="mono">02 · Confirm</span><strong>Check your inbox.</strong><span>Open the confirmation link we send to your email.</span></li><li><span class="mono">03 · Study</span><strong>Use the frameworks.</strong><span>Return to them as you work through a case.</span></li></ol></div></section>
{closing_cta("Need guidance for a specific case?", "The case library brings the encounter and the guide preview together.", "/cases/", "Find My Case", HUMAN_REVIEW, "Talk to a real person →")}"""
    write_page("free-resources", body, title="Free Resources", description="Free PDF frameworks for history, physical examination, differential diagnosis and management planning.", page_class="free-resources")


def build_simulator():
    stages = "".join(f'<li><span class="mono">{i:02}</span><div><h3>{title}</h3><p>{description}</p></div></li>' for i, (title, description) in enumerate([("History", "Ask focused questions."), ("Examination", "Select relevant assessments."), ("Differential", "Compare the evidence."), ("Management", "Explain the next step.")], 1))
    body = f"""<section class="hero hero-plain"><div class="container simulator-grid"><div class="simulator-copy"><span class="eyebrow">The practice lab · Coming soon</span><h1>A place to practice your clinical decisions.</h1><p class="hero-lede">We are developing an interactive case simulator for history, examination, differential diagnosis and management. Join the list for a launch notification.</p><form id="waitlistForm" class="waitlist-form search-card" novalidate><label for="wlEmail" class="search-card-title">Your email address</label><div class="capture-row"><input type="email" id="wlEmail" name="email" placeholder="you@email.com" required autocomplete="email"><button type="submit" id="wlBtn" class="btn btn-lime">Notify me at launch</button></div><p id="wlMsg" role="status" aria-live="polite"></p><p class="fine">One launch email. Unsubscribe any time.</p></form><div class="inline-links"><span>Ready to study today?</span><a href="/free-resources/">Free resources</a><a href="/cases/">Case library</a></div></div><div class="sheet sheet-solo"><div class="sheet-top"><span class="eyebrow-sm muted">The encounter</span><span class="tag">In development</span></div><h2>Think through each stage.</h2><ol class="workflow-list">{stages}</ol><p class="fine">Practice first. Reflect. Build your method.</p></div></div></section>"""
    write_page("simulator", body, title="Simulator Waitlist", description="The CPL clinical case simulator is in development. Join the waitlist for one launch notification.", page_class="simulator")


# ─── About, FAQ ───────────────────────────────────────────────────
def build_about():
    body = f"""{page_intro("About Clinical Performance Lab", "Clinical reasoning <em>deserves a method.</em>", "CPL helps nursing students connect the questions they ask, the findings they document, and the decisions they make — with resources when you can handle it yourself and real human support when you need more.")}
<section class="section"><div class="container about-grid"><div class="about-index"><span class="eyebrow">Our approach</span><p>01 · The encounter<br>02 · The evidence<br>03 · The student</p></div><div class="about-prose">
<section><span class="mono">01</span><h2>Begin with the actual case.</h2><p>A useful guide follows the encounter: history questions and patient responses, examination findings, key findings, a problem statement, differentials, tests, diagnosis, management and required documentation.</p><p>Free frameworks support the method. Case guides help you study a specific presentation.</p></section>
<section><span class="mono">02</span><h2>Keep versions distinct.</h2><p>The same name or diagnosis can appear in different course versions. Patient age, presenting concerns, assignment requirements and source material matter when identifying a case.</p><p>Preview pages identify whether they come from the listed guide or illustrate the format. Availability is confirmed before invoicing.</p></section>
<section id="integrity"><span class="mono">03</span><h2>The student does the reasoning.</h2><p>CPL materials support study, practice and interpretation. You complete your own encounter and documentation in line with your institution's academic requirements.</p><p>When we review your coursework, you remain the author. We review, strengthen and explain your work. We never write or submit it for you.</p><p>We are an independent educational resource with no affiliation to iHuman, Kaplan or any institution.</p></section>
<div class="btn-row"><a class="btn btn-lime" href="/cases/">Find My Case</a><a class="btn btn-ghost" href="{e(HUMAN_REVIEW)}">Talk to a reviewer</a></div></div></div></section>"""
    write_page("about", body, title="About CPL", description="Clinical Performance Lab helps nursing students study case encounters and build a connected clinical reasoning method.", page_class="about")


def build_faq():
    items = [
        ("How do I find my case?", "Search the library by patient, presentation, course or school. Check the patient age and course details, then open the guide preview. If the details differ, contact CPL before ordering."),
        ("Does a matching patient name mean it is the same case?", "A name alone is not enough. We check the age, presentation, course and available source version. Related names in the catalog are search references, not proof that findings or responses transfer."),
        ("What do I receive with a case guide?", "Word and PDF versions of the agreed case material. The structure follows the encounter. We confirm the available content, required sections and delivery window before payment."),
        ("How fast is delivery?", "The library distinguishes same-day guides, 24–48 hour builds, and cases that require an availability check. The confirmed delivery window depends on the case version and scope."),
        ("How does payment work?", "Request an invoice from a case page or a selected bundle. CPL confirms the case and scope. After payment and delivery, use the access code from your email to open your guide. Card details are not entered on this website."),
        ("What do the guides cost?", f"A single guide is ${PRICING['single']['price']} USD, a three-case bundle is ${PRICING['bundle3']['price']}, and a five-case bundle is ${PRICING['bundle5']['price']}. CPLFIRST15 takes 15% off your first single guide. Bundle prices are already discounted."),
        ("What does human support cover?", "A real person reviews your SOAP notes, care plans, concept maps, papers and other coursework for clarity, structure, APA 7 and rubric alignment. You remain the author: we review, strengthen and explain your work, and never write or submit it for you."),
        ("Are the free resources actually free?", "Yes. Choose any of the four PDF frameworks and enter your email. We send a confirmation link, then deliver the selected resources. The sequence includes a short clinical-insight follow-up, and you can unsubscribe at any time."),
        ("Can I use the simulator now?", "The simulator is in development. Join the waitlist to receive a launch notification. The free PDF resources and case guide previews are available now."),
        ("Can I report an error or request a correction?", f"Yes. Send the case name, the version details and the discrepancy to {build.SUPPORT_EMAIL}. The existing refund policy covers a wrong case or a substantive error that cannot be corrected; see the Terms of Use."),
        ("How should I use CPL material?", "Use it for personal study, practice and academic preparation. Complete your own encounter and documentation, follow your school's rules, and use current authoritative references for real clinical decisions."),
    ]
    faqs = "".join(f'<details class="faq-item"><summary><span>{e(q)}</span><span class="faq-toggle" aria-hidden="true">+</span></summary><div><p>{e(a)}</p></div></details>' for q, a in items)
    body = f"""{page_intro("Questions &amp; answers", "A few things <em>worth knowing.</em>", "Finding the right version, ordering your guide, human support and getting started with the free resources.")}<section class="section"><div class="container faq-layout"><div class="faq-side"><span class="eyebrow">Need a specific answer?</span><h2>Talk to CPL.</h2><p>Tell us your patient, course and the question in front of you.</p><a class="link-arrow" href="mailto:{build.CONTACT_EMAIL}">{build.CONTACT_EMAIL}</a></div><div class="faq-list">{faqs}</div></div></section>"""
    schema = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]})
    write_page("faq", body, title="Questions & Answers", description="Find answers about CPL case versions, availability, guide delivery, pricing, human support and free resources.", page_class="faq", head_extra=f'<script type="application/ld+json">{schema}</script>')


# ─── Email confirmation, thank-you, legal ─────────────────────────
def build_confirm():
    body = """<section class="status-page"><div class="container"><div class="status-card">
  <div class="status-badge" id="confirmBadge">…</div>
  <h1 id="confirmTitle">Confirming your email…</h1>
  <p id="confirmSub">Validating your confirmation link. This takes a few seconds.</p>
  <div id="confirmResult" class="btn-row"></div>
</div></div></section>
<script>
(async function() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get('t');
  const titleEl = document.getElementById('confirmTitle');
  const subEl = document.getElementById('confirmSub');
  const resultEl = document.getElementById('confirmResult');

  if (!token) {
    titleEl.textContent = "Missing confirmation token";
    subEl.textContent = "This link is incomplete. Open the confirmation link directly from your email, or request a new link.";
    resultEl.innerHTML = '<a href="/free-resources/" class="btn btn-lime">Request a new link</a>';
    return;
  }

  try {
    const res = await fetch('/api/confirm?t=' + encodeURIComponent(token));
    const data = await res.json();
    if (res.ok && data.ok) {
      var badge = document.getElementById('confirmBadge');
      if (badge) { badge.textContent = '✓'; badge.classList.add('ok'); }
      titleEl.textContent = "Your PDFs are on the way!";
      subEl.textContent = "Check your inbox in a minute. We've also scheduled a short follow-up over the next week with a clinical insight you can use.";
      resultEl.innerHTML = '<a href="/cases/" class="btn btn-lime">Browse the case library</a><a href="/simulator/" class="btn btn-ghost">Join simulator waitlist</a>';
    } else {
      titleEl.textContent = "Couldn't confirm";
      subEl.textContent = data.error || "This link is invalid or expired. Try requesting a new one from the free resources page.";
      resultEl.innerHTML = '<a href="/free-resources/" class="btn btn-lime">Get a new link</a>';
    }
  } catch (e) {
    titleEl.textContent = "Something went wrong";
    subEl.textContent = "We couldn't reach the confirmation service. Try again in a minute or email support@clinicalperformancelab.com.";
  }
})();
</script>"""
    write_page("confirm", body, title="Confirm your email", description="Confirm your email and get your CPL cheat sheets.", page_class="confirm")


def build_thankyou():
    body = """<section class="status-page"><div class="container"><div class="status-card"><span class="eyebrow">Your free resources</span><h1>Check your inbox.</h1><p>Open the confirmation link in the email we just sent. The link is valid for 24 hours. Once you confirm, we will send your selected PDFs.</p><div class="status-note"><h3>No email yet?</h3><p>Check your spam or promotions folder. If the address was mistyped, return to the resources page and try again.</p></div><div class="btn-row"><a href="/cases/" class="btn btn-lime">Explore the case library</a><a href="/free-resources/" class="btn btn-ghost">Back to resources</a></div></div></div></section>"""
    write_page("thank-you", body, title="Check your inbox", description="Confirm your email to receive your selected Clinical Performance Lab PDF resources.", page_class="thank-you")


def build_legal():
    terms_body = """<section class="section"><div class="container"><div class="prose">
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
</div></div></section>"""
    privacy_body = """<section class="section"><div class="container"><div class="prose">
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
</div></div></section>"""
    write_page("terms", terms_body, title="Terms of Use", page_class="legal")
    write_page("privacy", privacy_body, title="Privacy", page_class="legal")


def build_pages():
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
    build_thankyou()
    print("  ✓ confirm/ + thank-you/")
    build_simulator()
    print("  ✓ simulator/")
    build_sample_guide()
    print("  ✓ sample-guide/")
    build_about()
    build_faq()
    print("  ✓ about/ + faq/")
    build_legal()
    print("  ✓ terms/ + privacy/")
