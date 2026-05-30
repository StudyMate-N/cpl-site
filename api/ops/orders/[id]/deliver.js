// POST /api/ops/orders/:id/deliver  { files:[{name,type,data(base64)}] }
// Store guide files to Blob, mint access (code + magic link), status 'fulfilled',
// send delivery email. Only meaningful while status 'building' (custom builds).
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

  let body;
  try { body = await ops.readLargeJson(req, 8 * 1024 * 1024); }
  catch (e) { return json(res, 413, { error: 'upload too large or invalid (max ~6MB total)' }); }

  const files = (body && body.files) || [];
  if (!Array.isArray(files) || !files.length) return json(res, 400, { error: 'no files provided' });

  let stored;
  try { stored = await ops.storeFiles(order.id, files); }
  catch (e) { console.error('blob store failed:', e.message); return json(res, 502, { error: 'file storage failed: ' + e.message }); }
  if (!stored.length) return json(res, 400, { error: 'no valid files stored' });

  order.files = (order.files || []).concat(stored);
  if (!order.accessUrl) await ops.mintAccess(order);
  order.status = 'fulfilled';
  order.events.push(ops.ev('fulfilled', 'Guide delivered', stored.map(function (f) { return f.name; }).join(', '), ''));

  try {
    const sent = await sendOps('delivery', order);
    order.events.push(ops.ev('mail', 'Delivery email sent', '', order.email));
    await ops.saveOrder(order);
    return json(res, 200, { ok: true, order: order, sent: sent, stored: stored.map(function (f) { return { name: f.name, size: f.size }; }) });
  } catch (e) {
    await ops.saveOrder(order);
    return json(res, 502, { ok: false, order: order, error: 'delivered but email failed: ' + e.message });
  }
};
