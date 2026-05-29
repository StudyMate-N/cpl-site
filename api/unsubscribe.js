// GET /api/unsubscribe?t=TOKEN  (link in every email)
// POST /api/unsubscribe?t=TOKEN  (List-Unsubscribe-Post one-click compliance)
//
// Validates token, marks email unsubscribed, returns a plain HTML confirmation page.

const {
  verifyUnsubscribeToken, markUnsubscribed,
  SITE_URL, SITE_DOMAIN, REPLY_TO,
} = require('./_lib');

module.exports = async function handler(req, res) {
  const token = (req.query && req.query.t) || '';

  if (!token) {
    return sendHtml(res, 400, htmlPage(
      "Missing token",
      "This unsubscribe link is incomplete. Reply to any of our emails with 'unsubscribe' and we'll handle it manually."
    ));
  }

  let verified;
  try {
    verified = verifyUnsubscribeToken(token);
  } catch (e) {
    console.error('Unsub verify threw:', e.message);
    return sendHtml(res, 500, htmlPage("Server error", `Something went wrong. Try again or email ${REPLY_TO}.`));
  }

  if (!verified.ok) {
    return sendHtml(res, 400, htmlPage(
      "Invalid link",
      "This unsubscribe link is invalid. Reply to any of our emails with 'unsubscribe' and we'll handle it manually."
    ));
  }

  try {
    await markUnsubscribed(verified.email);
  } catch (e) {
    console.error('markUnsubscribed failed:', e.message);
    return sendHtml(res, 500, htmlPage("Server error", `Try again in a minute or email ${REPLY_TO}.`));
  }

  return sendHtml(res, 200, htmlPage(
    "You're unsubscribed.",
    `We won't email ${escapeHtml(verified.email)} again. If you change your mind, you can resubscribe any time at <a href="${SITE_URL}/free-resources/" style="color:#0F7A6B;">${SITE_DOMAIN}/free-resources/</a>.`
  ));
};

function escapeHtml(s) {
  if (s == null) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
}

function sendHtml(res, status, html) {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.statusCode = status;
  res.end(html);
}

function htmlPage(title, body) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${escapeHtml(title)} · CPL</title>
<style>
  body { margin:0; padding:0; background:#FAF7F0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; color:#1F3530; line-height:1.6; }
  .wrap { max-width:560px; margin:0 auto; padding:80px 24px; text-align:center; }
  h1 { font-family:Georgia,'Times New Roman',serif; font-weight:600; font-size:2rem; color:#0B1F1B; margin:0 0 16px; }
  p { font-size:1rem; color:#5C6E69; margin:0 0 16px; }
  .brand { display:inline-flex; align-items:center; gap:10px; margin-bottom:32px; }
  .logo { width:32px; height:32px; border-radius:50%; background:#B7E04E; display:inline-flex; align-items:center; justify-content:center; font-weight:700; font-size:0.8rem; color:#0B1F1B; }
  .home { display:inline-block; margin-top:24px; padding:12px 24px; background:#0B1F1B; color:#B7E04E; text-decoration:none; border-radius:999px; font-weight:600; font-size:0.95rem; }
  .home:hover { background:#064E45; }
</style>
</head>
<body>
<div class="wrap">
  <div class="brand">
    <span class="logo">CPL</span>
    <span style="font-weight:600; color:#0B1F1B;">Clinical Performance Lab</span>
  </div>
  <h1>${escapeHtml(title)}</h1>
  <p>${body}</p>
  <a class="home" href="${SITE_URL}">Back to ${SITE_DOMAIN} →</a>
</div>
</body>
</html>`;
}
