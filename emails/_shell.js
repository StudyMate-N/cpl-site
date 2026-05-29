// Shared HTML shell for all CPL transactional emails.
// Uses inline styles only (email clients strip <style> tags variably).

function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

// ─── Site / brand constants (single source of truth, env-driven) ──────
const SITE_URL = (process.env.CPL_BASE_URL || 'https://www.clinicalperformancelab.com').replace(/\/+$/, '');
const SITE_DOMAIN = SITE_URL.replace(/^https?:\/\//, '');
const REPLY_TO = process.env.CPL_REPLY_TO || 'hello@clinicalperformancelab.com';

/**
 * Wraps email body content in the CPL-branded shell.
 *
 * @param {object} opts
 * @param {string} opts.preheader - The hidden preview text shown next to subject in inbox.
 * @param {string} opts.bodyHtml - The main email HTML.
 * @param {string} opts.unsubscribeUrl - One-click unsub link (CAN-SPAM compliance).
 * @returns {string} Complete HTML email.
 */
function shell({ preheader, bodyHtml, unsubscribeUrl }) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Clinical Performance Lab</title>
</head>
<body style="margin:0; padding:0; background:#FAF7F0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color:#1F3530; line-height:1.6;">

<!-- Preheader: hidden but shows in inbox preview -->
<div style="display:none; max-height:0; overflow:hidden; mso-hide:all;">
  ${escapeHtml(preheader)}
</div>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FAF7F0;">
  <tr>
    <td align="center" style="padding:32px 16px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:580px; background:#ffffff; border-radius:14px; overflow:hidden; box-shadow:0 4px 14px rgba(11,31,27,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:#0B1F1B; padding:24px 32px; text-align:left;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="padding-right:12px;">
                  <div style="width:36px; height:36px; background:#B7E04E; border-radius:50%; display:inline-block; line-height:36px; text-align:center; font-weight:700; color:#0B1F1B; font-size:13px;">CPL</div>
                </td>
                <td>
                  <div style="color:#FAF7F0; font-weight:600; font-size:15px; letter-spacing:0.02em;">Clinical Performance Lab</div>
                  <div style="color:#C7E96B; font-size:11px; letter-spacing:0.04em;">The Cheat Sheet Library</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:36px 32px;">
            ${bodyHtml}
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#FAF7F0; padding:24px 32px; border-top:1px solid #E4DCC8;">
            <p style="margin:0 0 10px; font-size:12px; color:#5C6E69; line-height:1.5;">
              Clinical Performance Lab · Submission-ready iHuman case guides<br>
              Built from 200+ verified student submissions across NR509, NR511, NR602, NURS 6512, NRNP 6541.
            </p>
            <p style="margin:0; font-size:11px; color:#5C6E69; line-height:1.5;">
              You're receiving this because you requested resources from
              <a href="${SITE_URL}" style="color:#0F7A6B; text-decoration:none;">${SITE_DOMAIN}</a>.<br>
              <a href="${escapeHtml(unsubscribeUrl)}" style="color:#5C6E69; text-decoration:underline;">Unsubscribe</a>
              · Contact: <a href="mailto:${REPLY_TO}" style="color:#5C6E69;">${REPLY_TO}</a>
            </p>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>

</body>
</html>`;
}

/**
 * Helper: render a CTA button in the email body.
 */
function button({ url, label }) {
  return `<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:24px 0;">
    <tr>
      <td style="background:#0B1F1B; border-radius:999px;">
        <a href="${escapeHtml(url)}" style="display:inline-block; padding:14px 32px; color:#B7E04E; font-weight:600; text-decoration:none; font-size:15px;">${escapeHtml(label)} &rarr;</a>
      </td>
    </tr>
  </table>`;
}

module.exports = { shell, button, escapeHtml, SITE_URL, SITE_DOMAIN, REPLY_TO };
