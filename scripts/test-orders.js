// Exercise the real intake handler and catalog matcher with storage/mail mocked.
// Run from the repository root: node scripts/test-orders.js
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createRequire } = require('node:module');

function load(file, overrides) {
  const filename = path.resolve(__dirname, '..', file);
  const localRequire = createRequire(filename);
  const module = { exports: {} };
  const context = { module, exports: module.exports, process, console, Buffer,
    __dirname: path.dirname(filename), __filename: filename,
    require: name => Object.hasOwn(overrides, name) ? overrides[name] : localRequire(name) };
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), context, { filename });
  return module.exports;
}
const storage = new Map();
const kv = {
  get: async key => storage.get(key) ?? null,
  set: async (key, value) => { storage.set(key, value); },
  incr: async key => { const value = Number(storage.get(key) || 0) + 1; storage.set(key, value); return value; },
  lpush: async () => {},
  expire: async () => {},
};
const library = {
  readJsonBody: async req => req.body,
  isValidEmail: email => typeof email === 'string' && email.includes('@'),
  normalizeEmail: email => email.toLowerCase(),
  checkRateLimit: async () => ({ allowed: true }),
  getClientIp: () => '127.0.0.1',
  getKV: () => kv,
};
const catalogOps = load('api/_ops.js', { './_lib': library });
let created;
const ops = { ...catalogOps,
  createOrder: async data => { const order = await catalogOps.createOrder(data); created = order; return order; },
};
const handler = load('api/order.js', { './_ops': ops, './_lib': library, './_ops-mail': { sendOps: async () => {} } });
async function request(body) {
  created = null;
  const response = { code: 200, body: null, setHeader() {}, status(code) { this.code = code; return this; }, json(value) { this.body = value; return this; } };
  await handler({ method: 'POST', body }, response);
  return response;
}
async function run() {
  const catalog = catalogOps.loadCatalog();
  assert.ok(catalog.length >= 6, 'tests need the generated case catalog');
  const single = await request({ email: 'qa@example.invalid', case: catalog[0].title, price: '390' });
  assert.equal(single.code, 200);
  assert.equal(created.case, catalog[0].title);
  assert.equal(created.price, 150, 'single guide keeps its catalog price');
  for (const [count, price] of [[2,280],[3,390],[4,470],[5,540],[6,620]]) {
    const title = count + '-case bundle: ' + catalog.slice(0,count).map(c => c.title).join('; ');
    const response = await request({ email: 'qa@example.invalid', case: title, price: '150' });
    assert.equal(response.code, 200);
    assert.equal(created.case, title, 'every selected case survives intake');
    const saved = await catalogOps.getOrder(response.body.orderId);
    assert.equal(saved.case, title, 'the full selection is saved to storage');
    assert.equal(saved.price, price, 'the bundle price is saved to storage');
    assert.equal(created.price, price, 'bundle price is calculated on the server');
    assert.equal(created.ready, false, 'a bundle needs a fulfillment check');
  }
  await request({ email: 'qa@example.invalid', case: '3-case bundle', price: '390' });
  assert.equal(created.case, '3-case bundle', 'older checkout requests still work');
  assert.equal(created.price, 390);
  const all = catalog.length + '-case bundle: ' + catalog.map(c => c.title).join('; ');
  const allResponse = await request({ email: 'qa@example.invalid', case: all });
  assert.equal(allResponse.code, 200);
  assert.equal(created.case, all, 'large selections are not silently truncated');
  const tooLong = await request({ email: 'qa@example.invalid', case: 'x'.repeat(8001) });
  assert.equal(tooLong.code, 400);
  assert.equal(created, null);
  const badCount = await request({ email: 'qa@example.invalid', case: '999-case bundle' });
  assert.equal(badCount.code, 400);
  await catalogOps.saveOrder({ id: 'qa-fulfilled', accessUrl: '/g/qa-token' });
  storage.set('code:CPL-QA', 'qa-fulfilled');
  const badCode = await request({ code: 'invalid-qa' });
  assert.equal(badCode.code, 404);
  const code = await request({ code: 'cpl-qa' });
  assert.equal(code.code, 200);
  assert.equal(code.body.accessUrl, '/g/qa-token');
  assert.equal(created, null, 'unlocking does not create an order');
  console.log('PASS: single cases, 2–6 case bundles, full catalog selection, legacy requests, input limits, and access codes.');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
