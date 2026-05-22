// Email 3 — Day 2 clinical insight.
// Goal: prove ongoing value, demonstrate clinical depth, soft-touch.
// Insight: must-not-miss diagnoses students forget.

const { shell, button, escapeHtml } = require('./_shell');

function insightEmail({ baseUrl, unsubscribeUrl }) {
  const subject = "The must-not-miss diagnoses students keep forgetting";
  const preheader = "Even when you correctly identify it as less likely, the platform expects it on the list.";

  const bodyHtml = `
    <div style="margin-bottom:10px; font-size:11px; font-weight:700; color:#0F7A6B; letter-spacing:0.06em; text-transform:uppercase;">
      CLINICAL INSIGHT · DAY 2
    </div>

    <h1 style="margin:0 0 16px; font-family:Georgia, 'Times New Roman', serif; font-size:26px; font-weight:600; color:#0B1F1B; line-height:1.25;">
      The must-not-miss diagnoses students keep forgetting.
    </h1>

    <p style="margin:0 0 16px; font-size:15px; color:#1F3530; line-height:1.65;">
      Here's a scoring pattern that catches people on almost every case:
    </p>

    <p style="margin:0 0 16px; font-size:15px; color:#1F3530; line-height:1.65; padding:14px 18px; background:#FFFCF5; border-left:3px solid #14B896; border-radius:6px;">
      <strong>Every iHuman case has at least one must-not-miss diagnosis.</strong> The platform awards points for including it in your DDx — <em>even when you correctly identify it as less likely than the primary</em>. Forget to include it and you lose points you didn't know were on the table.
    </p>

    <p style="margin:0 0 12px; font-size:14px; color:#1F3530; font-weight:600;">
      The high-frequency must-not-miss by chief complaint:
    </p>

    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:0 0 24px; font-size:13.5px;">
      <tr style="background:#F4EFE2;">
        <td style="padding:10px 14px; font-weight:600; color:#0B1F1B; width:30%;">Chief complaint</td>
        <td style="padding:10px 14px; font-weight:600; color:#0B1F1B;">Must-not-miss</td>
      </tr>
      <tr><td style="padding:8px 14px; border-bottom:1px solid #E4DCC8; color:#1F3530;">Headache</td><td style="padding:8px 14px; border-bottom:1px solid #E4DCC8; color:#5C6E69;">Meningitis, SAH, brain tumor, temporal arteritis (&gt;50), cluster headache</td></tr>
      <tr><td style="padding:8px 14px; border-bottom:1px solid #E4DCC8; color:#1F3530;">Chest pain</td><td style="padding:8px 14px; border-bottom:1px solid #E4DCC8; color:#5C6E69;">MI, PE, aortic dissection, pneumothorax, pericarditis</td></tr>
      <tr><td style="padding:8px 14px; border-bottom:1px solid #E4DCC8; color:#1F3530;">Abdominal pain</td><td style="padding:8px 14px; border-bottom:1px solid #E4DCC8; color:#5C6E69;">Appendicitis, ectopic pregnancy, bowel obstruction, AAA (elderly)</td></tr>
      <tr><td style="padding:8px 14px; border-bottom:1px solid #E4DCC8; color:#1F3530;">Hypertension</td><td style="padding:8px 14px; border-bottom:1px solid #E4DCC8; color:#5C6E69;">Obstructive sleep apnea, secondary HTN, pheochromocytoma</td></tr>
      <tr><td style="padding:8px 14px; border-bottom:1px solid #E4DCC8; color:#1F3530;">Sore throat</td><td style="padding:8px 14px; border-bottom:1px solid #E4DCC8; color:#5C6E69;">GAS pharyngitis, mono, peritonsillar abscess, epiglottitis (peds)</td></tr>
      <tr><td style="padding:8px 14px; color:#1F3530;">Peds vomiting/diarrhea</td><td style="padding:8px 14px; color:#5C6E69;">Severe dehydration, bacterial GE, intussusception, pyloric stenosis</td></tr>
    </table>

    <p style="margin:0 0 16px; font-size:14px; color:#1F3530; line-height:1.65;">
      The rule: when ranking, the must-not-miss goes on the list. It doesn't have to be #1 — but it must be present.
    </p>

    <p style="margin:24px 0 12px; font-size:14px; color:#1F3530; font-weight:600;">
      Want the full must-not-miss reference?
    </p>
    <p style="margin:0 0 16px; font-size:14px; color:#1F3530; line-height:1.65;">
      It's all in <strong>Vol III: DDx &amp; Key Findings</strong>, which you already have. Page 5 has the visual map of must-not-miss by chief complaint — keep that one open while you work the case.
    </p>

    <p style="margin:24px 0 12px; font-size:14px; color:#1F3530; line-height:1.65;">
      Next email in a couple of days: the medication answers iHuman expects on the most common case templates. Including the one drug that's the most-frequent point loss across all HTN cases.
    </p>

    <p style="margin:24px 0 0; font-size:12px; color:#5C6E69; line-height:1.5;">
      Reply to this email if you'd like a specific topic covered.
    </p>
  `;

  const html = shell({ preheader, bodyHtml, unsubscribeUrl });

  const text = `The must-not-miss diagnoses students keep forgetting.

Every iHuman case has at least one must-not-miss diagnosis. The platform awards points for including it in your DDx — even when you correctly identify it as less likely than the primary.

By chief complaint:
- Headache: Meningitis, SAH, brain tumor, temporal arteritis (>50), cluster
- Chest pain: MI, PE, aortic dissection, pneumothorax, pericarditis
- Abdominal pain: Appendicitis, ectopic pregnancy, bowel obstruction, AAA
- HTN: OSA, secondary HTN, pheochromocytoma
- Sore throat: GAS, mono, peritonsillar abscess, epiglottitis (peds)
- Peds GE: severe dehydration, bacterial GE, intussusception, pyloric stenosis

The full map is in Vol III: DDx & Key Findings — page 5.

Next email: the medication answers iHuman expects on the most common case templates.

Clinical Performance Lab
${baseUrl}`;

  return { subject, html, text };
}

module.exports = insightEmail;
