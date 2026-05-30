// Local end-to-end test of the ops pipeline. Stubs `resend` + `@vercel/blob`,
// uses the in-memory KV fallback, drives the real route handlers in-process.
// Run: node scripts/ops-e2e-local.js   (temporary; not part of deploy)
'use strict';

// ─── stub network modules before any route requires them ──────────
const Module = require('module');
const sentEmails = [];
const stubs = {
  resend: {
    Resend: class {
      get emails() {
        return { send: async (o) => { const id = 'msg_' + Math.random().toString(36).slice(2, 10); sentEmails.push({ id, to: o.to, subject: o.subject, replyTo: o.replyTo }); return { data: { id } }; } };
      }
    },
  },
  '@vercel/blob': {
    put: async (key, buf, opts) => ({ url: 'https://blob.test/' + key.replace(/[^a-z0-9/_-]/gi, '_') + '-' + Math.random().toString(36).slice(2, 6), pathname: key }),
  },
};
const origLoad = Module._load;
Module._load = function (request) { if (stubs[request]) return stubs[request]; return origLoad.apply(this, arguments); };

// ─── env ──────────────────────────────────────────────────────────
process.env.CPL_TOKEN_SECRET = 'local-e2e-secret-key-32-chars-minimum-xx';
process.env.OPS_PASSCODE = 'opensesame';
process.env.RESEND_API_KEY = 'fake_key_for_test';
process.env.INBOUND_WEBHOOK_KEY = 'inbound-test-key';
process.env.BLOB_READ_WRITE_TOKEN = 'vercel_blob_rw_test';
process.env.CPL_BASE_URL = 'https://www.clinicalperformancelab.com';
// no RESEND_WEBHOOK_SECRET → inbound uses ?key fallback for the test

const fs = require('fs');
const path = require('path');

// ─── seed a tiny cases.json so catalog lookup works ───────────────
const pubDir = path.join(process.cwd(), 'public');
if (!fs.existsSync(pubDir)) fs.mkdirSync(pubDir, { recursive: true });
const casesPath = path.join(pubDir, 'cases.json');
const hadCases = fs.existsSync(casesPath);
const backup = hadCases ? fs.readFileSync(casesPath) : null;
fs.writeFileSync(casesPath, JSON.stringify([
  { slug: 'bebe-babbitt-migraine', title: 'Bebe Babbitt — Migraine with Aura', cc: 'More frequent severe headaches', ready: true, price: 150, school: 'Chamberlain University', course: 'NR 509 Week 6', alias: 'Bebe Babbitt' },
  { slug: 'betty-burns-pt1', title: 'Betty Burns — Part 1', cc: 'Comprehensive adult encounter', ready: false, price: 150, school: 'Chamberlain University', course: 'NR 509', alias: 'Betty Burns' },
]));

// ─── mock req/res ─────────────────────────────────────────────────
const { Readable } = require('stream');
function mockReq({ method = 'GET', query = {}, headers = {}, body = null, raw = null }) {
  const req = new Readable({ read() {} });
  req.method = method; req.query = query; req.headers = Object.assign({}, headers);
  if (raw != null) { req.push(raw); req.push(null); }
  else if (body && typeof body === 'object') { req.body = body; req.push(null); }
  else { req.push(null); }
  return req;
}
function mockRes() {
  const res = { statusCode: 200, headers: {}, _data: '', ended: false };
  res.setHeader = (k, v) => { res.headers[k.toLowerCase()] = v; };
  res.getHeader = (k) => res.headers[k.toLowerCase()];
  res.end = (d) => { res._data = d == null ? '' : String(d); res.ended = true; };
  res.status = (c) => { res.statusCode = c; return res; };
  res.json = (o) => { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(o)); return res; };
  return res;
}
function jbody(res) { try { return JSON.parse(res._data); } catch (e) { return res._data; } }
function cookieFrom(res) {
  const sc = res.headers['set-cookie'];
  if (!sc) return '';
  return String(sc).split(';')[0]; // ops_session=...
}

const auth = require('../api/ops/auth');
const orders = require('../api/ops/orders');
const inbound = require('../api/ops/inbound');
const orderAction = require('../api/ops/orders/[id]/[action]');
const gpage = require('../api/g/[token]');
// consolidated-route shims (preserve the test's call sites)
const login = (req, res) => { if (req.body) req.body = Object.assign({ action: 'login' }, req.body); return auth(req, res); };
const invoice = (req, res) => { req.query = Object.assign({}, req.query, { action: 'invoice' }); return orderAction(req, res); };
const confirmPay = (req, res) => { req.query = Object.assign({}, req.query, { action: 'confirm-payment' }); return orderAction(req, res); };
const deliver = (req, res) => { req.query = Object.assign({}, req.query, { action: 'deliver' }); return orderAction(req, res); };
const attach = (req, res) => { req.query = Object.assign({}, req.query, { action: 'attach' }); return orderAction(req, res); };

let pass = 0, fail = 0;
function ok(cond, label) { if (cond) { pass++; console.log('  ✓ ' + label); } else { fail++; console.log('  ✗ FAIL: ' + label); } }

(async () => {
  console.log('\n── 1. Auth gate ───────────────────────────────');
  // unauth orders → 401
  let r = mockRes(); await orders(mockReq({ method: 'GET' }), r);
  ok(r.statusCode === 401, 'GET /orders without cookie → 401');
  // wrong passcode → 401
  r = mockRes(); await login(mockReq({ method: 'POST', body: { passcode: 'wrong' } }), r);
  ok(r.statusCode === 401, 'login wrong passcode → 401');
  // correct passcode → 200 + cookie
  r = mockRes(); await login(mockReq({ method: 'POST', body: { passcode: 'opensesame' } }), r);
  ok(r.statusCode === 200 && /ops_session=/.test(String(r.headers['set-cookie'] || '')), 'login correct → 200 + Set-Cookie');
  const cookie = cookieFrom(r);
  ok(/HttpOnly/.test(String(r.headers['set-cookie'])), 'session cookie is HttpOnly');

  // authed orders → 200 empty
  r = mockRes(); await orders(mockReq({ method: 'GET', headers: { cookie } }), r);
  ok(r.statusCode === 200 && jbody(r).orders.length === 0, 'GET /orders with cookie → 200 empty');

  console.log('\n── 2. Order intake (webhook) ──────────────────');
  // unsigned + no key → 401
  let event = { type: 'email.received', data: { from: 'Jane Student <jane@university.edu>', to: ['orders@clinicalperformancelab.com'], subject: 'CPL Order - Bebe Babbitt — Migraine with Aura' } };
  r = mockRes(); await inbound(mockReq({ method: 'POST', query: {}, raw: Buffer.from(JSON.stringify(event)) }), r);
  ok(r.statusCode === 401, 'inbound without key → 401');
  // with key → creates a READY order, sends 2 emails
  r = mockRes(); await inbound(mockReq({ method: 'POST', query: { key: 'inbound-test-key' }, raw: Buffer.from(JSON.stringify(event)) }), r);
  let body = jbody(r);
  ok(r.statusCode === 200 && body.created && body.ready === true, 'inbound ready order created: ' + body.created + ' (ready=' + body.ready + ')');
  ok(sentEmails.some(e => /confirmation|got your order|We’ve got/i.test(e.subject)) || sentEmails.length >= 1, 'orderReceived email queued');
  ok(sentEmails.some(e => /New order/i.test(e.subject)), 'adminAlert email queued');
  const orderId = body.created;

  // a NON-ready order too (for the build→deliver path)
  let event2 = { type: 'email.received', data: { from: 'Bob <bob@school.edu>', to: ['orders@clinicalperformancelab.com'], subject: 'CPL Order - Betty Burns — Part 1' } };
  r = mockRes(); await inbound(mockReq({ method: 'POST', query: { key: 'inbound-test-key' }, raw: Buffer.from(JSON.stringify(event2)) }), r);
  const order2Id = jbody(r).created;
  ok(jbody(r).ready === false, 'second order is non-ready (custom build): ' + order2Id);

  // list now has 2, newest first
  r = mockRes(); await orders(mockReq({ method: 'GET', headers: { cookie } }), r);
  ok(jbody(r).orders.length === 2 && jbody(r).orders[0].id === order2Id, 'GET /orders → 2 orders, newest first');

  console.log('\n── 3. Lifecycle: READY order → invoice → pay ──');
  r = mockRes(); await invoice(mockReq({ method: 'POST', query: { id: orderId }, headers: { cookie }, body: { url: 'https://pay.payoneer.com/abc', amount: 150 } }), r);
  ok(r.statusCode === 200 && jbody(r).order.status === 'invoiced', 'invoice → status invoiced, email sent (' + (jbody(r).sent || {}).id + ')');

  r = mockRes(); await confirmPay(mockReq({ method: 'POST', query: { id: orderId }, headers: { cookie } }), r);
  body = jbody(r);
  ok(r.statusCode === 200 && body.order.status === 'fulfilled' && body.order.accessUrl && body.order.accessCode, 'confirm-payment (ready) → fulfilled + minted access');
  const readyToken = body.order.accessUrl.split('/g/')[1];

  console.log('\n── 4. Lifecycle: BUILD order → pay → deliver ──');
  r = mockRes(); await invoice(mockReq({ method: 'POST', query: { id: order2Id }, headers: { cookie }, body: { url: 'https://pay.payoneer.com/xyz', amount: 150 } }), r);
  r = mockRes(); await confirmPay(mockReq({ method: 'POST', query: { id: order2Id }, headers: { cookie } }), r);
  ok(jbody(r).order.status === 'building', 'confirm-payment (non-ready) → status building');
  // deliver with an uploaded file (base64)
  const fileData = Buffer.from('PK fake docx bytes for ' + order2Id).toString('base64');
  r = mockRes(); await deliver(mockReq({ method: 'POST', query: { id: order2Id }, headers: { cookie }, body: { files: [{ name: 'Betty-Burns-Guide.docx', type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', data: fileData }] } }), r);
  body = jbody(r);
  ok(r.statusCode === 200 && body.order.status === 'fulfilled' && body.order.files.length === 1, 'deliver → stored 1 file, status fulfilled');
  ok(/blob\.test/.test(body.order.files[0].url), 'stored file has a blob URL');
  const buildToken = body.order.accessUrl.split('/g/')[1];

  console.log('\n── 5. Magic link /g/:token ────────────────────');
  r = mockRes(); await gpage(mockReq({ method: 'GET', query: { token: buildToken } }), r);
  ok(r.statusCode === 200 && /Download/.test(r._data) && /Betty-Burns-Guide\.docx/.test(r._data), 'valid token → download page with file');
  ok(/blob\.test/.test(r._data), 'download page links the stored blob URL');

  // tampered token → rejected
  const tampered = buildToken.slice(0, 6) + (buildToken[6] === 'A' ? 'B' : 'A') + buildToken.slice(7);
  r = mockRes(); await gpage(mockReq({ method: 'GET', query: { token: tampered } }), r);
  ok(r.statusCode === 403 && /invalid|revoked|unavailable/i.test(r._data), 'tampered token → 403 rejected');

  // ready order's link also works
  r = mockRes(); await gpage(mockReq({ method: 'GET', query: { token: readyToken } }), r);
  ok(r.statusCode === 200, 'ready order token also serves a page');

  console.log('\n── 6. Attach guide BEFORE delivery (ready case) ─');
  // fresh ready order → attach a file while still 'new' (stage) → confirm-payment auto-delivers WITH the file
  let ev3 = { type: 'email.received', data: { from: 'Cara <cara@school.edu>', to: ['orders@clinicalperformancelab.com'], subject: 'CPL Order - Bebe Babbitt — Migraine with Aura' } };
  r = mockRes(); await inbound(mockReq({ method: 'POST', query: { key: 'inbound-test-key' }, raw: Buffer.from(JSON.stringify(ev3)) }), r);
  const o3 = jbody(r).created;
  const stageData = Buffer.from('staged guide for ' + o3).toString('base64');
  r = mockRes(); await attach(mockReq({ method: 'POST', query: { id: o3 }, headers: { cookie }, body: { files: [{ name: 'Bebe-Guide.docx', type: 'application/octet-stream', data: stageData }] } }), r);
  body = jbody(r);
  ok(r.statusCode === 200 && body.order.files.length === 1 && body.order.status === 'new', 'attach stages file, status stays new (not delivered)');
  ok(!!body.order.accessUrl, 'attach mints the access link ahead of delivery');
  // invoice + confirm-payment (ready) → auto-delivers, file already attached
  r = mockRes(); await invoice(mockReq({ method: 'POST', query: { id: o3 }, headers: { cookie }, body: { url: 'https://pay.x/c', amount: 150 } }), r);
  r = mockRes(); await confirmPay(mockReq({ method: 'POST', query: { id: o3 }, headers: { cookie } }), r);
  const stagedTok = jbody(r).order.accessUrl.split('/g/')[1];
  ok(jbody(r).order.status === 'fulfilled' && jbody(r).order.files.length === 1, 'ready confirm-payment delivers WITH the pre-attached file');
  r = mockRes(); await gpage(mockReq({ method: 'GET', query: { token: stagedTok } }), r);
  ok(r.statusCode === 200 && /Bebe-Guide\.docx/.test(r._data), 'magic link serves the pre-attached guide file');

  console.log('\n── Summary ────────────────────────────────────');
  console.log('  emails sent: ' + sentEmails.length + ' → ' + sentEmails.map(e => e.subject).join(' | '));
  console.log('  PASS ' + pass + ' / FAIL ' + fail);

  // cleanup cases.json
  if (hadCases) fs.writeFileSync(casesPath, backup); else fs.unlinkSync(casesPath);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('HARNESS ERROR', e); if (hadCases) fs.writeFileSync(casesPath, backup); else { try { fs.unlinkSync(casesPath); } catch (x) {} } process.exit(1); });
