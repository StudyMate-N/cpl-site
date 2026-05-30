// GET /api/ops/orders → list orders newest-first (gated). cpl-admin.js load().
'use strict';
const ops = require('../_ops');

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  if (ops.requireAuth(req, res)) return;
  if (req.method !== 'GET') { res.statusCode = 405; return res.end(JSON.stringify({ error: 'method not allowed' })); }
  try {
    const orders = await ops.listOrders(200);
    res.statusCode = 200;
    return res.end(JSON.stringify({ ok: true, orders: orders }));
  } catch (e) {
    res.statusCode = 500;
    return res.end(JSON.stringify({ error: 'failed to list orders' }));
  }
};
