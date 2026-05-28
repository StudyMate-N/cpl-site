// Email 1 — Confirmation (sent immediately after subscribe form submission).
// Goal: get them to click the confirm link.

const { shell, button, escapeHtml } = require('./_shell');

const VOLUME_LABELS = {
  'history':       'Vol I — The History Question Framework',
  'physical-exam': 'Vol II — The Universal PE Checklist',
  'ddx':           'Vol III — DDx & Key Findings',
  'plan':          'Vol IV — Management Plan & SOAP Note',
};

function confirmationEmail({ email, volumes, confirmUrl, unsubscribeUrl }) {
  const subject = 'Confirm to get your CPL cheat sheets';
  const preheader = "Click the link inside to get your free cheat sheets — it'll take 2 seconds.";

  const volumesList = (volumes || [])
    .map(v => `<li style="padding:4px 0; color:#1F3530;">${escapeHtml(VOLUME_LABELS[v] || v)}</li>`)
    .join('');

  const bodyHtml = `
    <div style="margin-bottom:10px; font-size:11px; font-weight:700; color:#0F7A6B; letter-spacing:0.06em; text-transform:uppercase;">
      ONE QUICK STEP
    </div>

    <h1 style="margin:0 0 16px; font-family:Georgia, 'Times New Roman', serif; font-size:28px; font-weight:600; color:#0B1F1B; line-height:1.2;">
      Confirm to get your cheat sheets.
    </h1>

    <p style="margin:0 0 16px; font-size:15px; color:#1F3530;">
      Thanks for requesting the CPL Cheat Sheet Library. To make sure you actually meant to subscribe (and that ${escapeHtml(email)} is really yours), please click below to confirm.
    </p>

    ${button({ url: confirmUrl, label: 'Confirm and send my PDFs' })}

    <p style="margin:0 0 8px; font-size:14px; color:#5C6E69;">
      You requested:
    </p>
    <ul style="margin:0 0 24px; padding-left:20px; font-size:14px;">
      ${volumesList}
    </ul>

    <p style="margin:0 0 16px; font-size:13px; color:#5C6E69; line-height:1.6;">
      The link expires in 24 hours. Once you click it, your PDFs arrive immediately — and we'll send a short follow-up over the next week with one clinical insight you can use on any iHuman case.
    </p>

    <p style="margin:0; font-size:13px; color:#5C6E69; line-height:1.6;">
      Didn't sign up? You can safely ignore this email — we'll never message you again.
    </p>
  `;

  const html = shell({ preheader, bodyHtml, unsubscribeUrl });
  const text = `Confirm to get your CPL cheat sheets.\n\nThanks for requesting the CPL Cheat Sheet Library. Click this link to confirm and we'll send your PDFs immediately:\n\n${confirmUrl}\n\nYou requested:\n${(volumes || []).map(v => '- ' + (VOLUME_LABELS[v] || v)).join('\n')}\n\nThe link expires in 24 hours. Didn't sign up? Ignore this email.\n\nClinical Performance Lab\ncpl-site.vercel.app`;

  return { subject, html, text };
}

module.exports = confirmationEmail;
