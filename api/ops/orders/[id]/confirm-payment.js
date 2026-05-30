// POST /api/ops/orders/:id/confirm-payment
//   ready  → mint access (code + magic link), status 'fulfilled', send delivery
//   !ready → status 'building', send building email (deliver step uploads later)
'use strict';
const ops = require('../../../_ops');
const { sendOps } = require('../../../_ops-mail');

function json(res, code, obj) { res.statusCode = code; res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(obj)); }

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  if (ops.requireAuth(req, res)) return;
  if (req.method !== 'POST') return json(res, 405, { error: 'method not allowed' });

  const id = req.query && req.query.id;
  const order = await ops.getOrder(id);
  if (!order) return json(res, 404, { error: 'order not found' });

  order.events.push(ops.ev('paid', 'Payment confirmed', '$' + (order.amount || order.price), ''));

  if (order.ready) {
    await ops.mintAccess(order);
    order.status = 'fulfilled';
    order.events.push(ops.ev('fulfilled', 'Guide unlocked', 'Pre-built · auto-delivered', ''));
    try {
      const sent = await sendOps('delivery', order);
      order.events.push(ops.ev('mail', 'Delivery email sent', '', order.email));
      await ops.saveOrder(order);
      return json(res, 200, { ok: true, order: order, sent: sent });
    } catch (e) {
      await ops.saveOrder(order);
      return json(res, 502, { ok: false, order: order, error: 'fulfilled but delivery email failed: ' + e.message });
    }
  }

  // not pre-built → goes into production; ops uploads via /deliver
  order.status = 'building';
  order.events.push(ops.ev('building', 'In production', 'Custom build', ''));
  try {
    const sent = await sendOps('building', order);
    order.events.push(ops.ev('mail', 'Build-started email sent', '', order.email));
    await ops.saveOrder(order);
    return json(res, 200, { ok: true, order: order, sent: sent });
  } catch (e) {
    await ops.saveOrder(order);
    return json(res, 502, { ok: false, order: order, error: 'building but email failed: ' + e.message });
  }
};
