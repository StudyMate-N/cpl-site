// GET /api/cron/drip
// Hourly Vercel Cron entry point.
// Reads due drip jobs from KV and sends them via Resend.
//
// Vercel Cron sends a special header that we validate. In dev, you can also pass
// ?secret=CRON_SECRET as a query param for manual triggering.

const { Resend } = require('resend');
const {
  DRIP_STEPS,
  getSubscriber,
  isUnsubscribed,
  signUnsubscribeToken,
  getDueDripJobs,
  removeDripJob,
} = require('../_lib');

const insightEmail = require('../../emails/insight');
const introEmail   = require('../../emails/intro');
const offerEmail   = require('../../emails/offer');

const FROM_ADDRESS = process.env.CPL_FROM_ADDRESS || 'CPL <onboarding@resend.dev>';
const BASE_URL = process.env.CPL_BASE_URL || 'https://clinicalperformancelab.vercel.app';

const EMAIL_BUILDERS = {
  insight: insightEmail,
  intro:   introEmail,
  offer:   offerEmail,
};

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');

  // ─── Auth: Vercel Cron sends 'x-vercel-cron' header. ──
  // Also support a query secret for manual triggering.
  const cronHeader = req.headers['x-vercel-cron'];
  const cronSecret = process.env.CRON_SECRET;
  const querySecret = req.query && req.query.secret;
  const isAuthorized =
    !!cronHeader ||
    (cronSecret && querySecret && querySecret === cronSecret);

  if (!isAuthorized) {
    return res.status(401).json({ ok: false, error: 'Unauthorized' });
  }

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ ok: false, error: 'RESEND_API_KEY not configured' });
  }
  const resend = new Resend(apiKey);

  let jobs;
  try {
    jobs = await getDueDripJobs(50);
  } catch (e) {
    console.error('Failed to load drip jobs:', e.message);
    return res.status(500).json({ ok: false, error: 'Could not load drip queue' });
  }

  if (jobs.length === 0) {
    return res.status(200).json({ ok: true, processed: 0 });
  }

  const results = { sent: 0, skipped: 0, failed: 0 };

  for (const job of jobs) {
    const { entry, email, stepId } = job;

    try {
      // Skip if unsubscribed
      if (await isUnsubscribed(email)) {
        await removeDripJob(entry);
        results.skipped++;
        continue;
      }

      // Skip if subscriber record missing or not confirmed
      const sub = await getSubscriber(email);
      if (!sub || sub.status !== 'confirmed') {
        await removeDripJob(entry);
        results.skipped++;
        continue;
      }

      const builder = EMAIL_BUILDERS[stepId];
      if (!builder) {
        console.error(`Unknown drip step: ${stepId}`);
        await removeDripJob(entry);
        results.skipped++;
        continue;
      }

      const unsubToken = signUnsubscribeToken(email);
      const unsubscribeUrl = `${BASE_URL}/api/unsubscribe?t=${encodeURIComponent(unsubToken)}`;

      const { subject, html, text } = builder({
        baseUrl: BASE_URL,
        unsubscribeUrl,
      });

      const { error } = await resend.emails.send({
        from: FROM_ADDRESS,
        to: email,
        replyTo: 'Tutorspot98@gmail.com',
        subject,
        html,
        text,
        headers: {
          'List-Unsubscribe': `<${unsubscribeUrl}>`,
          'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
        },
      });

      if (error) {
        console.error(`Drip ${stepId} → ${email} failed:`, error.statusCode, error.name);
        // Keep the job in queue for retry on next cron run.
        // (Could add an attempt counter if persistent failures become an issue.)
        results.failed++;
        continue;
      }

      // Success — remove from queue
      await removeDripJob(entry);
      results.sent++;

    } catch (e) {
      console.error(`Drip job error for ${email}/${stepId}:`, e.message);
      results.failed++;
    }
  }

  return res.status(200).json({ ok: true, ...results });
};
