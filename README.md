# Clinical Performance Lab

The CPL website: a single self-contained page (`public/index.html`) with the
case library, complete case package, live walkthroughs, editing requests and
the request-to-delivery journey. Fonts and images are embedded in the file.

## Deploy

Vercel's GitHub integration deploys `public/` on every push to `main`.
`vercel.json` sends every path to `index.html`, so in-app links such as
`/case/bebe-babbit` work on reload.

## Requests

There is no server backend. The request journey builds an email to
`support@unemployedproff.com` with a CPL reference in the subject.

## Local preview

```bash
python3 -m http.server 8000 --directory public
```
