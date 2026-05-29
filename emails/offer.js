// Email 5 — Day 7 discount offer. Last email in the sequence.
// Goal: convert with a modest, time-bounded incentive.

const { shell, button, escapeHtml, REPLY_TO } = require('./_shell');

function offerEmail({ baseUrl, unsubscribeUrl }) {
  const subject = "15% off your first CPL case guide (one-time code)";
  const preheader = "CPLFIRST15 — saves $22.50 on a single case guide.";

  const bodyHtml = `
    <div style="margin-bottom:10px; font-size:11px; font-weight:700; color:#0F7A6B; letter-spacing:0.06em; text-transform:uppercase;">
      ONE-TIME OFFER
    </div>

    <h1 style="margin:0 0 16px; font-family:Georgia, 'Times New Roman', serif; font-size:28px; font-weight:600; color:#0B1F1B; line-height:1.2;">
      15% off your first case guide.
    </h1>

    <p style="margin:0 0 20px; font-size:15px; color:#1F3530; line-height:1.65;">
      This is the last email in the sequence — and we wanted to make it worth opening. If you're working on a case right now (or one is coming up), here's a one-time code that knocks 15% off a single case guide:
    </p>

    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:24px 0;">
      <tr>
        <td style="background:#0B1F1B; border-radius:14px; padding:32px; text-align:center;">
          <div style="font-size:11px; color:#C7E96B; letter-spacing:0.08em; font-weight:700; margin-bottom:10px;">USE CODE</div>
          <div style="font-family:Georgia, 'Times New Roman', serif; font-size:38px; color:#B7E04E; font-weight:600; letter-spacing:0.02em; margin-bottom:10px;">CPLFIRST15</div>
          <div style="font-size:13px; color:rgba(250,247,240,0.78);">15% off your first single case · Saves $22.50</div>
        </td>
      </tr>
    </table>

    <p style="margin:0 0 16px; font-size:14px; color:#1F3530; line-height:1.65;">
      <strong>How to use it:</strong> Browse the catalog, find your case, and mention the code when you order via email or WhatsApp. We'll apply the discount before sending the invoice.
    </p>

    ${button({ url: `${baseUrl}/cases/`, label: 'Browse the case catalog' })}

    <p style="margin:28px 0 14px; font-size:14px; color:#1F3530; line-height:1.65; font-weight:600;">
      What you get for $127.50 (single case, after discount):
    </p>

    <ul style="margin:0 0 20px; padding-left:22px; font-size:14px; color:#1F3530; line-height:1.8;">
      <li>Verbatim history question bank with patient responses</li>
      <li>Complete physical exam checklist with documentation language</li>
      <li>Ranked differential diagnoses with platform-verified names</li>
      <li>Full EHR documentation (Subjective + Objective)</li>
      <li>Tests Ordered list with rationale</li>
      <li>Complete management plan in 6-part structure</li>
      <li>SOAP note ready to submit</li>
      <li>APA-formatted scholarly references</li>
      <li>Word + PDF, delivered same day to your inbox</li>
    </ul>

    <p style="margin:0 0 16px; font-size:14px; color:#1F3530; line-height:1.65;">
      Or if you've got a full term ahead of you, the 3-case bundle ($390, save $60) and 5-case bundle ($540, save $210) are already discounted — the code applies only to single cases.
    </p>

    <p style="margin:24px 0 0; font-size:13px; color:#5C6E69; line-height:1.6;">
      This is the last automated email you'll get from us. If you ever want resources for a new case or have a question, just reply — <a href="mailto:${REPLY_TO}" style="color:#0F7A6B;">${REPLY_TO}</a>.
    </p>

    <p style="margin:8px 0 0; font-size:13px; color:#5C6E69; line-height:1.6;">
      Good luck with your cases.<br>
      — The CPL team
    </p>
  `;

  const html = shell({ preheader, bodyHtml, unsubscribeUrl });
  const text = `15% off your first CPL case guide.

Use code: CPLFIRST15
(Saves $22.50 on a single case)

Mention the code when you order via email or WhatsApp. We'll apply the discount before sending the invoice.

Browse the catalog: ${baseUrl}/cases/

What you get for $127.50:
- Verbatim history with patient responses
- Complete PE checklist with documentation language
- Ranked differentials with platform-verified names
- Full EHR + SOAP note ready to submit
- Management plan in 6-part structure
- APA-formatted references
- Word + PDF, delivered same day

Bundle pricing (3-case $390, 5-case $540) is already discounted — code applies to single cases only.

This is the last automated email. Reply any time — ${REPLY_TO}.

Good luck with your cases.
— The CPL team`;

  return { subject, html, text };
}

module.exports = offerEmail;
