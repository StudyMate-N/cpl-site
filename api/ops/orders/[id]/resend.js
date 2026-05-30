// POST /api/ops/orders/:id/resend {which:'invoice'|'delivery'} → re-send that email.
'use strict';
const ops = require('../../../_ops');
const { readJsonBody } = require('../../../_lib');
const { sendOps } = require('../../../_ops-mail');

function json(res, code, obj) { res.statusCode = code; res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(obj)); }

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  if (ops.requireAuth(req, res)) return;
  if (req.method !== 'POST') return json(res, 405, { error: 'method not allowed' });

  const id = req.query && req.query.id;
  const order = await ops.getOrder(id);
  if (!order) return json(res, 404, { error: 'order not found' });

  let body;
  try { body = await readJsonBody(req); } catch (e) { return json(res, 400, { error: 'bad body' }); }
  const which = body && body.which;

  if (which === 'invoice') {
    if (!order.invoiceUrl) return json(res, 400, { error: 'no invoice on this order yet' });
  } else if (which === 'delivery') {
    if (!order.accessUrl) return json(res, 400, { error: 'order not fulfilled yet' });
  } else {
    return json(res, 400, { error: "which must be 'invoice' or 'delivery'" });
  }

  try {
    const sent = await sendOps(which, order);
    order.events.push(ops.ev('mail', (which === 'invoice' ? 'Invoice' : 'Delivery') + ' email re-sent', '', order.email));
    await ops.saveOrder(order);
    return json(res, 200, { ok: true, order: order, sent: sent });
  } catch (e) {
    return json(res, 502, { ok: false, error: 'resend failed: ' + e.message });
  }
};
