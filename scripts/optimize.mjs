#!/usr/bin/env node
/*
 * Post-processes the exported single-file app (source/index.html) into an
 * optimized static site in public/. Re-run whenever source/index.html changes:
 *
 *   npm --prefix scripts ci     # once, installs sharp
 *   node scripts/optimize.mjs
 *
 * The app's source isn't in this repo, so every change here is a careful
 * string transformation of the compiled HTML/JS/CSS. Each step fails loudly
 * if the pattern it expects is missing, rather than silently shipping a
 * half-optimized page.
 *
 * Outputs (regenerated each run): public/index.html, public/assets/*
 * Untouched: public/previews/* (maintained by hand)
 */
import { readFileSync, writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const SRC = join(ROOT, 'source', 'index.html');
const PUBLIC = join(ROOT, 'public');
const ASSETS = join(PUBLIC, 'assets');

const hash = (buf) => createHash('sha256').update(buf).digest('hex').slice(0, 10);
const kb = (n) => `${(n / 1024).toFixed(1)} KB`;

function fail(msg) {
  console.error(`optimize: ${msg}`);
  process.exit(1);
}

/* Writes a content-hashed file and returns its public URL. */
function emit(dir, name, ext, buf) {
  const file = `${name}.${hash(buf)}.${ext}`;
  writeFileSync(join(PUBLIC, dir, file), buf);
  return `/${dir}/${file}`;
}

/* Finds the `(0,x.jsx)("img",{...})` props object that contains `needle`. */
function imgPropsAround(js, needle) {
  const at = js.indexOf(needle);
  if (at < 0) fail(`image not found: ${needle.slice(0, 60)}`);
  const open = js.lastIndexOf('("img",{', at);
  if (open < 0) fail('could not locate <img> props for an embedded image');
  const start = open + '("img",'.length;
  let depth = 0;
  for (let i = start; i < js.length; i++) {
    if (js[i] === '{') depth++;
    else if (js[i] === '}' && --depth === 0) {
      // The props object must be the one that carries the needle (alt text).
      if (i < at) fail(`<img> props found for ${needle.slice(0, 40)} do not contain it`);
      return { start, end: i + 1 };
    }
  }
  fail('unterminated <img> props');
}

/* ─── Step 1: embedded photos → responsive WebP files ─────────────────────
   The three photos are base64 PNGs inside the JS. Each is matched by its alt
   text, decoded, re-encoded at the widths listed and wired up with srcSet and
   sizes. `sizes` reflects the *rendered* width: the CSS crops each photo with
   object-fit: cover at a fixed height, so the browser needs
   max(box width, box height × aspect ratio) pixels. */
const PHOTOS = [
  {
    alt: 'Case notes, a clinical study interface and a stethoscope on a desk',
    name: 'hero-desk',
    widths: [480, 800, 1200],
    quality: 80,
    // .hero-dossier is display:none ≤800px. There the 1px sizes slot makes the
    // browser pick the inline placeholder (declared 8w, so it satisfies screens
    // up to 8× density), so phones download nothing.
    sizes: '(max-width: 800px) 1px, (max-width: 1100px) 400px, 456px',
    hiddenOnMobile: true,
    preloadMedia: '(min-width: 801px)',
  },
  {
    alt: 'A reviewer annotating a SOAP note by hand',
    name: 'reviewer',
    widths: [660, 1000, 1400, 2000],
    quality: 78,
    sizes: '(max-width: 600px) 660px, (max-width: 800px) 800px, (max-width: 1100px) 1022px, 986px',
    lazy: true,
  },
  {
    alt: 'Practice questions, flashcards and a lime highlighter',
    name: 'exam-flatlay',
    widths: [420, 640, 840, 1200],
    quality: 78,
    sizes: '(max-width: 600px) 304px, (max-width: 800px) 356px, 408px',
    lazy: true,
  },
];
const BLANK = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';

async function extractPhotos(js, head) {
  const preloads = [];
  for (const photo of PHOTOS) {
    const { start, end } = imgPropsAround(js, `alt:"${photo.alt}"`);
    let props = js.slice(start, end);
    const m = props.match(/src:"data:image\/png;base64,([A-Za-z0-9+/=]+)"/);
    if (!m) fail(`no embedded PNG on "${photo.name}"`);
    const png = Buffer.from(m[1], 'base64');
    const meta = await sharp(png).metadata();

    const srcset = [];
    let fallback;
    for (const w of photo.widths.filter((w) => w <= meta.width)) {
      const buf = await sharp(png).resize({ width: w }).webp({ quality: photo.quality, effort: 6 }).toBuffer();
      const url = emit('assets', `${photo.name}-${w}`, 'webp', buf);
      srcset.push(`${url} ${w}w`);
      if (!fallback || w <= 1000) fallback = url;
      console.log(`  ${photo.name} ${w}w ${kb(buf.length)}`);
    }
    if (photo.hiddenOnMobile) srcset.unshift(`${BLANK} 8w`);

    props = props
      .replace(m[0], `src:"${fallback}",srcSet:"${srcset.join(', ')}",sizes:"${photo.sizes}"`)
      // The exported width/height attributes don't match the real image; fix the ratio.
      .replace(/width:"\d+"/, `width:"${meta.width}"`)
      .replace(/height:"\d+"/, `height:"${meta.height}"`);
    if (photo.lazy) {
      if (!/loading:"lazy"/.test(props)) props = props.replace(/^\{/, '{loading:"lazy",');
      if (!/decoding:/.test(props)) props = props.replace(/^\{/, '{decoding:"async",');
    }
    js = js.slice(0, start) + props + js.slice(end);

    if (photo.preloadMedia) {
      const real = srcset.filter((s) => !s.startsWith('data:')).join(', ');
      preloads.push(`<link rel="preload" as="image" imagesrcset="${real}" imagesizes="${photo.sizes}" media="${photo.preloadMedia}" fetchpriority="high">`);
    }
    console.log(`  ${photo.name}: ${meta.width}x${meta.height} PNG ${kb(png.length)} → ${srcset.length} srcset entries`);
  }
  return { js, head: head + preloads.join('') };
}

/* ─── Pipeline ───────────────────────────────────────────────────────── */
async function main() {
  const html = readFileSync(SRC, 'utf8');
  rmSync(ASSETS, { recursive: true, force: true });
  mkdirSync(ASSETS, { recursive: true });

  // Split the document: <head>…</head>, then the body with one inline app script.
  const headEnd = html.indexOf('</head>');
  const scriptOpen = html.indexOf('<script>', headEnd);
  const scriptClose = html.indexOf('</script>', scriptOpen);
  if (headEnd < 0 || scriptOpen < 0 || scriptClose < 0) fail('unexpected document shape');
  let head = html.slice(0, headEnd);
  const bodyStart = html.slice(headEnd, scriptOpen);
  let js = html.slice(scriptOpen + '<script>'.length, scriptClose);
  let tail = html.slice(scriptClose + '</script>'.length);

  console.log('Step 1: photos');
  ({ js, head } = await extractPhotos(js, head));

  const out = `${head}${bodyStart}<script>${js}</script>${tail}`;
  writeFileSync(join(PUBLIC, 'index.html'), out);
  console.log(`index.html ${kb(html.length)} → ${kb(Buffer.byteLength(out))}`);
}

main().catch((e) => fail(e.stack || String(e)));
