// POST /api/ops/orders/:id/invoice {url, amount} → status 'invoiced', send invoice.
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
  const url = body && body.url;
  const amount = body && body.amount != null ? Number(body.amount) : order.price;
  if (!url || !/^https?:\/\//i.test(String(url))) return json(res, 400, { error: 'valid invoice url required' });
  if (!(amount > 0)) return json(res, 400, { error: 'valid amount required' });

  order.invoiceUrl = String(url);
  order.amount = amount;
  order.status = 'invoiced';
  order.events.push(ops.ev('invoiced', 'Invoice sent', '$' + amount, ''));

  try {
    const sent = await sendOps('invoice', order);
    order.events.push(ops.ev('mail', 'Invoice email sent', '', order.email));
    await ops.saveOrder(order);
    return json(res, 200, { ok: true, order: order, sent: sent });
  } catch (e) {
    await ops.saveOrder(order); // status already advanced; surface the send error
    return json(res, 502, { ok: false, order: order, error: 'invoice saved but email failed: ' + e.message });
  }
};
