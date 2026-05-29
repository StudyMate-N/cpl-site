// Email 2 — Delivery (sent immediately after the user clicks the confirm link).
// Goal: get the PDFs in their hands and set up the next email expectation.

const { shell, button, escapeHtml, REPLY_TO } = require('./_shell');

const VOLUMES_META = {
  'history':       { label: 'Vol I · History Framework',     file: 'cpl-vol-1-history.pdf' },
  'physical-exam': { label: 'Vol II · Universal PE',         file: 'cpl-vol-2-physical-exam.pdf' },
  'ddx':           { label: 'Vol III · DDx & Key Findings',  file: 'cpl-vol-3-ddx.pdf' },
  'plan':          { label: 'Vol IV · Plan & SOAP',          file: 'cpl-vol-4-plan.pdf' },
};

function deliveryEmail({ email, volumes, baseUrl, unsubscribeUrl }) {
  const subject = 'Your CPL cheat sheets are here';
  const preheader = 'Your PDFs are attached. Tap any link below to download.';

  const linkRows = (volumes || [])
    .filter(v => VOLUMES_META[v])
    .map(v => {
      const meta = VOLUMES_META[v];
      const url = `${baseUrl}/cheat-sheets/${meta.file}`;
      return `
      <tr>
        <td style="padding:12px 0; border-bottom:1px solid #E4DCC8;">
          <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
            <tr>
              <td style="font-size:14px; font-weight:600; color:#0B1F1B;">
                ${escapeHtml(meta.label)}
              </td>
              <td align="right">
                <a href="${escapeHtml(url)}" style="background:#B7E04E; color:#0B1F1B; padding:8px 18px; border-radius:999px; text-decoration:none; font-size:13px; font-weight:600;">Download &rarr;</a>
              </td>
            </tr>
          </table>
        </td>
      </tr>`;
    })
    .join('');

  const bodyHtml = `
    <div style="margin-bottom:10px; font-size:11px; font-weight:700; color:#0F7A6B; letter-spacing:0.06em; text-transform:uppercase;">
      EMAIL CONFIRMED · PDFs READY
    </div>

    <h1 style="margin:0 0 16px; font-family:Georgia, 'Times New Roman', serif; font-size:28px; font-weight:600; color:#0B1F1B; line-height:1.2;">
      Your cheat sheets are ready.
    </h1>

    <p style="margin:0 0 24px; font-size:15px; color:#1F3530;">
      Tap each one below to download. Save them to your phone for quick reference during a case.
    </p>

    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:16px 0 28px;">
      ${linkRows}
    </table>

    <p style="margin:24px 0 12px; font-size:14px; color:#1F3530; font-weight:600;">
      What's next?
    </p>
    <p style="margin:0 0 16px; font-size:14px; color:#1F3530; line-height:1.7;">
      Over the next week, you'll get three short emails — one clinical insight each (about a day or two apart). Things like "the must-not-miss diagnoses you're forgetting to add to your DDx" and "the medication answers iHuman expects on the most common case templates." After that, we don't email you again unless you ask.
    </p>

    <p style="margin:0 0 16px; font-size:14px; color:#1F3530; line-height:1.7;">
      If you're working on a specific case and want the full answer key — the verbatim questions, the exact PE findings, the platform-verified DDx names — that's what our paid case guides are for.
    </p>

    ${button({ url: `${baseUrl}/cases/`, label: 'Browse the case catalog' })}

    <p style="margin:24px 0 0; font-size:13px; color:#5C6E69; line-height:1.6;">
      Questions? Just reply to this email — it goes straight to <a href="mailto:${REPLY_TO}" style="color:#0F7A6B;">${REPLY_TO}</a>.
    </p>
  `;

  const html = shell({ preheader, bodyHtml, unsubscribeUrl });

  // Plain-text fallback
  const linksText = (volumes || [])
    .filter(v => VOLUMES_META[v])
    .map(v => `- ${VOLUMES_META[v].label}: ${baseUrl}/cheat-sheets/${VOLUMES_META[v].file}`)
    .join('\n');
  const text = `Your CPL cheat sheets are ready.\n\nDownload links:\n${linksText}\n\nOver the next week, you'll get 3 short emails with one clinical insight each. After that, we don't email you again unless you ask.\n\nFor your specific case (verbatim questions, PE findings, platform-verified DDx) — browse our case guides:\n${baseUrl}/cases/\n\nQuestions? Reply to this email.\n\nClinical Performance Lab`;

  return { subject, html, text };
}

module.exports = deliveryEmail;
