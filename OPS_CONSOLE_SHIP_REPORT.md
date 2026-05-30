# CPL Ops Console — Ship Report

**Date:** 2026-05-30
**Status:** ✅ Live in production at `https://www.clinicalperformancelab.com/ops/`
**Scope:** Turned the approved demo front-end into a real, deployed fulfillment tool.
Payoneer stays a manual paste (out of scope, by decision).

---

## 1. New environment variables

| Var | Where it came from | Purpose |
|---|---|---|
| `OPS_PASSCODE` | set by owner | console login gate (constant-time check) |
| `RESEND_WEBHOOK_SECRET` | the inbound webhook's signing secret (`whsec_…`) | verify Resend Svix signature on `/api/ops/inbound` |
| `KV_REST_API_URL` / `KV_REST_API_TOKEN` (+`KV_URL`,`REDIS_URL`,`…READ_ONLY_TOKEN`) | Upstash Redis store **cpl-ops-kv** (created + linked) | order persistence, magic-link + access-code maps, login rate-limit |
| `BLOB_READ_WRITE_TOKEN` (+`BLOB_STORE_ID`,`BLOB_WEBHOOK_PUBLIC_KEY`) | Vercel Blob store **cpl-guides** (created + linked) | uploaded guide file storage |

Reused unchanged: `RESEND_API_KEY`, `CPL_TOKEN_SECRET` (**not rotated** — sessions + magic
links derive *namespaced* sub-keys from it), `CPL_FROM_ADDRESS`, `CPL_BASE_URL`, `CPL_REPLY_TO`.

> **Note:** an Upstash Redis (`cpl-ops-kv`) was provisioned. This also means the
> subscriber drip flow now has a *real* KV (previously it was silently using an
> in-memory dev fallback).

## 2. Storage choice

- **Orders + tokens → Upstash Redis (Vercel KV)** — `order:<id>`, `ops:index` (list),
  `ops:seq` (monotonic id), `g:<token>→{orderId,exp}`, `code:<CODE>→orderId`. Low volume;
  migratable to Postgres later.
- **Guide files → Vercel Blob** (`cpl-guides`, public) under `guides/<orderId>/…`.

## 3. Routes added (all `/api/ops/*` gated by signed httpOnly cookie)

| Route | Purpose |
|---|---|
| `POST /api/ops/auth` `{action:login\|logout}` / `GET` | login (constant-time + rate-limit), logout, session check |
| `GET /api/ops/orders` | list orders, newest first |
| `POST /api/ops/inbound` | **public**, Svix-verified Resend webhook → create order + send `orderReceived`+`adminAlert` |
| `POST /api/ops/orders/:id/:action` | `invoice` · `confirm-payment` · `deliver` · `resend` |
| `GET /g/:token` | **public** magic link → verify HMAC+30d expiry → branded download page |

(Routes consolidated to stay within Vercel's 12-function limit; URLs unchanged.)
Server email templates ported to `emails/ops-emails.js`; console mounted from
`src/ops/` → `public/ops/` (`OPS.mode='live'`, real auth, **LIVE** badge, Simulate hidden).
Catalog manifest `public/cases.json` (171 cases; 6 pre-built) emitted by `build.py`.

## 4. Real test order, end-to-end (with Resend message IDs)

A real email was sent from Gmail → `orders@clinicalperformancelab.com`,
subject `CPL Order - Harvey Hoya — Hypertension Stage 2`:

1. **Intake** — Resend MX → Svix-signed webhook → `/api/ops/inbound` created **CPL-1055**
   (`ready=true` via catalog lookup, chief-complaint auto-filled). Emails:
   - `orderReceived` → customer: `c59b4875-e775-4191-8a90-2ed54e60ce64`
   - `adminAlert` → orders@: `87c92587-f6d1-4056-af98-c232ccb00b17`
2. **Invoice** → status `invoiced`, email `06771429-977d-41ae-aa4b-bc3aea81e012`
3. **Confirm-payment** (pre-built → auto-deliver) → status `fulfilled`, access code
   `CPL-W2PD` minted, delivery email `dbe76a1a-bd85-4f98-8dba-0f4b980075f0`

The **build path** was also walked (CPL-1052, Ben Bundy COPD): invoice → confirm-payment
(`building`) → **deliver** (file uploaded to Blob, 102 B) → `fulfilled`, delivery email
`376120b1-e18f-4f08-95b1-7c846bcdf329`.

## 5. Magic link — serves a stored file + rejects a tampered token

- **Valid** `/g/<token>` (build order) → `200`, lists the file, shows access code, and the
  stored blob (`…public.blob.vercel-storage.com/guides/CPL-1052/…`) downloads with the exact
  uploaded content.
- **Tampered** token (one char flipped) → `403`.
- **Ready** order with no uploaded asset → `200` with a "guide is being attached" notice.

## 6. Security checks

- Auth gate: no cookie → `401`; wrong passcode → `401`; correct → `200` + `HttpOnly; Secure; SameSite=Strict` cookie. Login rate-limited (8 / 15 min).
- Webhook: **wrong Svix signature → `401`**, valid → `200`. (`RESEND_WEBHOOK_SECRET` enforced.)
- Resend domain `clinicalperformancelab.com` confirmed **Verified** before deploy.
- `CPL_TOKEN_SECRET` not rotated; subscriber drip flow untouched.

## 7. Notes / follow-ups

- **Test data:** 4 test orders (CPL-1052…1055) live in the queue from this validation.
  Harmless; can be cleared on request (no delete UI was built — out of scope).
- **Pre-built assets:** "ready" cases auto-deliver a magic link/code, but no guide *files*
  exist in storage yet, so their `/g` page shows the "being attached" notice until a file is
  uploaded (via the deliver step) or pre-built assets are added.
- **Passcode:** `OPS_PASSCODE` is 4 digits; rate-limiting mitigates brute force, but a longer
  passcode is recommended when convenient (change it in Vercel env → redeploy).
- Two Blob stores are linked (`Robbb` unused, `cpl-guides` active); harmless.
