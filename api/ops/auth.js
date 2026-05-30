// /api/ops/auth — consolidated auth endpoint (function-count budget).
//   GET                      → session check (200 {authed:true} | 401)
//   POST {action:'login', passcode}  → constant-time check, set cookie (rate-limited)
//   POST {action:'logout'}           → clear cookie
'use strict';
const ops = require('../_ops');
const { readJsonBody } = require('../_lib');

function json(res, code, obj) { res.statusCode = code; res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(obj)); }

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Cache-Control', 'no-store');

  // GET → session check
  if (req.method === 'GET') {
    if (ops.isAuthed(req)) return json(res, 200, { authed: true });
    return json(res, 401, { authed: false });
  }

  if (req.method !== 'POST') return json(res, 405, { error: 'method not allowed' });

  let body;
  try { body = await readJsonBody(req); } catch (e) { return json(res, 400, { error: 'bad body' }); }
  const action = body && body.action;

  if (action === 'logout') {
    ops.clearSessionCookie(res);
    return json(res, 200, { ok: true });
  }

  if (action === 'login') {
    const ip = ops.getClientIp(req);
    const rl = await ops.checkRateLimit('ops-login:' + ip, 8, 15 * 60); // 8 / 15min
    if (!rl.allowed) return json(res, 429, { error: 'too many attempts' });
    if (!ops.checkPasscode(body && body.passcode)) return json(res, 401, { ok: false, error: 'invalid passcode' });
    ops.setSessionCookie(res);
    return json(res, 200, { ok: true });
  }

  return json(res, 400, { error: "action must be 'login' or 'logout'" });
};
