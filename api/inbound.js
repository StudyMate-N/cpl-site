// POST /api/inbound?key=INBOUND_WEBHOOK_KEY
// Resend "email.received" inbound webhook → instant branded auto-acknowledgement
// for mail sent to orders@ (and support@). All other recipients/events are ignored.
//
// Auth: a shared secret in the URL query (?key=...) matched against
// INBOUND_WEBHOOK_KEY. This is reliable on Vercel (no raw-body needed, unlike
// Svix signature verification, which Vercel's body parsing makes fragile).

const { Resend } = require('resend');
const { REPLY_TO } = require('./_lib');

const FROM_ADDRESS = process.env.CPL_FROM_ADDRESS || 'CPL <hello@clinicalperformancelab.com>';
const WEBHOOK_KEY  = process.env.INBOUND_WEBHOOK_KEY || '';

// Addresses that receive an auto-acknowledgement, with tailored copy.
const ACK_RULES = {
  'orders@clinicalperformancelab.com': {
    subject: 'Got your order request — invoice on the way',
    body:
      "Thanks for your order request — we've received it.\n\n" +
      "You'll get your invoice within about 4 hours (usually much sooner). " +
      "As soon as it's paid, your complete guide and personal access code are delivered the same day, in Word + PDF.\n\n" +
      "First time ordering? Code CPLFIRST15 takes 15% off your first single case.\n\n" +
      "— Clinical Performance Lab",
  },
  'support@clinicalperformancelab.com': {
    subject: "We've got your message",
    body:
      "Thanks for reaching out — we've received your message and will reply within about 4 hours.\n\n" +
      "If this is about a delivered guide, replying with your order details (case name + the email you ordered with) helps us help you faster.\n\n" +
      "— Clinical Performance Lab",
  },
};

// Read the JSON body. Inbound emails can be large (full HTML), so we allow up
// to ~5 MB — far above the small cap used for the public form endpoints.
async function readJsonBody(req) {
  if (req.body && typeof req.body === 'object') return req.body;
  let data = '';
  for await (const chunk of req) {
    data += chunk;
    if (data.length > 5_000_000) throw new Error('Body too large');
  }
  return data ? JSON.parse(data) : {};
}

// Pull a bare lower-cased address out of "Name <addr>", "addr", or an array.
function extractEmail(addr) {
  if (!addr) return '';
  if (Array.isArray(addr)) addr = addr[0];
  if (addr && typeof addr === 'object') addr = addr.address || addr.email || '';
  const m = String(addr).match(/<([^>]+)>/);
  return (m ? m[1] : String(addr)).trim().toLowerCase();
}

// Collect every recipient address we can find in the payload (defensive across
// possible field shapes).
function allRecipients(data) {
  const out = [];
  const push = (v) => { (Array.isArray(v) ? v : [v]).forEach((x) => { const e = extractEmail(x); if (e) out.push(e); }); };
  push(data.to);
  push(data.recipient);
  if (data.envelope) push(data.envelope.to);
  return out;
}

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');

  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }

  // ─── Auth: shared secret in the URL ─────────────────────────────
  const key = (req.query && req.query.key) || '';
  if (!WEBHOOK_KEY || key !== WEBHOOK_KEY) {
    return res.status(401).json({ ok: false, error: 'Unauthorized' });
  }

  let event;
  try {
    event = await readJsonBody(req);
  } catch (e) {
    return res.status(400).json({ ok: false, error: 'Invalid body' });
  }

  // Only act on inbound received emails; 200 everything else so Resend is happy.
  if (!event || event.type !== 'email.received') {
    return res.status(200).json({ ok: true, ignored: event && event.type });
  }

  const data = event.data || {};
  const recipients = allRecipients(data);
  const fromAddr = extractEmail(data.from || (data.envelope && data.envelope.from) || data.sender);
  const origSubject = (data.subject || '').toString().slice(0, 120);

  // Which monitored address was this sent to?
  const matched = recipients.find((r) => ACK_RULES[r]);
  if (!matched) {
    return res.status(200).json({ ok: true, noAck: true });
  }

  // ─── Loop / abuse prevention ────────────────────────────────────
  // Never auto-reply to ourselves, no-reply mailboxes, or auto-generated mail.
  if (!fromAddr ||
      fromAddr.endsWith('@clinicalperformancelab.com') ||
      /(^|[._-])(no-?reply|do-?not-?reply|mailer-daemon|postmaster|bounce)/i.test(fromAddr)) {
    return res.status(200).json({ ok: true, skipped: 'loop-guard' });
  }
  const h = data.headers || {};
  const autoSubmitted = (h['auto-submitted'] || h['Auto-Submitted'] || '').toString().toLowerCase();
  if (autoSubmitted && autoSubmitted !== 'no') {
    return res.status(200).json({ ok: true, skipped: 'auto-submitted' });
  }

  // ─── Send the acknowledgement ───────────────────────────────────
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    console.error('RESEND_API_KEY not configured');
    return res.status(200).json({ ok: true, skipped: 'no-api-key' });
  }

  const rule = ACK_RULES[matched];
  try {
    const resend = new Resend(apiKey);
    await resend.emails.send({
      from: FROM_ADDRESS,
      to: fromAddr,
      replyTo: matched || REPLY_TO,
      subject: origSubject ? `${rule.subject} (re: ${origSubject})` : rule.subject,
      text: rule.body,
      headers: { 'Auto-Submitted': 'auto-replied' },  // prevent reply loops with other auto-responders
    });
  } catch (err) {
    console.error('Inbound ack send failed:', err.message);
    // Return 200 anyway so Resend does not retry the webhook indefinitely.
    return res.status(200).json({ ok: true, ackFailed: true });
  }

  return res.status(200).json({ ok: true, acked: matched });
};
