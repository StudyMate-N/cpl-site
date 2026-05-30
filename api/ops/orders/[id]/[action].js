// POST /api/ops/orders/:id/:action  (gated) — consolidates the order lifecycle
// actions into one function (Vercel function-count budget):
//   invoice          {url, amount}  → status 'invoiced', send invoice
//   confirm-payment  —              → ready: mint+fulfilled+delivery; else building
//   deliver          {files[]}      → store files, mint, fulfilled, delivery
//   resend           {which}        → re-send invoice|delivery
'use strict';
const ops = require('../../../_ops');
const { readJsonBody } = require('../../../_lib');
const { sendOps } = require('../../../_ops-mail');

function json(res, code, obj) { res.statusCode = code; res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(obj)); }

async function doInvoice(req, res, order) {
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
    await ops.saveOrder(order);
    return json(res, 502, { ok: false, order: order, error: 'invoice saved but email failed: ' + e.message });
  }
}

async function doConfirmPayment(req, res, order) {
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
}

async function doDeliver(req, res, order) {
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
}

// Stage guide files onto an order (Blob) WITHOUT delivering/emailing. Lets ops
// upload the guide at any point (e.g. before payment) so it's attached when the
// order delivers. Mints the access link/code if not present so it's ready.
async function doAttach(req, res, order) {
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
  if (!order.accessUrl) await ops.mintAccess(order); // link exists; not "delivered" until paid/sent
  order.events.push(ops.ev('files', 'Guide file(s) uploaded', stored.map(function (f) { return f.name; }).join(', '), ''));
  await ops.saveOrder(order);
  return json(res, 200, { ok: true, order: order, stored: stored.map(function (f) { return { name: f.name, size: f.size }; }) });
}

async function doResend(req, res, order) {
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
}

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  if (ops.requireAuth(req, res)) return;
  if (req.method !== 'POST') return json(res, 405, { error: 'method not allowed' });

  const id = req.query && req.query.id;
  const action = req.query && req.query.action;
  const order = await ops.getOrder(id);
  if (!order) return json(res, 404, { error: 'order not found' });

  switch (action) {
    case 'invoice': return doInvoice(req, res, order);
    case 'confirm-payment': return doConfirmPayment(req, res, order);
    case 'deliver': return doDeliver(req, res, order);
    case 'attach': return doAttach(req, res, order);
    case 'resend': return doResend(req, res, order);
    default: return json(res, 404, { error: 'unknown action: ' + action });
  }
};
