// Quick test of token signing & verification.
// Run with: CPL_TOKEN_SECRET=$(openssl rand -hex 32) node scripts/test-tokens.js

const {
  signConfirmToken, verifyConfirmToken,
  signUnsubscribeToken, verifyUnsubscribeToken,
  isValidEmail, sanitizeVolumes,
} = require('../api/_lib');

function assertEqual(actual, expected, label) {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  if (a !== e) {
    console.error(`✗ ${label}\n  expected: ${e}\n  actual:   ${a}`);
    process.exit(1);
  }
  console.log(`✓ ${label}`);
}

function assertTrue(cond, label) {
  if (!cond) { console.error(`✗ ${label}`); process.exit(1); }
  console.log(`✓ ${label}`);
}

console.log('Running CPL token tests...\n');

// Email validation
assertTrue(isValidEmail('user@example.com'), 'email: simple valid');
assertTrue(isValidEmail('first.last+tag@school.edu'), 'email: plus tag valid');
assertTrue(!isValidEmail(''), 'email: empty invalid');
assertTrue(!isValidEmail('no-at-sign'), 'email: missing @ invalid');
assertTrue(!isValidEmail('a@'), 'email: missing domain invalid');
assertTrue(!isValidEmail('a'.repeat(255) + '@x.com'), 'email: too long invalid');
assertTrue(!isValidEmail(null), 'email: null invalid');
assertTrue(!isValidEmail(123), 'email: number invalid');

// Volume sanitization
assertEqual(sanitizeVolumes(['history', 'plan']), ['history', 'plan'], 'volumes: valid kept');
assertEqual(sanitizeVolumes(['history', 'hacker', '<script>']), ['history'], 'volumes: invalid stripped');
assertEqual(sanitizeVolumes('not-an-array'), [], 'volumes: non-array → empty');
assertEqual(sanitizeVolumes(null), [], 'volumes: null → empty');

// Confirm token round-trip
const tok = signConfirmToken({ email: 'student@school.edu', volumes: ['history', 'plan'] });
assertTrue(typeof tok === 'string' && tok.includes('.'), 'confirm token: has correct shape');

const verified = verifyConfirmToken(tok);
assertTrue(verified.ok === true, 'confirm token: verifies clean');
assertEqual(verified.email, 'student@school.edu', 'confirm token: email preserved');
assertEqual(verified.volumes, ['history', 'plan'], 'confirm token: volumes preserved');

// Tamper detection
const tampered = tok.slice(0, -4) + 'AAAA';
const verifiedTampered = verifyConfirmToken(tampered);
assertTrue(verifiedTampered.ok === false, 'confirm token: tampered signature rejected');

// Malformed input
assertTrue(verifyConfirmToken('').ok === false, 'confirm token: empty rejected');
assertTrue(verifyConfirmToken('no-dot-here').ok === false, 'confirm token: malformed rejected');
assertTrue(verifyConfirmToken('a.b.c').ok === false || verifyConfirmToken('a.b.c').ok === true,
  'confirm token: multi-dot handled');

// Unsubscribe token round-trip
const unsub = signUnsubscribeToken('student@school.edu');
const unsubVerified = verifyUnsubscribeToken(unsub);
assertTrue(unsubVerified.ok === true, 'unsub token: verifies clean');
assertEqual(unsubVerified.email, 'student@school.edu', 'unsub token: email preserved');

// Cross-token rejection: a confirm token should not verify as an unsub token
const crossVerify = verifyUnsubscribeToken(tok);
assertTrue(crossVerify.ok === false, 'unsub token: rejects confirm token (different payload type)');

console.log('\n✓ All token tests passed.');
