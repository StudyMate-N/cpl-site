// GET /g/:token  (PUBLIC, rewritten to /api/g/[token])
// Verify HMAC + 30-day expiry → render a small branded download page listing
// the stored guide files. Tampered / expired / revoked tokens are rejected.
'use strict';
const ops = require('../_ops');

function esc(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function fmtSize(n) {
  if (!n) return '';
  if (n < 1024) return n + ' B';
  if (n < 1024 * 1024) return (n / 1024).toFixed(0) + ' KB';
  return (n / 1024 / 1024).toFixed(1) + ' MB';
}

function page(opts) {
  return '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<meta name="robots" content="noindex,nofollow">' +
    '<title>' + esc(opts.title) + ' · Clinical Performance Lab</title>' +
    '<style>' +
    ':root{--ink:#0B1F1B;--teal:#0F7A6B;--lime:#B7E04E;--cream:#FAF7F0;--cream2:#F4EFE2;--border:#E4DCC8;--muted:#5C6E69}' +
    '*{box-sizing:border-box}body{margin:0;background:#ECE7DA;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:28px 14px}' +
    '.card{width:560px;max-width:100%;background:var(--cream);border-radius:18px;overflow:hidden;box-shadow:0 8px 30px rgba(11,31,27,.12)}' +
    '.head{background:var(--ink);padding:20px 28px;display:flex;align-items:center;gap:11px}' +
    '.logo{width:34px;height:34px;border-radius:50%;background:var(--lime);color:var(--ink);font-weight:800;font-size:13px;text-align:center;line-height:34px}' +
    '.brand{font-size:14px;font-weight:600;color:var(--cream)}.brand small{display:block;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:rgba(250,247,240,.5);margin-top:2px}' +
    '.body{padding:30px 28px}h1{font-family:Georgia,serif;font-size:23px;font-weight:600;margin:0 0 8px;letter-spacing:-.01em}' +
    '.case{font-size:14px;color:var(--muted);margin:0 0 22px}' +
    '.file{display:flex;align-items:center;justify-content:space-between;gap:14px;background:#fff;border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin-bottom:10px;text-decoration:none}' +
    '.file .n{font-weight:600;font-size:14px;color:var(--ink)}.file .s{font-size:12px;color:var(--muted);margin-top:2px}' +
    '.dl{display:inline-block;background:var(--lime);color:var(--ink);font-weight:700;font-size:13px;padding:9px 18px;border-radius:999px;white-space:nowrap}' +
    '.code{margin:18px 0 0;font-size:13px;color:var(--muted)}.code b{font-family:monospace;color:var(--ink);letter-spacing:.06em}' +
    '.note{background:var(--cream2);border:1px solid var(--border);border-radius:12px;padding:14px 16px;font-size:13px;line-height:1.55;color:var(--muted)}' +
    '.foot{padding:18px 28px;border-top:1px solid var(--border);background:var(--cream2);font-size:11px;color:var(--muted)}' +
    '.foot a{color:var(--teal)}.err h1{color:var(--ink)}' +
    '</style></head><body><div class="card">' +
    '<div class="head"><div class="logo">CPL</div><div class="brand">Clinical Performance Lab<small>Secure guide access</small></div></div>' +
    '<div class="body' + (opts.err ? ' err' : '') + '">' + opts.html + '</div>' +
    '<div class="foot">Clinical Performance Lab · Study aid for exam preparation · ' +
    '<a href="mailto:support@clinicalperformancelab.com">support@clinicalperformancelab.com</a></div>' +
    '</div></body></html>';
}

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('X-Robots-Tag', 'noindex, nofollow');
  res.setHeader('Cache-Control', 'no-store');

  const token = req.query && req.query.token;
  const r = await ops.resolveMagic(token);

  if (!r.ok) {
    res.statusCode = (r.error === 'expired') ? 410 : 403;
    const msg = r.error === 'expired'
      ? 'This access link has expired. Links stay active for 30 days — reply to your delivery email and we’ll send a fresh one.'
      : 'This access link is invalid or has been revoked. Please use the exact link from your delivery email, or contact support.';
    return res.end(page({ err: true, title: 'Link unavailable', html:
      '<h1>Link unavailable</h1><div class="note">' + esc(msg) + '</div>' }));
  }

  const o = r.order;
  const files = Array.isArray(o.files) ? o.files : [];
  let filesHtml;
  if (files.length) {
    filesHtml = files.map(function (f) {
      return '<a class="file" href="' + esc(f.url) + '" download>' +
        '<span><span class="n">' + esc(f.name) + '</span>' + (f.size ? '<span class="s">' + esc(fmtSize(f.size)) + '</span>' : '') + '</span>' +
        '<span class="dl">Download →</span></a>';
    }).join('');
  } else {
    filesHtml = '<div class="note">Your guide is being attached — if it isn’t here yet, it will appear shortly. Questions? Reply to your delivery email any time.</div>';
  }

  res.statusCode = 200;
  return res.end(page({
    title: 'Your guide',
    html:
      '<h1>Your guide is ready</h1>' +
      '<p class="case">' + esc(o.case) + (o.id ? ' · ' + esc(o.id) : '') + '</p>' +
      filesHtml +
      (o.accessCode ? '<p class="code">Backup access code: <b>' + esc(o.accessCode) + '</b></p>' : ''),
  }));
};
