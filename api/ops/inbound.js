// POST /api/ops/inbound — Resend "email.received" webhook (PUBLIC, but the
// payload signature is verified). Supersedes /api/inbound:
//   • orders@ with subject "CPL Order - <case>" → create Order, send
//     orderReceived (customer) + adminAlert (ORDER_EMAIL).
//   • orders@/support@ otherwise → branded auto-acknowledgement (unchanged copy).
//
// Auth: if RESEND_WEBHOOK_SECRET is set, a valid Svix signature is REQUIRED
// (unsigned/forged → 401). Body parsing is disabled so we can verify the raw
// bytes. A ?key= shared-secret fallback is honored only when no Svix secret is
// configured (local/manual testing).
'use strict';

const { Resend } = require('resend');
const { REPLY_TO } = require('../_lib');
const ops = require('../_ops');
const { sendOps, ORDER_EMAIL } = require('../_ops-mail');

module.exports.config = { api: { bodyParser: false } };

const FROM_ADDRESS = process.env.CPL_FROM_ADDRESS || 'CPL <hello@clinicalperformancelab.com>';
const SUPPORT_EMAIL = process.env.CPL_SUPPORT_EMAIL || 'support@clinicalperformancelab.com';

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

function extractEmail(addr) {
  if (!addr) return '';
  if (Array.isArray(addr)) addr = addr[0];
  if (addr && typeof addr === 'object') addr = addr.address || addr.email || '';
  const m = String(addr).match(/<([^>]+)>/);
  return (m ? m[1] : String(addr)).trim().toLowerCase();
}
function allRecipients(data) {
  const out = [];
  const push = (v) => { (Array.isArray(v) ? v : [v]).forEach((x) => { const e = extractEmail(x); if (e) out.push(e); }); };
  push(data.to); push(data.recipient);
  if (data.envelope) push(data.envelope.to);
  return out;
}
function parseOrderSubject(subject) {
  const m = String(subject || '').match(/^\s*CPL\s+Order\s*[-–—:]\s*(.+?)\s*$/i);
  return m ? m[1].trim() : null;
}

function json(res, code, obj) { res.statusCode = code; res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(obj)); }

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') return json(res, 405, { error: 'method not allowed' });

  // ─── read raw body (bodyParser disabled) ────────────────────────
  let raw;
  try { raw = await ops.readRawBody(req, 5 * 1024 * 1024); }
  catch (e) { return json(res, 400, { error: 'body too large' }); }

  // ─── auth: Svix signature (required if secret configured) ───────
  if (process.env.RESEND_WEBHOOK_SECRET) {
    const v = ops.verifySvix(raw, req.headers);
    if (!v.ok) return json(res, 401, { error: 'invalid signature', detail: v.error });
  } else {
    const key = (req.query && req.query.key) || '';
    if (!process.env.INBOUND_WEBHOOK_KEY || key !== process.env.INBOUND_WEBHOOK_KEY) {
      return json(res, 401, { error: 'unauthorized' });
    }
  }

  let event;
  try { event = JSON.parse(raw.toString('utf8') || '{}'); }
  catch (e) { return json(res, 400, { error: 'invalid json' }); }

  if (!event || event.type !== 'email.received') return json(res, 200, { ok: true, ignored: event && event.type });

  const data = event.data || {};
  const recipients = allRecipients(data);
  const fromAddr = extractEmail(data.from || (data.envelope && data.envelope.from) || data.sender);
  const subject = (data.subject || '').toString();

  // ─── loop / abuse guards ────────────────────────────────────────
  if (!fromAddr ||
      fromAddr.endsWith('@clinicalperformancelab.com') ||
      /(^|[._-])(no-?reply|do-?not-?reply|mailer-daemon|postmaster|bounce)/i.test(fromAddr)) {
    return json(res, 200, { ok: true, skipped: 'loop-guard' });
  }
  const h = data.headers || {};
  const autoSubmitted = (h['auto-submitted'] || h['Auto-Submitted'] || '').toString().toLowerCase();
  if (autoSubmitted && autoSubmitted !== 'no') return json(res, 200, { ok: true, skipped: 'auto-submitted' });

  // ─── order intake: orders@ + "CPL Order - <case>" ───────────────
  const toOrders = recipients.includes(ORDER_EMAIL.toLowerCase());
  const caseTitle = parseOrderSubject(subject);

  if (toOrders && caseTitle) {
    try {
      const cat = ops.lookupCase(caseTitle);
      const order = await ops.createOrder({
        email: fromAddr,
        case: (cat && (cat.title || cat.case)) || caseTitle,
        cc: (cat && cat.cc) || '',
        price: (cat && cat.price) || 150,
        ready: cat ? !!cat.ready : false,
        school: (cat && cat.school) || '',
        course: (cat && cat.course) || '',
        alias: (cat && cat.alias) || '',
      });

      const sent = {};
      try { sent.customer = await sendOps('orderReceived', order); order.events.push(ops.ev('mail', 'Order confirmation sent', '', order.email)); }
      catch (e) { console.error('orderReceived send failed:', e.message); }
      try { sent.admin = await sendOps('adminAlert', order); }
      catch (e) { console.error('adminAlert send failed:', e.message); }
      await ops.saveOrder(order);

      return json(res, 200, { ok: true, created: order.id, ready: order.ready, sent: sent });
    } catch (e) {
      console.error('order intake failed:', e.message);
      return json(res, 200, { ok: true, intakeError: e.message }); // 200 so Resend stops retrying
    }
  }

  // ─── otherwise: branded auto-ack (orders@ no-subject / support@) ─
  const matched = recipients.find((r) => ACK_RULES[r]);
  if (!matched) return json(res, 200, { ok: true, noAck: true });

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) return json(res, 200, { ok: true, skipped: 'no-api-key' });
  const rule = ACK_RULES[matched];
  const origSubject = subject.slice(0, 120);
  try {
    const resend = new Resend(apiKey);
    const r = await resend.emails.send({
      from: FROM_ADDRESS,
      to: fromAddr,
      replyTo: matched || REPLY_TO,
      subject: origSubject ? `${rule.subject} (re: ${origSubject})` : rule.subject,
      text: rule.body,
      headers: { 'Auto-Submitted': 'auto-replied' },
    });
    return json(res, 200, { ok: true, acked: matched, id: r && r.data ? r.data.id : null });
  } catch (err) {
    console.error('Inbound ack send failed:', err.message);
    return json(res, 200, { ok: true, ackFailed: true });
  }
};
