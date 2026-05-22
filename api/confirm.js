// GET /api/confirm?t=TOKEN
// Validates HMAC-signed confirm token, records the subscriber, schedules drip,
// sends the delivery email (with PDF download links).
//
// Returns JSON so the /confirm/ landing page can render the result via fetch.

const { Resend } = require('resend');
const {
  verifyConfirmToken,
  signUnsubscribeToken,
  getSubscriber, setSubscriber,
  isUnsubscribed,
  scheduleDrip,
} = require('./_lib');
const deliveryEmail = require('../emails/delivery');

const FROM_ADDRESS = process.env.CPL_FROM_ADDRESS || 'CPL <onboarding@resend.dev>';
const BASE_URL = process.env.CPL_BASE_URL || 'https://clinicalperformancelab.vercel.app';

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');

  if (req.method !== 'GET') {
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }

  const token = (req.query && req.query.t) || '';
  if (!token) {
    return res.status(400).json({ ok: false, error: 'Missing token' });
  }

  // ─── Verify HMAC token ──────────────────────────────
  let verified;
  try {
    verified = verifyConfirmToken(token);
  } catch (e) {
    console.error('Token verify threw:', e.message);
    return res.status(500).json({ ok: false, error: 'Server configuration error.' });
  }
  if (!verified.ok) {
    return res.status(400).json({ ok: false, error: verified.error || 'Invalid or expired link.' });
  }
  const { email, volumes } = verified;

  // ─── Honor unsubscribe (someone might have unsubbed between subscribe and confirm) ──
  if (await isUnsubscribed(email)) {
    return res.status(200).json({ ok: true, email, volumes, note: 'Already unsubscribed; no further emails.' });
  }

  // ─── Idempotency: if already confirmed, don't re-trigger drip ──
  const existing = await getSubscriber(email);
  if (existing && existing.status === 'confirmed') {
    // Still send the delivery email again (in case they lost the PDFs)
    // but skip the drip schedule.
    await sendDelivery(email, volumes);
    return res.status(200).json({
      ok: true,
      email,
      volumes,
      note: 'Already confirmed — resent delivery email.',
    });
  }

  // ─── Record subscriber ──────────────────────────────
  const now = Date.now();
  const record = {
    email,
    volumes,
    status: 'confirmed',
    createdAt: existing?.createdAt || now,
    confirmedAt: now,
  };
  try {
    await setSubscriber(email, record);
  } catch (e) {
    console.error('Failed to write subscriber:', e.message);
    // Continue — KV failure shouldn't block delivery
  }

  // ─── Schedule drip sequence ─────────────────────────
  try {
    await scheduleDrip(email);
  } catch (e) {
    console.error('Failed to schedule drip:', e.message);
    // Continue — drip failure shouldn't block delivery
  }

  // ─── Send delivery email ────────────────────────────
  const deliverResult = await sendDelivery(email, volumes);
  if (!deliverResult.ok) {
    // Still consider the confirm successful — they're recorded — but warn.
    return res.status(200).json({
      ok: true,
      email,
      volumes,
      warning: 'Confirmed, but delivery email failed to send. Reply to confirmation email and we will resend.',
    });
  }

  return res.status(200).json({ ok: true, email, volumes });
};

async function sendDelivery(email, volumes) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    console.error('RESEND_API_KEY not configured');
    return { ok: false };
  }

  const unsubToken = signUnsubscribeToken(email);
  const unsubscribeUrl = `${BASE_URL}/api/unsubscribe?t=${encodeURIComponent(unsubToken)}`;

  try {
    const resend = new Resend(apiKey);
    const { subject, html, text } = deliveryEmail({
      email, volumes, baseUrl: BASE_URL, unsubscribeUrl,
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
      console.error('Delivery email error:', { code: error.statusCode, name: error.name });
      return { ok: false };
    }
    return { ok: true, messageId: data?.id };
  } catch (err) {
    console.error('Delivery send threw:', err.message);
    return { ok: false };
  }
}
