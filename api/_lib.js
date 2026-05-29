// Shared utilities used by all API endpoints.
// HMAC token signing, KV helpers, validation, rate limiting.

const crypto = require('crypto');

const VALID_VOLUMES = ['history', 'physical-exam', 'ddx', 'plan'];
const TOKEN_TTL_HOURS = 24;
const SUBSCRIBER_TTL_DAYS = 90;  // keep records for 90 days after last activity

// ─── Site / brand constants (single source of truth) ──────────────
// All endpoints + email templates derive links and contact addresses
// from these env-driven values so the brand can change in one place.
const SITE_URL = (process.env.CPL_BASE_URL || 'https://www.clinicalperformancelab.com').replace(/\/+$/, '');
const SITE_DOMAIN = SITE_URL.replace(/^https?:\/\//, '');
const REPLY_TO = process.env.CPL_REPLY_TO || 'hello@clinicalperformancelab.com';

// ─── Email validation ─────────────────────────────────────────────
const EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

function isValidEmail(email) {
  if (typeof email !== 'string') return false;
  email = email.trim();
  // RFC 5321 length limit
  if (email.length < 3 || email.length > 254) return false;
  return EMAIL_REGEX.test(email);
}

function normalizeEmail(email) {
  return String(email).trim().toLowerCase();
}

// ─── Volume validation ────────────────────────────────────────────
function sanitizeVolumes(volumes) {
  if (!Array.isArray(volumes)) return [];
  return volumes
    .filter(v => typeof v === 'string')
    .filter(v => VALID_VOLUMES.includes(v));
}

// ─── HMAC token signing ───────────────────────────────────────────
// Token format: base64url(payload).base64url(signature)
// Payload: JSON { email, volumes, exp, nonce }
// This way we don't need a DB lookup just to validate confirm links.

function getSecret() {
  const secret = process.env.CPL_TOKEN_SECRET;
  if (!secret || secret.length < 32) {
    throw new Error('CPL_TOKEN_SECRET environment variable must be set (32+ chars)');
  }
  return secret;
}

function b64urlEncode(buf) {
  return Buffer.from(buf).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

function b64urlDecode(str) {
  let s = String(str).replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  return Buffer.from(s, 'base64');
}

function signConfirmToken({ email, volumes }) {
  const payload = {
    e: email,
    v: volumes,
    x: Date.now() + (TOKEN_TTL_HOURS * 60 * 60 * 1000),
    n: crypto.randomBytes(8).toString('hex'),
  };
  const payloadStr = JSON.stringify(payload);
  const payloadB64 = b64urlEncode(payloadStr);
  const sig = crypto.createHmac('sha256', getSecret())
    .update(payloadB64)
    .digest();
  return payloadB64 + '.' + b64urlEncode(sig);
}

function verifyConfirmToken(token) {
  if (typeof token !== 'string' || !token.includes('.')) {
    return { ok: false, error: 'Malformed token' };
  }
  const [payloadB64, sigB64] = token.split('.', 2);
  if (!payloadB64 || !sigB64) {
    return { ok: false, error: 'Malformed token' };
  }
  const expectedSig = crypto.createHmac('sha256', getSecret())
    .update(payloadB64)
    .digest();
  const actualSig = b64urlDecode(sigB64);
  // Constant-time comparison
  if (expectedSig.length !== actualSig.length ||
      !crypto.timingSafeEqual(expectedSig, actualSig)) {
    return { ok: false, error: 'Invalid signature' };
  }
  let payload;
  try {
    payload = JSON.parse(b64urlDecode(payloadB64).toString('utf8'));
  } catch (e) {
    return { ok: false, error: 'Invalid payload' };
  }
  if (typeof payload.x !== 'number' || payload.x < Date.now()) {
    return { ok: false, error: 'Token expired' };
  }
  if (!isValidEmail(payload.e)) {
    return { ok: false, error: 'Invalid email in token' };
  }
  const volumes = sanitizeVolumes(payload.v);
  if (volumes.length === 0) {
    return { ok: false, error: 'No valid volumes in token' };
  }
  return { ok: true, email: normalizeEmail(payload.e), volumes };
}

// Unsubscribe tokens — long-lived, signed
function signUnsubscribeToken(email) {
  const payloadStr = JSON.stringify({ e: email, t: 'unsub' });
  const payloadB64 = b64urlEncode(payloadStr);
  const sig = crypto.createHmac('sha256', getSecret())
    .update(payloadB64)
    .digest();
  return payloadB64 + '.' + b64urlEncode(sig);
}

function verifyUnsubscribeToken(token) {
  if (typeof token !== 'string' || !token.includes('.')) {
    return { ok: false };
  }
  const [payloadB64, sigB64] = token.split('.', 2);
  if (!payloadB64 || !sigB64) return { ok: false };
  const expectedSig = crypto.createHmac('sha256', getSecret())
    .update(payloadB64)
    .digest();
  const actualSig = b64urlDecode(sigB64);
  if (expectedSig.length !== actualSig.length ||
      !crypto.timingSafeEqual(expectedSig, actualSig)) {
    return { ok: false };
  }
  try {
    const payload = JSON.parse(b64urlDecode(payloadB64).toString('utf8'));
    if (payload.t !== 'unsub') return { ok: false };
    if (!isValidEmail(payload.e)) return { ok: false };
    return { ok: true, email: normalizeEmail(payload.e) };
  } catch (e) {
    return { ok: false };
  }
}

// ─── KV helper (Upstash Redis) ────────────────────────────────────
let _kv = null;
function getKV() {
  if (_kv) return _kv;
  const url = process.env.UPSTASH_REDIS_REST_URL || process.env.KV_REST_API_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN || process.env.KV_REST_API_TOKEN;
  if (url && token) {
    const { Redis } = require('@upstash/redis');
    _kv = new Redis({ url, token });
    return _kv;
  }
  // In-memory fallback for local dev without Redis configured
  console.warn('Redis unavailable, using in-memory fallback (DEV ONLY)');
  const store = new Map();
  _kv = {
    get: async (k) => store.has(k) ? store.get(k) : null,
    set: async (k, v, opts) => store.set(k, v),
    del: async (k) => store.delete(k),
    incr: async (k) => { const v = (store.get(k) || 0) + 1; store.set(k, v); return v; },
    expire: async (k, s) => {},
    lpush: async (k, ...vals) => {
      const arr = store.get(k) || [];
      arr.unshift(...vals);
      store.set(k, arr);
      return arr.length;
    },
    lrange: async (k, start, stop) => {
      const arr = store.get(k) || [];
      if (stop === -1) return arr.slice(start);
      return arr.slice(start, stop + 1);
    },
    lrem: async (k, count, val) => {
      const arr = store.get(k) || [];
      const idx = arr.indexOf(val);
      if (idx >= 0) arr.splice(idx, 1);
      store.set(k, arr);
      return idx >= 0 ? 1 : 0;
    },
  };
  return _kv;
}

// ─── Subscriber records ───────────────────────────────────────────
// Keys:
//   sub:{email}            → { email, volumes, status, createdAt, confirmedAt }
//   drip:scheduled         → list of "{email}|{stepId}|{dueAt}" entries (sorted by dueAt)
//   unsub:{email}          → "1" if unsubscribed
//   rl:ip:{ip}             → integer count for rate limiting

async function getSubscriber(email) {
  const kv = getKV();
  const raw = await kv.get(`sub:${email}`);
  if (!raw) return null;
  if (typeof raw === 'string') {
    try { return JSON.parse(raw); } catch { return null; }
  }
  return raw;
}

async function setSubscriber(email, record) {
  const kv = getKV();
  await kv.set(`sub:${email}`, JSON.stringify(record));
  await kv.expire(`sub:${email}`, SUBSCRIBER_TTL_DAYS * 24 * 60 * 60);
}

async function isUnsubscribed(email) {
  const kv = getKV();
  const v = await kv.get(`unsub:${email}`);
  return !!v;
}

async function markUnsubscribed(email) {
  const kv = getKV();
  await kv.set(`unsub:${email}`, '1');
}

// ─── Drip queue ────────────────────────────────────────────────────
// Each entry is the string "{email}|{stepId}|{dueAtMs}"
// We use a simple list and filter by dueAt in the cron job.
// (For higher scale we'd use a sorted set, but lists keep this simple.)

const DRIP_STEPS = [
  { id: 'insight', delayHours: 48,  emailModule: 'insight' },   // Day 2
  { id: 'intro',   delayHours: 96,  emailModule: 'intro' },     // Day 4
  { id: 'offer',   delayHours: 168, emailModule: 'offer' },     // Day 7
];

async function scheduleDrip(email) {
  const kv = getKV();
  const now = Date.now();
  for (const step of DRIP_STEPS) {
    const dueAt = now + (step.delayHours * 60 * 60 * 1000);
    const entry = `${email}|${step.id}|${dueAt}`;
    await kv.lpush('drip:scheduled', entry);
  }
}

async function getDueDripJobs(maxBatch = 50) {
  const kv = getKV();
  const all = await kv.lrange('drip:scheduled', 0, -1);
  const now = Date.now();
  const due = [];
  for (const entry of all) {
    const parts = entry.split('|');
    if (parts.length !== 3) continue;
    const [email, stepId, dueAtStr] = parts;
    const dueAt = parseInt(dueAtStr, 10);
    if (!isNaN(dueAt) && dueAt <= now) {
      due.push({ entry, email, stepId, dueAt });
      if (due.length >= maxBatch) break;
    }
  }
  return due;
}

async function removeDripJob(entry) {
  const kv = getKV();
  await kv.lrem('drip:scheduled', 1, entry);
}

// ─── Rate limiting ────────────────────────────────────────────────
async function checkRateLimit(ip, limit = 5, windowSec = 3600) {
  if (!ip) return { allowed: true };
  const kv = getKV();
  const key = `rl:ip:${ip}`;
  const count = await kv.incr(key);
  if (count === 1) {
    await kv.expire(key, windowSec);
  }
  return { allowed: count <= limit, count, limit };
}

// ─── Request body parsing (Vercel Node functions) ─────────────────
async function readJsonBody(req) {
  if (req.body && typeof req.body === 'object') {
    return req.body;
  }
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', chunk => {
      data += chunk;
      if (data.length > 10000) {
        req.destroy();
        reject(new Error('Body too large'));
      }
    });
    req.on('end', () => {
      try {
        resolve(data ? JSON.parse(data) : {});
      } catch (e) {
        reject(new Error('Invalid JSON'));
      }
    });
    req.on('error', reject);
  });
}

function getClientIp(req) {
  const xff = req.headers['x-forwarded-for'];
  if (xff) return String(xff).split(',')[0].trim();
  return req.headers['x-real-ip'] || req.socket?.remoteAddress || '';
}

module.exports = {
  VALID_VOLUMES,
  DRIP_STEPS,
  SITE_URL,
  SITE_DOMAIN,
  REPLY_TO,
  isValidEmail,
  normalizeEmail,
  sanitizeVolumes,
  signConfirmToken,
  verifyConfirmToken,
  signUnsubscribeToken,
  verifyUnsubscribeToken,
  getKV,
  getSubscriber,
  setSubscriber,
  isUnsubscribed,
  markUnsubscribed,
  scheduleDrip,
  getDueDripJobs,
  removeDripJob,
  checkRateLimit,
  readJsonBody,
  getClientIp,
};
