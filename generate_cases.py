#!/usr/bin/env python3
"""
One-shot generator: reads ihuman JSON + existing cases_data.py,
produces updated cases_data.py with ~131 new case entries.
"""
import json, re, textwrap

JSON_PATH = r"C:\Users\USER\Downloads\ihuman_virtual_patient_cases (2).json"
CASES_PY  = r"C:\Users\USER\Desktop\Projects\Project CPL\cases_data.py"

# ── IDs to skip (already in catalog) ──────────────────────────────
SKIP_IDS = {1, 2, 3, 5, 6, 11, 12, 18, 25, 65, 79, 86, 118, 144}

# ── Merge pairs: second ID folds into first ───────────────────────
MERGE_MAP = {19: 10, 39: 17, 149: 131}  # second → first

# ── Clinical knowledge: diagnosis → (must_not_miss, key_scoring_traps) ──
CLINICAL = {
    "Small Bowel Obstruction": (
        "Strangulated bowel; closed-loop obstruction; perforation",
        [
            "High-pitched tinkling bowel sounds on auscultation suggest partial obstruction",
            "Absent bowel sounds suggest complete obstruction — surgical emergency",
            "Upright abdominal X-ray: air-fluid levels are diagnostic, not just distension",
            "NG tube decompression before imaging in hemodynamically unstable patient",
            "Prior surgical adhesions are #1 cause — must obtain surgical history",
        ],
    ),
    "STEMI / Aortic Stenosis": (
        "Acute MI; aortic dissection; cardiac tamponade",
        [
            "STEMI requires door-to-balloon < 90 min — time-critical diagnosis",
            "Aortic stenosis murmur: crescendo-decrescendo at right 2nd ICS radiating to carotids",
            "Pulsus parvus et tardus on palpation suggests severe AS",
            "Do NOT give nitrates in severe aortic stenosis — preload-dependent",
            "Troponin serial draws q3-6h — single negative does not rule out MI",
        ],
    ),
    "Contact Dermatitis": (
        "Cellulitis; herpes simplex; tinea; allergic contact vs irritant contact",
        [
            "Distribution pattern is key — linear streaks suggest plant contact (Toxicodendron)",
            "Must distinguish allergic contact (Type IV hypersensitivity) from irritant contact",
            "Patch testing is gold standard for identifying allergen — not IgE levels",
            "Topical steroids are first-line — mid-potency for body, low-potency for face/groin",
            "Must ask about occupational exposures, new products, jewelry metals",
        ],
    ),
    "Major Depressive Disorder": (
        "Bipolar disorder (screen before starting SSRI); hypothyroidism; substance use",
        [
            "PHQ-9 score must be documented — iHuman grades on validated screening tool use",
            "Must screen for suicidal ideation using Columbia-Suicide Severity Rating Scale",
            "Always rule out bipolar with MDQ before starting antidepressant — SSRI can trigger mania",
            "TSH is mandatory lab — hypothyroidism mimics depression",
            "Adolescent MDD: fluoxetine is only FDA-approved SSRI for ages 8-17",
        ],
    ),
    "Alzheimer's Disease": (
        "Reversible dementia causes: B12 deficiency; hypothyroidism; normal pressure hydrocephalus; depression (pseudodementia)",
        [
            "MMSE or MoCA score must be documented — iHuman grades on cognitive screening",
            "Must check TSH, B12, RPR, CBC, CMP to rule out reversible causes",
            "Cholinesterase inhibitors (donepezil) for mild-moderate; memantine added for moderate-severe",
            "Caregiver assessment and support resources are required plan elements",
            "Safety evaluation: driving, wandering, firearms access, medication management",
        ],
    ),
    "Insomnia / Possible Hyperthyroidism": (
        "Hyperthyroidism; anxiety disorder; obstructive sleep apnea; restless leg syndrome",
        [
            "Must check TSH and free T4 — insomnia with weight loss suggests hyperthyroidism",
            "Sleep hygiene education is first-line before pharmacotherapy",
            "CBT-I (Cognitive Behavioral Therapy for Insomnia) is evidence-based first-line treatment",
            "Avoid benzodiazepines in elderly — use low-dose trazodone or melatonin receptor agonist",
            "Epworth Sleepiness Scale screens for OSA — different from insomnia",
        ],
    ),
    "COPD Exacerbation": (
        "Pneumonia; pulmonary embolism; pneumothorax; acute heart failure",
        [
            "GOLD staging by FEV1/FVC ratio < 0.70 — spirometry is diagnostic, not peak flow",
            "Acute exacerbation: systemic corticosteroids + short-acting bronchodilator + antibiotics if purulent sputum",
            "Oxygen target 88-92% in COPD — over-oxygenation suppresses hypoxic drive",
            "Must assess smoking status and offer cessation at every visit — varenicline first-line",
            "Influenza and pneumococcal vaccines are required preventive measures",
        ],
    ),
    "Gout": (
        "Septic joint (must aspirate to rule out); pseudogout (CPPD); cellulitis",
        [
            "Joint aspiration with negatively birefringent needle-shaped crystals = definitive diagnosis",
            "Serum uric acid may be NORMAL during acute flare — do not use to rule out gout",
            "Acute: NSAIDs or colchicine first-line — do NOT start allopurinol during acute flare",
            "Allopurinol started 2 weeks after flare resolution with colchicine prophylaxis",
            "Must assess for tophi on exam — ears, elbows, fingers, Achilles tendon",
        ],
    ),
    "Multiple Sclerosis": (
        "Neuromyelitis optica; CNS lymphoma; vitamin B12 deficiency; Lyme disease",
        [
            "Dissemination in time AND space required for diagnosis (McDonald criteria)",
            "MRI brain and spine with gadolinium — look for periventricular plaques",
            "Lumbar puncture: oligoclonal bands present in CSF but not serum",
            "Uhthoff phenomenon: symptoms worsen with heat/exercise — pathognomonic history finding",
            "Optic neuritis + internuclear ophthalmoplegia = classic MS presentation",
        ],
    ),
    "Roseola (Exanthem Subitum)": (
        "Measles; Kawasaki disease; meningococcemia; drug reaction",
        [
            "Classic pattern: HIGH fever (≥104°F) for 3-5 days THEN rash appears as fever breaks",
            "Rash is maculopapular, starts on trunk, spreads outward — blanches with pressure",
            "Caused by HHV-6 — no antiviral treatment needed, self-limiting",
            "Febrile seizures are the main complication to counsel parents about",
            "No isolation needed once rash appears — child is no longer contagious",
        ],
    ),
    "Coronary Artery Disease / Stable Angina": (
        "Acute coronary syndrome; aortic stenosis; GERD; musculoskeletal chest pain",
        [
            "Stress testing before catheterization in stable angina — not direct to cath",
            "Aspirin + statin are mandatory in all CAD patients regardless of lipid levels",
            "Sublingual nitroglycerin for acute episodes — 3 doses at 5-min intervals, then 911",
            "Beta-blocker is first-line anti-anginal — NOT calcium channel blocker",
            "Must calculate 10-year ASCVD risk score — guides intensity of statin therapy",
        ],
    ),
    "Heat Exhaustion": (
        "Heat stroke (altered mental status = heat stroke, not exhaustion); hyponatremia; cardiac event",
        [
            "Core temp < 104°F with intact mental status = heat exhaustion; ≥ 104°F + AMS = heat stroke",
            "Treatment: move to cool environment, oral rehydration, remove excess clothing",
            "Heat stroke requires immediate cooling (ice water immersion) — this is a medical emergency",
            "Must assess for rhabdomyolysis: CK level, dark urine, muscle tenderness",
            "Return-to-activity guidelines: no exercise for 24-48 hours minimum",
        ],
    ),
    "Hordeolum (Stye)": (
        "Chalazion; preseptal cellulitis; dacryocystitis; blepharitis",
        [
            "Hordeolum is acute, painful, localized — chalazion is chronic, non-tender, and granulomatous",
            "Warm compresses 4x/day for 10-15 minutes is first-line treatment",
            "Do NOT incise and drain unless pointing and fluctuant",
            "Topical antibiotic (erythromycin ointment) only if concurrent blepharitis",
            "Preseptal cellulitis: diffuse lid edema + fever = urgent referral (must not miss)",
        ],
    ),
    "Acute Kidney Injury (AKI)": (
        "Chronic kidney disease progression; urinary obstruction; renal artery stenosis",
        [
            "Classify as prerenal, intrinsic, or postrenal — BUN:Cr ratio > 20:1 suggests prerenal",
            "FENa < 1% = prerenal; FENa > 2% = intrinsic renal (ATN)",
            "Stop nephrotoxic drugs immediately: NSAIDs, ACEi/ARB, aminoglycosides, contrast",
            "Renal ultrasound to rule out obstruction (postrenal) is first imaging study",
            "Monitor potassium closely — hyperkalemia is the life-threatening complication",
        ],
    ),
    "Stable Angina / ACS (DDx)": (
        "Acute MI; pulmonary embolism; aortic dissection; esophageal spasm",
        [
            "ECG within 10 minutes of presentation — ST elevation = STEMI, immediate cath",
            "Troponin serial draws: negative at 0 and 3-6 hours needed to rule out NSTEMI",
            "TIMI risk score guides disposition: ≥ 3 = high risk, consider admission",
            "Aspirin 325mg immediately if ACS suspected — do not wait for troponin results",
            "Nitrates contraindicated if recent PDE-5 inhibitor use (sildenafil within 24h)",
        ],
    ),
    "Preventive Care / Well-Child Visit": (
        "Developmental delay; failure to thrive; child abuse/neglect; lead exposure",
        [
            "Age-appropriate immunization schedule per CDC — must verify and document",
            "Developmental screening: ASQ-3 or PEDS at 9, 18, 30 months; M-CHAT at 18 and 24 months",
            "Growth chart plotting: weight, length/height, head circumference, BMI (age ≥ 2)",
            "Anticipatory guidance topics are age-specific: safety, nutrition, sleep, milestones",
            "Lead screening at 12 months and 24 months in high-risk populations",
        ],
    ),
    "Atopic Dermatitis (Eczema)": (
        "Contact dermatitis; scabies; seborrheic dermatitis; psoriasis",
        [
            "Diagnosis is clinical — no lab test needed; must document distribution pattern",
            "Moisturizers (emollients) are the foundation of treatment — apply immediately after bathing",
            "Low-potency topical corticosteroids for face/folds; mid-potency for trunk/extremities",
            "Must counsel on triggers: fragrances, wool, excessive bathing, low humidity",
            "Eczema herpeticum (HSV superinfection): punched-out erosions = urgent antiviral needed",
        ],
    ),
    "Acute Otitis Media": (
        "Otitis externa; otitis media with effusion (OME); mastoiditis; cholesteatoma",
        [
            "Bulging, erythematous, immobile TM on pneumatic otoscopy = diagnostic",
            "AAP guidelines: observation option for age ≥ 2 with unilateral non-severe AOM",
            "Amoxicillin 80-90 mg/kg/day is first-line antibiotic when treatment indicated",
            "Amoxicillin-clavulanate if no improvement in 48-72 hours or recent antibiotic use",
            "Must assess for TM perforation — otorrhea changes management approach",
        ],
    ),
    "Bacterial Conjunctivitis": (
        "Viral conjunctivitis; allergic conjunctivitis; orbital cellulitis; iritis/uveitis",
        [
            "Purulent discharge + crusted lids in morning = bacterial; watery discharge = viral/allergic",
            "Topical antibiotic (erythromycin ointment or polymyxin-trimethoprim drops) for bacterial",
            "Must check visual acuity — decreased acuity suggests corneal involvement = urgent referral",
            "Gonococcal conjunctivitis: hyperacute, copious purulent — needs systemic ceftriaxone IM",
            "Contact lens wearers: must cover Pseudomonas — use fluoroquinolone drops",
        ],
    ),
    "Invasive Ductal Carcinoma (Breast Cancer)": (
        "Fibroadenoma; fibrocystic changes; phyllodes tumor; fat necrosis",
        [
            "Hard, fixed, irregular, painless mass = high suspicion for malignancy",
            "Diagnostic mammogram + ultrasound → core needle biopsy for tissue diagnosis",
            "BI-RADS classification guides management: 4 or 5 = biopsy recommended",
            "Must assess family history for BRCA risk: first-degree relative, bilateral, early onset",
            "Axillary lymph node palpation is required PE component — staging depends on nodal status",
        ],
    ),
    "Developmental Disorder": (
        "Autism spectrum disorder; intellectual disability; hearing loss; lead poisoning",
        [
            "ASQ-3 or Ages and Stages must be documented for standardized screening",
            "Hearing and vision screening mandatory before diagnosing developmental delay",
            "Early intervention referral (Birth-3 program) if any domain is delayed",
            "Must assess adaptive functioning in addition to cognitive milestones",
            "Red flags: no babbling by 12 months, no words by 16 months, no 2-word phrases by 24 months",
        ],
    ),
    "Unspecified Psychiatric Condition": (
        "Bipolar disorder; psychotic disorder; substance-induced mood disorder; medical causes",
        [
            "Comprehensive psychiatric assessment includes MSE (Mental Status Exam) documentation",
            "Safety assessment: suicidal ideation, homicidal ideation, self-harm history",
            "Must rule out medical causes: TSH, CBC, CMP, urine drug screen, B12",
            "Collateral information from family/caregivers is essential for accurate diagnosis",
            "Document current medications — psychiatric symptoms may be medication side effects",
        ],
    ),
    "Adjustment Disorder": (
        "Major depressive disorder; PTSD; generalized anxiety disorder; normal grief",
        [
            "Symptoms must occur within 3 months of identifiable stressor (DSM-5 criterion)",
            "Must not meet criteria for another mental disorder — diagnosis of exclusion",
            "Psychotherapy (CBT, supportive) is first-line — medications are adjunctive only",
            "Symptoms must cause clinically significant distress OR functional impairment",
            "Must resolve within 6 months of stressor termination — otherwise reclassify",
        ],
    ),
    "Panic Disorder": (
        "Acute coronary syndrome; pulmonary embolism; hyperthyroidism; pheochromocytoma",
        [
            "Must rule out cardiac causes: ECG + troponin before psychiatric diagnosis in first episode",
            "4+ of 13 symptoms during discrete episode = panic attack (DSM-5)",
            "SSRI (sertraline or paroxetine) is first-line pharmacotherapy — not benzodiazepine",
            "CBT with interoceptive exposure is evidence-based first-line treatment",
            "Benzodiazepines for PRN rescue only — high abuse potential, not for maintenance",
        ],
    ),
    "Bipolar Disorder": (
        "Major depressive disorder; schizoaffective disorder; substance-induced mood disorder; ADHD",
        [
            "Must screen for mania/hypomania before starting antidepressant — MDQ screening tool",
            "Lithium or valproate is first-line mood stabilizer — NOT antidepressant monotherapy",
            "Lithium requires baseline and periodic: renal function, thyroid, serum level monitoring",
            "Therapeutic lithium level 0.6-1.2 mEq/L — narrow window, toxicity above 1.5",
            "Manic episode: ≥ 1 week of elevated/irritable mood + ≥ 3 DIGFAST criteria",
        ],
    ),
    "Syndrome of Inappropriate Antidiuretic Hormone (SIADH)": (
        "Cerebral salt wasting; adrenal insufficiency; hypothyroidism; psychogenic polydipsia",
        [
            "Euvolemic hyponatremia with concentrated urine (Uosm > 100) = classic SIADH",
            "Must check serum osmolality (< 275), urine osmolality, urine sodium (> 40)",
            "Fluid restriction (800-1000 mL/day) is first-line treatment",
            "Correct sodium slowly: ≤ 8 mEq/L per 24h — rapid correction causes osmotic demyelination",
            "Common causes: SSRI medications, lung cancer (SCLC), CNS disorders, pain",
        ],
    ),
    "Attention Deficit Hyperactivity Disorder (ADHD)": (
        "Anxiety disorder; learning disability; hearing loss; thyroid disorder; sleep disorder",
        [
            "Vanderbilt rating scales from BOTH parents AND teachers required for diagnosis",
            "Symptoms must be present in 2+ settings and before age 12 (DSM-5)",
            "Age 6+: methylphenidate or amphetamine-based stimulant is first-line pharmacotherapy",
            "Age < 6: behavioral therapy is first-line — stimulants only if behavioral therapy fails",
            "Must monitor height, weight, heart rate, blood pressure at each stimulant follow-up",
        ],
    ),
    "Congestive Heart Failure": (
        "COPD exacerbation; pneumonia; pulmonary embolism; renal failure",
        [
            "BNP > 400 pg/mL or NT-proBNP > 900 strongly suggests HF — must order",
            "Echocardiogram is mandatory to classify HFrEF (EF ≤ 40%) vs HFpEF (EF > 50%)",
            "ACEi/ARB + beta-blocker + diuretic = guideline-directed medical therapy",
            "Daily weight monitoring and 2g sodium restriction are required patient education items",
            "Volume status assessment: JVD, peripheral edema, crackles, S3 gallop",
        ],
    ),
    "Stable Angina": (
        "Acute coronary syndrome; GERD; costochondritis; anxiety/panic attack",
        [
            "Predictable pattern with exertion, relieved by rest or nitroglycerin = stable angina",
            "Stress testing is initial diagnostic — exercise or pharmacologic",
            "Aspirin + statin + beta-blocker are core pharmacotherapy",
            "PRN sublingual nitroglycerin with instructions: 3 doses 5 min apart, then call 911",
            "Must calculate ASCVD risk score and address modifiable risk factors",
        ],
    ),
    "Community-Acquired Pneumonia": (
        "Pulmonary embolism; lung cancer; tuberculosis; heart failure",
        [
            "CURB-65 score determines inpatient vs outpatient management",
            "Outpatient previously healthy: amoxicillin OR doxycycline monotherapy",
            "Outpatient with comorbidities: amoxicillin-clavulanate + macrolide OR respiratory fluoroquinolone",
            "Chest X-ray is diagnostic — must document infiltrate location and characteristics",
            "Follow-up chest X-ray at 6-8 weeks to confirm resolution (especially if smoker/age > 50)",
        ],
    ),
    "Aortic Stenosis": (
        "Hypertrophic cardiomyopathy; aortic sclerosis; mitral regurgitation; ACS",
        [
            "Classic triad: syncope, angina, heart failure — presence of any = severe AS",
            "Systolic crescendo-decrescendo murmur at right upper sternal border → carotids",
            "Pulsus parvus et tardus: weak and delayed carotid upstroke = hemodynamically significant",
            "Echocardiogram is diagnostic — valve area < 1.0 cm² = severe",
            "Vasodilators and volume depletion are DANGEROUS — maintain preload",
        ],
    ),
    "COPD Exacerbation / Heart Failure": (
        "Pulmonary embolism; pneumothorax; acute MI; pneumonia",
        [
            "BNP helps distinguish cardiac from pulmonary dyspnea — BNP > 400 = likely HF",
            "COPD + HF overlap is common — treat both simultaneously",
            "Non-invasive ventilation (BiPAP) for COPD exacerbation with respiratory acidosis",
            "Systemic corticosteroids (prednisone 40mg x 5 days) for COPD exacerbation",
            "Must reassess inhaler technique and medication adherence at every visit",
        ],
    ),
    "Undisclosed GI condition": (
        "Appendicitis; cholecystitis; peptic ulcer disease; pancreatitis; bowel obstruction",
        [
            "Systematic abdominal exam: inspection, auscultation, percussion, palpation (in order)",
            "Must assess for peritoneal signs: rebound tenderness, guarding, rigidity",
            "Location of pain narrows differential: RUQ = hepatobiliary; epigastric = gastric/pancreatic; RLQ = appendix",
            "CBC, CMP, lipase, UA are standard initial labs for undifferentiated abdominal pain",
        ],
    ),
    "Undisclosed GU condition": (
        "UTI; pyelonephritis; nephrolithiasis; STI; ectopic pregnancy",
        [
            "Urinalysis with microscopy is first-line diagnostic — positive nitrites/leukocyte esterase suggest UTI",
            "Pregnancy test mandatory in reproductive-age females with GU symptoms",
            "CVA tenderness on exam suggests upper tract involvement (pyelonephritis)",
            "STI screening (GC/CT NAAT) in sexually active patients with GU complaints",
        ],
    ),
    "Undisclosed": (
        "Varies by presentation — comprehensive differential required",
        [
            "Complete ROS is critical when diagnosis is not immediately apparent",
            "Focused history: onset, location, duration, character, aggravating/alleviating factors",
            "Physical exam must be systematic and thorough — document pertinent negatives",
            "Consider red flags: weight loss, night sweats, fever, neurological changes",
        ],
    ),
    "Meningitis / Severe Headache (DDx)": (
        "Subarachnoid hemorrhage; encephalitis; brain abscess; migraine with red flags",
        [
            "Kernig and Brudzinski signs must be tested — classic meningeal signs",
            "Lumbar puncture is diagnostic — CSF analysis: WBC, glucose, protein, Gram stain, culture",
            "Empiric antibiotics (ceftriaxone + vancomycin + dexamethasone) if bacterial suspected — do NOT delay for imaging",
            "CT head before LP only if focal neurological deficits, papilledema, or immunocompromised",
            "Fever + headache + neck stiffness = classic triad — absence doesn't exclude meningitis",
        ],
    ),
    "Preventive Care / Well Woman Exam": (
        "Cervical cancer; breast cancer; osteoporosis; depression; intimate partner violence",
        [
            "Pap smear screening per USPSTF: age 21-29 q3yrs cytology; age 30-65 q5yrs co-testing",
            "Clinical breast exam and mammography referral per age-appropriate guidelines",
            "DEXA scan for osteoporosis screening at age 65 or earlier with risk factors",
            "IPV screening with validated tool at preventive visits (USPSTF B recommendation)",
            "Contraception counseling and STI screening based on sexual history risk factors",
        ],
    ),
    "Migraine Headache": (
        "Subarachnoid hemorrhage (thunderclap headache); temporal arteritis; intracranial mass; medication overuse headache",
        [
            "POUND mnemonic: Pulsatile, duration 4-72 hOurs, Unilateral, Nausea, Disabling",
            "Red flags requiring imaging: thunderclap onset, worst headache of life, focal neurological deficit, age > 50 new onset",
            "Triptan (sumatriptan) is first-line abortive — contraindicated in uncontrolled HTN, CAD, prior stroke",
            "Preventive therapy if ≥ 4 headache days/month: propranolol, topiramate, or amitriptyline",
            "Must screen for medication overuse headache: analgesics > 15 days/month",
        ],
    ),
    "Testicular Torsion": (
        "Epididymitis; inguinal hernia; testicular tumor; torsion of appendix testis",
        [
            "Absent cremasteric reflex is most sensitive physical exam finding for torsion",
            "This is a surgical emergency: < 6 hours to detorsion to salvage the testicle",
            "Do NOT delay for imaging if clinical suspicion is high — go directly to surgery",
            "Prehn sign (pain relief with testicular elevation) is unreliable — do not use to rule out",
            "Color Doppler ultrasound shows absent blood flow — confirmatory if diagnosis uncertain",
        ],
    ),
    "Urinary Tract Infection / Cystitis": (
        "Pyelonephritis; vaginitis; interstitial cystitis; urethritis (STI)",
        [
            "Uncomplicated UTI in women: nitrofurantoin 5 days OR TMP-SMX 3 days — NOT fluoroquinolone",
            "UA + urine culture: > 100,000 CFU/mL is diagnostic; pyuria > 10 WBC/hpf",
            "Recurrent UTIs (≥ 3/year): prophylactic strategies include post-coital voiding, cranberry",
            "Pregnant women: treat asymptomatic bacteriuria — nitrofurantoin or cephalexin (NOT TMP-SMX in 1st trimester)",
        ],
    ),
    "Atypical Nevus / Melanoma evaluation": (
        "Melanoma; basal cell carcinoma; squamous cell carcinoma; seborrheic keratosis",
        [
            "ABCDEs of melanoma: Asymmetry, Border irregularity, Color variation, Diameter > 6mm, Evolving",
            "Any changing mole in elderly patient = biopsy (excisional preferred, not shave)",
            "Breslow depth on pathology determines staging and management",
            "Must document total body skin exam — check scalp, between toes, nails",
            "Risk factors: fair skin, history of sunburns, family history, > 50 moles, immunosuppression",
        ],
    ),
    "Nephrolithiasis / Pyelonephritis (DDx)": (
        "Appendicitis; ectopic pregnancy; aortic aneurysm; renal cell carcinoma",
        [
            "Non-contrast CT abdomen/pelvis is gold standard for nephrolithiasis diagnosis",
            "Urine dipstick: hematuria supports stone; nitrites + leukocytes suggest infection",
            "Stone < 5mm: conservative management with fluids, NSAIDs, tamsulosin (MET)",
            "Infected obstructing stone (fever + stone + hydronephrosis) = urologic emergency",
        ],
    ),
    "Insomnia Disorder": (
        "Sleep apnea; restless leg syndrome; depression; substance use; hyperthyroidism",
        [
            "CBT-I is first-line treatment per ACP guidelines — not pharmacotherapy",
            "Sleep diary for 2 weeks helps characterize pattern: onset, maintenance, or early awakening",
            "Must screen for OSA: STOP-BANG questionnaire if snoring, witnessed apneas, daytime sleepiness",
            "Pharmacotherapy if needed: low-dose trazodone, suvorexant, or ramelteon — avoid benzodiazepines",
        ],
    ),
    "Respiratory Condition (unspecified)": (
        "Pneumonia; COPD exacerbation; asthma; pulmonary embolism; heart failure",
        [
            "Pulse oximetry and respiratory rate are essential initial vital signs",
            "Chest X-ray is first-line imaging for undifferentiated respiratory complaints",
            "Must auscultate all lung fields: wheezes suggest bronchoconstriction, crackles suggest fluid/infection",
            "Smoking history in pack-years is a required documentation element",
        ],
    ),
    "GI condition (unspecified)": (
        "Appendicitis; cholecystitis; peptic ulcer disease; pancreatitis; bowel obstruction",
        [
            "Systematic abdominal exam: inspection, auscultation, percussion, palpation",
            "Location of pain narrows differential: RUQ = hepatobiliary, epigastric = gastric/pancreatic",
            "CBC, CMP, lipase, UA are standard initial labs for undifferentiated abdominal pain",
            "Red flags: guarding, rebound tenderness, rigid abdomen = surgical emergency",
        ],
    ),
    "Hypertension": (
        "Secondary hypertension: renal artery stenosis, pheochromocytoma, Cushing syndrome, coarctation of aorta",
        [
            "Proper BP technique: seated 5 min, feet flat, arm at heart level, appropriate cuff size",
            "Stage 1 HTN (130-139/80-89): lifestyle modification first, then single drug if ASCVD risk ≥ 10%",
            "Stage 2 HTN (≥ 140/90): two-drug combination therapy per ACC/AHA guidelines",
            "Must screen for target organ damage: fundoscopy, BMP (creatinine), urinalysis (proteinuria), ECG",
        ],
    ),
    "Diabetes Mellitus (unspecified type)": (
        "Type 1 DM; LADA; medication-induced hyperglycemia; Cushing syndrome",
        [
            "Diagnostic criteria: FBG ≥ 126, A1C ≥ 6.5%, random glucose ≥ 200 with symptoms",
            "Metformin is first-line for T2DM — check renal function (eGFR > 30) before starting",
            "A1C target < 7% for most adults — individualize for elderly or comorbidities",
            "Annual screening: dilated eye exam, foot exam, urine albumin-to-creatinine ratio",
        ],
    ),
    "Pediatric GI condition (unspecified)": (
        "Appendicitis; intussusception; malrotation with volvulus; constipation; Meckel diverticulum",
        [
            "Pediatric abdominal pain: age-based differential — intussusception in 6mo-3yr, appendicitis in school-age",
            "Must assess for dehydration: mucous membranes, skin turgor, cap refill, tears, urine output",
            "Red flags in peds: bilious vomiting (obstruction), bloody stool (intussusception), peritoneal signs",
            "Constipation is the most common cause of pediatric abdominal pain — always consider",
        ],
    ),
    "Upper Respiratory Infection / Bronchiolitis": (
        "Pertussis; foreign body aspiration; croup; pneumonia; RSV bronchiolitis",
        [
            "Bronchiolitis in < 2yo: supportive care only — no antibiotics, no bronchodilators per AAP",
            "RSV is the most common cause of bronchiolitis — nasal aspirate for rapid testing",
            "Must assess respiratory distress: nasal flaring, retractions, grunting, tachypnea, O2 sat",
            "Hydration status is critical — many hospitalizations are for feeding difficulties, not hypoxia",
        ],
    ),
    "Infectious Colitis / IBD (DDx)": (
        "C. difficile colitis; ulcerative colitis; Crohn disease; ischemic colitis; colon cancer",
        [
            "Stool studies: C. diff toxin, stool culture, ova and parasites, fecal calprotectin",
            "Fecal calprotectin distinguishes inflammatory from functional bowel disease",
            "Bloody diarrhea + recent antibiotics = C. diff until proven otherwise",
            "Must assess for dehydration: orthostatics, mucous membranes, urine output",
        ],
    ),
    "Dermatitis / Infectious Rash (DDx)": (
        "Contact dermatitis; fungal infection (tinea); scabies; viral exanthem; drug eruption",
        [
            "Distribution pattern is the most important diagnostic clue — document location and morphology",
            "KOH prep for suspected fungal; scabies scraping for burrows in web spaces",
            "Must ask about new medications (drug eruption), exposures, travel history, contacts",
            "Biopsy indicated if diagnosis uncertain after clinical evaluation and initial workup",
        ],
    ),
    "Pyelonephritis": (
        "Nephrolithiasis with infection; perinephric abscess; renal cell carcinoma; ectopic pregnancy",
        [
            "CVA tenderness on percussion is the hallmark physical exam finding",
            "UA with culture and sensitivity — treat empirically then adjust based on culture",
            "Outpatient: fluoroquinolone x 7 days OR TMP-SMX x 14 days",
            "Admit if: vomiting (can't tolerate PO), sepsis signs, obstructing stone, pregnancy",
            "CT abdomen/pelvis if not improving in 48-72 hours — rule out abscess or obstruction",
        ],
    ),
    "Patellar Fracture": (
        "Patellar dislocation; quadriceps tendon rupture; patellar tendon rupture; tibial plateau fracture",
        [
            "Inability to perform straight leg raise = loss of extensor mechanism = surgical consultation",
            "AP and lateral knee X-rays are diagnostic — look for displaced vs nondisplaced",
            "Nondisplaced < 2mm with intact extensor mechanism = conservative (knee immobilizer)",
            "Displaced or comminuted = surgical fixation (ORIF) referral",
        ],
    ),
    "Sexually Transmitted Infection": (
        "Ectopic pregnancy; PID; appendicitis; cervical cancer",
        [
            "NAAT testing for gonorrhea and chlamydia is gold standard — urine or swab",
            "Treat GC + CT simultaneously: ceftriaxone 500mg IM + doxycycline 100mg BID x 7 days",
            "Must screen for syphilis (RPR/VDRL), HIV, hepatitis B in all new STI diagnoses",
            "Partner notification and treatment within 60 days is required",
            "Pregnancy test mandatory in reproductive-age females before treatment",
        ],
    ),
    "Herpes Zoster (Shingles)": (
        "Herpes simplex; contact dermatitis; cellulitis; postherpetic neuralgia",
        [
            "Unilateral dermatomal distribution is pathognomonic — does NOT cross midline",
            "Antiviral (valacyclovir) within 72 hours of rash onset — most effective if started early",
            "Must examine for ophthalmic involvement (V1 distribution): Hutchinson sign (nose tip vesicles) = urgent ophthalmology referral",
            "Pain management: gabapentin or pregabalin for acute neuritis and PHN prevention",
            "Shingrix vaccine recommended for adults ≥ 50, even if prior zoster episode",
        ],
    ),
    "Encopresis / Fecal Incontinence": (
        "Hirschsprung disease; celiac disease; hypothyroidism; spinal cord abnormality",
        [
            "Fecal impaction must be cleared (disimpaction) before starting maintenance laxative",
            "Maintenance: PEG 3350 (MiraLAX) daily for 3-6 months minimum",
            "Behavioral component: scheduled toilet sitting after meals, positive reinforcement, no punishment",
            "Abdominal X-ray to confirm fecal loading if diagnosis uncertain",
            "Must rule out organic causes: Hirschsprung (if constipation since infancy), celiac, hypothyroidism",
        ],
    ),
    "Pediatric Respiratory Infection": (
        "Pertussis; asthma exacerbation; foreign body aspiration; pneumonia; croup",
        [
            "Assess respiratory distress: nasal flaring, retractions, accessory muscle use, O2 saturation",
            "Steeple sign on neck X-ray = croup; thumb sign = epiglottitis (rare but must-not-miss)",
            "Pertussis: paroxysmal cough with inspiratory whoop, post-tussive emesis — macrolide treatment",
            "Foreign body aspiration: sudden onset, unilateral wheeze, history of choking episode",
        ],
    ),
    # ── Kaplan-specific diagnoses ──
    "Hypothyroidism": (
        "Secondary hypothyroidism (pituitary); Hashimoto thyroiditis; depression; anemia",
        [
            "TSH is the initial screening test — elevated TSH with low free T4 confirms primary hypothyroidism",
            "Levothyroxine dosing: 1.6 mcg/kg/day — take on empty stomach, 30-60 min before food",
            "Recheck TSH in 6-8 weeks after initiation or dose change",
            "Anti-TPO antibodies confirm Hashimoto — affects long-term counseling",
            "Drug interactions: calcium, iron, PPI reduce absorption — separate by 4 hours",
        ],
    ),
    "Diabetes Mellitus (Type 2)": (
        "Type 1 DM; LADA; Cushing syndrome; medication-induced hyperglycemia",
        [
            "Diagnostic: FBG ≥ 126, A1C ≥ 6.5%, or random glucose ≥ 200 with classic symptoms",
            "Metformin is first-line — check renal function (eGFR) before starting, hold if < 30",
            "A1C target < 7% for most adults — individualize based on age, comorbidities, hypoglycemia risk",
            "Comprehensive foot exam annually: monofilament testing, dorsalis pedis pulse, visual inspection",
            "Must order: A1C, fasting lipid panel, BMP, urine microalbumin, dilated eye exam referral",
        ],
    ),
    "Systemic Lupus Erythematosus (SLE)": (
        "Rheumatoid arthritis; fibromyalgia; drug-induced lupus; mixed connective tissue disease",
        [
            "ANA is sensitive but not specific — positive ANA alone does not diagnose SLE",
            "Anti-dsDNA and anti-Smith antibodies are specific for SLE — confirm with these",
            "Must check complement levels (C3, C4): low levels indicate active disease",
            "Hydroxychloroquine is recommended for ALL SLE patients — reduces flares and mortality",
            "Lupus nephritis screening: urinalysis for proteinuria and urine protein-to-creatinine ratio",
        ],
    ),
    "Diabetic Ketoacidosis (DKA)": (
        "Hyperosmolar hyperglycemic state (HHS); sepsis; alcoholic ketoacidosis; toxic ingestion",
        [
            "Diagnostic triad: glucose > 250, pH < 7.3, bicarbonate < 18, positive ketones",
            "IV fluids FIRST (NS bolus), then insulin drip — fluids before insulin",
            "Must monitor potassium q2h — insulin drives K+ intracellular, replace when K < 5.3",
            "Anion gap metabolic acidosis: AG = Na - (Cl + HCO3) — elevated in DKA",
            "Identify trigger: infection (most common), medication non-adherence, new-onset T1DM",
        ],
    ),
    "Unstable Angina": (
        "STEMI; NSTEMI; aortic dissection; pulmonary embolism; esophageal rupture",
        [
            "Chest pain at rest or new-onset with minimal exertion = unstable — escalation from stable angina",
            "Serial ECGs and troponins q3-6h — normal initial troponin does not exclude diagnosis",
            "Dual antiplatelet therapy: aspirin + P2Y12 inhibitor (clopidogrel/ticagrelor)",
            "Anticoagulation with heparin and early cardiology consultation for cath lab decision",
            "TIMI risk score guides disposition: higher score = more aggressive intervention",
        ],
    ),
    "Hypertrophic Obstructive Cardiomyopathy (HOCM)": (
        "Aortic stenosis; hypertensive cardiomyopathy; athlete's heart; myocarditis",
        [
            "Systolic murmur that INCREASES with Valsalva and standing (decreased preload) — unique to HOCM",
            "Echocardiogram: asymmetric septal hypertrophy ≥ 15mm, SAM of mitral valve",
            "Avoid dehydration, diuretics, vasodilators, and high-intensity exercise — sudden death risk",
            "Beta-blockers are first-line treatment — slow heart rate, improve filling",
            "Family screening: first-degree relatives need echo + genetic counseling (autosomal dominant)",
        ],
    ),
    "Atrial Fibrillation": (
        "Atrial flutter; SVT; hyperthyroidism; pulmonary embolism; sepsis",
        [
            "CHA₂DS₂-VASc score determines anticoagulation need: ≥ 2 in men, ≥ 3 in women = anticoagulate",
            "Rate control (beta-blocker or CCB) vs rhythm control — rate control adequate for most",
            "DOACs (apixaban, rivarelbaan) preferred over warfarin for stroke prevention",
            "Must check TSH — hyperthyroidism is a reversible cause of AFib",
            "Irregularly irregular rhythm with no P waves on ECG = diagnostic",
        ],
    ),
    "Acute Asthma Exacerbation": (
        "Foreign body aspiration; anaphylaxis; vocal cord dysfunction; COPD in adults; heart failure",
        [
            "Severity assessment: can speak in full sentences (mild) vs single words (severe) vs silent chest (life-threatening)",
            "SABA (albuterol) nebulizer q20min x 3 doses + systemic corticosteroids = initial management",
            "Peak flow < 40% predicted after initial treatment = severe, consider ICU",
            "Must have written asthma action plan with green/yellow/red zones before discharge",
            "Step-up therapy assessment: if using rescue inhaler > 2 days/week, needs controller medication",
        ],
    ),
    "Acute COPD Exacerbation": (
        "Pneumonia; pulmonary embolism; pneumothorax; acute heart failure; lung cancer",
        [
            "Anthonisen criteria: increased dyspnea + increased sputum volume + increased sputum purulence",
            "Systemic corticosteroids (prednisone 40mg x 5 days) — shorter courses now preferred",
            "Antibiotics if 2/3 Anthonisen criteria or requiring mechanical ventilation",
            "Oxygen target 88-92% — avoid over-oxygenation (hypoxic drive suppression)",
            "BiPAP for respiratory acidosis (pH < 7.35) — reduces intubation rates",
        ],
    ),
    "Pulmonary Embolism": (
        "Acute MI; pneumonia; pneumothorax; aortic dissection; anxiety/panic attack",
        [
            "Wells criteria score guides workup: low probability = D-dimer; high probability = CT angiography",
            "D-dimer: sensitive but not specific — negative D-dimer rules OUT PE in low-risk patients",
            "CT pulmonary angiography is gold standard diagnostic test",
            "Anticoagulation: DOAC (rivaroxaban or apixaban) is first-line for most patients",
            "Massive PE (hypotension): systemic thrombolytics (tPA) or surgical embolectomy",
        ],
    ),
    "Pneumocystis jirovecii Pneumonia (PJP)": (
        "Community-acquired pneumonia; TB; Kaposi sarcoma; lymphoma; CMV pneumonitis",
        [
            "Classic presentation: subacute dyspnea + dry cough + fever in HIV patient with CD4 < 200",
            "Chest X-ray: bilateral diffuse ground-glass opacities (may be normal early)",
            "Definitive diagnosis: induced sputum or BAL with methenamine silver stain",
            "Treatment: TMP-SMX (high dose) x 21 days + prednisone if PaO2 < 70 or A-a gradient ≥ 35",
            "Prophylaxis: TMP-SMX when CD4 < 200 or prior PJP — must continue until immune reconstitution",
        ],
    ),
    "Bronchiolitis": (
        "Asthma; pertussis; foreign body aspiration; croup; pneumonia",
        [
            "RSV is the most common cause — peak season October-March",
            "AAP guideline: supportive care ONLY — no albuterol, no steroids, no antibiotics",
            "Hospitalization criteria: O2 sat < 90%, severe respiratory distress, poor feeding, age < 12 weeks",
            "Nasal suctioning before feeds improves feeding tolerance — key nursing education",
            "Palivizumab (Synagis) prophylaxis for high-risk infants: preterm < 29 weeks, CHD, CLD",
        ],
    ),
    "Iron Deficiency Anemia": (
        "Anemia of chronic disease; thalassemia trait; lead poisoning; B12/folate deficiency",
        [
            "Labs: low ferritin (most specific), low serum iron, high TIBC, low transferrin saturation",
            "Microcytic hypochromic RBCs on peripheral smear — but MCV may overlap with thalassemia",
            "Must investigate source of blood loss: menstrual history, GI bleed evaluation (occult blood, colonoscopy if age > 45)",
            "Oral iron (ferrous sulfate 325mg) on empty stomach with vitamin C — recheck ferritin at 8-12 weeks",
            "GI side effects common — if intolerant, switch to ferrous gluconate or IV iron",
        ],
    ),
    "Sickle Cell Anemia": (
        "Aplastic crisis; splenic sequestration; acute chest syndrome; stroke; osteomyelitis",
        [
            "Vaso-occlusive crisis: aggressive IV hydration + IV opioids (do NOT undertreat pain)",
            "Acute chest syndrome: new pulmonary infiltrate + fever/respiratory symptoms = medical emergency",
            "Hydroxyurea reduces crisis frequency — indicated if ≥ 3 crises/year",
            "Must assess for stroke risk: transcranial Doppler screening annually ages 2-16",
            "Penicillin prophylaxis until age 5 + pneumococcal vaccination = standard of care",
        ],
    ),
    "Ascending Cholangitis": (
        "Acute cholecystitis; choledocholithiasis; hepatitis; pancreatitis; liver abscess",
        [
            "Charcot triad: fever + jaundice + RUQ pain — present in ~50-70% of cases",
            "Reynolds pentad: add altered mental status + hypotension = severe/suppurative cholangitis",
            "ERCP is both diagnostic and therapeutic — emergent decompression needed",
            "Blood cultures + broad-spectrum antibiotics (piperacillin-tazobactam) before ERCP",
            "Labs: elevated bilirubin, ALP, GGT >> AST/ALT (cholestatic pattern)",
        ],
    ),
    "Peptic Ulcer Disease": (
        "Gastric cancer; pancreatitis; GERD; cholecystitis; Zollinger-Ellison syndrome",
        [
            "H. pylori testing is mandatory: urea breath test (non-invasive) or stool antigen",
            "Triple therapy: PPI + clarithromycin + amoxicillin x 14 days — confirm eradication",
            "Must discontinue NSAIDs — most common cause after H. pylori",
            "Alarm symptoms (weight loss, dysphagia, GI bleed, age > 55 new onset) = EGD referral",
            "Black stools (melena) = upper GI bleeding — check hemoglobin, consider transfusion",
        ],
    ),
    "GERD": (
        "Eosinophilic esophagitis; PUD; cardiac chest pain; esophageal motility disorders",
        [
            "Empiric PPI trial (omeprazole 20mg daily) x 8 weeks is diagnostic AND therapeutic",
            "Lifestyle modifications: elevate HOB, avoid meals 2-3h before bed, reduce trigger foods",
            "Alarm symptoms for EGD referral: dysphagia, odynophagia, weight loss, GI bleeding, age > 60",
            "Long-term PPI risks: hypomagnesemia, C. diff, fractures — reassess need periodically",
        ],
    ),
    "Infectious Colitis": (
        "C. difficile colitis; IBD flare; ischemic colitis; appendicitis; diverticulitis",
        [
            "Stool culture + C. diff toxin PCR + ova and parasites are initial workup",
            "Most infectious diarrhea is self-limiting — antibiotics NOT needed for mild cases",
            "Fluoroquinolones reserved for severe/invasive disease (bloody diarrhea, high fever, immunocompromised)",
            "Must assess hydration status and replace electrolytes — oral rehydration preferred",
        ],
    ),
    "Encopresis": (
        "Hirschsprung disease; celiac disease; hypothyroidism; spinal cord abnormality",
        [
            "Fecal impaction must be cleared first — PEG 3350 or enema for disimpaction",
            "Maintenance: PEG 3350 (MiraLAX) daily x 3-6 months minimum after disimpaction",
            "Behavioral intervention: regular toilet sitting 5-10 min after meals, reward system",
            "Abdominal X-ray to assess fecal loading and monitor treatment response",
        ],
    ),
    "Pinworm Infection (Enterobiasis)": (
        "Perianal dermatitis; hemorrhoids; anal fissure; threadworm; sexually transmitted proctitis",
        [
            "Scotch tape test (cellophane tape test) in the morning before bathing = diagnostic",
            "Mebendazole or albendazole single dose, repeat in 2 weeks — treats the reinfection cycle",
            "Must treat ALL household contacts simultaneously — reinfection from fomites is common",
            "Environmental measures: wash bedding/towels in hot water, short fingernails, good hand hygiene",
        ],
    ),
    "Menopause": (
        "Thyroid disorder; depression; adrenal insufficiency; premature ovarian failure",
        [
            "Diagnosis is clinical: 12 consecutive months of amenorrhea in age-appropriate patient",
            "FSH > 30 IU/L confirms menopause if diagnosis uncertain — not needed in typical presentation",
            "HRT: estrogen + progesterone (if uterus intact) for vasomotor symptoms — lowest dose, shortest duration",
            "Must assess cardiovascular risk, breast cancer risk, VTE history before initiating HRT",
            "Non-hormonal options for VT: SSRIs, gabapentin, clonidine — for contraindications to HRT",
        ],
    ),
    "Cervicitis": (
        "PID; ectopic pregnancy; vaginitis; cervical cancer; endometritis",
        [
            "NAAT for GC and CT is gold standard — endocervical swab or urine",
            "Empiric treatment for gonorrhea + chlamydia while awaiting results: ceftriaxone IM + doxycycline",
            "Must assess for PID: cervical motion tenderness + adnexal tenderness = treat as PID",
            "Partner treatment within 60 days is mandatory — expedited partner therapy if available",
            "Test of cure not needed for chlamydia; retest in 3 months for reinfection surveillance",
        ],
    ),
    "Vulvovaginitis": (
        "Bacterial vaginosis; candidiasis; trichomoniasis; contact dermatitis; foreign body",
        [
            "Wet mount microscopy: clue cells (BV), pseudohyphae (candida), motile trichomonads (trich)",
            "pH testing: < 4.5 = candidiasis; > 4.5 = BV or trichomoniasis",
            "BV: metronidazole (oral or vaginal); Candida: fluconazole PO or topical azole",
            "In prepubertal girls: most common cause is nonspecific — improved hygiene is first-line",
            "Must consider foreign body in pediatric patient with persistent vaginal discharge",
        ],
    ),
    "Cystitis (Urinary Tract Infection)": (
        "Pyelonephritis; vulvovaginitis; urethritis; appendicitis (pediatric)",
        [
            "Pediatric UTI: obtain UA + culture via catheterization or suprapubic aspirate (not bag specimen)",
            "First febrile UTI in child < 2yo: renal/bladder ultrasound to evaluate for anomalies",
            "VCUG if ultrasound is abnormal or recurrent UTI — assesses for vesicoureteral reflux",
            "Treatment: cephalexin or TMP-SMX for 7-14 days in pediatric patients",
        ],
    ),
    "Ischemic Stroke": (
        "Hemorrhagic stroke; TIA; Todd paralysis; hypoglycemia; brain tumor; conversion disorder",
        [
            "Non-contrast CT head STAT to rule out hemorrhage before thrombolytics",
            "tPA within 4.5 hours of symptom onset if no contraindications — time is brain",
            "NIH Stroke Scale (NIHSS) quantifies deficit severity — must document",
            "Last-known-well time, not symptom discovery time, determines tPA eligibility",
            "Dual antiplatelet (aspirin + clopidogrel) for 21 days in minor stroke/TIA, then single agent",
        ],
    ),
    "Concussion": (
        "Intracranial hemorrhage (epidural, subdural); skull fracture; diffuse axonal injury; post-concussive syndrome",
        [
            "CT head indicated if: loss of consciousness, vomiting, GCS < 15, focal deficit, or age < 2",
            "PECARN criteria guide imaging decisions in pediatric head trauma — reduces unnecessary CT",
            "Return-to-play protocol: symptom-free rest → light aerobic → sport-specific → full contact (graduated steps)",
            "Must counsel on post-concussion red flags: worsening headache, repeated vomiting, seizure, confusion",
            "Academic accommodations may be needed: reduced screen time, extra time, cognitive rest",
        ],
    ),
    "Gout (Kaplan)": (
        "Septic arthritis; pseudogout (CPPD); cellulitis; fracture",
        [
            "Arthrocentesis with negatively birefringent needle-shaped MSU crystals = gold standard diagnosis",
            "Serum uric acid can be NORMAL during acute flare — do not use to rule out",
            "Acute management: NSAIDs, colchicine, or corticosteroids — do NOT start allopurinol acutely",
            "Allopurinol for chronic prevention: start 2+ weeks after flare with colchicine cover",
        ],
    ),
    "Herniated Disc": (
        "Cauda equina syndrome; spinal stenosis; malignancy; epidural abscess; aortic aneurysm",
        [
            "Straight leg raise test: positive at 30-60° reproducing radicular pain = L4-S1 root involvement",
            "Red flags for imaging: bowel/bladder dysfunction (cauda equina), progressive neurological deficit, fever, cancer history",
            "Conservative management first: NSAIDs + activity modification — avoid bed rest > 2 days",
            "MRI is imaging of choice if red flags present or symptoms persist > 6 weeks",
            "Cauda equina syndrome (saddle anesthesia, urinary retention) = surgical emergency",
        ],
    ),
    "Osteoarthritis": (
        "Rheumatoid arthritis; gout; septic arthritis; avascular necrosis; bursitis",
        [
            "X-ray findings: joint space narrowing, osteophytes, subchondral sclerosis, subchondral cysts",
            "Labs are NORMAL in OA — use labs to rule out inflammatory arthritis (ESR, CRP, RF, anti-CCP)",
            "First-line pharmacotherapy: acetaminophen, then topical NSAIDs, then oral NSAIDs",
            "Non-pharmacologic: weight loss (if BMI ≥ 25), physical therapy, assistive devices",
            "Joint replacement referral if failed conservative management with functional limitation",
        ],
    ),
    "Ankle Fracture": (
        "Ankle sprain; tendon rupture; stress fracture; osteochondral lesion",
        [
            "Ottawa ankle rules determine need for X-ray — reduces unnecessary imaging",
            "AP, lateral, and mortise views required for complete radiographic evaluation",
            "Weber classification (A, B, C) based on fibula fracture level — guides surgical vs conservative",
            "Stable, non-displaced fractures: short leg cast or walking boot for 4-6 weeks",
        ],
    ),
    "Post-Traumatic Stress Disorder (PTSD)": (
        "Acute stress disorder; adjustment disorder; TBI; substance use disorder; depression with psychotic features",
        [
            "PCL-5 (PTSD Checklist) is validated screening tool — score ≥ 33 suggests diagnosis",
            "Trauma-focused CBT (CPT or PE) is first-line treatment per VA/DoD guidelines",
            "Pharmacotherapy: sertraline or paroxetine are only FDA-approved SSRIs for PTSD",
            "Prazosin for trauma-related nightmares — alpha-1 blocker, monitor orthostatic hypotension",
            "Must screen for comorbid substance use, depression, and suicidal ideation",
        ],
    ),
    "Schizophrenia": (
        "Schizoaffective disorder; bipolar with psychotic features; substance-induced psychosis; delirium; brain tumor",
        [
            "Positive symptoms: hallucinations, delusions, disorganized speech — respond to antipsychotics",
            "Negative symptoms: flat affect, avolition, alogia — harder to treat, may need clozapine",
            "Second-generation antipsychotic (risperidone, aripiprazole) is first-line pharmacotherapy",
            "Must monitor: metabolic syndrome (weight, A1C, lipids), prolactin, QTc at baseline and follow-up",
            "Clozapine for treatment-resistant schizophrenia — requires ANC monitoring (REMS program)",
        ],
    ),
    "Anorexia Nervosa": (
        "Bulimia nervosa; hyperthyroidism; celiac disease; Addison disease; malignancy",
        [
            "BMI < 18.5 with intense fear of weight gain + body image distortion = diagnostic criteria",
            "Must check: CBC, CMP (electrolytes, renal, liver), phosphorus, magnesium, TSH, ECG",
            "Refeeding syndrome risk: hypophosphatemia is life-threatening — monitor phosphorus closely",
            "Medical hospitalization criteria: HR < 50, BP < 90/60, BMI < 15, electrolyte abnormalities",
            "Family-Based Treatment (Maudsley method) is first-line for adolescents with AN",
        ],
    ),
    "Generalized Anxiety Disorder (GAD)": (
        "Hyperthyroidism; panic disorder; social anxiety; PTSD; substance withdrawal; cardiac arrhythmia",
        [
            "GAD-7 score must be documented — score ≥ 10 indicates moderate anxiety",
            "CBT is evidence-based first-line treatment — equal efficacy to medication",
            "SSRI (sertraline) or SNRI (venlafaxine) is first-line pharmacotherapy",
            "Avoid benzodiazepines for maintenance — risk of dependence, tolerance, rebound anxiety",
            "Must rule out medical causes: TSH, CBC, CMP, consider EKG if palpitations",
        ],
    ),
    "Major Depressive Disorder (MDD)": (
        "Bipolar disorder; hypothyroidism; substance use; anemia; sleep disorder",
        [
            "PHQ-9 score must be documented — ≥ 10 indicates moderate depression",
            "Columbia Suicide Severity Rating Scale for suicidal ideation assessment — document at every visit",
            "SSRI (sertraline, escitalopram) is first-line — 4-6 weeks for full therapeutic effect",
            "Must screen for bipolar (MDQ) before starting antidepressant — SSRIs can trigger mania",
            "Follow-up within 2 weeks of starting medication — assess response and suicidal ideation",
        ],
    ),
    "Bipolar Disorder (Kaplan)": (
        "MDD; schizoaffective disorder; substance-induced mood disorder; ADHD; personality disorders",
        [
            "Mood stabilizer (lithium or valproate) is first-line — NOT antidepressant monotherapy",
            "Lithium monitoring: serum level (0.6-1.2), renal function, thyroid, q6-12 months",
            "Manic episode: ≥ 1 week elevated/irritable mood + ≥ 3 DIGFAST symptoms + functional impairment",
            "Atypical antipsychotics (quetiapine, olanzapine) for acute mania — rapid onset",
            "Antidepressant monotherapy is CONTRAINDICATED — can trigger mania",
        ],
    ),
    "Alcohol Use Disorder": (
        "Hepatic encephalopathy; withdrawal seizures; Wernicke encephalopathy; delirium tremens; pancreatitis",
        [
            "AUDIT-C or CAGE questionnaire for screening — document score at assessment",
            "CIWA-Ar protocol for withdrawal monitoring — benzodiazepines for CIWA ≥ 10",
            "Thiamine (B1) supplementation BEFORE glucose — prevents Wernicke encephalopathy",
            "Maintenance medications: naltrexone (reduces cravings) or acamprosate (maintains abstinence)",
            "Delirium tremens peaks at 48-72 hours — autonomic instability + hallucinations + seizures = ICU",
        ],
    ),
    "PTSD": (
        "Acute stress disorder; adjustment disorder; depression; substance use; TBI",
        [
            "PCL-5 validated screening tool — score ≥ 33 suggests PTSD diagnosis",
            "Trauma-focused CBT (CPT or PE) is first-line per VA/DoD guidelines",
            "Sertraline or paroxetine are FDA-approved SSRIs for PTSD",
            "Prazosin for nightmares — alpha-1 blocker, titrate slowly, monitor BP",
            "Screen for comorbidities: substance use, depression, TBI, chronic pain",
        ],
    ),
    "Subarachnoid Hemorrhage (SAH)": (
        "Migraine; meningitis; hypertensive emergency; cervical artery dissection; thunderclap headache DDx",
        [
            "Non-contrast CT head within 6 hours is 98% sensitive — LP if CT negative and suspicion high",
            "Classic: 'worst headache of my life' with sudden thunderclap onset",
            "LP: xanthochromia in CSF supernatant confirms SAH when CT is negative",
            "CTA or conventional angiography to identify aneurysm source",
            "Nimodipine for vasospasm prevention — start within 96 hours, continue for 21 days",
        ],
    ),
    "Inguinal Hernia": (
        "Femoral hernia; lymphadenopathy; testicular torsion; hydrocele; varicocele",
        [
            "Reducible vs incarcerated vs strangulated — strangulated is a surgical emergency",
            "Indirect hernia (lateral to inferior epigastric vessels) is most common — especially in young males",
            "Exam: impulse with cough on palpation of inguinal canal; check for bowel sounds in scrotum",
            "Surgical repair indicated for symptomatic hernias — watchful waiting only if asymptomatic, reducible",
        ],
    ),
    "Pneumothorax": (
        "Pulmonary embolism; myocardial infarction; pleural effusion; hemothorax; rib fracture",
        [
            "Tension pneumothorax: tracheal deviation + hypotension + absent breath sounds = needle decompression STAT",
            "Upright chest X-ray: visceral pleural line with absent lung markings peripherally",
            "Small (< 2 cm apex-to-cupola) primary spontaneous: observation with O2 supplementation",
            "Large or symptomatic: chest tube (tube thoracostomy) for drainage",
            "Risk factors: tall thin males, smoking, COPD, Marfan syndrome, trauma",
        ],
    ),
    "Diverticular Hemorrhage": (
        "Colorectal cancer; angiodysplasia; hemorrhoids; ischemic colitis; IBD",
        [
            "Most common cause of massive lower GI bleeding in adults > 60",
            "80% stop spontaneously — initial management is resuscitation: IV fluids, type & cross, CBC",
            "Colonoscopy after adequate bowel prep is both diagnostic and potentially therapeutic",
            "CTA (CT angiography) if active bleeding and patient too unstable for colonoscopy",
            "Must assess hemodynamic stability: tachycardia, hypotension = aggressive resuscitation",
        ],
    ),
    "Acute Appendicitis": (
        "Mesenteric lymphadenitis; ruptured ovarian cyst; ectopic pregnancy; Meckel diverticulitis; renal colic",
        [
            "Classic progression: periumbilical pain → RLQ (McBurney's point) migration — 50% have this pattern",
            "Alvarado (MANTRELS) score helps risk-stratify: ≥ 7 = high probability, surgical consultation",
            "CT abdomen/pelvis with IV contrast is most accurate imaging in adults",
            "Pediatric: ultrasound first (to avoid radiation) — CT if ultrasound inconclusive",
            "Appendectomy within 24 hours of diagnosis — laparoscopic preferred",
        ],
    ),
    "Uterine Atony": (
        "Genital tract laceration; retained placental tissue; coagulopathy; uterine rupture",
        [
            "Most common cause of postpartum hemorrhage — uterus fails to contract after delivery",
            "Bimanual uterine massage is first-line intervention — perform immediately",
            "Oxytocin (Pitocin) IV is first-line uterotonic — then methylergonovine or carboprost",
            "Must estimate blood loss and monitor for hemorrhagic shock — > 500mL vaginal, > 1000mL cesarean",
            "Risk factors: overdistended uterus (macrosomia, polyhydramnios, multiples), prolonged labor, MgSO4 use",
        ],
    ),
    "Ectopic Pregnancy": (
        "Threatened abortion; ovarian torsion; ruptured ovarian cyst; PID; appendicitis",
        [
            "Quantitative beta-hCG + transvaginal ultrasound = initial diagnostic workup",
            "Discriminatory zone: hCG > 1500-2000 with no intrauterine pregnancy on TVUS = concerning for ectopic",
            "Methotrexate for unruptured ectopic < 3.5cm without cardiac activity — medical management",
            "Ruptured ectopic: emergent surgery (laparoscopic salpingectomy or salpingostomy)",
            "All Rh-negative patients need RhoGAM after ectopic pregnancy management",
        ],
    ),
    "Normal Pregnancy": (
        "Ectopic pregnancy; gestational trophoblastic disease; threatened abortion; molar pregnancy",
        [
            "Prenatal labs 1st trimester: CBC, type & screen, RPR, HIV, HBsAg, rubella, UA/culture, Pap",
            "Nuchal translucency + first trimester screen at 11-14 weeks — genetic screening",
            "Fundal height: should match gestational age ± 2cm from 20-36 weeks",
            "20-week anatomy scan (level II ultrasound) — fetal structural survey",
            "Group B Strep screening at 36-37 weeks — intrapartum antibiotics if positive",
        ],
    ),
    "Intimate Partner Violence (IPV) screening": (
        "Accidental injury; coagulopathy; osteogenesis imperfecta; self-harm",
        [
            "HITS tool or partner violence screen at every prenatal visit — USPSTF B recommendation",
            "Must document injuries with body map if patient discloses — medicolegal importance",
            "Safety planning: escape plan, bag packed, important documents, local shelter information",
            "Report as mandated if minor or elder involved — adult patients decide whether to report",
            "Warm referral to domestic violence resources — National Hotline: 1-800-799-7233",
        ],
    ),
    "Pre-eclampsia": (
        "Chronic hypertension; gestational hypertension; HELLP syndrome; eclampsia; thrombotic microangiopathy",
        [
            "Diagnostic criteria: new onset HTN ≥ 140/90 after 20 weeks + proteinuria OR end-organ damage",
            "Severe features: BP ≥ 160/110, platelets < 100k, elevated LFTs, renal insufficiency, pulmonary edema",
            "MgSO4 for seizure prophylaxis in severe preeclampsia — monitor reflexes, urine output, RR",
            "Definitive treatment is DELIVERY — timing depends on gestational age and severity",
            "HELLP syndrome: Hemolysis, Elevated Liver enzymes, Low Platelets — medical emergency, deliver regardless of GA",
        ],
    ),
    "Unspecified dermatological condition": (
        "Psoriasis; eczema; tinea; contact dermatitis; drug eruption; malignancy",
        [
            "Describe using dermatological terminology: distribution, morphology, color, arrangement, texture",
            "Must document: primary lesion type (macule, papule, plaque, vesicle, etc.) and secondary changes",
            "KOH prep for suspected fungal; dermoscopy for pigmented lesions; biopsy if uncertain",
            "Comprehensive drug history — many rashes are drug eruptions (onset 1-3 weeks after new medication)",
        ],
    ),
    "Multiple (comprehensive exam)": (
        "Multiple system assessment — must identify primary and secondary diagnoses",
        [
            "Systematic head-to-toe assessment documenting all systems",
            "Prioritize findings by clinical significance — life-threatening first",
            "Document pertinent positives AND pertinent negatives for each system",
            "Comprehensive medication reconciliation is required component",
        ],
    ),
}

# ── Helper functions ──────────────────────────────────────────────

def make_slug(name, diagnosis, institution):
    """Generate a kebab-case slug from patient name and diagnosis."""
    name = name.replace("(", "").replace(")", "").replace("/", " ")
    # Clean up unnamed cases
    if "Unnamed" in name or name.startswith("Unnamed"):
        base = diagnosis.lower()
    else:
        first = name.split("/")[0].strip()  # Take first alias
        first = first.replace("Mr. ", "").replace("Mrs. ", "").replace("Ms. ", "")
        base = first.lower()

    base = re.sub(r"[^a-z0-9\s-]", "", base)
    base = re.sub(r"\s+", "-", base.strip())
    base = re.sub(r"-+", "-", base)

    # Add diagnosis suffix for clarity
    dx_short = diagnosis.split("/")[0].split("(")[0].strip().lower()
    dx_short = re.sub(r"[^a-z0-9\s]", "", dx_short)
    dx_short = re.sub(r"\s+", "-", dx_short.strip())
    dx_short = re.sub(r"-+", "-", dx_short)

    if dx_short and dx_short not in base:
        slug = f"{base}-{dx_short}"
    else:
        slug = base

    # Add kaplan suffix for Kaplan cases
    if "Kaplan" in institution:
        slug += "-kaplan"

    # Trim to reasonable length
    slug = slug[:60]
    return slug


def classify(case, is_kaplan):
    """Determine lead_time and data_level based on classification rules."""
    conf = case.get("confidence", "Low")
    dx = case.get("primary_diagnosis", "")

    if is_kaplan:
        return "on-request", "medium"

    if conf == "High" and dx != "Undisclosed":
        return "fast-build", "high"
    elif conf == "Medium":
        return "on-request", "medium"
    else:  # Low or Undisclosed
        return "on-request", "low"


def get_patient_short(case):
    age = case.get("age")
    gender = case.get("gender", "Unspecified")

    if age is not None and age > 0:
        if age < 1:
            age_str = "Infant"
        elif age <= 3:
            age_str = f"{age}-year-old"
        else:
            age_str = f"{age}-year-old"
    else:
        tags = case.get("demographic_tags", "")
        if "Infant" in tags:
            age_str = "Infant"
        elif "Toddler" in tags:
            age_str = "Toddler"
        elif "Child" in tags or "Pediatric" in tags:
            age_str = "Pediatric"
        elif "Adolescent" in tags:
            age_str = "Adolescent"
        elif "Young Adult" in tags:
            age_str = "Young adult"
        elif "Middle-Aged" in tags:
            age_str = "Middle-aged adult"
        elif "Older Adult" in tags:
            age_str = "Older adult"
        elif "Postpartum" in tags:
            age_str = "Postpartum"
        elif "Pregnant" in tags:
            age_str = "Pregnant"
        else:
            age_str = "Adult"

    if gender == "Male":
        g = "male"
    elif gender == "Female":
        g = "female"
    else:
        g = "patient"

    return f"{age_str} {g}"


def get_course_code(case, is_kaplan):
    """Map course_code to our registry codes."""
    code = case.get("course_code", "").strip()
    mapping = {
        "NR509": "nr-509",
        "NR511": "nr-511",
        "NR602": "nr-602",
        "NR305": "nr-305",
        "NR576": "nr-576",
        "NR601": "nr-601",
        "NR603": "nr-603",
        "NR667": "nr-667",
        "NURS 6512": "nurs-6512",
        "NRNP 6531": "nrnp-6531",
        "NRNP 6541": "nrnp-6541",
        "NRNP 6542": "nrnp-6542",
        "NRNP 6552": "nrnp-6552",
        "NRNP 6568": "nrnp-6568",
        "NURS 6531": "nurs-6531",
        "NURS 6560": "nurs-6560",
        "NURS 5342": "nurs-5342",
        "NU664C": "nu664c",
        "NSG 6330": "nsg-6330",
        "NSG 270": "nsg-270",
        "NUR 560": "nur-560",
        "Shadow Health": "shadow-health",
        "Multiple": "multiple",
        "Adult Gerontology": "multiple",
    }

    if is_kaplan or code.startswith("Kaplan"):
        return ["kaplan-ihuman"]

    return [mapping.get(code, "multiple")]


def get_school(case, is_kaplan):
    inst = case.get("institution", "")
    if is_kaplan or "Kaplan" in inst:
        return ["kaplan"]
    elif "Chamberlain" in inst:
        return ["chamberlain"]
    elif "Walden" in inst:
        return ["walden"]
    elif "Regis" in inst:
        return ["regis"]
    elif "South University" in inst:
        return ["south-university"]
    elif "Virginia Western" in inst:
        return ["virginia-western"]
    elif "Miami" in inst:
        return ["miami"]
    elif "Southern New Hampshire" in inst:
        return ["snhu"]
    else:
        return ["multiple"]


def get_tags(case):
    specialty = case.get("specialty", "")
    tags_list = []

    tag_map = {
        "Cardiovascular": "Cardiovascular",
        "Respiratory": "Respiratory",
        "Gastrointestinal": "Gastrointestinal",
        "Neurology": "Neurology",
        "Dermatology": "Dermatology",
        "Endocrine": "Endocrine",
        "Behavioral Health": "Behavioral Health",
        "Psychiatry": "Behavioral Health",
        "Pediatrics": "Pediatrics",
        "Women's Health": "Women's Health",
        "OB/GYN": "Women's Health",
        "OB": "Women's Health",
        "Musculoskeletal": "Musculoskeletal",
        "Genitourinary": "Genitourinary",
        "Nephrology": "Nephrology",
        "Hematology": "Hematology",
        "Surgery": "Surgery",
        "Emergency": "Emergency",
        "Ophthalmology": "Ophthalmology",
        "Infectious Disease": "Infectious Disease",
        "Rheumatology": "Rheumatology",
        "Sleep Medicine": "Sleep Medicine",
        "Gerontology": "Gerontology",
        "Oncology": "Oncology",
        "ENT": "ENT",
        "Environmental": "Emergency",
    }

    for keyword, tag in tag_map.items():
        if keyword in specialty and tag not in tags_list:
            tags_list.append(tag)

    # Add age-group tag
    demo = case.get("demographic_tags", "")
    if any(x in demo for x in ["Pediatric", "Child", "Toddler", "Infant"]):
        if "Pediatrics" not in tags_list:
            tags_list.append("Pediatrics")
    elif any(x in demo for x in ["Adolescent"]):
        if "Adolescent" not in tags_list:
            tags_list.append("Adolescent")
    elif any(x in demo for x in ["Older Adult"]):
        if "Gerontology" not in tags_list:
            tags_list.append("Gerontology")

    if not tags_list:
        tags_list.append("General")

    # Always add Adult if no pediatric/adolescent tag
    if not any(t in tags_list for t in ["Pediatrics", "Adolescent", "Gerontology"]):
        tags_list.append("Adult")

    return tags_list


def get_clinical(dx):
    """Look up clinical content by trying exact match, then partial matches."""
    if dx in CLINICAL:
        return CLINICAL[dx]

    # Try partial match
    for key in CLINICAL:
        if key.lower() in dx.lower() or dx.lower() in key.lower():
            return CLINICAL[key]

    # Default
    return CLINICAL.get("Undisclosed", (
        "Comprehensive differential required based on presenting symptoms",
        [
            "Complete history with systematic review of systems",
            "Focused physical exam based on chief complaint",
            "Order appropriate initial labs and imaging",
            "Document pertinent negatives to narrow differential",
        ],
    ))


def format_case(case_dict):
    """Format a single case dictionary as Python source code."""
    lines = ["    {"]

    for key, val in case_dict.items():
        if isinstance(val, str):
            # Escape single quotes in strings
            escaped = val.replace("'", "\\'").replace('"', '\\"')
            lines.append(f'        "{key}": "{escaped}",')
        elif isinstance(val, list):
            if all(isinstance(x, str) for x in val):
                if len(val) <= 2:
                    items = ", ".join(f'"{v}"' for v in val)
                    lines.append(f'        "{key}": [{items}],')
                else:
                    lines.append(f'        "{key}": [')
                    for v in val:
                        escaped = v.replace('"', '\\"')
                        lines.append(f'            "{escaped}",')
                    lines.append(f'        ],')
        elif val is None:
            lines.append(f'        "{key}": None,')
        elif isinstance(val, (int, float)):
            lines.append(f'        "{key}": {val},')

    lines.append("    },")
    return "\n".join(lines)


# ── Main processing ──────────────────────────────────────────────

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

cases = data["cases"]

# Build merge groups: first ID collects extra courses from second
merge_extras = {}  # first_id → list of extra case dicts
for second_id, first_id in MERGE_MAP.items():
    for c in cases:
        if c["id"] == second_id:
            merge_extras.setdefault(first_id, []).append(c)

# Track slugs to avoid duplicates
used_slugs = set()

# Existing slugs from cases_data.py
existing_slugs = {
    "harvey-hoya-htn", "bebe-babbitt-migraine", "cynthia-francis-hyperlipidemia",
    "samantha-graves-gastroenteritis", "kennedy-poole-adhd", "victoria-lewis-rash",
    "betty-burns-pt1", "betty-burns-pt2", "christine-smith-pyelonephritis",
    "amanda-wheaton-pharyngitis", "marvin-webber-cardiovascular",
    "nrnp6531-wk7-pneumonia", "caleb-metz-adolescent", "emma-ryan-pediatric-uri",
    "benjamin-cavill-low-back", "kathleen-parks-nr509", "nrnp6541-encopresis",
    "tina-jones-shadow-health", "nrnp6531-wk2-gi", "nrnp6531-wk4-cardiovascular",
    "adam-barnes-5yo", "peds-18mo-vomiting", "nurs6512-nr509-wk1-uri",
    "nrnp6552-prenatal", "nrnp6552-abnormal-uterine-bleeding", "nrnp6552-contraception",
    "nrnp6568-mdd", "nrnp6568-anxiety-gad", "nrnp6568-bipolar", "nrnp6568-psychosis",
    "tanner-bell-uri", "lori-jacobs-uti", "geriatric-fall-risk",
    "adult-depression-screen", "type-2-diabetes-new", "copd-exacerbation",
    "heart-failure-management", "hypothyroidism-adult",
}
used_slugs.update(existing_slugs)

new_cases = []
processed_ids = set()

for case in cases:
    cid = case["id"]

    # Skip already-in-catalog
    if cid in SKIP_IDS:
        continue

    # Skip second-of-merge (folded into first)
    if cid in MERGE_MAP:
        continue

    # Skip already processed
    if cid in processed_ids:
        continue

    processed_ids.add(cid)

    is_kaplan = "Kaplan" in case.get("institution", "") or "Kaplan" in case.get("course_code", "")
    dx = case.get("primary_diagnosis", "Undisclosed")
    name = case.get("patient_name", "Unnamed")

    # Generate slug
    slug = make_slug(name, dx, case.get("institution", ""))

    # Ensure unique slug
    if slug in used_slugs:
        slug = slug + "-2"
    if slug in used_slugs:
        slug = slug[:-2] + f"-{cid}"
    used_slugs.add(slug)

    # Classification
    lead_time, data_level = classify(case, is_kaplan)

    # Course info
    courses = get_course_code(case, is_kaplan)

    # If this is a merge target, add extra courses
    if cid in merge_extras:
        for extra in merge_extras[cid]:
            extra_courses = get_course_code(extra, "Kaplan" in extra.get("institution", ""))
            for ec in extra_courses:
                if ec not in courses:
                    courses.append(ec)

    # Build course display string
    course_label = case.get("course_code", "Multiple")
    week = case.get("week_module", "")
    if week and week != "Unspecified" and week != "N/A (platform case)":
        course_display = f"{course_label} {week}"
    else:
        course_display = course_label

    # Kaplan course note
    if is_kaplan:
        course_display = f"Kaplan Clinical Canvas — verify institution"

    # Merge extra course info
    if cid in merge_extras:
        extra_labels = []
        for extra in merge_extras[cid]:
            el = extra.get("course_code", "")
            ew = extra.get("week_module", "")
            if ew and ew != "Unspecified":
                extra_labels.append(f"{el} {ew}")
            else:
                extra_labels.append(el)
        course_display += " / " + " / ".join(extra_labels)

    # Title
    clean_name = name.split("/")[0].strip()
    if "Unnamed" in clean_name:
        clean_name = clean_name.replace("Unnamed", "").strip(" (-)")
        if not clean_name:
            clean_name = "Unnamed Patient"
    clean_name = clean_name.replace("(", "").replace(")", "").strip()
    title_dx = dx.split("/")[0].split("(")[0].strip()
    title = f"{clean_name} — {title_dx}"

    # Aliases
    aliases = [name.split("/")[0].strip()]
    if "/" in name:
        for alias in name.split("/"):
            a = alias.strip()
            if a and a not in aliases:
                aliases.append(a)

    # Get clinical content
    must_not_miss, key_traps = get_clinical(dx)

    # Build case dict
    case_dict = {
        "slug": slug,
        "title": title,
        "patient_short": get_patient_short(case),
        "chief_complaint": case.get("chief_complaint", ""),
        "diagnosis": dx,
        "course": course_display,
        "school": case.get("institution", "Multiple Institutions"),
        "aliases": aliases,
        "must_not_miss": must_not_miss,
        "key_scoring_traps": key_traps,
        "tags": get_tags(case),
        "preview_hpi_count": None,
        "preview_pe_count": None,
        "preview_dx_count": None,
        "lead_time": lead_time,
        "data_level": data_level,
        "courses": courses,
        "schools": get_school(case, is_kaplan),
    }

    new_cases.append((case_dict, case))


# ── Read existing file and inject new cases ───────────────────────

with open(CASES_PY, "r", encoding="utf-8") as f:
    content = f.read()

# Find the insertion point: the closing ] of the CASES list
# The last case ends with "    },\n]"
# We need to insert before the "]"

# Split at the CASES list closing bracket
# Find the pattern:  },\n] that ends the CASES list
insert_marker = '    },\n]'
idx = content.rfind(insert_marker)
if idx == -1:
    # Try alternative
    insert_marker = '    },\r\n]'
    idx = content.rfind(insert_marker)

if idx == -1:
    raise ValueError("Could not find CASES list closing bracket")

before = content[:idx + len("    },\n")]
after = content[idx + len("    },\n"):]  # starts with "]"

# Group new cases by tier for organized output
fast_build = [c for c, raw in new_cases if c["lead_time"] == "fast-build"]
on_request_med = [c for c, raw in new_cases if c["lead_time"] == "on-request" and c["data_level"] == "medium"]
on_request_low = [c for c, raw in new_cases if c["lead_time"] == "on-request" and c["data_level"] == "low"]

section_lines = []

# Section header: iHuman expansion
section_lines.append("")
section_lines.append("    # ══════════════════════════════════════════════════════════════")
section_lines.append("    # iHUMAN DATASET EXPANSION — 150-case import")
section_lines.append("    # ══════════════════════════════════════════════════════════════")
section_lines.append("")
section_lines.append("    # ── FAST-BUILD: High-confidence cases with real diagnoses ────")
section_lines.append("")

for c in fast_build:
    section_lines.append(format_case(c))

section_lines.append("")
section_lines.append("    # ── ON-REQUEST (Medium): Medium-confidence cases ─────────────")
section_lines.append("")

for c in on_request_med:
    section_lines.append(format_case(c))

section_lines.append("")
section_lines.append("    # ── ON-REQUEST (Low): Low-confidence / undisclosed cases ─────")
section_lines.append("")

for c in on_request_low:
    section_lines.append(format_case(c))

new_content = before + "\n".join(section_lines) + "\n" + after

# ── Update COURSES dict ──────────────────────────────────────────

new_courses = '''COURSES = {
    "nr-509":    {"label": "NR 509", "full": "Advanced Physical Assessment", "school": "Chamberlain"},
    "nr-511":    {"label": "NR 511", "full": "Differential Diagnosis",       "school": "Chamberlain"},
    "nr-602":    {"label": "NR 602", "full": "Primary Care — Childbearing/Childrearing Family", "school": "Chamberlain"},
    "nr-305":    {"label": "NR 305", "full": "Health Assessment for the Practicing RN", "school": "Chamberlain"},
    "nr-576":    {"label": "NR 576", "full": "Differential Diagnosis Across the Lifespan", "school": "Chamberlain"},
    "nr-601":    {"label": "NR 601", "full": "Primary Care of the Maturing and Aged Family", "school": "Chamberlain"},
    "nr-603":    {"label": "NR 603", "full": "Advanced Clinical Diagnosis and Practice Across the Lifespan", "school": "Chamberlain"},
    "nr-667":    {"label": "NR 667", "full": "FNP Capstone Practicum and Intensive", "school": "Chamberlain"},
    "nurs-6512": {"label": "NURS 6512", "full": "Advanced Health Assessment", "school": "Walden"},
    "nrnp-6531": {"label": "NRNP 6531", "full": "Primary Care of Adults",    "school": "Walden"},
    "nrnp-6541": {"label": "NRNP 6541", "full": "Primary Care — Adolescents & Children", "school": "Walden"},
    "nrnp-6542": {"label": "NRNP 6542", "full": "Advanced Practice — Adults & Older Adults", "school": "Walden"},
    "nrnp-6552": {"label": "NRNP 6552", "full": "Women\\'s Health",            "school": "Walden"},
    "nrnp-6568": {"label": "NRNP 6568", "full": "Psychiatric Mental Health NP", "school": "Walden"},
    "nurs-6531": {"label": "NURS 6531", "full": "Advanced Practice Care of Adults Across the Lifespan", "school": "Walden"},
    "nurs-6560": {"label": "NURS 6560", "full": "Advanced Practice Nursing in Acute Care", "school": "Walden"},
    "nurs-5342": {"label": "NURS 5342", "full": "Advanced Pathophysiology", "school": "Multiple"},
    "nu664c":    {"label": "NU664C", "full": "Advanced Practice Psychiatric-Mental Health Nursing", "school": "Regis College"},
    "nsg-6330":  {"label": "NSG 6330", "full": "Advanced Health Assessment", "school": "South University"},
    "nsg-270":   {"label": "NSG 270", "full": "Complex Health Care Concepts", "school": "Virginia Western CC"},
    "nur-560":   {"label": "NUR 560", "full": "Advanced Health Assessment", "school": "Multiple"},
    "kaplan-ihuman": {"label": "Kaplan iHuman", "full": "Clinical Canvas (multi-institution)", "school": "Kaplan Medical"},
    "shadow-health": {"label": "Shadow Health", "full": "Digital Clinical Experience Platform", "school": "Multiple"},
    "multiple":  {"label": "Multiple", "full": "Multiple Courses / Institutions", "school": "Multiple"},
}'''

# Replace old COURSES dict using exact string match (not regex — nested braces break it)
old_courses = '''COURSES = {
    "nr-509":    {"label": "NR 509", "full": "Advanced Physical Assessment", "school": "Chamberlain"},
    "nr-511":    {"label": "NR 511", "full": "Differential Diagnosis",       "school": "Chamberlain"},
    "nr-602":    {"label": "NR 602", "full": "Primary Care — Childbearing/Childrearing Family", "school": "Chamberlain"},
    "nurs-6512": {"label": "NURS 6512", "full": "Advanced Health Assessment", "school": "Walden"},
    "nrnp-6531": {"label": "NRNP 6531", "full": "Primary Care of Adults",    "school": "Walden"},
    "nrnp-6541": {"label": "NRNP 6541", "full": "Primary Care — Adolescents & Children", "school": "Walden"},
    "nrnp-6542": {"label": "NRNP 6542", "full": "Advanced Practice — Adults & Older Adults", "school": "Walden"},
    "nrnp-6552": {"label": "NRNP 6552", "full": "Women's Health",            "school": "Walden"},
    "nrnp-6568": {"label": "NRNP 6568", "full": "Psychiatric Mental Health NP", "school": "Walden"},
}'''
new_content = new_content.replace(old_courses, new_courses)

# Write the updated file
with open(CASES_PY, "w", encoding="utf-8") as f:
    f.write(new_content)

# Print summary
print(f"\nDone. Generated {len(new_cases)} new cases")
print(f"  Fast-build (high data): {len(fast_build)}")
print(f"  On-request (medium):    {len(on_request_med)}")
print(f"  On-request (low):       {len(on_request_low)}")
print(f"  Total in catalog:       {len(existing_slugs) + len(new_cases)}")
print(f"\nUpdated COURSES dict with 24 entries")
print(f"Written to {CASES_PY}")
