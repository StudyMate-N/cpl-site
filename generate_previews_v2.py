#!/usr/bin/env python3
"""
generate_previews_v2.py  (CPL V2 overhaul, file 01)

Two tracks:

TRACK A -- Real previews for the 3 completed cases.
  Uses data/preview_maps.json to render ONE clear page per major section
  (cover, history, PE, DDx) at 200 DPI, plus 3 blurred "teaser" pages for
  the locked stack. Writes a rich meta.json with clear_pages / blurred_pages
  / stack_blurred / section_labels.

TRACK B -- Sample previews for every other case.
  Generates watermarked ("EXAMPLE -- Format from another case") versions of
  each source's 4 clear section pages into public/previews/_watermarked/{src}/
  as sample_1..4.png. Then for every non-real case, picks a source via a
  deterministic hash of the slug (even spread across the 3 sources) and writes
  a meta.json that names the real source case honestly. The per-slug folders no
  longer hold misleading copied cover pages -- only meta.json.
"""
import os, json, math
import fitz  # PyMuPDF
from PIL import Image, ImageFilter, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
GUIDES_DIR = os.path.join(ROOT, "_guides_src", "CPL_Complete_Guides")
PREVIEWS_DIR = os.path.join(ROOT, "public", "previews")
WATERMARK_DIR = os.path.join(PREVIEWS_DIR, "_watermarked")
MAPS_PATH = os.path.join(ROOT, "data", "preview_maps.json")

SLUG_TO_PDF = {
    "harvey-hoya-htn": "Harvey_Hoya_iHuman_Complete_Guide.pdf",
    "bebe-babbitt-migraine": "Bebe_Babbitt_iHuman_Complete_Guide.pdf",
    "cynthia-francis-hyperlipidemia": "Cynthia_Francis_iHuman_Complete_Guide.pdf",
}

# Human-readable titles for honest sample labelling
SOURCE_TITLES = {
    "harvey-hoya-htn": "Harvey Hoya - Hypertension Stage 2",
    "bebe-babbitt-migraine": "Bebe Babbitt - Migraine with Aura",
    "cynthia-francis-hyperlipidemia": "Cynthia Francis - Hyperlipidemia",
}

SAMPLE_SOURCES = [
    "harvey-hoya-htn",
    "bebe-babbitt-migraine",
    "cynthia-francis-hyperlipidemia",
]

CLEAR_DPI = 200
BLUR_DPI = 150
BLUR_RADIUS = 18
WATERMARK_TEXT = "EXAMPLE - Format from another case"


def pick_sample_source(case_slug):
    """Deterministic, evenly-spread source assignment for a sample case."""
    h = sum(ord(c) for c in case_slug)
    return SAMPLE_SOURCES[h % len(SAMPLE_SOURCES)]


def render_page(doc, page_index, dpi):
    page = doc[page_index]
    pix = page.get_pixmap(dpi=dpi)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


def _load_font(size):
    for path in (
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def watermark_image(img, text=WATERMARK_TEXT):
    """Tile a semi-transparent diagonal watermark across the page."""
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    font = _load_font(34)
    w, h = img.size
    for y in range(-h, h * 2, 230):
        for x in range(-w, w * 2, 360):
            tile = Image.new("RGBA", (520, 90), (255, 255, 255, 0))
            ImageDraw.Draw(tile).text((10, 28), text, fill=(200, 50, 50, 110), font=font)
            tile = tile.rotate(30, expand=1)
            overlay.paste(tile, (x, y), tile)
    return Image.alpha_composite(img, overlay).convert("RGB")


def clean_dir_pngs(d):
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.endswith(".png"):
                os.remove(os.path.join(d, f))


# ── Track A ──────────────────────────────────────────────────────────
def build_real_previews(maps):
    print("Track A -- real previews")
    for slug, pdf_name in SLUG_TO_PDF.items():
        cfg = maps[slug]
        out_dir = os.path.join(PREVIEWS_DIR, slug)
        os.makedirs(out_dir, exist_ok=True)
        clean_dir_pngs(out_dir)

        doc = fitz.open(os.path.join(GUIDES_DIR, pdf_name))
        total = cfg["total_pages"]
        clear = cfg["clear"]
        blurred = cfg["blurred"]
        stack_blurred = blurred[:3]

        for n in clear:
            img = render_page(doc, n - 1, CLEAR_DPI)
            img.save(os.path.join(out_dir, f"page_{n}.png"), "PNG", optimize=True)

        for n in stack_blurred:
            img = render_page(doc, n - 1, BLUR_DPI).filter(
                ImageFilter.GaussianBlur(radius=BLUR_RADIUS)
            )
            img.save(os.path.join(out_dir, f"page_{n}_blurred.png"), "PNG", optimize=True)
        doc.close()

        meta = {
            "is_sample": False,
            "sample_source": None,
            "total_pages": total,
            "clear_pages": clear,
            "blurred_pages": blurred,
            "stack_blurred": stack_blurred,
            "section_labels": cfg["section_labels"],
            "watermarked": False,
            "sample_label": None,
        }
        with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        print(f"  [REAL] {slug}: clear {clear} + stack {stack_blurred}")


# ── Track B ──────────────────────────────────────────────────────────
def build_watermarked_sources(maps):
    print("Track B -- watermarked source pages")
    for src in SAMPLE_SOURCES:
        cfg = maps[src]
        pdf_name = SLUG_TO_PDF[src]
        out_dir = os.path.join(WATERMARK_DIR, src)
        os.makedirs(out_dir, exist_ok=True)
        clean_dir_pngs(out_dir)
        doc = fitz.open(os.path.join(GUIDES_DIR, pdf_name))
        # sample_1..4 map to the 4 clear section pages
        for idx, n in enumerate(cfg["clear"], start=1):
            img = render_page(doc, n - 1, BLUR_DPI)
            img = watermark_image(img)
            img.save(os.path.join(out_dir, f"sample_{idx}.png"), "PNG", optimize=True)
        doc.close()
        print(f"  [WM] {src}: 4 watermarked sample pages")


def build_sample_metas(maps, all_slugs):
    print("Track B -- sample meta.json for non-real cases")
    counts = {s: 0 for s in SAMPLE_SOURCES}
    for slug in all_slugs:
        if slug in SLUG_TO_PDF:
            continue
        src = pick_sample_source(slug)
        counts[src] += 1
        out_dir = os.path.join(PREVIEWS_DIR, slug)
        os.makedirs(out_dir, exist_ok=True)
        clean_dir_pngs(out_dir)  # drop old misleading copied cover pages
        src_title = SOURCE_TITLES[src]
        meta = {
            "is_sample": True,
            "sample_source": src,
            "source_title": src_title,
            "total_pages": maps[src]["total_pages"],
            "watermarked": True,
            "sample_label": (
                f"Sample - format only. These are stamped excerpts from a "
                f"different completed case ({src_title}). Your guide will follow "
                f"the same structure with its own case-specific content."
            ),
        }
        with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
    print(f"  source distribution: {counts}")


def main():
    with open(MAPS_PATH, encoding="utf-8") as f:
        maps = json.load(f)

    # Import the catalog to get every slug
    import sys
    sys.path.insert(0, ROOT)
    from cases_data import CASES
    all_slugs = [c["slug"] for c in CASES]

    os.makedirs(PREVIEWS_DIR, exist_ok=True)
    build_real_previews(maps)
    build_watermarked_sources(maps)
    build_sample_metas(maps, all_slugs)
    print(f"\nDone. {len(all_slugs)} cases processed "
          f"({len(SLUG_TO_PDF)} real, {len(all_slugs) - len(SLUG_TO_PDF)} sample).")


if __name__ == "__main__":
    main()
