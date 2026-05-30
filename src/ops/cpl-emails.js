/* CPL — Resend email templates (production-ready HTML)
   Each fn(order) returns a full HTML document string. Table layout + inline
   styles for email-client safety. Brand: ink/teal/lime/cream, Georgia headings
   (Fraunces fallback), system sans body.
   Exposed as window.CPLEmails. Used by the admin dashboard for live preview AND
   directly portable to Resend (resend.emails.send({ html: CPLEmails.invoice(order) })). */
(function () {
  'use strict';

  var C = {
    ink: '#0B1F1B', ink2: '#1F3530', teal: '#0F7A6B', teal8: '#0A6358',
    lime: '#B7E04E', cream: '#FAF7F0', cream2: '#F4EFE2', cream3: '#ECE7DA',
    border: '#E4DCC8', muted: '#5C6E69', amber: '#946115', warm: '#FFFCF5', warmB: '#E8B566'
  };
  var SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif";
  var SERIF = "Georgia,'Times New Roman',serif";

  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function money(n) { return '$' + Number(n).toLocaleString('en-US'); }

  /* ── shared shell ─────────────────────────────────────────────── */
  function shell(opts) {
    // opts: { preheader, badge, badgeColor, title, intro, body, cta, footnote, admin }
    var btn = '';
    if (opts.cta) {
      btn =
        '<table role="presentation" cellpadding="0" cellspacing="0" style="margin:26px 0 4px;"><tr><td bgcolor="' + (opts.cta.bg || C.lime) + '" style="border-radius:999px;">' +
        '<a href="' + esc(opts.cta.href) + '" style="display:inline-block;padding:15px 32px;font-family:' + SANS + ';font-size:16px;font-weight:700;color:' + (opts.cta.fg || C.ink) + ';text-decoration:none;border-radius:999px;">' + esc(opts.cta.label) + '</a>' +
        '</td></tr></table>';
    }
    var badge = '';
    if (opts.badge) {
      badge = '<span style="display:inline-block;font-family:' + SANS + ';font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:' + (opts.badgeColor || C.teal) + ';background:' + C.cream2 + ';border:1px solid ' + C.border + ';padding:5px 12px;border-radius:999px;margin-bottom:16px;">' + esc(opts.badge) + '</span>';
    }
    return '' +
'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="x-apple-disable-message-reformatting"><title>' + esc(opts.title) + '</title></head>' +
'<body style="margin:0;padding:0;background:' + C.cream3 + ';-webkit-font-smoothing:antialiased;">' +
'<div style="display:none;max-height:0;overflow:hidden;opacity:0;">' + esc(opts.preheader || '') + '</div>' +
'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:' + C.cream3 + ';"><tr><td align="center" style="padding:30px 14px;">' +
  '<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="width:560px;max-width:100%;background:' + C.cream + ';border-radius:18px;overflow:hidden;box-shadow:0 8px 30px rgba(11,31,27,.10);">' +
    // header band
    '<tr><td style="background:' + C.ink + ';padding:22px 30px;">' +
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>' +
        '<td style="vertical-align:middle;"><table role="presentation" cellpadding="0" cellspacing="0"><tr>' +
          '<td style="vertical-align:middle;"><div style="width:34px;height:34px;border-radius:50%;background:' + C.lime + ';color:' + C.ink + ';font-family:' + SANS + ';font-weight:800;font-size:13px;text-align:center;line-height:34px;">CPL</div></td>' +
          '<td style="vertical-align:middle;padding-left:11px;"><div style="font-family:' + SANS + ';font-size:14px;font-weight:600;color:' + C.cream + ';line-height:1.1;">Clinical Performance Lab</div><div style="font-family:' + SANS + ';font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:rgba(250,247,240,.5);margin-top:2px;">' + (opts.admin ? 'Operations' : 'Submission-ready clinical reasoning') + '</div></td>' +
        '</tr></table></td>' +
        '<td align="right" style="vertical-align:middle;font-family:' + SANS + ';font-size:11px;color:rgba(250,247,240,.45);">' + esc(opts.headRight || '') + '</td>' +
      '</tr></table>' +
    '</td></tr>' +
    // body
    '<tr><td style="padding:34px 30px 30px;">' +
      badge +
      '<h1 style="margin:0 0 14px;font-family:' + SERIF + ';font-size:25px;line-height:1.2;font-weight:600;color:' + C.ink + ';letter-spacing:-.01em;">' + opts.title + '</h1>' +
      (opts.intro ? '<p style="margin:0 0 18px;font-family:' + SANS + ';font-size:15px;line-height:1.6;color:' + C.ink2 + ';">' + opts.intro + '</p>' : '') +
      (opts.body || '') +
      btn +
    '</td></tr>' +
    // footer
    '<tr><td style="padding:22px 30px 26px;border-top:1px solid ' + C.border + ';background:' + C.cream2 + ';">' +
      (opts.footnote ? '<p style="margin:0 0 12px;font-family:' + SANS + ';font-size:12px;line-height:1.55;color:' + C.muted + ';">' + opts.footnote + '</p>' : '') +
      '<p style="margin:0;font-family:' + SANS + ';font-size:11px;line-height:1.5;color:' + C.muted + ';">Clinical Performance Lab · Study aid for exam preparation. ' +
      (opts.admin ? 'Internal operations notice.' : '<a href="{{unsubscribe}}" style="color:' + C.teal + ';">Unsubscribe</a> · <a href="mailto:hello@clinicalperformancelab.com" style="color:' + C.teal + ';">Contact support</a>') +
      '</p>' +
    '</td></tr>' +
  '</table>' +
'</td></tr></table></body></html>';
  }

  /* a tidy summary card used inside several emails */
  function caseCard(order, accent) {
    accent = accent || C.teal;
    var sub = [order.school, order.course].filter(Boolean).join(' · ');
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border:1px solid ' + C.border + ';border-left:4px solid ' + accent + ';border-radius:12px;margin:0 0 8px;"><tr>' +
      '<td style="padding:16px 18px;">' +
        '<div style="font-family:' + SANS + ';font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:' + C.muted + ';margin-bottom:5px;">Your order · ' + esc(order.id) + '</div>' +
        '<div style="font-family:' + SERIF + ';font-size:17px;font-weight:600;color:' + C.ink + ';line-height:1.25;">' + esc(order.case) + '</div>' +
        (order.cc ? '<div style="font-family:' + SANS + ';font-size:13px;font-style:italic;color:' + C.muted + ';margin-top:3px;">' + esc(order.cc) + '</div>' : '') +
        (sub ? '<div style="font-family:' + SANS + ';font-size:12px;color:' + C.muted + ';margin-top:7px;">' + esc(sub) + '</div>' : '') +
      '</td>' +
      '<td align="right" style="padding:16px 18px 16px 0;vertical-align:top;white-space:nowrap;"><div style="font-family:' + SERIF + ';font-size:22px;font-weight:600;color:' + C.ink + ';">' + money(order.amount || order.price) + '</div></td>' +
    '</tr></table>';
  }

  function steps(items) {
    var rows = items.map(function (it, i) {
      return '<tr>' +
        '<td style="vertical-align:top;width:30px;padding:0 0 ' + (i === items.length - 1 ? '0' : '14px') + ';"><div style="width:22px;height:22px;border-radius:50%;background:' + (it.done ? C.lime : C.cream2) + ';border:1px solid ' + (it.done ? C.lime : C.border) + ';color:' + C.ink + ';font-family:' + SANS + ';font-size:11px;font-weight:700;text-align:center;line-height:22px;">' + (it.done ? '&#10003;' : (i + 1)) + '</div></td>' +
        '<td style="vertical-align:top;padding:1px 0 ' + (i === items.length - 1 ? '0' : '14px') + ' 10px;font-family:' + SANS + ';font-size:13.5px;line-height:1.45;color:' + (it.done ? C.muted : C.ink2) + ';">' + it.html + '</td>' +
      '</tr>';
    }).join('');
    return '<table role="presentation" cellpadding="0" cellspacing="0" style="margin:4px 0 6px;">' + rows + '</table>';
  }

  /* ── 1. Order received (→ student, instant) ───────────────────── */
  function orderReceived(o) {
    return shell({
      preheader: 'We\u2019ve got your order for ' + o.case + '. Your invoice is on the way.',
      headRight: 'Order received',
      badge: 'Order received', badgeColor: C.teal,
      title: 'We\u2019ve got it \u2014 your invoice is on the way.',
      intro: 'Thanks for your order. Here\u2019s exactly what happens next, so there are no surprises:',
      body:
        caseCard(o, C.teal) +
        '<div style="height:10px;"></div>' +
        steps([
          { html: '<b style="color:' + C.ink + ';">Invoice incoming.</b> We\u2019ll email you a secure Payoneer invoice \u2014 usually within the hour.' },
          { html: '<b style="color:' + C.ink + ';">You pay safely</b> through Payoneer\u2019s checkout. No account needed.' },
          { html: '<b style="color:' + C.ink + ';">Your guide unlocks instantly.</b> The moment payment clears, your complete guide arrives here \u2014 open it with one tap, no code to type.' }
        ]),
      footnote: 'Didn\u2019t place this order? You can safely ignore this email \u2014 no charge is made until you pay an invoice.'
    });
  }

  /* ── 2. Admin alert (→ ops) ───────────────────────────────────── */
  function adminAlert(o) {
    var rows = [
      ['Order', o.id], ['Case', o.case], ['Customer', o.email],
      ['School / course', [o.school, o.course].filter(Boolean).join(' · ') || '\u2014'],
      ['Patient alias', o.alias || '\u2014'],
      ['Price', money(o.price)],
      ['iHuman case', o.ready ? '\u2713 Pre-built \u2014 auto-delivers on payment' : '\u26a0 Needs build \u2014 upload required after payment']
    ].map(function (r) {
      return '<tr><td style="padding:9px 0;border-bottom:1px solid ' + C.border + ';font-family:' + SANS + ';font-size:12px;color:' + C.muted + ';width:130px;vertical-align:top;">' + esc(r[0]) + '</td>' +
        '<td style="padding:9px 0;border-bottom:1px solid ' + C.border + ';font-family:' + SANS + ';font-size:13.5px;color:' + C.ink2 + ';font-weight:500;">' + esc(r[1]) + '</td></tr>';
    }).join('');
    return shell({
      admin: true,
      preheader: 'New order ' + o.id + ' \u2014 ' + o.case,
      headRight: 'New order',
      badge: 'Action needed', badgeColor: C.amber,
      title: 'New order \u2014 generate a Payoneer invoice.',
      intro: 'A student just placed an order. Open it in the dashboard to paste the Payoneer invoice link; the system handles the rest.',
      body:
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border:1px solid ' + C.border + ';border-radius:12px;margin:2px 0 6px;"><tr><td style="padding:6px 18px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">' + rows + '</table></td></tr></table>',
      cta: { label: 'Open in dashboard \u2192', href: '{{dashboardUrl}}', bg: C.ink, fg: C.lime }
    });
  }

  /* ── 3. Invoice (→ student) ───────────────────────────────────── */
  function invoice(o) {
    return shell({
      preheader: 'Your invoice for ' + o.case + ' \u2014 ' + money(o.amount || o.price) + '. Pay to unlock your guide.',
      headRight: 'Invoice',
      badge: 'Invoice ready', badgeColor: C.teal,
      title: 'Your invoice is ready.',
      intro: 'Here\u2019s the secure invoice for your guide. Pay through Payoneer\u2019s checkout and your complete guide unlocks automatically \u2014 no further steps.',
      body:
        caseCard(o, C.teal) +
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:14px 0 2px;background:' + C.warm + ';border:1px solid ' + C.warmB + ';border-radius:12px;"><tr><td style="padding:14px 18px;font-family:' + SANS + ';font-size:13px;line-height:1.55;color:' + C.ink2 + ';">' +
          '<b style="color:' + C.amber + ';">Total due: ' + money(o.amount || o.price) + '</b> &nbsp;·&nbsp; paid securely via Payoneer. The button below opens your personal invoice.' +
        '</td></tr></table>',
      cta: { label: 'Pay invoice securely \u2192', href: o.invoiceUrl || '{{invoiceUrl}}', bg: C.lime, fg: C.ink },
      footnote: 'Trouble with the button? Copy this link into your browser: <span style="color:' + C.teal + ';word-break:break-all;">' + esc(o.invoiceUrl || '{{invoiceUrl}}') + '</span><br>Invoice questions? Just reply to this email.'
    });
  }

  /* ── 4. Access delivery (→ student) ───────────────────────────── */
  function delivery(o) {
    return shell({
      preheader: 'Payment confirmed \u2014 your ' + o.case + ' guide is ready. Open it now.',
      headRight: 'Guide ready',
      badge: 'Payment confirmed', badgeColor: C.teal,
      title: 'Your guide is ready \u2014 open it now.',
      intro: 'Payment received, thank you. Your complete, submission-ready guide is unlocked. Tap below to open it \u2014 no code required.',
      body:
        caseCard(o, C.lime) +
        '<div style="height:6px;"></div>',
      cta: { label: 'Open my guide \u2192', href: o.accessUrl || '{{accessUrl}}', bg: C.lime, fg: C.ink },
      footnote:
        'Prefer a code? Yours is <b style="color:' + C.ink + ';font-family:monospace;letter-spacing:.06em;">' + esc(o.accessCode || '{{accessCode}}') + '</b> \u2014 enter it on the guide page if the button doesn\u2019t open. ' +
        'Your link stays active for 30 days and works on any device. Questions? Reply any time.'
    });
  }

  /* ── 5. Build in progress (→ student, when case not pre-built) ── */
  function building(o) {
    return shell({
      preheader: 'Payment confirmed \u2014 we\u2019re building your ' + o.case + ' guide now.',
      headRight: 'In production',
      badge: 'Payment confirmed', badgeColor: C.teal,
      title: 'Payment confirmed \u2014 we\u2019re building your guide.',
      intro: 'Thanks, your payment cleared. This case is custom-built for accuracy, so our team is putting it together now. You don\u2019t need to do anything \u2014 we\u2019ll email your complete guide the moment it\u2019s ready.',
      body:
        caseCard(o, C.warmB) +
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:14px 0 2px;background:' + C.warm + ';border:1px solid ' + C.warmB + ';border-radius:12px;"><tr><td style="padding:14px 18px;font-family:' + SANS + ';font-size:13px;line-height:1.55;color:' + C.ink2 + ';">' +
          '<b style="color:' + C.amber + ';">Typical turnaround: 12\u201324 hours.</b> Your guide will arrive in this same inbox, ready to open with one tap.' +
        '</td></tr></table>',
      footnote: 'Hold tight \u2014 no action needed on your end. If you have a deadline today, reply and we\u2019ll prioritize it.'
    });
  }

  window.CPLEmails = {
    orderReceived: orderReceived,
    adminAlert: adminAlert,
    invoice: invoice,
    delivery: delivery,
    building: building,
    _colors: C
  };
})();
