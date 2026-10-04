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

/* ─── Step 2: embedded fonts → /fonts/*.woff2 ─────────────────────────────
   The export inlines ten @font-face rules as base64, but Newsreader 400/500/600
   and IBM Plex Sans 400–700 are each one variable font repeated per weight.
   Content-hashed filenames collapse the repeats, so five files are downloaded
   instead of ten copies. Every weight is kept: Plex Sans 700 (bold <th> in the
   case tables) and Plex Mono 500 (reader-tab numbers) are used on case pages. */

// Fallback faces sized to match the web fonts, so the swap doesn't move text.
// Metrics come from the font files (fontTools) against Times New Roman / Arial
// (via their metric-compatible Liberation clones). Newsreader's width relative
// to Times varies with optical size (×1.09 at the 45px mobile h1, ×1.16 at the
// 73px desktop h1), so its size-adjust was tuned empirically: 112% gave the
// lowest CLS across 360–1920px with fonts delayed 1.5s (max 0.015); 113%+
// re-wraps the mobile h1. Re-tune if the fonts or the hero copy change.
const FALLBACKS = {
  Newsreader: {
    local: ['Times New Roman', 'Liberation Serif', 'Tinos'],
    css: 'size-adjust:112%;ascent-override:65.63%;descent-override:23.66%;line-gap-override:0%',
  },
  'IBM Plex Sans': {
    local: ['Arial', 'Liberation Sans', 'Arimo'],
    css: 'size-adjust:100.18%;ascent-override:102.32%;descent-override:27.45%;line-gap-override:0%',
  },
};
// Fonts the first screen paints with: hero h1 (Newsreader 500), "start here."
// (Newsreader 500 italic) and body copy (Plex Sans 400).
const PRELOAD = [
  ['Newsreader', '500', 'normal'],
  ['Newsreader', '500', 'italic'],
  ['IBM Plex Sans', '400', 'normal'],
];

function extractFonts(head) {
  mkdirSync(join(PUBLIC, 'fonts'), { recursive: true });
  const urls = {};
  let count = 0;
  head = head.replace(/@font-face\s*\{[^}]*\}/g, (rule) => {
    const family = rule.match(/font-family:\s*'([^']+)'/)?.[1];
    const weight = rule.match(/font-weight:\s*(\d+)/)?.[1];
    const style = rule.match(/font-style:\s*(\w+)/)?.[1] || 'normal';
    const data = rule.match(/url\(data:font\/woff2;base64,([A-Za-z0-9+/=]+)\)/);
    if (!family || !weight || !data) return rule;
    const buf = Buffer.from(data[1], 'base64');
    const slug = `${family.toLowerCase().replace(/\s+/g, '-')}${style === 'italic' ? '-italic' : ''}`;
    const url = emit('fonts', slug, 'woff2', buf);
    urls[`${family}|${weight}|${style}`] = url;
    count++;
    return rule.replace(data[0], `url(${url})`);
  });
  if (count === 0) fail('no embedded fonts found');
  const unique = new Set(Object.values(urls));
  console.log(`  ${count} @font-face rules → ${unique.size} files`);

  const fallbackCss = Object.entries(FALLBACKS)
    .map(([family, f]) => `@font-face{font-family:"${family} Fallback";src:${f.local.map((n) => `local("${n}")`).join(',')};${f.css}}`)
    .join('');
  const styleAt = head.indexOf('<style>');
  if (styleAt < 0) fail('no <style> block for fallback faces');
  head = head.slice(0, styleAt + 7) + fallbackCss + head.slice(styleAt + 7);

  // Put the fallback right after each web font in every font-family stack.
  let stacks = 0;
  for (const family of Object.keys(FALLBACKS)) {
    const re = new RegExp(`(font-family:\\s*(?:"${family}"|${family.includes(' ') ? `"${family}"` : family}))(?=\\s*,)`, 'g');
    head = head.replace(re, (m) => { stacks++; return `${m},"${family} Fallback"`; });
  }
  console.log(`  fallback faces added to ${stacks} font-family stacks`);

  const preloads = [...new Set(PRELOAD.map(([f, w, s]) => {
    const url = urls[`${f}|${w}|${s}`];
    if (!url) fail(`preload font missing: ${f} ${w} ${s}`);
    return url;
  }))].map((url) => `<link rel="preload" as="font" type="font/woff2" href="${url}" crossorigin>`);
  return head + preloads.join('');
}

/* ─── Pipeline ───────────────────────────────────────────────────────── */
async function main() {
  const html = readFileSync(SRC, 'utf8');
  for (const dir of ['assets', 'fonts']) rmSync(join(PUBLIC, dir), { recursive: true, force: true });
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

  console.log('Step 2: fonts');
  head = extractFonts(head);

  /* Step 3: CSS and JS become hashed, cacheable files referenced from <head>.
     The app script was a classic inline script after #root; `defer` keeps
     that ordering (it runs once the document is parsed). The preview add-on
     loads right after it, also deferred, instead of being discovered only
     at the end of the body. */
  console.log('Step 3: external CSS/JS');
  const style = head.match(/<style>([\s\S]*?)<\/style>/);
  if (!style) fail('no <style> block to extract');
  const cssUrl = emit('assets', 'app', 'css', Buffer.from(style[1]));
  const jsUrl = emit('assets', 'app', 'js', Buffer.from(js));
  head = head.replace(style[0], '');
  const PREVIEW_TAGS = /<link rel="stylesheet" href="\/previews\/cpl-previews\.css">|<script src="\/previews\/cpl-previews\.js" defer><\/script>/g;
  tail = tail.replace(PREVIEW_TAGS, '');
  head += `<link rel="stylesheet" href="${cssUrl}"><link rel="stylesheet" href="/previews/cpl-previews.css">` +
    `<script defer src="${jsUrl}"></script><script defer src="/previews/cpl-previews.js"></script>`;
  console.log(`  ${cssUrl} ${kb(style[1].length)}, ${jsUrl} ${kb(Buffer.byteLength(js))}`);

  const out = `${head}${bodyStart.replace(PREVIEW_TAGS, '')}${tail}`;
  writeFileSync(join(PUBLIC, 'index.html'), out);
  console.log(`index.html ${kb(html.length)} → ${kb(Buffer.byteLength(out))}`);
}

main().catch((e) => fail(e.stack || String(e)));
