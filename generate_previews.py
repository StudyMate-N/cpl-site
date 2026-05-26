#!/usr/bin/env python3
"""
Generate blurred PDF preview images for case pages.
Rule: Show exactly ceil(total_pages * 0.15) pages.
  Page 1 = clear (150 DPI PNG)
  Pages 2..N = Gaussian blur radius 18 (150 DPI PNG)
"""
import os, math
import fitz  # PyMuPDF
from PIL import Image, ImageFilter

GUIDES_DIR = r"C:\Users\USER\Desktop\Projects\Project CPL\_guides_src\CPL_Complete_Guides"
OUTPUT_DIR = r"C:\Users\USER\Desktop\Projects\Project CPL\public\previews"

# Map: case-slug -> PDF filename (use the primary name for each alias cluster)
SLUG_TO_PDF = {
    "harvey-hoya-htn": "Harvey_Hoya_iHuman_Complete_Guide.pdf",
    "bebe-babbitt-migraine": "Bebe_Babbitt_iHuman_Complete_Guide.pdf",
    "cynthia-francis-hyperlipidemia": "Cynthia_Francis_iHuman_Complete_Guide.pdf",
    # Kennedy Poole DOCX is corrupted - skip for now
}

DPI = 150
BLUR_RADIUS = 18


def generate_preview(slug, pdf_filename):
    pdf_path = os.path.join(GUIDES_DIR, pdf_filename)
    out_dir = os.path.join(OUTPUT_DIR, slug)
    os.makedirs(out_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    total_pages = doc.page_count
    preview_count = max(2, math.ceil(total_pages * 0.15))

    print(f"  {slug}: {total_pages} pages, showing {preview_count} preview pages")

    for i in range(preview_count):
        page = doc[i]
        pix = page.get_pixmap(dpi=DPI)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        if i > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))

        out_path = os.path.join(out_dir, f"page_{i + 1}.png")
        img.save(out_path, "PNG", optimize=True)

    doc.close()
    return preview_count


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Generating PDF previews...")

    for slug, pdf_file in SLUG_TO_PDF.items():
        count = generate_preview(slug, pdf_file)
        print(f"    -> {count} images saved to public/previews/{slug}/")

    print("\nDone.")
