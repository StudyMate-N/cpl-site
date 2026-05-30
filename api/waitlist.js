// POST /api/waitlist  { email, source }
// Lightweight waitlist capture (e.g. the not-yet-launched simulator). Stores
// the email in KV and sends a single "you're on the list" confirmation.
// Distinct from /api/subscribe (which is the cheat-sheet double-opt-in + drip).

const { Resend } = require('resend');
const {
  isValidEmail, normalizeEmail, checkRateLimit, readJsonBody,
  getClientIp, getKV, SITE_URL, REPLY_TO,
} = require('./_lib');

const FROM_ADDRESS = process.env.CPL_FROM_ADDRESS || 'CPL <hello@clinicalperformancelab.com>';

// Allow-listed waitlists → human label (prevents arbitrary list keys).
const LISTS = { simulator: 'Case Simulator' };

function confirmEmail(label) {
  var C = { ink: '#0B1F1B', teal: '#0F7A6B', lime: '#B7E04E', cream: '#FAF7F0', cream2: '#F4EFE2', border: '#E4DCC8', muted: '#5C6E69' };
  var SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif";
  var SERIF = "Georgia,'Times New Roman',serif";
  var html =
    '<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>' +
    '<body style="margin:0;background:' + C.cream2 + ';font-family:' + SANS + ';">' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:30px 14px;">' +
    '<table role="presentation" width="520" cellpadding="0" cellspacing="0" style="width:520px;max-width:100%;background:' + C.cream + ';border-radius:16px;overflow:hidden;box-shadow:0 8px 30px rgba(11,31,27,.10);">' +
    '<tr><td style="background:' + C.ink + ';padding:20px 28px;"><table role="presentation" cellpadding="0" cellspacing="0"><tr>' +
    '<td><div style="width:32px;height:32px;border-radius:50%;background:' + C.lime + ';color:' + C.ink + ';font-weight:800;font-size:12px;text-align:center;line-height:32px;">CPL</div></td>' +
    '<td style="padding-left:10px;color:' + C.cream + ';font-size:14px;font-weight:600;">Clinical Performance Lab</td></tr></table></td></tr>' +
    '<tr><td style="padding:32px 28px 28px;">' +
    '<span style="display:inline-block;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:' + C.teal + ';background:' + C.cream2 + ';border:1px solid ' + C.border + ';padding:5px 12px;border-radius:999px;margin-bottom:16px;">You’re on the list</span>' +
    '<h1 style="margin:0 0 12px;font-family:' + SERIF + ';font-size:23px;color:' + C.ink + ';">You’re on the ' + label + ' waitlist.</h1>' +
    '<p style="margin:0 0 14px;font-size:15px;line-height:1.6;color:#1F3530;">Thanks for your interest! We’ll email you the moment the free ' + label + ' goes live — you’ll be among the first to try it.</p>' +
    '<p style="margin:0 0 4px;font-size:15px;line-height:1.6;color:#1F3530;">In the meantime, these are free and ready right now:</p>' +
    '<p style="margin:0 0 18px;font-size:15px;line-height:1.8;">' +
    '&bull; <a href="' + SITE_URL + '/free-resources/" style="color:' + C.teal + ';">Free clinical cheat sheets</a><br>' +
    '&bull; <a href="' + SITE_URL + '/sample-guide/" style="color:' + C.teal + ';">A full sample case guide</a></p>' +
    '</td></tr>' +
    '<tr><td style="padding:18px 28px;border-top:1px solid ' + C.border + ';background:' + C.cream2 + ';font-size:11px;color:' + C.muted + ';">' +
    'Clinical Performance Lab · Study aid for exam preparation. You got this email because you joined a waitlist at clinicalperformancelab.com. ' +
    'Not you? You can ignore this — we won’t email again unless the simulator launches.' +
    '</td></tr></table></td></tr></table></body></html>';
  var text = 'You’re on the ' + label + ' waitlist.\n\nWe’ll email you the moment the free ' + label + ' goes live.\n\nIn the meantime (free + ready now):\n- Free cheat sheets: ' + SITE_URL + '/free-resources/\n- Sample guide: ' + SITE_URL + '/sample-guide/\n\n— Clinical Performance Lab';
  return { html: html, text: text };
}

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  if (req.method !== 'POST') return res.status(405).json({ ok: false, error: 'Method not allowed' });

  let body;
  try { body = await readJsonBody(req); } catch (e) { return res.status(400).json({ ok: false, error: 'Invalid request' }); }

  if (!isValidEmail(body.email)) return res.status(400).json({ ok: false, error: 'Please enter a valid email address.' });
  const email = normalizeEmail(body.email);
  const source = LISTS[body.source] ? body.source : 'simulator';
  const label = LISTS[source];

  const ip = getClientIp(req);
  const rl = await checkRateLimit('wl:' + ip, 6, 3600);
  if (!rl.allowed) return res.status(429).json({ ok: false, error: 'Too many requests. Try again later.' });

  // ─── store (dedupe per list) ────────────────────────────────────
  try {
    const kv = getKV();
    const dedupeKey = 'wl:' + source + ':' + email;
    const already = await kv.get(dedupeKey);
    if (already) return res.status(200).json({ ok: true, already: true });
    await kv.set(dedupeKey, Date.now());
    await kv.lpush('waitlist:' + source, email + '|' + Date.now());
  } catch (e) {
    console.error('waitlist store failed:', e.message);
    return res.status(500).json({ ok: false, error: 'Could not save your spot. Please try again.' });
  }

  // ─── confirmation email (best-effort) ───────────────────────────
  const apiKey = process.env.RESEND_API_KEY;
  if (apiKey) {
    try {
      const resend = new Resend(apiKey);
      const mail = confirmEmail(label);
      await resend.emails.send({
        from: FROM_ADDRESS, to: email, replyTo: REPLY_TO,
        subject: 'You’re on the ' + label + ' waitlist',
        html: mail.html, text: mail.text,
      });
    } catch (e) { console.error('waitlist email failed:', e.message); }
  }

  return res.status(200).json({ ok: true });
};
