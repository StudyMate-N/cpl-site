// POST /api/ops/logout → clear the session cookie.
'use strict';
const ops = require('../_ops');

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  if (req.method !== 'POST') { res.statusCode = 405; return res.end(JSON.stringify({ error: 'method not allowed' })); }
  ops.clearSessionCookie(res);
  res.statusCode = 200;
  return res.end(JSON.stringify({ ok: true }));
};
