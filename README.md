# Clinical Performance Lab

**Brand:** Clinical Performance Lab (CPL)
**Tagline:** Clinical reasoning, case by case
**Primary product:** iHuman case guides ($150 / 3 for $390 / 5 for $540)
**Lead magnet:** 4 free cheat sheet PDFs (one per case stage)

This repo contains everything CPL needs to run as a self-contained static site
with a serverless email-capture backend.

---

## What's in here

```
cpl-site/
├── build.py                    # Orchestrator: pages, assets, manifests, ops, PDFs
├── web/                        # Public page templates (homepage v2 design system)
│   ├── layout.py               #   page shell, header, footer
│   ├── components.py           #   logo, icons, case cards, school strip data
│   └── pages.py                #   one builder per public page
├── src/                        # Front-end sources copied into public/
│   ├── site.css                #   design system → public/styles.css
│   ├── cpl*.js                 #   behaviour (cpl-home.js = homepage search/strip)
│   └── img/                    #   optimized WebP imagery
├── cases_data.py               # 171-case catalog
├── cheat_sheet_content.py      # Content for the 4 cheat sheet PDFs
├── cheat_sheet_flowables.py    # ReportLab diagrams (cardiac, SNOOP4, etc.)
├── generate_cheat_sheets.py    # PDF generator (Fraunces + Inter typography)
│
├── public/                     # ← Vercel deploys this directory
│   ├── index.html
│   ├── styles.css              # Brand stylesheet
│   ├── cpl.js                  # Front-end form handling
│   ├── favicon.svg
│   ├── sitemap.xml, robots.txt
│   ├── cheat-sheets/*.pdf      # 4 free PDFs (~78 KB each)
│   ├── case/{slug}/            # 171 case preview pages
│   ├── free-resources/         # Lead-magnet hub
│   ├── cases/                  # Catalog grid
│   ├── confirm/                # Token validation landing
│   ├── thank-you/              # Post-form landing
│   ├── about/, faq/, terms/, privacy/
│
├── api/                        # Vercel serverless functions
│   ├── _lib.js                 # HMAC tokens, KV helpers, rate limit
│   ├── subscribe.js            # POST: form → confirmation email
│   ├── confirm.js              # GET:  validate token, deliver PDFs, schedule drip
│   ├── unsubscribe.js          # GET:  one-click unsubscribe
│   └── cron/drip.js            # Hourly cron: send due drip emails
│
├── emails/                     # Email template modules
│   ├── _shell.js               # Branded HTML wrapper
│   ├── confirmation.js         # Email 1 (immediate)
│   ├── delivery.js             # Email 2 (after confirm)
│   ├── insight.js              # Email 3 (Day 2)
│   ├── intro.js                # Email 4 (Day 4)
│   └── offer.js                # Email 5 (Day 7, CPLFIRST15 code)
│
├── scripts/
│   └── test-tokens.js          # HMAC round-trip tests
│
├── vercel.json                 # Routes + cron schedule
├── package.json                # Node deps (resend, @vercel/kv)
└── .env.example                # Documented env vars
```

---

## Local development

```bash
# Build the entire site (HTML pages + PDFs)
python3 build.py

# Serve locally
python3 -m http.server 8000 --directory public
# Open http://localhost:8000

# Run token security tests
CPL_TOKEN_SECRET=$(openssl rand -hex 32) node scripts/test-tokens.js
```

API routes won't work in `python -m http.server` (no Node runtime). For local
API testing, use:

```bash
npm install -g vercel
vercel dev
```

`vercel dev` will load `.env.local` if present.

---

## Deployment to Vercel

### 1. One-time setup

```bash
# Install Vercel CLI
npm install -g vercel

# From this directory
vercel link        # Link to a Vercel project (create new if needed)
```

In the Vercel dashboard for your project:

**a. Add Vercel KV storage:**
- Storage tab → Create database → KV (Redis)
- Connect to the project
- Vercel auto-populates `KV_REST_API_URL`, `KV_REST_API_TOKEN`, etc.

**b. Set environment variables:**
```
RESEND_API_KEY          = re_xxxxxxxxxxxxxxxx        (from https://resend.com/api-keys)
CPL_TOKEN_SECRET        = <64-char hex>              (run: openssl rand -hex 32)
CPL_FROM_ADDRESS        = CPL <onboarding@resend.dev>
CPL_BASE_URL            = https://cpl-site.vercel.app
```

### 2. Deploy

```bash
vercel --prod
```

That's it. Vercel will:
- Run `python3 build.py` to generate the site
- Deploy `public/` as static assets
- Deploy `api/` as serverless functions
- Schedule the hourly drip cron from `vercel.json`

### 3. Verify

After first deploy, manually trigger the drip cron to confirm it works:

```bash
curl https://cpl-site.vercel.app/api/cron/drip \
  -H "x-vercel-cron: 1"
# Expected: {"ok":true,"processed":0}
```

Then test the full flow:
1. Visit `/free-resources/`, submit your email with 1+ volume selected
2. Check your inbox for the confirmation email
3. Click the confirm link
4. Verify the delivery email lands with PDF links
5. Click a PDF link — should download from `/cheat-sheets/*.pdf`

### 4. Resend setup (sender identity)

By default, emails are sent from `onboarding@resend.dev` (Resend's sandbox sender).
This works out of the box but emails may land in Promotions/spam.

To send from your own domain (e.g. `hello@clinicalperformancelab.com`):
1. In Resend → Domains → Add domain
2. Add the DNS records they provide (SPF, DKIM, optionally DMARC) to your DNS provider
3. Wait for verification (~5 minutes)
4. Update `CPL_FROM_ADDRESS` env var in Vercel:
   `CPL_FROM_ADDRESS = CPL <hello@clinicalperformancelab.com>`
5. Redeploy

---

## Architecture decisions

### Why HMAC tokens (not DB-stored confirm UUIDs)?

Standard pattern: generate UUID, store `{uuid → email}` in DB, lookup on confirm.

We sign tokens with HMAC-SHA256 instead. The token *contains* the email and
selected volumes, cryptographically signed. On confirm we just verify the
signature — no DB read. This means:
- No race conditions between subscribe and confirm
- Subscribe endpoint works without DB writes (KV is only touched on confirm)
- Tokens have an embedded expiry — 24h after issue
- Token tampering is detected via constant-time signature comparison

The tradeoff: tokens carry payload (longer URLs). Fine for an email link.

### Why drip-as-KV-list (not a proper job queue)?

Volume is low (hundreds of subscribers, not millions). Vercel KV's `lpush` /
`lrange` / `lrem` give us a simple FIFO. The hourly cron filters by `dueAt`
timestamp embedded in each entry, sends due ones, removes them from the list.

For 10,000+ subscribers, switch to a Redis sorted set with `ZADD score=dueAt`.

### Why no DB for subscribers?

Vercel KV stores `sub:{email} → {status, volumes, createdAt, confirmedAt}` with
90-day TTL. That's enough to:
- Prevent duplicate drips (check `status === 'confirmed'`)
- Resend delivery on repeat confirm
- Audit recent signups via KV browser

No analytics, no historical retention. The point isn't data; it's email delivery.

### Why double opt-in?

1. **Deliverability.** Single opt-in gets flagged by major email providers.
2. **Reduces typo signups** (someone enters `gmial.com`, gets no confirmation, fixes).
3. **CAN-SPAM compliance** is stronger with confirmed consent.

The tradeoff: ~20–30% of submitters never click the confirm link. We accept that.

### Why a one-time discount code (CPLFIRST15) instead of always-on pricing?

A static discount becomes the new price. A time-bounded code creates urgency
*and* tracks attribution (we can see who used the code at order time).

The 15% / $22.50 number is small enough to be a goodwill gesture, not a hit
to margins.

---

## Security checklist

- [x] HMAC-signed tokens (24h TTL) — no DB lookup for confirm
- [x] Email validation (regex + RFC 5321 length)
- [x] Volume allowlist (`history`/`physical-exam`/`ddx`/`plan` only)
- [x] HTML-escape user-supplied fields before email body interpolation
- [x] Rate limiting (5 subscribe / IP / hour, via KV)
- [x] List-Unsubscribe + List-Unsubscribe-Post one-click headers (Gmail compliance)
- [x] X-Content-Type-Options, X-Frame-Options, Referrer-Policy on API routes
- [x] Cron protected by `x-vercel-cron` header
- [x] No secrets in code (all via env vars)
- [x] Constant-time signature comparison (timing attack resistance)
- [x] Unsubscribe always honored — silently succeeds even after unsub
- [x] PII minimization — only email + 4-item volume list stored, 90-day TTL

---

## Public site — homepage v2 (October 2026)

The public front-end was rebuilt from the Claude Design "CPL Homepage v2"
handoff. Everything public is generated from `web/` + `src/`; the API,
emails, ops console (`src/ops/`), case data and PDFs are unchanged.

- **Design tokens** live at the top of `src/site.css` (lime/ink palette,
  Newsreader + IBM Plex Sans + IBM Plex Mono). Change a color or spacing
  value there and it applies site-wide.
- **Homepage** (`web/pages.py → build_home`): live case search (reads
  `/cases.json`), "what's on your mind" chips, a moving school strip with
  per-school panels, featured same-day cases, services, human support,
  exam path and a mobile quick-action dock.
- **Schools** in the strip are configured in `web/components.py → SCHOOLS`
  (name, brand color, catalog match text). Case counts come from the catalog.
- **Checkout, access codes, support chat, bundles and free-resource capture**
  keep their existing DOM contracts and API calls.

To regenerate the site without changing the existing PDFs:

```bash
python3 build.py --skip-pdfs
```

Commit the generated `public/` pages and assets with the source changes.
The existing main-branch GitHub Actions workflow deploys them to Vercel.
Bump `ASSET_VERSION` in `build.py` when CSS/JS changes so browsers refetch.
Bundle requests preserve every selected case; intake uses the bundle price rather than a fuzzy single-case match. Run `npm run test:orders` to check this flow with storage and email mocked.
The simulator remains a waitlist. Search includes aliases, but patient age,
presentation and course must be checked to match a guide version.

## Maintenance

### Add a new case to the catalog

Edit `cases_data.py`, append to `CASES` list with all fields populated. Then:
```bash
python3 build.py
vercel --prod
```

The new case auto-generates:
- `/case/{slug}/` preview page
- An entry on `/cases/`
- A sitemap.xml entry

### Edit the drip sequence content

Edit the relevant module in `emails/` (`insight.js`, `intro.js`, `offer.js`).
No DB migration needed — the cron always builds fresh content per send.

Redeploy with `vercel --prod`.

### Change the drip schedule (e.g. shorten/lengthen delays)

Edit `DRIP_STEPS` in `api/_lib.js`:
```js
const DRIP_STEPS = [
  { id: 'insight', delayHours: 48, ... },   // Day 2 → change this number
  { id: 'intro',   delayHours: 96, ... },   // Day 4
  { id: 'offer',   delayHours: 168, ... },  // Day 7
];
```

Note: this affects only *new* subscriptions. Already-scheduled drip jobs in KV
keep their original `dueAt`.

### Manually trigger drip cron (debugging)

```bash
# In Vercel env vars, set:
CRON_SECRET=somerandomstring

# Then trigger:
curl "https://cpl-site.vercel.app/api/cron/drip?secret=somerandomstring"
```

### See current KV contents

In Vercel dashboard → Storage → your KV → Data Browser. Useful keys:
- `sub:{email}` — subscriber records
- `drip:scheduled` — pending drip jobs list
- `unsub:{email}` — unsubscribed addresses
- `rl:ip:{ip}` — per-IP rate limit counters

### Update copyright year / footer text

Edit `web/layout.py` → `footer_html()`.

---

## Pricing

| Tier | Price | Saves | Use |
|---|---|---|---|
| Single guide | $150 | — | Pick one case, single delivery |
| 3-case bundle | $390 | $60 | Mid-term, multiple cases |
| 5-case bundle | $540 | $210 | Full term, best value |

**Discount code:** `CPLFIRST15` — 15% off first single case ($22.50 off).
Sent in Email 5 of the drip sequence (Day 7).
One-time use per email. Bundles already discounted.

---

## Contact

- **Operations:** Tutorspot98@gmail.com
- **Brand domain:** www.clinicalperformancelab.com
- **GitHub:** StudyMate-N/cpl-site · **Vercel project:** cpl-site

---

## Current public interactions

- Homepage search sends the query to the case library. Course shortcuts use the same URL query.
- The library searches patients, presentations, institutions, courses and aliases. Filters and queries remain in the URL; results load 24 at a time.
- Bundle selection calculates existing pricing tiers and submits all selected case titles. Order intake calculates bundle pricing before saving the request.
- Native checkboxes select the free PDFs. Forms handle validation, submission errors, confirmation and double opt-in delivery through the existing API routes.
- Guide-page previews open in a keyboard-accessible dialog. Mobile navigation and checkout return focus to the control that opened them.
- The simulator page collects its launch waitlist. Support quick answers describe actual availability and case-version checks.

The public pages keep their existing URLs. Case-specific history excerpts are published only when explicitly supplied in the catalog data; unrelated preview pages are identified as examples of the format.
