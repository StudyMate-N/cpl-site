# Clinical Performance Lab

The CPL website: the case library, complete case package, live walkthroughs,
editing requests and the request-to-delivery journey, plus guide previews.

## Layout

```
source/index.html        the app as exported (single file, images/fonts inlined) — edit/replace this
scripts/optimize.mjs     turns source/index.html into the optimized site below
public/index.html        generated: tiny HTML shell
public/assets/           generated: app.<hash>.js, app.<hash>.css, responsive WebP photos
public/fonts/            generated: hashed woff2 files
public/previews/         hand-maintained: guide preview pages + cpl-previews.js/.css
vercel.json              SPA rewrite + cache headers
```

## Updating the app

When a new export of the app arrives, replace `source/index.html` and run:

```bash
npm --prefix scripts ci        # once: installs sharp (image encoding)
node scripts/optimize.mjs      # regenerates public/index.html, assets/, fonts/
```

Commit `source/` and `public/` together. The script stops with an error if
the export's shape changes (e.g. a photo's alt text), rather than shipping a
half-optimized page. Photo widths, `sizes`, preloaded fonts and the fallback
font metrics are configured at the top of each step in the script.

## Deploy

Vercel's GitHub integration deploys `public/` on every push (production from
`main`, previews from other branches). There is no build step on Vercel.
`vercel.json` sends every path to `index.html`, so in-app links such as
`/case/bebe-babbit` work on reload. Hashed files in `/assets` and `/fonts`
are cached for a year; `/previews` for a day.

## Requests

There is no server backend. Request buttons open a WhatsApp/email chooser
with the case details pre-filled (WhatsApp +1 205 727 9363,
`support@unemployedproff.com`).

## Local preview

```bash
python3 -m http.server 8000 --directory public
```
