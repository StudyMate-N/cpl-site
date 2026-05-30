// GET /api/ops/session → 200 {authed:true} if the session cookie is valid, else 401.
// Lets the front-end confirm an httpOnly session it can't read on page load.
'use strict';
const ops = require('../_ops');

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Cache-Control', 'no-store');
  if (ops.isAuthed(req)) { res.statusCode = 200; return res.end(JSON.stringify({ authed: true })); }
  res.statusCode = 401;
  return res.end(JSON.stringify({ authed: false }));
};
