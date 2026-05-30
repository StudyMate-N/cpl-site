// CPL Ops — outbound email sender. Wraps the Resend client + the ported
// ops-emails templates, fills role-appropriate from/replyTo, and the
// {{unsubscribe}}/{{dashboardUrl}} placeholders. Returns the Resend message id.

'use strict';

const { Resend } = require('resend');
const { SITE_URL, REPLY_TO, signUnsubscribeToken } = require('./_lib');
const opsEmails = require('../emails/ops-emails');

const FROM_ADDRESS  = process.env.CPL_FROM_ADDRESS || 'CPL <hello@clinicalperformancelab.com>';
const ORDER_EMAIL   = process.env.CPL_ORDER_EMAIL  || 'orders@clinicalperformancelab.com';
const SUPPORT_EMAIL = process.env.CPL_SUPPORT_EMAIL || 'support@clinicalperformancelab.com';
const DASHBOARD_URL = SITE_URL + '/ops/';

// template → { recipient(order), replyTo, admin }
const ROUTING = {
  orderReceived: { to: function (o) { return o.email; }, replyTo: ORDER_EMAIL },
  adminAlert:    { to: function (o) { return ORDER_EMAIL; }, replyTo: ORDER_EMAIL, admin: true },
  invoice:       { to: function (o) { return o.email; }, replyTo: ORDER_EMAIL },
  delivery:      { to: function (o) { return o.email; }, replyTo: SUPPORT_EMAIL },
  building:      { to: function (o) { return o.email; }, replyTo: SUPPORT_EMAIL },
};

function unsubUrl(email) {
  try { return SITE_URL + '/api/unsubscribe?t=' + encodeURIComponent(signUnsubscribeToken(email)); }
  catch (e) { return 'mailto:' + REPLY_TO; }
}

// sendOps(template, order) → { id }  (throws on hard send failure)
async function sendOps(template, order, overrides) {
  const route = ROUTING[template];
  if (!route) throw new Error('Unknown ops email template: ' + template);
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) throw new Error('RESEND_API_KEY not configured');

  const to = (overrides && overrides.to) || route.to(order);
  const ctx = {
    dashboardUrl: DASHBOARD_URL,
    invoiceUrl: order.invoiceUrl || '',
    accessUrl: order.accessUrl || '',
    accessCode: order.accessCode || '',
    unsubscribeUrl: route.admin ? undefined : unsubUrl(order.email),
  };
  const { subject, html } = opsEmails.render(template, order, ctx);

  const headers = { 'X-Entity-Ref-ID': order.id + ':' + template };
  if (!route.admin) headers['List-Unsubscribe'] = '<' + ctx.unsubscribeUrl + '>';

  const resend = new Resend(apiKey);
  const result = await resend.emails.send({
    from: FROM_ADDRESS,
    to: to,
    replyTo: route.replyTo,
    subject: subject,
    html: html,
    headers: headers,
  });
  if (result && result.error) throw new Error('Resend: ' + (result.error.message || JSON.stringify(result.error)));
  return { id: result && result.data ? result.data.id : (result && result.id) || null, to: to, template: template };
}

module.exports = { sendOps, ORDER_EMAIL, SUPPORT_EMAIL, FROM_ADDRESS, DASHBOARD_URL };
