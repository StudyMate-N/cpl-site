// POST /api/ops/login {passcode} → constant-time check vs OPS_PASSCODE,
// set signed httpOnly session cookie. Rate-limited per IP.
'use strict';
const ops = require('../_ops');
const { readJsonBody } = require('../_lib');

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  if (req.method !== 'POST') { res.statusCode = 405; return res.end(JSON.stringify({ error: 'method not allowed' })); }

  const ip = ops.getClientIp(req);
  const rl = await ops.checkRateLimit('ops-login:' + ip, 8, 15 * 60); // 8 / 15min
  if (!rl.allowed) { res.statusCode = 429; return res.end(JSON.stringify({ error: 'too many attempts' })); }

  let body;
  try { body = await readJsonBody(req); } catch (e) { res.statusCode = 400; return res.end(JSON.stringify({ error: 'bad body' })); }

  if (!ops.checkPasscode(body && body.passcode)) {
    res.statusCode = 401;
    return res.end(JSON.stringify({ ok: false, error: 'invalid passcode' }));
  }
  ops.setSessionCookie(res);
  res.statusCode = 200;
  return res.end(JSON.stringify({ ok: true }));
};
