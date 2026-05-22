// Email 4 — Day 4 soft introduction of paid case guides.
// Goal: introduce the product without being salesy. Demonstrate fit.

const { shell, button, escapeHtml } = require('./_shell');

function introEmail({ baseUrl, unsubscribeUrl }) {
  const subject = "What's in a CPL case guide (and why students buy)";
  const preheader = "If the cheat sheets are the framework, the case guide is the answer key.";

  const bodyHtml = `
    <div style="margin-bottom:10px; font-size:11px; font-weight:700; color:#0F7A6B; letter-spacing:0.06em; text-transform:uppercase;">
      CLINICAL INSIGHT · DAY 4
    </div>

    <h1 style="margin:0 0 16px; font-family:Georgia, 'Times New Roman', serif; font-size:26px; font-weight:600; color:#0B1F1B; line-height:1.25;">
      The medication answers iHuman expects.
    </h1>

    <p style="margin:0 0 16px; font-size:15px; color:#1F3530; line-height:1.65;">
      You've probably noticed by now that iHuman has very specific expectations for medication answers. Not just the right drug class — the right starting dose, the right dispense quantity, the right refills. Faculty look for all six elements.
    </p>

    <p style="margin:0 0 16px; font-size:15px; color:#1F3530; line-height:1.65; padding:14px 18px; background:#FFF6E8; border-left:3px solid #946115; border-radius:6px;">
      <strong>The most common medication point-loss:</strong> on Stage 2 HTN cases (Harvey Hoya, Felipe Garcia, Herbie Romero, Anselmo Lopez), students prescribe Lisinopril alone. The 2017 ACC/AHA guidelines require <em>two</em> first-line agents for Stage 2 — Lisinopril 10 mg + Hydrochlorothiazide 25 mg. Single-drug therapy loses faculty points every time.
    </p>

    <p style="margin:0 0 16px; font-size:14px; color:#1F3530; line-height:1.65;">
      The other patterns:
    </p>

    <ul style="margin:0 0 24px; padding-left:22px; font-size:14px; color:#1F3530; line-height:1.8;">
      <li><strong>GAS Pharyngitis:</strong> Penicillin V 500 mg BID × <em>10 days full course</em>. Shorter courses lose points even if the drug is right.</li>
      <li><strong>Migraine acute:</strong> Sumatriptan 50 mg, may repeat ×1 after 2h, max 200 mg/day. Hold if pregnant — must be documented.</li>
      <li><strong>Pediatric viral GE:</strong> ORS only. No antiemetics in mild dehydration. Ordering Zofran can flag harmful.</li>
      <li><strong>ADHD inattentive:</strong> Methylphenidate ER 18 mg starting dose. Baseline ECG required before start.</li>
    </ul>

    <p style="margin:0 0 16px; font-size:14px; color:#1F3530; line-height:1.65;">
      All of these are in <strong>Vol IV: Management Plan &amp; SOAP Note</strong> (page 5) — the medication answer key reference card. If you have the cheat sheet you already have it.
    </p>

    <p style="margin:28px 0 16px; font-size:15px; color:#1F3530; line-height:1.65; font-weight:600;">
      And if you want the full case-specific guide…
    </p>

    <p style="margin:0 0 16px; font-size:14px; color:#1F3530; line-height:1.65;">
      The cheat sheets cover universal patterns. For your <em>specific case</em> — every history question with the patient's verbatim response, every PE finding with documentation language, every test with rationale, the platform's preferred DDx names, the complete EHR + SOAP note ready to submit — that's what the CPL case guides are.
    </p>

    <p style="margin:0 0 8px; font-size:14px; color:#1F3530; line-height:1.65;">
      Each one is roughly 40+ pages, built from verified student submissions, delivered same day in Word + PDF.
    </p>

    ${button({ url: `${baseUrl}/cases/`, label: 'Browse the catalog' })}

    <p style="margin:24px 0 0; font-size:13px; color:#5C6E69; line-height:1.6;">
      One more email coming in a few days. After that, we don't message you again unless you ask.
    </p>
  `;

  const html = shell({ preheader, bodyHtml, unsubscribeUrl });
  const text = `The medication answers iHuman expects.

Most common point loss: on Stage 2 HTN cases, students prescribe Lisinopril alone. ACC/AHA 2017 requires two first-line agents — Lisinopril 10 mg + Hydrochlorothiazide 25 mg.

Other patterns:
- GAS Pharyngitis: Penicillin V 500 mg BID × 10 days (full course)
- Migraine acute: Sumatriptan 50 mg, may repeat ×1 after 2h, max 200 mg/day
- Peds viral GE: ORS only. No antiemetics in mild dehydration.
- ADHD inattentive: Methylphenidate ER 18 mg, baseline ECG required

All in Vol IV (page 5).

For your specific case, the CPL case guides walk through every section:
${baseUrl}/cases/

Clinical Performance Lab`;

  return { subject, html, text };
}

module.exports = introEmail;
