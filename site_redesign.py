"""Public CPL presentation using the existing catalog, previews and API contracts."""
import html
import json
from urllib.parse import urlencode

B = {}
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
RESOURCE_TEXT = {
    "history": "Build a focused interview with OLDCARTS, a relevant review of systems, and clear clinical language.",
    "physical-exam": "Organize the examination around the presentation and document the findings clearly.",
    "ddx": "Connect key findings to a problem statement and a reasoned differential.",
    "plan": "Structure management, patient education, follow-up and SOAP documentation.",
}
LEAD = {"same-day": "Same-day guide", "fast-build": "24–48h build", "on-request": "Confirm availability"}


def e(value):
    return html.escape(str(value or ""), quote=True)


def search_url(query):
    return "/cases/?" + urlencode({"q": query})


def icon(name, size=20):
    paths = {
        "search": '<circle cx="10.8" cy="10.8" r="6.5"/><path d="m16 16 4.5 4.5"/>',
        "book": '<path d="M12 5.5C8 3 4 4 3 4.5v15c3-1 6-1 9 1 3-2 6-2 9-1v-15c-3-1-6-1-9 1Z"/><path d="M12 5.5v15"/>',
        "lock": '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/><path d="M12 14v3"/>',
        "layers": '<path d="m12 3 10 5-10 5L2 8l10-5Z"/><path d="m2 12 10 5 10-5M2 16l10 5 10-5"/>',
        "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    }
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg>'


def nav_html():
    return f"""
<a class="skip-link" href="#main-content">Skip to content</a>
<header class="nav"><div class="nav-inner">
  <a href="/" class="nav-brand" aria-label="Clinical Performance Lab home"><span class="nav-logo">CPL<span></span></span><span class="brand-name">Clinical<br>Performance Lab</span></a>
  <nav aria-label="Main navigation"><ul class="nav-links"><li><a href="/cases/">Case library</a></li><li><a href="/free-resources/">Free resources</a></li><li><a href="/simulator/">Simulator <span class="nav-soon">Soon</span></a></li><li><a href="/about/">About</a></li></ul></nav>
  <div class="nav-actions"><button class="guide-access nav-cta-desktop" data-access-code>{icon('lock',16)} Access my guide</button><button class="nav-burger" aria-label="Open menu" aria-expanded="false" aria-controls="mobileMenu">{icon('menu',24)}</button></div>
</div></header>
<div class="menu-backdrop"></div>
<nav class="mobile-menu" id="mobileMenu" aria-label="Mobile navigation" aria-hidden="true" inert>
  <div class="mobile-menu-head"><span class="small-label">Clinical Performance Lab</span><button class="mobile-menu-close" data-menu-close aria-label="Close menu">×</button></div>
  <a href="/cases/" data-menu-close>Case library</a><a href="/free-resources/" data-menu-close>Free resources</a><a href="/simulator/" data-menu-close>Simulator · coming soon</a><a href="/sample-guide/" data-menu-close>Sample guide</a><a href="/about/" data-menu-close>About CPL</a><a href="/faq/" data-menu-close>Questions &amp; answers</a><button class="btn btn-primary" data-access-code data-menu-close>Access my guide</button>
</nav>"""


def footer_html():
    return f"""
<footer class="footer"><div class="container footer-inner">
  <div class="footer-intro"><a class="footer-brand" href="/">Clinical Performance Lab<span>™</span></a><p>Study the encounter.<br>Understand the reasoning.</p><a class="footer-email" href="mailto:{B['CONTACT_EMAIL']}">{B['CONTACT_EMAIL']}</a></div>
  <div><h3>Study</h3><a href="/cases/">Case library</a><a href="/sample-guide/">Sample guide</a><a href="/free-resources/">Free resources</a><a href="/simulator/">Simulator waitlist</a></div>
  <div><h3>Get help</h3><a href="/faq/">Questions &amp; answers</a><a href="/about/">About CPL</a><a href="mailto:{B['SUPPORT_EMAIL']}">Contact support</a><button data-access-code>Access my guide</button></div>
  <div><h3>The details</h3><a href="/terms/">Terms of use</a><a href="/privacy/">Privacy</a><p class="footer-note">Independent educational resource.<br>Not affiliated with iHuman, Kaplan, or any institution.</p></div>
</div><div class="container footer-bottom"><span>© {B['datetime'].now(B['timezone'].utc).year} Clinical Performance Lab</span><span>For personal study and academic preparation.</span></div></footer>"""


def case_card_html(case):
    name, _, focus = case["title"].partition("—")
    lead = case.get("lead_time", "on-request")
    tags = [t for t in case.get("tags", []) if t != "Adult"]
    return f"""
<a class="case-card" href="/case/{e(case['slug'])}/">
  <div class="card-top"><span class="system-label">{e(tags[0] if tags else 'Clinical')}</span>{icon('book',19)}</div>
  <h3>{e(name.strip())}</h3><p class="case-focus">{e(focus.strip() or case.get('diagnosis'))}</p><p class="case-cc">{e(case.get('chief_complaint'))}</p>
  <div class="card-course">{e(case.get('course') or 'Course to confirm')}<span>{e(case.get('school') or 'Institution to confirm')}</span></div>
  <div class="case-bottom"><span class="availability {'ready' if lead == 'same-day' else ''}">{e(LEAD[lead])}</span><span class="case-view">View case</span></div>
</a>"""


def resource_card(cs, selected=False):
    return f"""
<label class="resource-card {'selected' if selected else ''}" data-id="{e(cs['id'])}">
  <input type="checkbox" name="volumes" value="{e(cs['id'])}" {'checked' if selected else ''}>
  <span class="resource-stage">Volume {e(cs['vol'])} <span>PDF</span></span><span class="resource-title">{e(cs['title'])}</span><span class="resource-description">{e(RESOURCE_TEXT[cs['id']])}</span><span class="resource-meta">{cs['pages']} pages · Free resource</span>
</label>"""


def capture_html(selected=True):
    cards = "".join(resource_card(cs, selected) for cs in B["CHEAT_SHEETS"])
    return f"""
<form data-capture class="resource-form"><div class="resource-grid">{cards}</div>
<div class="capture"><div class="capture-copy"><h3>Send these to my inbox.</h3><p>Choose your PDFs. Confirm your email. Start studying.</p></div><div class="capture-fields"><label class="sr-only" for="resourceEmail">Your email address</label><div class="capture-row"><input type="email" id="resourceEmail" name="email" placeholder="Your email address" required autocomplete="email"><button type="submit" class="btn btn-lime">Send my resources</button></div><p class="capture-fine">Includes a short clinical-insight follow-up. Unsubscribe any time.</p><p data-capture-msg role="status" aria-live="polite" hidden></p></div></div></form>"""


def pricing_html():
    cards = ""
    for key, feature in [("single", False), ("bundle3", True), ("bundle5", False)]:
        p = B["PRICING"][key]
        count = {"single": 1, "bundle3": 3, "bundle5": 5}[key]
        detail = "Word + PDF" if not p["saves"] else f"Save &#36;{p['saves']} with the bundle"
        cards += f"""
<article class="price-card {'featured' if feature else ''}"><div class="price-top"><h3>{e(p['label'])}</h3>{'<span class="price-tag">Popular bundle</span>' if feature else ''}</div><p class="price-amount"><span>$</span>{p['price']}<small>USD</small></p><p>{'Focus on one case.' if count == 1 else f'Choose any {count} cases from the library.'}</p><div class="price-detail">{detail}</div><a href="/cases/" class="btn {'btn-lime' if feature else 'btn-ghost'}">{'Find my case' if count == 1 else 'Build my bundle'}</a></article>"""
    return f"""<section class="section" id="pricing"><div class="container"><div class="section-heading"><div><span class="small-label">Case guides</span><h2>Focused support.<br>Clear pricing.</h2></div><p>Preview the format, confirm your case version, then request an invoice. Availability is shown for each case.</p></div><div class="pricing-grid">{cards}</div><p class="pricing-note">First single guide? Use <strong>CPLFIRST15</strong> for 15% off. Bundle prices are already discounted.</p></div></section>"""


def build_home():
    featured = [c for c in B["CASES"] if c.get("lead_time") == "same-day"][:6]
    cases = "".join(case_card_html(c) for c in featured)
    courses = [("Chamberlain", "NR 509", "Advanced physical assessment"), ("Chamberlain", "NR 602", "Pediatric & family care"), ("Walden", "NURS 6512", "Health assessment & reasoning"), ("Walden", "NRNP 6531", "Adult primary care")]
    course_html = "".join(f'<a class="course-tile" href="{e(search_url(code))}"><span>{e(school)}</span><h3>{e(code)}</h3><p>{e(label)}</p></a>' for school, code, label in courses)
    body = f"""
<section class="lab-hero"><div class="container hero-grid"><div class="hero-copy">
  <span class="small-label hero-label">A lab for clinical reasoning</span><h1>Understand the case.<br><em>Explain your decisions.</em></h1><p class="hero-description">Case guides and practical frameworks for nursing students. Work through the encounter, from the first question to a clear management plan.</p>
  <form action="/cases/" method="get" class="hero-search" role="search">{icon('search')}<label class="sr-only" for="homeSearch">Find a patient, course, or presentation</label><input id="homeSearch" type="search" name="q" placeholder="Patient or course" autocomplete="off"><button class="btn btn-primary" type="submit">Find a case</button></form>
  <div class="popular-searches"><span>Explore</span><a href="{e(search_url('NR 509'))}">NR 509</a><a href="{e(search_url('NR 602'))}">NR 602</a><a href="{e(search_url('Walden'))}">Walden cases</a></div><div class="hero-small-links"><a href="/free-resources/">{icon('layers',17)} Start with free resources</a><a href="/sample-guide/">{icon('book',17)} Explore a sample guide</a></div>
</div><div class="encounter"><div class="encounter-top"><span>{icon('book',17)} Inside the encounter</span><span class="transcript-label">History</span></div><div class="encounter-patient"><span class="small-label">Case transcript · Kristina Hart</span><h2>A better question.<br>A clearer picture.</h2></div>
  <div class="excerpt-tabs" role="tablist" aria-label="Recorded history questions"><button id="excerptTab0" role="tab" aria-selected="true" aria-controls="excerptPanel" data-excerpt="0">01 · Presenting concern</button><button id="excerptTab1" role="tab" aria-selected="false" aria-controls="excerptPanel" tabindex="-1" data-excerpt="1">02 · Other symptoms</button></div>
  <div id="excerptPanel" class="excerpt-panel" role="tabpanel" aria-labelledby="excerptTab0" tabindex="0"><span class="question-label">Question asked</span><p class="excerpt-question" data-excerpt-question>“How can I help you today?”</p><div class="patient-response"><span class="question-label">Patient response</span><p data-excerpt-response>“I've been having some pain and burning when I urinate.”</p></div></div>
  <div class="encounter-foot"><span>Actual recorded exchange</span><a href="/case/kristina-hart-cervicitis-kaplan/">Explore this case</a></div>
</div></div></section>
<section class="course-section"><div class="container"><div class="course-heading"><span class="small-label">Find your course</span><a href="/cases/">View the full library</a></div><div class="course-grid">{course_html}</div></div></section>
<section class="section" id="cases"><div class="container"><div class="section-heading"><div><span class="small-label">The case library</span><h2>Your next encounter<br>starts here.</h2></div><div class="section-side"><p>Browse {len(B['CASES'])} catalog records. Check the patient, presentation and course to find the right version.</p><a class="text-link" href="/cases/">Browse all cases</a></div></div><div class="case-grid">{cases}</div></div></section>
<section class="method-section" id="how"><div class="container method-grid"><div><span class="small-label">The method</span><h2>Follow the encounter.<br>Keep the reasoning connected.</h2><p>Each stage should help explain the next. Use your case guide alongside your current assignment instructions.</p><a class="btn btn-lime" href="/sample-guide/">See the guide structure</a></div><ol class="method-list"><li><span>01</span><div><h3>Ask with purpose</h3><p>History questions, patient responses and relevant findings.</p></div></li><li><span>02</span><div><h3>Examine what matters</h3><p>Physical examination choices and documentation.</p></div></li><li><span>03</span><div><h3>Reason from the evidence</h3><p>Key findings, differentials, tests and diagnosis.</p></div></li><li><span>04</span><div><h3>Make the plan clear</h3><p>Management, education, follow-up and required notes.</p></div></li></ol></div></section>
<section class="section resources-section" id="free"><div class="container"><div class="section-heading"><div><span class="small-label">Free resources</span><h2>A method you can<br>return to.</h2></div><p>Four PDF frameworks for the core stages of a clinical encounter. Choose the areas you want to strengthen.</p></div>{capture_html()}</div></section>
{pricing_html()}
<section class="closing-section"><div class="container closing-inner"><div><span class="small-label">Need a little direction?</span><h2>Bring us the case<br>in front of you.</h2></div><div><p>Different patient name, uncertain course mapping, or a case you cannot find? We can help you check the match.</p><a class="btn btn-primary" href="mailto:{B['CONTACT_EMAIL']}">Talk to CPL</a><a class="text-link" href="/faq/">Read the FAQs</a></div></div></section>"""
    B["write_page"]("", body, description="Explore iHuman case guides and free clinical reasoning resources. Search by patient, presentation, school or course.", page_class="home")


def build_catalog():
    data = [{"t": c["title"], "cc": c.get("chief_complaint", ""), "dx": c.get("diagnosis", ""), "sys": c.get("tags", []), "school": c.get("school") or "Institution to confirm", "course": c.get("course", ""), "aliases": c.get("aliases", []), "patient": c.get("patient_short", ""), "lead": c.get("lead_time", "on-request"), "href": f"/case/{c['slug']}/"} for c in B["CASES"]]
    initial = "".join(case_card_html(c) for c in B["CASES"][:24])
    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    body = f"""
<section class="page-intro library-intro"><div class="container"><div class="intro-row"><div><span class="small-label">The case library</span><h1>Find the case<br>in front of you.</h1></div><p>Search by patient, presentation, school or course. Check the age and clinical details before choosing a guide.</p></div><div class="library-search" role="search">{icon('search',24)}<label class="sr-only" for="catSearch">Search the case library</label><input type="search" id="catSearch" placeholder="Search a patient, condition, course or school" autocomplete="off"><button id="catSearchClear" aria-label="Clear search" hidden>×</button><span class="search-records">{len(data)} records</span></div></div></section>
<section class="library-body" id="catalog"><div class="container"><div class="catalog-toolbar">
  <label class="filter-field"><span>Clinical topic</span><select id="fSystem"><option value="">All topics</option></select></label><label class="filter-field"><span>Institution</span><select id="fSchool"><option value="">All institutions</option></select></label><label class="filter-field"><span>Availability</span><select id="fLead"><option value="">All availability</option><option value="same-day">Same-day guide</option><option value="fast-build">24–48h build</option><option value="on-request">Confirm availability</option></select></label><button class="filter-clear" id="filterClear" hidden>Reset filters</button>
</div><div class="catalog-results-head"><p id="catCount" role="status" aria-live="polite">{len(data)} cases in the library</p><span>Preview a guide before requesting it.</span></div><div class="case-grid" id="caseGrid">{initial}</div><div class="cat-empty" id="catEmpty" hidden>{icon('search',30)}<h2>No matching cases yet.</h2><p>Try a patient surname, another course code, or fewer filters.</p><button class="btn btn-primary" data-reset-catalog>Reset my search</button><a class="text-link" href="mailto:{B['CONTACT_EMAIL']}">Ask us about your case</a></div><div class="load-more-wrap"><button id="catLoadMore" class="btn btn-ghost">Show more cases</button></div>
<noscript><p>JavaScript enables search and bundle selection. The complete list is available below.</p><div class="case-grid">{''.join(case_card_html(c) for c in B['CASES'][24:])}</div></noscript>
</div></section><div class="bundle-bar" id="bundleBar" role="region" aria-label="Selected case bundle" aria-live="polite" inert><div class="bundle-bar-inner"><div class="bundle-info"><span data-bundle-count>0 cases</span><span data-bundle-total>$0</span><span data-bundle-save></span></div><div class="bundle-list" data-bundle-list></div><button class="btn btn-lime" data-bundle-order>Request bundle invoice</button></div></div>"""
    B["write_page"]("cases", body, title="Case Library", description=f"Search {len(data)} CPL catalog records by patient, condition, school or course. Preview guide pages and confirm your case version.", page_class="catalog", body_scripts=f'<script>window.CPL_CASES={data_json};</script><script src="/cpl-catalog.js?v=20261002-redesign" defer></script>')


def build_free_resources():
    body = f"""
<section class="page-intro"><div class="container intro-row"><div><span class="small-label">Free clinical learning resources</span><h1>Build your method.<br><em>Keep it close.</em></h1></div><p>Four practical PDF frameworks, from the patient interview to the management plan. Choose a single volume or keep the full set.</p></div></section><section class="section resource-download-section"><div class="container">{capture_html()}<div class="resource-explanation"><div><span class="small-label">01 · Choose</span><h3>Pick your focus.</h3><p>Select the stages you want to review.</p></div><div><span class="small-label">02 · Confirm</span><h3>Check your inbox.</h3><p>Open the confirmation link we send to your email.</p></div><div><span class="small-label">03 · Study</span><h3>Use the frameworks.</h3><p>Return to them as you work through a case.</p></div></div></div></section><section class="closing-section"><div class="container closing-inner"><h2>Need guidance<br>for a specific case?</h2><div><p>The case library brings the encounter and the guide preview together.</p><a class="btn btn-primary" href="/cases/">Explore the case library</a></div></div></section>"""
    B["write_page"]("free-resources", body, title="Free Resources", description="Free PDF frameworks for history, physical examination, differential diagnosis and management planning.", page_class="free-resources")


def gallery_html(case, preview):
    if not preview:
        return '<div class="preview-notice"><h3>Case-specific preview pending.</h3><p>Contact CPL to confirm the available material for this case before requesting an invoice.</p><a class="text-link" href="/sample-guide/">Explore the sample guide format</a></div>'
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
    return f'<div class="preview-heading"><span class="small-label">{e(label)}</span><h2>Look inside the guide.</h2><p>{e(description)}</p></div><div class="gallery">{cards}</div>'


def build_case_preview(case):
    name, _, focus = case["title"].partition("—")
    lead = case.get("lead_time", "on-request")
    preview = B["get_preview_data"](case["slug"])
    topic = (case.get("tags") or ["Clinical"])[0]
    metadata = "".join(f'<div><dt>{e(label)}</dt><dd>{e(value or "To confirm")}</dd></div>' for label, value in [("Patient", case.get("patient_short")), ("Course", case.get("course")), ("Institution", case.get("school")), ("Clinical topic", topic)])
    workflow = "".join(f'<li><span>{i:02}</span><div><h3>{e(title)}</h3><p>{e(description)}</p></div></li>' for i, (title, description) in enumerate(WORKFLOW, 1))
    source_note = case.get("source_note", "Confirm the patient age, presentation and course against your current assignment. Patient names alone do not establish a case match.")
    transcript = ""
    if case.get("history_excerpt"):
        rows = "".join(f'<div class="transcript-row"><span class="small-label">Question asked</span><h3>{e(q)}</h3><span class="small-label">Patient response</span><p>“{e(a)}”</p></div>' for q, a in case["history_excerpt"])
        transcript = f'<section class="case-section" id="history"><span class="small-label">Source excerpt · History</span><h2>The recorded interview.</h2><div class="transcript-list">{rows}</div><p class="source-caption">Excerpt from the Kristina Hart interview transcript supplied to CPL. These responses belong to this recorded encounter.</p></section>'
    body = f"""
<section class="case-intro"><div class="container"><nav class="breadcrumb" aria-label="Breadcrumb"><a href="/cases/">Case library</a><span>/</span><span>{e(topic)}</span><span>/</span><span>{e(name.strip())}</span></nav><div class="case-intro-grid"><div><span class="small-label">Case guide preview</span><h1>{e(name.strip())}</h1><p class="case-condition">{e(focus.strip() or case.get('diagnosis'))}</p><p class="case-presenting">{e(case.get('chief_complaint'))}</p></div><div class="case-version-note"><span class="small-label">Check the version</span><p>{e(source_note)}</p><a href="mailto:{B['CONTACT_EMAIL']}">Help me confirm my case</a></div></div><dl class="case-metadata">{metadata}</dl></div></section>
<section class="case-detail"><div class="container case-detail-grid"><div class="case-main"><div class="case-stage-nav"><a href="#overview">Overview</a>{'<a href="#history">History excerpt</a>' if transcript else ''}<a href="#guide-preview">Guide preview</a><a href="#case-workflow">Case workflow</a></div>
<section class="case-section" id="overview"><span class="small-label">The case at a glance</span><h2>Start with the presentation.</h2><div class="case-overview-grid"><div><span class="small-label">Reason for encounter</span><p>{e(case.get('chief_complaint'))}</p></div><div><span class="small-label">Listed assessment</span><p>{e(case.get('diagnosis'))}</p></div></div></section>{transcript}
<section class="case-section" id="guide-preview">{gallery_html(case, preview)}</section><section class="case-section" id="case-workflow"><span class="small-label">From encounter to documentation</span><h2>A connected case workflow.</h2><p class="section-description">This is the structure we use to organize case material. The required sections and available evidence are confirmed for your version and course.</p><ol class="workflow-list">{workflow}</ol></section></div>
<aside class="case-aside"><div class="order-card" id="order"><span class="small-label">Your case guide</span><h2>Study this encounter.</h2><div class="order-price"><span>$</span>150<small>USD</small></div><span class="availability {'ready' if lead == 'same-day' else ''}">{e(LEAD[lead])}</span><p>Word + PDF. Confirm the case match and delivery window before payment.</p><button class="btn btn-lime" data-order="{e(case['title'])}" data-price="150" data-delivery="{e(LEAD[lead])}">Request an invoice</button><button class="btn btn-ghost-dark" data-access-code>{icon('lock',16)} Enter my access code</button><ol class="order-steps"><li>Tell us your case and course.</li><li>Confirm scope and payment.</li><li>Receive access to your guide.</li></ol><p class="order-discount">First single guide: <b>CPLFIRST15</b> takes 15% off.</p></div><div class="aside-resource"><span class="small-label">Start free</span><h3>Strengthen your method.</h3><p>History, examination, differentials and management: four free PDF frameworks.</p><a class="text-link" href="/free-resources/">Get the free resources</a></div></aside></div></section>"""
    B["write_page"](f"case/{case['slug']}", body, title=case["title"], description=f"{case['title']}. {case.get('chief_complaint','')} Explore the guide format and confirm your case version.", page_class="case-preview")


def build_sample_guide():
    case = next(c for c in B["CASES"] if c["slug"] == "bebe-babbitt-migraine")
    preview = B["get_preview_data"](case["slug"])
    body = f"""<section class="page-intro"><div class="container intro-row"><div><span class="small-label">A sample CPL guide</span><h1>See the structure.<br><em>Read the actual pages.</em></h1></div><p>Explore selected pages from the Bebe Babbitt migraine guide: case overview, history, physical examination, and diagnostic reasoning.</p></div></section><section class="section sample-body"><div class="container">{gallery_html(case, preview)}<div class="sample-bottom"><div><h2>Make sure the guide<br>matches your encounter.</h2><p>Use the patient details, presentation and course to check the version.</p></div><a class="btn btn-primary" href="/case/{case['slug']}/">View the Bebe Babbitt case</a></div></div></section>"""
    B["write_page"]("sample-guide", body, title="Sample Guide", description="Read selected pages from a CPL case guide: overview, history, examination and diagnostic reasoning.", page_class="sample-guide")
    B["write_page"]("case-preview", body, title="Sample Guide", description="Explore the CPL case guide format.", page_class="sample-guide")


def build_simulator():
    stages = "".join(f'<li><span>{i:02}</span><div><h3>{title}</h3><p>{description}</p></div></li>' for i, (title, description) in enumerate([("History", "Ask focused questions."), ("Examination", "Select relevant assessments."), ("Differential", "Compare the evidence."), ("Management", "Explain the next step.")], 1))
    body = f"""<section class="simulator-section"><div class="container simulator-grid"><div class="simulator-copy"><span class="small-label">The practice lab · Coming soon</span><h1>A place to practice<br><em>your clinical decisions.</em></h1><p>We are developing an interactive case simulator for history, examination, differential diagnosis and management. Join the list for a launch notification.</p><form id="waitlistForm" class="waitlist-form" novalidate><label for="wlEmail">Your email address</label><div class="capture-row"><input type="email" id="wlEmail" name="email" placeholder="you@email.com" required autocomplete="email"><button type="submit" id="wlBtn" class="btn btn-primary">Notify me at launch</button></div><p id="wlMsg" role="status" aria-live="polite"></p><p class="form-fine">One launch email. Unsubscribe any time.</p></form><div class="simulator-links"><span>Ready to study today?</span><a href="/free-resources/">Free resources</a><a href="/cases/">Case library</a></div></div><div class="simulator-outline"><div class="outline-header">{icon('layers',20)}<span>THE ENCOUNTER</span><span class="outline-status">In development</span></div><h2>Think through<br>each stage.</h2><ol>{stages}</ol><div class="outline-footer">Practice first. Reflect. Build your method.</div></div></div></section>"""
    B["write_page"]("simulator", body, title="Simulator Waitlist", description="The CPL clinical case simulator is in development. Join the waitlist for one launch notification.", page_class="simulator")


def build_about():
    body = """<section class="page-intro"><div class="container intro-row"><div><span class="small-label">About Clinical Performance Lab</span><h1>Clinical reasoning<br><em>deserves a method.</em></h1></div><p>CPL helps nursing students connect the questions they ask, the findings they document, and the decisions they make in a clinical encounter.</p></div></section><section class="section"><div class="container about-grid"><div class="about-index"><span class="small-label">Our approach</span><p>01 · The encounter<br>02 · The evidence<br>03 · The student</p></div><div class="about-prose"><section><span class="small-label">01</span><h2>Begin with the actual case.</h2><p>A useful guide follows the encounter: history questions and patient responses, examination findings, key findings, a problem statement, differentials, tests, diagnosis, management and required documentation.</p><p>Free frameworks support the method. Case guides help you study a specific presentation.</p></section><section><span class="small-label">02</span><h2>Keep versions distinct.</h2><p>The same name or diagnosis can appear in different course versions. Patient age, presenting concerns, assignment requirements and source material matter when identifying a case.</p><p>Preview pages identify whether they come from the listed guide or illustrate the format. Availability is confirmed before invoicing.</p></section><section><span class="small-label">03</span><h2>The student does the reasoning.</h2><p>CPL materials support study, practice and interpretation. You complete your own encounter and documentation in line with your institution's academic requirements.</p><p>We are an independent educational resource with no affiliation to iHuman, Kaplan or any institution.</p></section><a class="btn btn-primary" href="/cases/">Explore the case library</a></div></div></section>"""
    B["write_page"]("about", body, title="About CPL", description="Clinical Performance Lab helps nursing students study case encounters and build a connected clinical reasoning method.", page_class="about")


def build_faq():
    items = [
        ("How do I find my case?", "Search the library by patient, presentation, course or school. Check the patient age and course details, then open the guide preview. If the details differ, contact CPL before ordering."),
        ("Does a matching patient name mean it is the same case?", "A name alone is not enough. We check the age, presentation, course and available source version. Related names in the catalog are search references, not proof that findings or responses transfer."),
        ("What do I receive with a case guide?", "Word and PDF versions of the agreed case material. The structure follows the encounter. We confirm the available content, required sections and delivery window before payment."),
        ("How fast is delivery?", "The library distinguishes same-day guides, 24–48 hour builds, and cases that require an availability check. The confirmed delivery window depends on the case version and scope."),
        ("How does payment work?", "Request an invoice from a case page or a selected bundle. CPL confirms the case and scope. After payment and delivery, use the access code from your email to open your guide. Card details are not entered on this website."),
        ("What do the guides cost?", "A single guide is $150 USD, a three-case bundle is $390, and a five-case bundle is $540. CPLFIRST15 takes 15% off your first single guide. Bundle prices are already discounted."),
        ("Are the free resources actually free?", "Yes. Choose any of the four PDF frameworks and enter your email. We send a confirmation link, then deliver the selected resources. The sequence includes a short clinical-insight follow-up, and you can unsubscribe at any time."),
        ("Can I use the simulator now?", "The simulator is in development. Join the waitlist to receive a launch notification. The free PDF resources and case guide previews are available now."),
        ("Can I report an error or request a correction?", f"Yes. Send the case name, the version details and the discrepancy to {B['SUPPORT_EMAIL']}. The existing refund policy covers a wrong case or a substantive error that cannot be corrected; see the Terms of Use."),
        ("How should I use CPL material?", "Use it for personal study, practice and academic preparation. Complete your own encounter and documentation, follow your school's rules, and use current authoritative references for real clinical decisions."),
    ]
    faqs = "".join(f'<details class="faq-item"><summary><span>{e(q)}</span><span class="faq-toggle" aria-hidden="true">+</span></summary><div><p>{e(a)}</p></div></details>' for q, a in items)
    body = f"""<section class="page-intro"><div class="container intro-row"><div><span class="small-label">Questions &amp; answers</span><h1>A few things<br><em>worth knowing.</em></h1></div><p>Finding the right version, ordering your guide, and getting started with the free resources.</p></div></section><section class="section"><div class="container faq-layout"><div><span class="small-label">Need a specific answer?</span><h2>Talk to CPL.</h2><p>Tell us your patient, course and the question in front of you.</p><a class="text-link" href="mailto:{B['CONTACT_EMAIL']}">{B['CONTACT_EMAIL']}</a></div><div class="faq-list">{faqs}</div></div></section>"""
    schema = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]})
    B["write_page"]("faq", body, title="Questions & Answers", description="Find answers about CPL case versions, availability, guide delivery, pricing and free resources.", page_class="faq", head_extra=f'<script type="application/ld+json">{schema}</script>')


def build_thankyou():
    body = """<section class="status-page"><div class="container"><div class="status-card"><span class="small-label">Your free resources</span><h1>Check your inbox.</h1><p>Open the confirmation link in the email we just sent. The link is valid for 24 hours. Once you confirm, we will send your selected PDFs.</p><div class="status-note"><h3>No email yet?</h3><p>Check your spam or promotions folder. If the address was mistyped, return to the resources page and try again.</p></div><div class="status-ctas"><a href="/cases/" class="btn btn-primary">Explore the case library</a><a href="/free-resources/" class="btn btn-ghost">Back to resources</a></div></div></div></section>"""
    B["write_page"]("thank-you", body, title="Check your inbox", description="Confirm your email to receive your selected Clinical Performance Lab PDF resources.", page_class="thank-you")


def install(builder):
    """Keep data, APIs and private operations; replace only public presentation."""
    global B
    B = builder
    B["SITE_TAG"] = "Case guides and clinical reasoning resources for nursing students."
    for name in ["nav_html", "footer_html", "case_card_html", "build_home", "build_catalog", "build_free_resources", "build_case_preview", "build_sample_guide", "build_simulator", "build_about", "build_faq", "build_thankyou"]:
        B[name] = globals()[name]
