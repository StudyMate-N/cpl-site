// GET  /api/ops/orders → list orders newest-first (gated). cpl-admin.js load().
// POST /api/ops/orders → ops-initiated manual order. If an invoice link is
//   supplied it invoices in one step (status 'invoiced' + invoice email) —
//   "place the order and send the payment link in one go". Otherwise it just
//   creates the order (status 'new') and emails the order confirmation.
'use strict';
const ops = require('../_ops');
const { isValidEmail, normalizeEmail } = require('../_lib');
const { sendOps } = require('../_ops-mail');

function clip(v, n) { return (v == null ? '' : String(v)).trim().slice(0, n || 120); }

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  if (ops.requireAuth(req, res)) return;

  if (req.method === 'GET') {
    try {
      const orders = await ops.listOrders(200);
      res.statusCode = 200;
      return res.end(JSON.stringify({ ok: true, orders: orders }));
    } catch (e) {
      res.statusCode = 500;
      return res.end(JSON.stringify({ error: 'failed to list orders' }));
    }
  }

  if (req.method === 'POST') {
    let body;
    // larger reader so an attached guide file (base64) fits in the same request
    try { body = await ops.readLargeJson(req, 8 * 1024 * 1024); } catch (e) { res.statusCode = 413; return res.end(JSON.stringify({ error: 'request too large or invalid (attached file > ~6MB?)' })); }

    if (!isValidEmail(body && body.email)) { res.statusCode = 400; return res.end(JSON.stringify({ error: 'valid customer email required' })); }
    const email = normalizeEmail(body.email);
    const caseTitle = clip(body.case, 160);
    if (!caseTitle) { res.statusCode = 400; return res.end(JSON.stringify({ error: 'case / guide name required' })); }

    const invoiceUrl = clip(body.invoiceUrl, 400);
    if (invoiceUrl && !/^https?:\/\//i.test(invoiceUrl)) { res.statusCode = 400; return res.end(JSON.stringify({ error: 'invoice link must be a valid URL' })); }

    try {
      const cat = ops.lookupCase(caseTitle);
      const price = Number(body.price) || (cat && cat.price) || 150;
      const order = await ops.createOrder({
        email: email,
        case: (cat && (cat.title || cat.case)) || caseTitle,
        cc: clip(body.cc, 120) || (cat && cat.cc) || '',
        price: price,
        amount: Number(body.amount) || price,
        ready: (body.ready != null) ? !!body.ready : (cat ? !!cat.ready : false),
        school: clip(body.school, 80),
        course: clip(body.course, 80),
        alias: clip(body.alias, 80),
      });
      order.events[order.events.length - 1].sub = 'Created by ops (manual)';

      // optionally stage the guide now so it auto-delivers the moment payment clears.
      // fileUrls = uploaded straight to Blob from the browser (large files);
      // files = small base64 inline (legacy / tiny files).
      try {
        let stored = ops.normalizeFileUrls(body.fileUrls);
        if (body.files && Array.isArray(body.files) && body.files.length) {
          stored = stored.concat(await ops.storeFiles(order.id, body.files));
        }
        if (stored.length) {
          order.files = (order.files || []).concat(stored);
          if (!order.accessUrl) await ops.mintAccess(order);
          order.events.push(ops.ev('files', 'Guide file(s) attached', stored.map(function (f) { return f.name; }).join(', '), ''));
        }
      } catch (e) { console.error('manual attach failed:', e.message); }

      const sent = {};
      if (invoiceUrl) {
        // create + invoice in one go
        order.invoiceUrl = invoiceUrl;
        order.amount = Number(body.amount) || order.price;
        order.status = 'invoiced';
        order.events.push(ops.ev('invoiced', 'Invoice sent', '$' + order.amount, ''));
        try { sent.invoice = await sendOps('invoice', order); order.events.push(ops.ev('mail', 'Invoice email sent', '', order.email)); }
        catch (e) { console.error('manual invoice email failed:', e.message); sent.invoiceError = e.message; }
      } else {
        try { sent.received = await sendOps('orderReceived', order); order.events.push(ops.ev('mail', 'Order confirmation sent', '', order.email)); }
        catch (e) { console.error('manual orderReceived failed:', e.message); }
      }
      await ops.saveOrder(order);

      res.statusCode = 200;
      return res.end(JSON.stringify({ ok: true, order: order, sent: sent }));
    } catch (e) {
      console.error('manual order failed:', e.message);
      res.statusCode = 500;
      return res.end(JSON.stringify({ error: 'could not create order: ' + e.message }));
    }
  }

  res.statusCode = 405;
  return res.end(JSON.stringify({ error: 'method not allowed' }));
};
