// CPL Ops — server library for the fulfillment console.
// Order model (KV) · magic-link mint/verify (HMAC + 30d) · signed session
// cookie (constant-time passcode) · Blob storage · cases.json catalog ·
// Resend (Svix) inbound signature verify.
//
// Security: reuses CPL_TOKEN_SECRET (never rotated) with NAMESPACED derived
// keys so ops sessions / magic links / subscriber tokens can never collide.

'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { getKV, checkRateLimit, getClientIp, SITE_URL } = require('./_lib');

// ─── primitives ───────────────────────────────────────────────────
function getSecret() {
  const s = process.env.CPL_TOKEN_SECRET;
  if (!s || s.length < 32) throw new Error('CPL_TOKEN_SECRET must be set (32+ chars)');
  return s;
}
// Namespaced sub-keys derived from the master secret (HKDF-style separation).
function derive(label) {
  return crypto.createHmac('sha256', getSecret()).update('cpl-ops:' + label).digest();
}
function b64urlEncode(buf) {
  return Buffer.from(buf).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}
function b64urlDecode(str) {
  let s = String(str).replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  return Buffer.from(s, 'base64');
}
function hmac(key, msg) { return crypto.createHmac('sha256', key).update(msg).digest(); }
function timingEqual(a, b) {
  const ba = Buffer.isBuffer(a) ? a : Buffer.from(String(a));
  const bb = Buffer.isBuffer(b) ? b : Buffer.from(String(b));
  if (ba.length !== bb.length) return false;
  return crypto.timingSafeEqual(ba, bb);
}

const DAY = 24 * 60 * 60 * 1000;
const MAGIC_TTL_MS = 30 * DAY;
const SESSION_TTL_MS = 7 * DAY;
const ORDER_TTL_SEC = 400 * 24 * 60 * 60; // keep orders ~13 months

// ─── KV order model ───────────────────────────────────────────────
const SEQ_KEY = 'ops:seq';
const INDEX_KEY = 'ops:index';
const SEQ_START = 1051; // first minted id → CPL-1052 (matches demo seed)

async function nextOrderId() {
  const kv = getKV();
  let n = await kv.get(SEQ_KEY);
  if (n == null) { await kv.set(SEQ_KEY, SEQ_START); }
  const v = await kv.incr(SEQ_KEY);
  return 'CPL-' + v;
}

// event shape mirrors cpl-admin.js ev(): {type, at, label, sub, mail}
function ev(type, label, sub, mail) {
  return { type: type, at: nowMs(), label: label || '', sub: sub || '', mail: mail || '' };
}
// nowMs is injectable-free but Date.now is unavailable inside Workflow scripts only;
// in serverless runtime it's fine.
function nowMs() { return Date.now(); }

function newOrder(fields) {
  const f = fields || {};
  return {
    id: f.id,
    placedAt: f.placedAt || nowMs(),
    email: f.email || '',
    case: f.case || '',
    cc: f.cc || '',
    price: Number(f.price || 0),
    amount: Number(f.amount != null ? f.amount : (f.price || 0)),
    ready: !!f.ready,
    school: f.school || '',
    course: f.course || '',
    alias: f.alias || '',
    status: f.status || 'new',
    invoiceUrl: f.invoiceUrl || '',
    accessCode: f.accessCode || '',
    accessUrl: f.accessUrl || '',
    files: Array.isArray(f.files) ? f.files : [],
    events: Array.isArray(f.events) ? f.events : [],
  };
}

async function getOrder(id) {
  if (!id) return null;
  const kv = getKV();
  const raw = await kv.get('order:' + id);
  if (!raw) return null;
  if (typeof raw === 'string') { try { return JSON.parse(raw); } catch (e) { return null; } }
  return raw;
}

async function saveOrder(order) {
  const kv = getKV();
  await kv.set('order:' + order.id, JSON.stringify(order));
  if (kv.expire) { try { await kv.expire('order:' + order.id, ORDER_TTL_SEC); } catch (e) {} }
  return order;
}

async function createOrder(fields) {
  const id = await nextOrderId();
  const order = newOrder(Object.assign({ id: id }, fields));
  if (!order.events.length) {
    order.events.push(ev('placed', 'Order placed', order.case, ''));
  }
  await saveOrder(order);
  const kv = getKV();
  await kv.lpush(INDEX_KEY, id);
  return order;
}

async function listOrders(limit) {
  const kv = getKV();
  const ids = await kv.lrange(INDEX_KEY, 0, (limit ? limit - 1 : -1));
  const out = [];
  for (const id of ids) {
    const o = await getOrder(id);
    if (o) out.push(o);
  }
  return out; // newest first (lpush prepends)
}

// ─── magic links + access codes ───────────────────────────────────
const CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // no I/O/0/1
function makeAccessCode() {
  const bytes = crypto.randomBytes(4);
  let s = '';
  for (let i = 0; i < 4; i++) s += CODE_ALPHABET[bytes[i] % CODE_ALPHABET.length];
  return 'CPL-' + s;
}

// token = b64url({oid,x}) . b64url(hmac). Stateless verify (sig+exp); KV
// g:<token> mapping is also written for revocation + code resolution.
function signMagicToken(orderId, expMs) {
  const payload = { oid: orderId, x: expMs };
  const pB64 = b64urlEncode(JSON.stringify(payload));
  const sig = hmac(derive('magic-v1'), pB64);
  return pB64 + '.' + b64urlEncode(sig);
}
function verifyMagicToken(token) {
  if (typeof token !== 'string' || token.indexOf('.') < 0) return { ok: false, error: 'malformed' };
  const parts = token.split('.', 2);
  const pB64 = parts[0], sigB64 = parts[1];
  if (!pB64 || !sigB64) return { ok: false, error: 'malformed' };
  const expected = hmac(derive('magic-v1'), pB64);
  if (!timingEqual(expected, b64urlDecode(sigB64))) return { ok: false, error: 'bad signature' };
  let payload;
  try { payload = JSON.parse(b64urlDecode(pB64).toString('utf8')); }
  catch (e) { return { ok: false, error: 'bad payload' }; }
  if (typeof payload.x !== 'number' || payload.x < nowMs()) return { ok: false, error: 'expired' };
  if (!payload.oid) return { ok: false, error: 'no order' };
  return { ok: true, orderId: payload.oid, exp: payload.x };
}

// Mint code + magic link, persist mappings, attach to order.
async function mintAccess(order) {
  const exp = nowMs() + MAGIC_TTL_MS;
  const token = signMagicToken(order.id, exp);
  const code = makeAccessCode();
  const kv = getKV();
  const ttlSec = Math.ceil(MAGIC_TTL_MS / 1000);
  await kv.set('g:' + token, JSON.stringify({ orderId: order.id, exp: exp }));
  if (kv.expire) { try { await kv.expire('g:' + token, ttlSec); } catch (e) {} }
  await kv.set('code:' + code, order.id);
  if (kv.expire) { try { await kv.expire('code:' + code, ttlSec); } catch (e) {} }
  order.accessCode = code;
  order.accessUrl = SITE_URL + '/g/' + token;
  return { code: code, token: token, accessUrl: order.accessUrl, exp: exp };
}

// Resolve /g/:token → order (verify HMAC+exp, confirm not revoked, load order).
async function resolveMagic(token) {
  const v = verifyMagicToken(token);
  if (!v.ok) return { ok: false, error: v.error };
  const kv = getKV();
  const raw = await kv.get('g:' + token);
  if (!raw) return { ok: false, error: 'revoked' }; // deleted/expired in KV
  const order = await getOrder(v.orderId);
  if (!order) return { ok: false, error: 'order missing' };
  return { ok: true, order: order };
}

// ─── session (passcode gate) ──────────────────────────────────────
const SESSION_COOKIE = 'ops_session';

function signSession(expMs) {
  const payload = { x: expMs };
  const pB64 = b64urlEncode(JSON.stringify(payload));
  const sig = hmac(derive('session-v1'), pB64);
  return pB64 + '.' + b64urlEncode(sig);
}
function verifySession(value) {
  if (typeof value !== 'string' || value.indexOf('.') < 0) return false;
  const parts = value.split('.', 2);
  const pB64 = parts[0], sigB64 = parts[1];
  if (!pB64 || !sigB64) return false;
  const expected = hmac(derive('session-v1'), pB64);
  if (!timingEqual(expected, b64urlDecode(sigB64))) return false;
  try {
    const payload = JSON.parse(b64urlDecode(pB64).toString('utf8'));
    return typeof payload.x === 'number' && payload.x > nowMs();
  } catch (e) { return false; }
}

function checkPasscode(input) {
  const expected = process.env.OPS_PASSCODE || '';
  if (!expected) return false;
  // hash both to fixed length so comparison time never leaks length
  const a = crypto.createHash('sha256').update(String(input)).digest();
  const b = crypto.createHash('sha256').update(expected).digest();
  return timingEqual(a, b);
}

function parseCookies(req) {
  const out = {};
  const h = req.headers && req.headers.cookie;
  if (!h) return out;
  String(h).split(';').forEach(function (p) {
    const i = p.indexOf('=');
    if (i < 0) return;
    out[p.slice(0, i).trim()] = decodeURIComponent(p.slice(i + 1).trim());
  });
  return out;
}

function sessionCookie(value, maxAgeSec) {
  const attrs = [
    SESSION_COOKIE + '=' + value,
    'Path=/',
    'HttpOnly',
    'Secure',
    'SameSite=Strict',
    'Max-Age=' + maxAgeSec,
  ];
  return attrs.join('; ');
}
function setSessionCookie(res) {
  const exp = nowMs() + SESSION_TTL_MS;
  res.setHeader('Set-Cookie', sessionCookie(signSession(exp), Math.ceil(SESSION_TTL_MS / 1000)));
}
function clearSessionCookie(res) {
  res.setHeader('Set-Cookie', SESSION_COOKIE + '=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0');
}
function isAuthed(req) {
  const c = parseCookies(req);
  return verifySession(c[SESSION_COOKIE] || '');
}
// Guard for /api/ops/* mutation routes; returns true if it already 401'd.
function requireAuth(req, res) {
  if (isAuthed(req)) return false;
  res.statusCode = 401;
  res.setHeader('Content-Type', 'application/json');
  res.end(JSON.stringify({ error: 'unauthorized' }));
  return true;
}

// ─── Blob file storage ────────────────────────────────────────────
// files: [{ name, type, data(base64) }] → stored, returns [{name,url,size,type}]
async function storeFiles(orderId, files) {
  if (!Array.isArray(files) || !files.length) return [];
  const { put } = require('@vercel/blob');
  const token = process.env.BLOB_READ_WRITE_TOKEN;
  const safeId = String(orderId).replace(/[^A-Za-z0-9_-]/g, '');
  const out = [];
  for (const f of files) {
    if (!f || !f.name || !f.data) continue;
    const buf = Buffer.from(f.data, 'base64');
    const safeName = String(f.name).replace(/[^A-Za-z0-9._-]/g, '_');
    const key = 'guides/' + safeId + '/' + safeName;
    const res = await put(key, buf, {
      access: 'public',
      addRandomSuffix: true,
      contentType: f.type || 'application/octet-stream',
      token: token,
    });
    out.push({ name: safeName, url: res.url, size: buf.length, type: f.type || '' });
  }
  return out;
}

// ─── catalog (cases.json emitted by build.py) ─────────────────────
let _catalog = null;
function loadCatalog() {
  if (_catalog) return _catalog;
  const candidates = [
    path.join(process.cwd(), 'public', 'cases.json'),
    path.join(process.cwd(), 'cases.json'),
    path.join(__dirname, '..', 'public', 'cases.json'),
  ];
  for (const p of candidates) {
    try {
      if (fs.existsSync(p)) {
        const arr = JSON.parse(fs.readFileSync(p, 'utf8'));
        _catalog = Array.isArray(arr) ? arr : (arr.cases || []);
        return _catalog;
      }
    } catch (e) { /* try next */ }
  }
  _catalog = [];
  return _catalog;
}
function normalizeTitle(s) {
  return String(s || '').toLowerCase().replace(/[‒-―−]/g, '-').replace(/[^a-z0-9]+/g, ' ').trim();
}
// Find a catalog entry by case title (from the order subject). Fuzzy on normalized title.
function lookupCase(title) {
  const cat = loadCatalog();
  const want = normalizeTitle(title);
  if (!want) return null;
  let best = null;
  for (const c of cat) {
    const t = normalizeTitle(c.title || c.case || c.name);
    if (!t) continue;
    if (t === want) return c;
    if (!best && (t.indexOf(want) >= 0 || want.indexOf(t) >= 0)) best = c;
  }
  return best;
}

// ─── Resend inbound (Svix) signature verify ───────────────────────
// Headers: svix-id, svix-timestamp, svix-signature ("v1,<b64sig> ...").
// Secret: RESEND_WEBHOOK_SECRET, "whsec_<base64>". Signed content = id.ts.body.
function verifySvix(rawBody, headers) {
  const secret = process.env.RESEND_WEBHOOK_SECRET || '';
  if (!secret) return { ok: false, error: 'no webhook secret configured' };
  const id = headers['svix-id'] || headers['webhook-id'];
  const ts = headers['svix-timestamp'] || headers['webhook-timestamp'];
  const sigHeader = headers['svix-signature'] || headers['webhook-signature'];
  if (!id || !ts || !sigHeader) return { ok: false, error: 'missing svix headers' };
  // reject stale (>5 min skew)
  const tsNum = parseInt(ts, 10);
  if (isNaN(tsNum) || Math.abs(nowMs() / 1000 - tsNum) > 300) return { ok: false, error: 'timestamp skew' };
  const key = Buffer.from(secret.replace(/^whsec_/, ''), 'base64');
  const signedContent = id + '.' + ts + '.' + (Buffer.isBuffer(rawBody) ? rawBody.toString('utf8') : String(rawBody));
  const expected = crypto.createHmac('sha256', key).update(signedContent).digest('base64');
  const passed = String(sigHeader).split(' ').some(function (part) {
    const v = part.split(',');
    const sig = v.length > 1 ? v[1] : v[0];
    try { return timingEqual(Buffer.from(sig, 'base64'), Buffer.from(expected, 'base64')); }
    catch (e) { return false; }
  });
  return passed ? { ok: true } : { ok: false, error: 'signature mismatch' };
}

// ─── body readers ─────────────────────────────────────────────────
// Raw body (for Svix verify) — requires bodyParser:false on the route.
function readRawBody(req, maxBytes) {
  const cap = maxBytes || 1024 * 1024; // 1MB
  return new Promise(function (resolve, reject) {
    if (req.body && (typeof req.body === 'string' || Buffer.isBuffer(req.body))) {
      return resolve(Buffer.isBuffer(req.body) ? req.body : Buffer.from(req.body));
    }
    let chunks = [], len = 0;
    req.on('data', function (c) {
      len += c.length;
      if (len > cap) { req.destroy(); return reject(new Error('body too large')); }
      chunks.push(c);
    });
    req.on('end', function () { resolve(Buffer.concat(chunks)); });
    req.on('error', reject);
  });
}
// Large JSON (file uploads as base64) — own cap, separate from _lib's 10KB reader.
async function readLargeJson(req, maxBytes) {
  if (req.body && typeof req.body === 'object' && !Buffer.isBuffer(req.body)) return req.body;
  const buf = await readRawBody(req, maxBytes || 6 * 1024 * 1024); // 6MB
  if (!buf.length) return {};
  try { return JSON.parse(buf.toString('utf8')); }
  catch (e) { throw new Error('invalid JSON'); }
}

module.exports = {
  // model
  nowMs, ev, newOrder, getOrder, saveOrder, createOrder, listOrders, nextOrderId,
  // magic links
  makeAccessCode, signMagicToken, verifyMagicToken, mintAccess, resolveMagic,
  // session
  SESSION_COOKIE, signSession, verifySession, checkPasscode, parseCookies,
  setSessionCookie, clearSessionCookie, isAuthed, requireAuth,
  // storage
  storeFiles,
  // catalog
  loadCatalog, lookupCase, normalizeTitle,
  // webhook
  verifySvix,
  // body
  readRawBody, readLargeJson,
  // re-exports
  checkRateLimit, getClientIp, SITE_URL,
};
