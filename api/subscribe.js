// POST /api/subscribe
// Body: { email: string, volumes: string[] }
// Sends a confirmation email with an HMAC-signed link.

const { Resend } = require('resend');
const {
  isValidEmail, normalizeEmail, sanitizeVolumes,
  signConfirmToken, signUnsubscribeToken,
  isUnsubscribed,
  checkRateLimit,
  readJsonBody, getClientIp,
} = require('./_lib');
const confirmationEmail = require('../emails/confirmation');

const FROM_ADDRESS = process.env.CPL_FROM_ADDRESS || 'CPL <onboarding@resend.dev>';
const BASE_URL = process.env.CPL_BASE_URL || 'https://clinicalperformancelab.vercel.app';

module.exports = async function handler(req, res) {
  // CORS — same-origin only (Vercel handles this automatically when API+site are on the same domain)
  res.setHeader('Content-Type', 'application/json');

  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }

  let body;
  try {
    body = await readJsonBody(req);
  } catch (e) {
    return res.status(400).json({ ok: false, error: 'Invalid request' });
  }

  // ─── Validate input ─────────────────────────────────
  const emailRaw = body.email;
  if (!isValidEmail(emailRaw)) {
    return res.status(400).json({ ok: false, error: 'Please enter a valid email address.' });
  }
  const email = normalizeEmail(emailRaw);

  const volumes = sanitizeVolumes(body.volumes);
  if (volumes.length === 0) {
    return res.status(400).json({ ok: false, error: 'Please select at least one cheat sheet.' });
  }

  // ─── Rate limit (per IP) ────────────────────────────
  const ip = getClientIp(req);
  const rl = await checkRateLimit(ip, 5, 3600);
  if (!rl.allowed) {
    return res.status(429).json({ ok: false, error: 'Too many requests. Try again in an hour.' });
  }

  // ─── Honor unsubscribe ──────────────────────────────
  if (await isUnsubscribed(email)) {
    // Don't reveal the unsubscribe status; pretend success.
    return res.status(200).json({ ok: true });
  }

  // ─── Generate confirmation token + URL ──────────────
  let token;
  try {
    token = signConfirmToken({ email, volumes });
  } catch (e) {
    console.error('Token signing failed:', e.message);
    return res.status(500).json({ ok: false, error: 'Server configuration error.' });
  }
  const confirmUrl = `${BASE_URL}/confirm/?t=${encodeURIComponent(token)}`;

  const unsubToken = signUnsubscribeToken(email);
  const unsubscribeUrl = `${BASE_URL}/api/unsubscribe?t=${encodeURIComponent(unsubToken)}`;

  // ─── Send confirmation email ────────────────────────
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    console.error('RESEND_API_KEY not configured');
    return res.status(500).json({ ok: false, error: 'Email service not configured.' });
  }

  try {
    const resend = new Resend(apiKey);
    const { subject, html, text } = confirmationEmail({
      email, volumes, confirmUrl, unsubscribeUrl,
    });

    const { data, error } = await resend.emails.send({
      from: FROM_ADDRESS,
      to: email,
      replyTo: 'Tutorspot98@gmail.com',
      subject,
      html,
      text,
      headers: {
        'List-Unsubscribe': `<${unsubscribeUrl}>`,
        'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
      },
    });

    if (error) {
      console.error('Resend error:', { code: error.statusCode, name: error.name });
      return res.status(500).json({ ok: false, error: 'Could not send confirmation email.' });
    }

    return res.status(200).json({ ok: true, messageId: data?.id });
  } catch (err) {
    console.error('Send failed:', err.message);
    return res.status(500).json({ ok: false, error: 'Could not send confirmation email.' });
  }
};
