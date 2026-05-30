// POST /api/order  — public order intake from the checkout modal.
//   { case, email, school?, course?, alias?, price? }  → create a real Order
//        (status 'new'), send orderReceived (customer) + adminAlert (ops).
//   { code }                                            → unlock: resolve an
//        access code to its guide link (/g/<token>).
// This is what makes a student order actually show up in /ops/.

const ops = require('./_ops');
const { sendOps } = require('./_ops-mail');
const { readJsonBody, isValidEmail, normalizeEmail, checkRateLimit, getClientIp, getKV } = require('./_lib');

function clip(v, n) { return (v == null ? '' : String(v)).trim().slice(0, n || 120); }

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  if (req.method !== 'POST') return res.status(405).json({ ok: false, error: 'Method not allowed' });

  let body;
  try { body = await readJsonBody(req); } catch (e) { return res.status(400).json({ ok: false, error: 'Invalid request' }); }

  const ip = getClientIp(req);

  // ─── unlock branch: access code → guide link ────────────────────
  if (body && body.code) {
    const rl = await checkRateLimit('unlock:' + ip, 12, 3600);
    if (!rl.allowed) return res.status(429).json({ ok: false, error: 'Too many attempts. Try again later.' });
    const code = clip(body.code, 24).toUpperCase().replace(/\s+/g, '');
    try {
      const kv = getKV();
      const orderId = await kv.get('code:' + code);
      if (!orderId) return res.status(404).json({ ok: false, error: 'That code didn’t match. Check your delivery email.' });
      const order = await ops.getOrder(orderId);
      if (!order || !order.accessUrl) return res.status(404).json({ ok: false, error: 'That code didn’t match. Check your delivery email.' });
      return res.status(200).json({ ok: true, accessUrl: order.accessUrl });
    } catch (e) {
      console.error('unlock failed:', e.message);
      return res.status(500).json({ ok: false, error: 'Could not verify the code. Please try again.' });
    }
  }

  // ─── order branch: create a new order ───────────────────────────
  if (!isValidEmail(body && body.email)) return res.status(400).json({ ok: false, error: 'Please enter a valid email address.' });
  const email = normalizeEmail(body.email);
  const caseTitle = clip(body.case, 160);
  if (!caseTitle) return res.status(400).json({ ok: false, error: 'Please choose a case.' });

  const rl = await checkRateLimit('order:' + ip, 8, 3600);
  if (!rl.allowed) return res.status(429).json({ ok: false, error: 'Too many requests. Please try again later.' });

  try {
    const cat = ops.lookupCase(caseTitle);
    const order = await ops.createOrder({
      email: email,
      case: (cat && (cat.title || cat.case)) || caseTitle,
      cc: (cat && cat.cc) || '',
      price: (cat && cat.price) || Number(body.price) || 150,
      ready: cat ? !!cat.ready : false,
      school: clip(body.school, 80),
      course: clip(body.course, 80),
      alias: clip(body.alias, 80),
    });

    try { await sendOps('orderReceived', order); order.events.push(ops.ev('mail', 'Order confirmation sent', '', order.email)); }
    catch (e) { console.error('orderReceived failed:', e.message); }
    try { await sendOps('adminAlert', order); }
    catch (e) { console.error('adminAlert failed:', e.message); }
    await ops.saveOrder(order);

    return res.status(200).json({ ok: true, orderId: order.id });
  } catch (e) {
    console.error('order intake failed:', e.message);
    return res.status(500).json({ ok: false, error: 'Could not place your order. Please email orders@clinicalperformancelab.com.' });
  }
};
