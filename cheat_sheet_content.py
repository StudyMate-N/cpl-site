"""
Cheat sheet content database for CPL Cheat Sheet Library.
Four volumes, one per iHuman case stage.

Editorial voice: Hybrid — conversational intro, then reference-style content.
Each volume stands alone; each plugs the others quietly at the end.

Content sourced from project knowledge databases:
- History_Questions*.docx (4 files)
- Physical exam Ihuman kaplan.docx
- TESTS_ORDERED.docx
- Differentials_1.docx + Differentials_2.docx
"""

# ═══════════════════════════════════════════════════════════════════════
# VOLUME I — THE HISTORY QUESTION FRAMEWORK
# ═══════════════════════════════════════════════════════════════════════
VOL_I = {
  "volume_label": "Vol I of IV",
  "title": "The History Question Framework",
  "subtitle": "Universal questions that score on every iHuman case",
  "tagline": "History is ~40% of your score. Most students lose points not on what they ask — but on what they forget to ask.",
  "stage_id": "history",

  "intro_voice": [
    ("Here's the thing about iHuman history scoring most students don't realize:",
     "It's not testing whether you can interview the patient. It's testing whether you can systematically cover every domain that a competent clinician would cover — even when the chief complaint seems narrow."),
    ("A patient comes in with headaches. You ask about the headaches.",
     "Great. But did you ask about smoking? Family history of cardiovascular disease? Sleep quality? Recent travel? Medications including OTC and herbal? Sexual history if relevant? These are scored on most cases, regardless of the chief complaint. Miss them and you lose 10–20% before you even start."),
    ("This cheat sheet is the universal scaffolding that should be in your head before you start any iHuman case.",
     "Use it as a checklist while you're playing. Print it. Pin it. The same framework applies whether your patient is 18 months old with vomiting or 57 years old with hypertension."),
  ],

  "sections": [
    {
      "title": "The Opening Question",
      "kind": "framework",
      "body": [
        "**Always start with the patient-centered opener.** The exact phrasing matters because iHuman scores you on bedside manner.",
        "**For an adult patient:** *\"How can I help you today?\"*",
        "**For a pediatric patient (with parent):** *\"How can I help [child's name] today?\"* — directed to the parent, not the child.",
        "",
        "**The scored variation:** Some cases score a follow-up *\"What symptom is the most distressing for you?\"* — known as the pivotal communication question. Missing this is one of the most common point losses across all cases.",
      ],
    },

    {
      "title": "OLDCARTS — The HPI Mnemonic",
      "kind": "flowable",
      "flowable": "oldcarts_mnemonic",
    },

    {
      "title": "Worked Example: OLDCARTS Applied",
      "kind": "framework",
      "body": [
        "**Patient presents with chest pain.** Here's the OLDCARTS in action — the exact question script:",
        "",
        "**O**nset — *\"When did the chest pain start? What were you doing when it began?\"*",
        "**L**ocation — *\"Can you point to where it hurts? Is it in one spot or spread out?\"*",
        "**D**uration — *\"How long does each episode last? Is it constant or does it come and go?\"*",
        "**C**haracter — *\"How would you describe the pain? Sharp, dull, pressure, burning, crushing?\"*",
        "**A**ggravating — *\"What makes it worse? Exertion, eating, lying down, deep breaths?\"*",
        "**A**lleviating — *\"What makes it better? Rest, position changes, nitroglycerin, antacids?\"*",
        "**R**adiation — *\"Does the pain spread anywhere? Arm, jaw, back, shoulder?\"*",
        "**T**iming — *\"What time of day is it worse? Is there a pattern?\"*",
        "**S**everity — *\"On a scale of 1–10, how bad is it at its worst? How is it affecting your daily life?\"*",
        "",
        "**Plus associated symptoms:** *\"Any nausea, sweating, shortness of breath, palpitations, dizziness?\"*",
        "**Plus treatments tried:** *\"Have you taken anything for it? Did it help?\"*",
      ],
    },

    {
      "title": "Past Medical History (PMH) — Required Items",
      "kind": "checklist",
      "items": [
        "Existing medical conditions (chronic and acute)",
        "Hospitalizations — when and why",
        "Prior surgeries — type, date, complications",
        "Allergies — drug, food, environmental (with reaction type)",
        "Current medications — Rx, OTC, herbal, supplements",
        "Immunizations — current status (especially flu, COVID, pneumococcal, HPV)",
        "Screenings — last colonoscopy, mammogram, Pap, DXA scan (age-appropriate)",
      ],
    },

    {
      "title": "Family History (FH) — Score-Relevant Conditions",
      "kind": "checklist",
      "items": [
        "Cardiovascular: HTN, CAD, MI, stroke (note age of onset — early = significant)",
        "Endocrine: Diabetes Type 1 / Type 2, thyroid disease",
        "Cancer: type, age at diagnosis, first-degree relatives",
        "Mental health: depression, bipolar, suicide history",
        "Neurologic: seizures, dementia, migraines",
        "Genetic / hereditary conditions",
        "**Premature CVD** (MI before age 55 men, 65 women) — major risk factor; always document",
      ],
    },

    {
      "title": "",
      "kind": "mid_cta",
    },

    {
      "title": "Social History (SH) — Always-Scored Items",
      "kind": "checklist",
      "items": [
        "**Tobacco** — current, past, never. Pack-years if applicable. (1 PPD × years = pack-years)",
        "**Alcohol** — drinks/week, type, pattern",
        "**Recreational drugs** — past and current; ask non-judgmentally",
        "**Occupation** — current and relevant past exposures",
        "**Living situation** — alone, with family, safe environment",
        "**Diet** — pattern, restrictions, recent changes",
        "**Exercise** — frequency, type, duration",
        "**Sleep** — hours, quality, snoring, daytime fatigue",
        "**Sexual history** (when relevant) — partners, protection, STI history",
        "**Stress** — current stressors, coping, support system",
      ],
    },

    {
      "title": "Review of Systems (ROS) — The 14 Domains",
      "kind": "framework",
      "body": [
        "iHuman expects you to cover relevant systems even if the chief complaint is focused. Quick screening questions per system:",
        "",
        "**Constitutional** — fever, weight change, fatigue, night sweats",
        "**HEENT** — headaches, vision, hearing, sinus, throat, dental",
        "**Cardiovascular** — chest pain, palpitations, edema, dyspnea on exertion",
        "**Respiratory** — cough, sputum, SOB, wheezing, hemoptysis",
        "**GI** — appetite, nausea, vomiting, bowel habits, blood in stool, abdominal pain",
        "**GU** — frequency, urgency, dysuria, hematuria, incontinence",
        "**Musculoskeletal** — joint pain, swelling, stiffness, weakness",
        "**Skin** — rashes, lesions, itching, hair/nail changes",
        "**Neurologic** — headache, dizziness, weakness, numbness, seizures",
        "**Psychiatric** — mood, anxiety, sleep, suicidal ideation",
        "**Endocrine** — heat/cold intolerance, polyuria, polydipsia, weight changes",
        "**Hematologic/Lymphatic** — bruising, bleeding, lymph swelling",
        "**Allergic/Immunologic** — recurrent infections, allergies",
        "**Reproductive** — menstrual, pregnancies, contraception, menopause / erectile function",
      ],
    },

    {
      "title": "SNOOP4 — Headache Red Flag Screen",
      "kind": "flowable",
      "flowable": "snoop_mnemonic",
    },

    {
      "title": "Lay Language to Clinical Language",
      "kind": "translation",
      "body": [
        "**iHuman scores you on documentation. Lay language in the EHR loses points.** Use clinical terms in your notes even when the patient describes things colloquially.",
      ],
      "translations": [
        ("\"Zig-zaggy lights before my headache\"", "Scintillating scotomas (visual aura)"),
        ("\"Sensitive to light\"", "Photophobia"),
        ("\"Sensitive to sound\"", "Phonophobia"),
        ("\"Heart shifted to the side\"", "Laterally displaced PMI"),
        ("\"Eye changes\"", "Arteriovenous nicking / hypertensive retinopathy"),
        ("\"Very high blood pressure\"", "Stage 2 hypertension"),
        ("\"Bad headache with visual changes\"", "Migraine with aura"),
        ("\"Yellow spots on eyelids\"", "Xanthelasma"),
        ("\"Grey rings around the eyes\"", "Corneal arcus"),
        ("\"Trouble breathing at night\"", "Paroxysmal nocturnal dyspnea (or orthopnea if positional)"),
        ("\"Tired all the time\"", "Fatigue (note duration and impact on ADLs)"),
        ("\"Bathroom a lot at night\"", "Nocturia"),
        ("\"Pain spread to the arm\"", "Pain radiated to the arm"),
        ("\"Throwing up blood\"", "Hematemesis"),
        ("\"Blood in poop\"", "Hematochezia (bright red) or melena (dark, tarry)"),
        ("\"Couldn't catch my breath\"", "Dyspnea / shortness of breath"),
      ],
    },

    {
      "title": "Common History Traps That Cost Points",
      "kind": "traps",
      "items": [
        ("Skipping the pivotal communication question",
         "*\"What symptom is the most distressing for you?\"* — scored on most cases. Forget this and you lose pivotal-comm points."),
        ("Forgetting tobacco/alcohol history",
         "Required on virtually every case, regardless of chief complaint."),
        ("Not asking about OTC and herbal medications",
         "Patients self-medicate. The omeprazole, ibuprofen, melatonin, or fish oil they didn't think to mention is often clinically relevant."),
        ("Missing family history details",
         "Age of onset matters. *\"My dad had a heart attack\"* is different from *\"My dad had an MI at 48.\"* Premature CVD is a major risk factor and must be documented."),
        ("Asking adult-style questions to pediatric patients",
         "Pediatric history questions go to the parent. The opener is *\"How can I help [her/him] today?\"* — not *\"How can I help you?\"*"),
        ("Stopping at the HPI",
         "OLDCARTS is the start, not the end. You must cover PMH, FH, SH, and ROS even when the case feels focused."),
      ],
    },
  ],

  "outro": [
    "**The next one in the library covers Physical Exam — the other 40% of your score.** Many of the same patterns apply: there's a universal set of items that score on nearly every case (cardiac auscultation, lung fields, abdominal exam with bowel sound interpretation, fundoscopy, carotid auscultation, thyroid palpation, PMI). Miss any one of them on a case where it's scored and you lose multiple points.",
  ],
}

# ═══════════════════════════════════════════════════════════════════════
# VOLUME II — UNIVERSAL PHYSICAL EXAM ITEMS
# ═══════════════════════════════════════════════════════════════════════
VOL_II = {
  "volume_label": "Vol II of IV",
  "title": "The Universal PE Checklist",
  "subtitle": "Physical exam items that score on every iHuman case",
  "tagline": "Physical exam is the other ~40%. Most students miss the same handful of items on every case.",
  "stage_id": "physical-exam",

  "intro_voice": [
    ("Here's the pattern most students miss:",
     "iHuman doesn't just score the PE items that match the chief complaint. It scores a set of universal items that should be performed on virtually any adult clinical encounter — regardless of why the patient came in."),
    ("A patient with headaches still needs a cardiac exam. A patient with hypertension still needs a fundoscopic exam. A patient with abdominal pain still needs lung auscultation.",
     "If you're triggering the exam based only on the chief complaint, you'll consistently miss 15–20% of PE points on every case you play."),
    ("This sheet covers the universal items — the ones that score on most cases regardless of presentation.",
     "Combine this with a case-specific exam (cardiac complaints → JVP, peripheral pulses; respiratory → percussion, tactile fremitus; etc.) and you'll cover the full PE rubric on any case."),
  ],

  "sections": [
    {
      "title": "Vitals (Always Required)",
      "kind": "checklist",
      "items": [
        "**Cognitive status / level of consciousness** — A&O × 4",
        "Height, weight, BMI",
        "Blood pressure — both arms if cardiovascular complaint",
        "Heart rate — rate, regularity, strength",
        "Respiratory rate — rate, effort",
        "Temperature — oral, tympanic, or as available",
        "SpO₂ on room air",
        "**Critical**: You must view vitals in EHR Current Visit tab for credit. Performing the vital ≠ documenting it.",
      ],
    },

    {
      "title": "HEENT — The Universal Items",
      "kind": "checklist",
      "items": [
        "Inspect head — normocephalic, atraumatic",
        "**Test visual acuity** (PE item, NOT a test to order)",
        "**Examine pupils** — PERRLA",
        "**Perform fundoscopic exam** — papilledema check; AV ratio; optic disc",
        "Look in ears with otoscope — TMs, canal",
        "**Assess hearing** (PE item, NOT a test to order)",
        "Inspect nose external/internal",
        "Inspect mouth and pharynx",
        "Palpate sinuses",
      ],
    },

    {
      "title": "Neck — Always Scored",
      "kind": "checklist",
      "starred": True,
      "items": [
        "Inspect neck — symmetry, masses, JVD",
        "Palpate cervical lymph nodes",
        "**Palpate thyroid** — size, nodules, tenderness",
        "**Auscultate carotid arteries** — bruits",
        "Evaluate cervical spine ROM (if not contraindicated)",
      ],
    },

    {
      "title": "Cardiac — The 5-Point Auscultation",
      "kind": "flowable",
      "flowable": "cardiac_diagram",
    },

    {
      "title": "Documenting the Cardiac Exam",
      "kind": "framework",
      "body": [
        "**Document at minimum:** Rate, rhythm, S1/S2, presence/absence of murmurs, gallops, rubs.",
        "",
        "**Also required on most cases:**",
        "**Palpate point of maximal impulse (PMI)** — laterally displaced PMI = LVH (target organ damage in HTN)",
        "Check peripheral pulses if cardiovascular complaint",
        "Inspect for peripheral edema",
        "",
        "**Mnemonic for what to document:** *Rate, Rhythm, S1/S2, Extra sounds (M-G-R: Murmurs, Gallops, Rubs), Edema.*",
      ],
    },

    {
      "title": "Lung Field Auscultation",
      "kind": "flowable",
      "flowable": "lung_fields",
    },

    {
      "title": "Documenting Lung Findings",
      "kind": "framework",
      "body": [
        "**Listen for at each point:** Clear vs. crackles, wheezes, rhonchi, decreased breath sounds.",
        "",
        "**On a respiratory case, also do:**",
        "Percussion (resonance vs. dullness)",
        "Tactile fremitus",
        "Inspection — accessory muscle use, retractions",
        "",
        "**Documentation in the EHR:** *Lungs CTA bilaterally; no adventitious sounds; respirations even and unlabored.* If anything is abnormal, name the lobe and side.",
      ],
    },

    {
      "title": "",
      "kind": "mid_cta",
    },

    {
      "title": "Abdominal Exam",
      "kind": "flowable",
      "flowable": "abdominal_quadrants",
    },

    {
      "title": "The Order Matters: I-A-P-P",
      "kind": "framework",
      "body": [
        "**Inspect → Auscultate → Percuss → Palpate.** Auscultate *before* palpating — palpation can alter bowel sound activity.",
        "",
        "**Required steps:**",
        "**Inspect** — contour, scars, visible peristalsis",
        "**Auscultate bowel sounds in all 4 quadrants** — and *interpret* (normoactive, hyperactive, hypoactive, absent)",
        "**Auscultate for abdominal bruits** — renal artery stenosis screen, AAA",
        "Percuss — tympany vs. dullness, liver span",
        "Palpate — light then deep; note tenderness, masses, organomegaly",
        "Check for rebound, guarding, Murphy's sign if right upper quadrant",
        "",
        "**The trap:** Many students auscultate but don't *interpret* the bowel sounds in the EHR. *\"Bowel sounds present\"* loses points; *\"Normoactive bowel sounds in all four quadrants\"* earns them.",
      ],
    },

    {
      "title": "Neurologic — Standard Mini-Screen",
      "kind": "checklist",
      "items": [
        "Mental status — A&O × 4, mood, speech",
        "Cranial nerves I–XII (especially II, III, IV, VI for vision; V, VII for face; VIII for hearing; IX, X, XII for swallow/speech)",
        "Motor — strength testing in upper and lower extremities",
        "Sensation — light touch, pain, proprioception",
        "Reflexes — biceps, triceps, brachioradialis, patellar, Achilles",
        "Coordination — finger-to-nose, heel-to-shin, rapid alternating movements",
        "Gait — observe walking, tandem gait, Romberg",
      ],
    },

    {
      "title": "PE Items Often Mistaken for Tests",
      "kind": "framework",
      "body": [
        "**A subtle scoring trap:** Some items appear test-like but iHuman classifies them as Physical Exam. Listing them under \"Tests Ordered\" can trigger a faculty deduction.",
        "",
        "**These are PE items, not tests:**",
        "Visual acuity testing (Snellen)",
        "Hearing assessment (whisper test, finger rub)",
        "Mental status examination (MSE)",
        "Mini-mental state exam (MMSE)",
        "Romberg test",
        "Brudzinski's / Kernig's signs",
        "Dix-Hallpike maneuver",
      ],
    },

    {
      "title": "Common PE Traps That Cost Points",
      "kind": "traps",
      "items": [
        ("Skipping fundoscopy on cardiovascular cases",
         "Required to rule out hypertensive retinopathy. Missing AV nicking on a HTN case = missing target organ damage = wrong staging."),
        ("Documenting 'bowel sounds present' without interpretation",
         "iHuman expects *normoactive / hyperactive / hypoactive / absent.* Documenting only 'present' loses partial credit."),
        ("Forgetting PMI palpation on a HTN case",
         "Laterally displaced PMI = LVH. Skipping the palpation means missing one of two target organ damage findings."),
        ("Skipping carotid auscultation on adult cases",
         "Bruits screen is universal on adult cases — required pertinent negative."),
        ("Missing skin turgor on dehydration concerns",
         "Required on peds GE, elderly vomiting/diarrhea, DKA presentations."),
        ("Listing PE items in the Tests Ordered section",
         "Visual acuity, hearing assessment, MSE, Romberg — these are PE items. Listing under Tests triggers a deduction."),
      ],
    },
  ],

  "outro": [
    "**Next in the library: DDx and Key Findings** — how iHuman scores your differential ranking, the must-not-miss framework, and the 2–3 sentence problem statement structure that faculty look for.",
  ],
}

# ═══════════════════════════════════════════════════════════════════════
# VOLUME III — DIFFERENTIAL DIAGNOSIS & KEY FINDINGS
# ═══════════════════════════════════════════════════════════════════════
VOL_III = {
  "volume_label": "Vol III of IV",
  "title": "DDx Ranking & Key Findings",
  "subtitle": "How iHuman scores your differential — and why most students rank wrong",
  "tagline": "The Assessment section is where clinical reasoning shows. Faculty scrutinize this part — and the platform's auto-scoring is strict.",
  "stage_id": "ddx",

  "intro_voice": [
    ("Here's the thing about iHuman's differential diagnosis scoring:",
     "It's not just asking you to *list* possible diagnoses. It's testing whether you can rank them correctly — most likely first, must-not-miss prominently positioned, and ruled-out conditions explicitly addressed."),
    ("Get the ranking wrong and the score drops even when you have the right diagnosis on the list.",
     "Faculty notice this. And on top of the auto-scoring, the problem statement is faculty-scored — they're checking whether your 2-3 sentence summary captures the case clinically and uses the right level of medical language."),
    ("This sheet covers how to think about DDx ranking, how to write a strong problem statement, and how to select key findings without padding the list.",
     "These are skills, not memorization. Apply them across every case."),
  ],

  "sections": [
    {
      "title": "The Three Buckets of DDx",
      "kind": "framework",
      "body": [
        "Every differential diagnosis on iHuman falls into one of three categories. Your ranking should reflect this:",
        "",
        "**1. Most-Likely Diagnoses** — supported by history + PE + risk factors",
        "Examples: GAS pharyngitis with Centor 4/4; Stage 2 HTN with target organ damage",
        "",
        "**2. Must-Not-Miss Diagnoses** — less likely but high consequence if missed",
        "Examples: Meningitis on any headache case; OSA on any HTN/snoring case; appendicitis on RLQ pain",
        "",
        "**3. Ruled-Out (or Less Likely) Diagnoses** — considered and excluded based on evidence",
        "Examples: Hypothyroidism (ruled out by normal TSH); secondary HTN (ruled out by normal renal labs)",
        "",
        "**The structure of your DDx list should mirror these buckets** — most likely first, must-not-miss prominently, ruled-out near the bottom with explicit ruling-out rationale.",
      ],
    },

    {
      "title": "How iHuman Auto-Scores DDx",
      "kind": "framework",
      "body": [
        "**Selection matters.** Each DDx you select scores positive if it's a valid consideration, negative if it's harmful or wildly off-track.",
        "",
        "**Ranking matters.** The platform weights how you order the list. The final/primary diagnosis should be ranked #1.",
        "",
        "**Must-not-miss matters separately.** A case with a must-not-miss diagnosis (e.g., cluster headache on a migraine case, OSA on an HTN case) scores additional points only if the must-not-miss is explicitly included on your list.",
        "",
        "**Verbatim names matter.** iHuman uses a fixed dictionary of diagnosis names. If your platform expects \"Acute viral gastroenteritis\" and you select \"Stomach bug,\" you get zero. Always pick the exact platform diagnosis name.",
      ],
    },

    {
      "title": "Writing the Problem Statement",
      "kind": "flowable",
      "flowable": "problem_statement",
    },

    {
      "title": "What Faculty Look For",
      "kind": "framework",
      "body": [
        "**Clinical language** — no lay terms, no patient quotes",
        "**Inclusion of both positives and risk factors** — not just symptoms",
        "**Naming both the primary AND must-not-miss diagnoses**",
        "**Appropriate medical brevity** — 3 sentences, not 6",
      ],
    },

    {
      "title": "Centor Criteria — Sore Throat Cases",
      "kind": "flowable",
      "flowable": "centor_criteria",
    },

    {
      "title": "",
      "kind": "mid_cta",
    },

    {
      "title": "Selecting Key Findings — The Goldilocks Problem",
      "kind": "framework",
      "body": [
        "**iHuman gives you a list of 12–20 findings on most cases.** You're asked to select the ones that are *present* and *clinically relevant.*",
        "",
        "**Too many** (selecting everything): Lowers score — flags poor clinical judgment.",
        "**Too few** (selecting only obvious ones): Lowers score — misses pertinent positives.",
        "**Goldilocks** (5–10 selections on a typical case): Strongest signal of clinical reasoning.",
        "",
        "**Select if it's:**",
        "A direct symptom or sign of the working diagnosis",
        "A risk factor that strengthens the diagnosis",
        "A pertinent negative that rules out a serious alternative",
        "",
        "**Don't select if it's:**",
        "Normal/baseline (unless explicitly a pertinent negative for must-not-miss)",
        "Tangentially related to another finding already selected",
        "An incidental finding with no clinical bearing on the case",
      ],
    },

    {
      "title": "Must-Not-Miss by Chief Complaint",
      "kind": "framework",
      "body": [
        "**Every case has at least one must-not-miss diagnosis.** Faculty award points for including it in the DDx, even when you correctly identify it as less likely than the primary.",
        "",
        "**Patterns by chief complaint:**",
        "",
        "**Headache** → meningitis, subarachnoid hemorrhage, brain tumor, temporal arteritis (age >50), cluster headache",
        "**Chest pain** → MI, PE, aortic dissection, pneumothorax, pericarditis",
        "**Abdominal pain** → appendicitis, ectopic pregnancy (women of childbearing age), bowel obstruction, AAA (elderly)",
        "**HTN** → OSA, secondary HTN (renal, endocrine), pheochromocytoma",
        "**Sore throat** → GAS pharyngitis, infectious mononucleosis, peritonsillar abscess, epiglottitis (peds)",
        "**Pediatric vomiting/diarrhea** → severe dehydration, bacterial gastroenteritis vs viral, intussusception, pyloric stenosis (infants)",
        "**Pediatric academic decline** → vision impairment, hearing impairment, ADHD, learning disability, depression",
        "",
        "**The rule:** When ranking, your must-not-miss goes on the list. It doesn't have to be #1 — but it must be present.",
      ],
    },

    {
      "title": "Common DDx Traps",
      "kind": "traps",
      "items": [
        ("Selecting too many diagnoses",
         "Picking everything that's even slightly plausible suggests poor clinical judgment. Be selective."),
        ("Missing the must-not-miss",
         "Even if you correctly identify it as less likely, the platform expects it on the list."),
        ("Wrong final-diagnosis ranking",
         "Your top-ranked DDx should match your final diagnosis. Mismatches cost points."),
        ("Using non-platform terminology",
         "iHuman uses fixed diagnosis names. \"Severe high blood pressure\" doesn't match \"Hypertension, Stage 2.\""),
        ("Not addressing ruled-out conditions",
         "When labs come back normal, *explicitly* rule out the conditions they ruled out. Silent dismissal loses points."),
        ("Padding the problem statement",
         "Three sentences. Concise. Clinical language. Faculty want diagnostic reasoning, not a re-summary of the entire HPI."),
      ],
    },
  ],

  "outro": [
    "**Last in the library: Management Plan + SOAP Note** — the part that's 100% faculty-scored. Tests to order, the harmful-flag trap, the 6-part management plan structure, and the SOAP note template that faculty look for.",
  ],
}

# ═══════════════════════════════════════════════════════════════════════
# VOLUME IV — MANAGEMENT PLAN & SOAP NOTE
# ═══════════════════════════════════════════════════════════════════════
VOL_IV = {
  "volume_label": "Vol IV of IV",
  "title": "Management Plan & SOAP Note",
  "subtitle": "The faculty-scored 20% — and how to avoid the harmful-to-patient flag",
  "tagline": "The Plan section is where faculty actually read your work. Get this part right and you can compensate for weaker history/PE scores.",
  "stage_id": "plan",

  "intro_voice": [
    ("Here's the thing about the Management Plan: it's the only section that's 100% faculty-scored.",
     "Auto-grading stops at the differential. From there, a human nursing faculty member reads what you wrote and assigns the remaining 20% of your grade based on the quality of your plan, your medication choices, your patient education, and your follow-up scheduling."),
    ("Faculty are looking for evidence-based practice (EBP), correct medication dosing, appropriate referrals, and a follow-up timeline that matches the diagnosis severity.",
     "They're also looking for one specific trap: ordering harmful tests. iHuman flags certain tests as \"harmful to patient\" on certain cases — and one trigger can drop your Tests score to zero."),
    ("This sheet covers the 6-part management plan structure faculty look for, the harmful-flag trap, the medication dosing reference, and the SOAP note template that scores well across programs.",
     "Apply it across every case."),
  ],

  "sections": [
    {
      "title": "The Harmful-to-Patient Flag",
      "kind": "trap_callout",
      "body": [
        "**This is the single biggest scoring trap in iHuman.**",
        "",
        "If you order a test that the platform considers harmful for that patient — too aggressive, too invasive, contraindicated, or unnecessary given the clinical picture — the platform flags it and your Tests score drops to 0%.",
        "",
        "**Classic examples:**",
        "**Migraine with aura, normal exam, no red flags** → Don't order CT or MRI. Clinical diagnosis. Ordering imaging = harmful flag.",
        "**Headache with negative SNOOP4** → Same. Imaging is not indicated.",
        "**Stable URI** → Don't order chest X-ray.",
        "**Simple viral gastroenteritis in a child with normal vitals** → Don't order CBC, BMP. Clinical management.",
        "",
        "**The rule:** Order tests when they will change your management. If a test result wouldn't change what you do next, don't order it. The phrase to remember from Choosing Wisely: \"More tests, more problems.\"",
      ],
    },

    {
      "title": "The 6-Part Management Plan",
      "kind": "flowable",
      "flowable": "six_part_plan",
    },

    {
      "title": "Why Each Part Matters",
      "kind": "framework",
      "body": [
        "Faculty expect all six domains covered. Each scores separately.",
        "",
        "**Missing any section flags incompleteness.** Even a brief sentence per section is better than skipping one.",
      ],
    },

    {
      "title": "Medication Documentation — Six Required Elements",
      "kind": "framework",
      "body": [
        "**Every medication needs all six elements** or it gets flagged as incomplete:",
        "",
        "**1. Name** (generic + brand if relevant)",
        "**2. Dose** (e.g., 10 mg)",
        "**3. Route** (PO, IM, IV, topical)",
        "**4. Frequency** (e.g., daily, BID, TID, QID, PRN)",
        "**5. Duration** (e.g., 10 days, 30 days, ongoing)",
        "**6. Dispense quantity** and **refills** (e.g., #30, 2 refills)",
        "",
        "**Skipping the dispense/refill quantity is a frequent point-loss item** — faculty look for it.",
      ],
    },

    {
      "title": "Medication Answer Key (by case)",
      "kind": "flowable",
      "flowable": "med_dosing",
    },

    {
      "title": "",
      "kind": "mid_cta",
    },

    {
      "title": "EBP References — What Faculty Cite",
      "kind": "framework",
      "body": [
        "Most programs expect 2–3 scholarly references in APA format. Faculty want recent, authoritative sources.",
        "",
        "**Tier 1 — Always acceptable:**",
        "Clinical practice guidelines (e.g., ACC/AHA, GINA, ADA, IDSA)",
        "UpToDate (cite the topic and date accessed)",
        "Peer-reviewed journal articles (within last 5 years)",
        "AAP guidelines for pediatric cases",
        "",
        "**Tier 2 — Acceptable but secondary:**",
        "Textbooks (current edition) — Bates, Dunphy, Hollier",
        "CDC guidelines",
        "WHO recommendations",
        "",
        "**Avoid:**",
        "Wikipedia",
        "Medscape (use sparingly — not all programs accept)",
        "Patient-facing health blogs",
        "Pharmaceutical company websites",
        "",
        "**Format reminder:** APA 7th edition. In-text citation: (Author, Year). Reference list at the end.",
      ],
    },

    {
      "title": "Follow-Up Timeline by Diagnosis Severity",
      "kind": "checklist",
      "items": [
        "**Acute, self-limiting (URI, viral GE)** — 7–14 days or PRN if not resolving",
        "**Acute, treatable (GAS pharyngitis, UTI)** — 7–10 days to confirm resolution",
        "**Chronic, controlled (stable HTN on meds, DM)** — 3 months",
        "**Chronic, new or uncontrolled (newly diagnosed HTN, new DM)** — 2–4 weeks",
        "**Severe / pre-treatment (Stage 2 HTN before meds adjusted)** — 1–2 weeks",
        "**Mental health (new SSRI start)** — 2 weeks for tolerability, 4–6 weeks for efficacy",
        "**Pediatric ADHD med initiation** — 2–4 weeks to titrate, then monthly until stable",
        "",
        "**Always document ER warning signs** — chest pain, severe headache, vision changes, dyspnea, BP > 180/120, fever > 102 with neck stiffness, etc. (case-specific).",
      ],
    },

    {
      "title": "The SOAP Note Template",
      "kind": "framework",
      "body": [
        "**S — Subjective:**",
        "Chief complaint (in patient's own words, in quotes)",
        "HPI in narrative form, organized by OLDCARTS",
        "PMH, FH, SH (brief, relevant)",
        "ROS (positives and significant negatives only)",
        "",
        "**O — Objective:**",
        "Vitals",
        "General appearance",
        "PE findings by system (positives and pertinent negatives)",
        "Test results if available",
        "",
        "**A — Assessment:**",
        "Primary diagnosis (with ICD-10 if required by program)",
        "Differential diagnoses (3–5, ranked)",
        "Brief diagnostic reasoning (1–2 sentences)",
        "",
        "**P — Plan:**",
        "Diagnostics, pharmacologic, non-pharm, referrals, education, follow-up (the 6-part structure above)",
        "Reference list in APA format",
      ],
    },

    {
      "title": "Common Plan Traps That Cost Faculty Points",
      "kind": "traps",
      "items": [
        ("Ordering harmful tests",
         "The biggest single trap — drops Tests score to 0% if triggered. Always ask: will this result change my management?"),
        ("Incomplete medication orders",
         "Missing dose, route, frequency, duration, dispense quantity, or refills. Faculty look for all six."),
        ("Forgetting NSAID counseling on hypertension cases",
         "NSAIDs raise BP. If your HTN patient is taking ibuprofen, you must D/C and switch to acetaminophen. Skipping this loses points."),
        ("Skipping patient education on warning signs",
         "Faculty want to see explicit ER return precautions for every diagnosis."),
        ("Wrong follow-up timeline",
         "Stage 2 HTN with new meds → 2 weeks, not 3 months. Match severity to interval."),
        ("Generic references",
         "*\"WebMD\"* or *\"Mayo Clinic patient portal\"* gets flagged. Use clinical guidelines and peer-reviewed sources."),
        ("Missing OSA referral on HTN cases",
         "Snoring + HTN + male/overweight = sleep study referral. Scored as a separate management item."),
      ],
    },
  ],

  "outro": [
    "**You've completed the CPL Cheat Sheet Library.** Volumes I–IV cover the universal patterns that apply across every iHuman case.",
  ],
}

ALL_VOLUMES = [VOL_I, VOL_II, VOL_III, VOL_IV]

# Metadata for the lead magnet landing page + thumbnails
VOLUME_META = [
  {
    "id": "history",
    "filename": "cpl-vol-1-history.pdf",
    "title": "Vol I — History Framework",
    "subtitle": "Universal history questions that score on every iHuman case",
    "stage": "Stage 1 of 4",
    "duration": "~10 min read",
    "pages": 8,
    "color": "teal",
  },
  {
    "id": "physical-exam",
    "filename": "cpl-vol-2-physical-exam.pdf",
    "title": "Vol II — Universal PE Checklist",
    "subtitle": "Physical exam items that score on every case, regardless of CC",
    "stage": "Stage 2 of 4",
    "duration": "~10 min read",
    "pages": 9,
    "color": "lime",
  },
  {
    "id": "ddx",
    "filename": "cpl-vol-3-ddx.pdf",
    "title": "Vol III — DDx & Key Findings",
    "subtitle": "How to rank differentials the way iHuman scores them",
    "stage": "Stage 3 of 4",
    "duration": "~8 min read",
    "pages": 7,
    "color": "ink",
  },
  {
    "id": "plan",
    "filename": "cpl-vol-4-plan.pdf",
    "title": "Vol IV — Management Plan & SOAP",
    "subtitle": "The faculty-scored 20% — and the harmful-flag trap",
    "stage": "Stage 4 of 4",
    "duration": "~10 min read",
    "pages": 9,
    "color": "teal",
  },
]


if __name__ == "__main__":
  for v in ALL_VOLUMES:
    print(f"{v['volume_label']}: {v['title']} — {len(v['sections'])} sections")
