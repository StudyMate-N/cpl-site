# Clinical Performance Lab — V3

**Brand:** Clinical Performance Lab (CPL)
**Tagline:** Submission-ready clinical reasoning for nursing students
**Primary product:** iHuman case guides ($150 / 3 for $390 / 5 for $540)
**Lead magnet:** 4 free cheat sheet PDFs (one per case stage)

This repo contains everything CPL needs to run as a self-contained static site
with a serverless email-capture backend.

---

## What's in here

```
cpl-v3/
├── build.py                    # Generates static site + cheat sheets
├── cases_data.py               # 16-case product catalog
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
│   ├── case/{slug}/            # 16 case preview pages
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
CPL_BASE_URL            = https://clinicalperformancelab.vercel.app
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
curl https://clinicalperformancelab.vercel.app/api/cron/drip \
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
curl "https://clinicalperformancelab.vercel.app/api/cron/drip?secret=somerandomstring"
```

### See current KV contents

In Vercel dashboard → Storage → your KV → Data Browser. Useful keys:
- `sub:{email}` — subscriber records
- `drip:scheduled` — pending drip jobs list
- `unsub:{email}` — unsubscribed addresses
- `rl:ip:{ip}` — per-IP rate limit counters

### Update copyright year / footer text

Edit `build.py` → `footer_html()`.

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
- **Brand domain:** clinicalperformancelab.vercel.app
- **GitHub / Vercel project:** (configure via `vercel link`)

---

## Phase 3 — Dynamic site layer

Phase 3 added interactive JavaScript functionality on top of the static HTML foundation. All pages remain static HTML for SEO/performance, but `cpl.js` wires in client-side dynamism after load.

### What changed

**Case catalog (`/cases/`):**
- Unified grid — no more "coming soon" split. All 16 cases orderable today.
- Live search box (debounced 100ms) — searches title, CC, diagnosis, course, aliases
- 3-row filter rail — School · System · Lead Time. Click to toggle. "Clear filters" appears only when active.
- Live result counter ("Showing N of 16 cases")
- Empty state with "Show all cases" reset button

**Bundle Builder (bottom of /cases/):**
- Two-column interactive builder — click cases on the left, pricing updates on the right
- Pricing tiers: 1=$150, 2=$280, 3=$390, 4=$470, 5=$540, beyond=$540+$80/case
- Live save calculation with strikethrough original price
- "Order this bundle →" generates prefilled mailto with case list
- Selection persists in localStorage (survives page refresh)
- Mobile: stacks to single column, cart below pool

**Case preview pages:**
- ⚡ / ⌛ lead-time badge in hero eyebrow
- Scoring trap callouts reveal on scroll with configurable stagger delay
- "Recently viewed" sidebar block appears after navigating 2+ cases
- Sticky sidebar gains box-shadow after 200px scroll

**Site-wide:**
- Scroll-reveal animations on hero elements (`data-reveal` attribute + `is-revealed` class)
- Animated number counters (`data-counter` attribute) with easeOutCubic
- All animations respect `prefers-reduced-motion`

**Engagement popup:**
- Scores session engagement (time on page, scroll depth, pages visited, case clicks, returning visitor)
- Fires when score ≥ 6, after 5s minimum on page
- Suppressed for 30 days after subscribe (localStorage)
- ESC, click-outside, × button all close it; suppressed for the session after close

**Exit-intent capture:**
- Arms after 8s on case-preview pages
- Fires popup when cursor exits top of viewport
- Suppressed if popup already shown this session

### Architecture of `cpl.js`

Source lives in `src/cpl.js` (759 lines). `build.py`'s `build_js()` copies it to `public/cpl.js`.

9 self-contained modules inside an IIFE:

```
reveal       — IntersectionObserver + CSS class toggle
counters     — requestAnimationFrame easeOutCubic ticker
catalog      — filter state machine + live DOM hide/show
bundle       — case selection Set, pricing lookup, mailto generator
recent       — localStorage read/write + DOM injection
popup        — engagement scorer + form submit handler
exitIntent   — mouseleave listener (case pages only)
forms        — resource card checkbox toggling + lead-magnet AJAX
sticky       — scroll listener for sidebar shadow
```

Exposed at `window.cpl` for debugging. E.g.:

```javascript
// Force the popup to fire (useful for testing)
window.cpl.popup.fire('manual-test');

// Add a case to the bundle builder
window.cpl.bundle.addCaseBySlug('harvey-hoya-htn');

// Check if subscriber
window.cpl.isSubscribed();  // → true/false
```

### Adding / editing a case

Edit `cases_data.py` → set `"lead_time": "same-day"` for battle-tested cases, `"fast-build"` for on-demand.
The filter data attributes are auto-generated during build from `tags`, `course`, and `school` fields.

```bash
python3 build.py && vercel --prod
```

### Tuning the engagement popup threshold

In `src/cpl.js`, find `const FIRE_THRESHOLD = 6;` and the score breakdown:

```javascript
+1  if time on page ≥ 15s
+2  if scroll depth ≥ 40%
+3  if scroll depth ≥ 75%
+3  if visited ≥ 2 pages this session
+5  if clicked a case card
+2  if returning visitor
```

Lower `FIRE_THRESHOLD` for more aggressive capture, raise it for less interruption.
After editing `src/cpl.js`, run `python3 build.py` to copy it to `public/cpl.js`.
