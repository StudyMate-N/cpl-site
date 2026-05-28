"""
generate_sample_previews.py

Creates sample preview folders for all cases that do not have a real PDF.
Copies images from the category-matched real preview folder.
Creates meta.json for every preview folder (real and sample).

Run from project root:
    python scripts/generate_sample_previews.py
"""

import os
import json
import shutil
import sys

# ── Configuration ──────────────────────────────────────────────────
PREVIEWS_DIR = os.path.join('public', 'previews')
os.makedirs(PREVIEWS_DIR, exist_ok=True)

# Real guides confirmed built in Part 1
REAL_GUIDES = {
    'harvey-hoya-htn':                {'total_pages': 24},
    'bebe-babbitt-migraine':          {'total_pages': 25},
    'cynthia-francis-hyperlipidemia': {'total_pages': 21},
    # kennedy-poole-adhd added after Step 0 PDF conversion
}

# Category-to-source mapping
# Priority order: first matching tag wins
CATEGORY_MAP = [
    ('Cardiovascular',  'harvey-hoya-htn'),
    ('Neurologic',      'bebe-babbitt-migraine'),
    ('Endocrine',       'cynthia-francis-hyperlipidemia'),
    ('Mental Health',   'kennedy-poole-adhd'),
    ("Women's Health",  'bebe-babbitt-migraine'),
    ('Pediatric',       'samantha-graves-gastroenteritis'),
    ('Adolescent',      'kennedy-poole-adhd'),
    ('GU',              'christine-smith-pyelonephritis'),
    ('GI',              'samantha-graves-gastroenteritis'),
    ('Respiratory',     'harvey-hoya-htn'),
    ('Musculoskeletal', 'harvey-hoya-htn'),
    ('Geriatric',       'harvey-hoya-htn'),
    ('Dermatology',     'victoria-lewis-rash'),
    ('ENT',             'harvey-hoya-htn'),
    ('Shadow Health',   'harvey-hoya-htn'),
]

# Final fallback if no tag matches or source folder not available
ULTIMATE_FALLBACK = 'harvey-hoya-htn'

def get_sample_source(tags):
    """Return the best available source slug for a given tag list."""
    for tag, source in CATEGORY_MAP:
        if tag in tags:
            # Check if source folder actually has images
            source_path = os.path.join(PREVIEWS_DIR, source)
            if os.path.isdir(source_path) and os.path.exists(
                    os.path.join(source_path, 'page_1.png')):
                return source
            # Source not available yet -- try next match
            continue
    # Ultimate fallback
    fallback_path = os.path.join(PREVIEWS_DIR, ULTIMATE_FALLBACK)
    if os.path.isdir(fallback_path):
        return ULTIMATE_FALLBACK
    raise RuntimeError(f"Fallback source {ULTIMATE_FALLBACK} not available. "
                       "Run Part 1 first.")

def get_source_page_count(source_slug):
    """Read total_pages from meta.json of the source folder."""
    meta_path = os.path.join(PREVIEWS_DIR, source_slug, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            data = json.load(f)
        return data.get('total_pages', 24)
    # Fallback to known values
    return REAL_GUIDES.get(source_slug, {}).get('total_pages', 24)

def copy_sample_preview(source_slug, dest_slug, case_title):
    """Copy preview images from source to dest and create meta.json."""
    src_dir = os.path.join(PREVIEWS_DIR, source_slug)
    dst_dir = os.path.join(PREVIEWS_DIR, dest_slug)
    os.makedirs(dst_dir, exist_ok=True)

    # Copy all PNG files
    copied = 0
    for fname in sorted(os.listdir(src_dir)):
        if fname.endswith('.png'):
            shutil.copy2(
                os.path.join(src_dir, fname),
                os.path.join(dst_dir, fname)
            )
            copied += 1

    if copied == 0:
        print(f"  WARNING: No PNG files found in source {source_slug}")
        return False

    # Create meta.json
    total_pages = get_source_page_count(source_slug)
    sample_label = (
        f"Sample preview from a completed CPL guide. "
        f"Your {case_title} guide follows this exact format and structure."
    )
    meta = {
        "is_sample": True,
        "sample_source": source_slug,
        "total_pages": total_pages,
        "sample_label": sample_label
    }
    with open(os.path.join(dst_dir, 'meta.json'), 'w') as f:
        json.dump(meta, f, indent=2)

    return True

def ensure_real_meta(slug, total_pages):
    """Ensure meta.json exists for a real guide folder."""
    meta_path = os.path.join(PREVIEWS_DIR, slug, 'meta.json')
    if not os.path.exists(meta_path):
        with open(meta_path, 'w') as f:
            json.dump({
                "is_sample": False,
                "sample_source": None,
                "total_pages": total_pages,
                "sample_label": None
            }, f, indent=2)
        print(f"  Created meta.json for real guide: {slug}")

# ── Main ───────────────────────────────────────────────────────────

# Step A: Ensure meta.json exists for all real guides
print("Step A -- Verifying real guide meta.json files...")
for slug, info in REAL_GUIDES.items():
    ensure_real_meta(slug, info['total_pages'])

# Also handle kennedy-poole if its folder now exists
kp_path = os.path.join(PREVIEWS_DIR, 'kennedy-poole-adhd')
if os.path.isdir(kp_path) and os.path.exists(os.path.join(kp_path, 'page_1.png')):
    kp_meta = os.path.join(kp_path, 'meta.json')
    if not os.path.exists(kp_meta):
        # Count pages from actual images
        pages = len([f for f in os.listdir(kp_path) if f.endswith('.png')])
        ensure_real_meta('kennedy-poole-adhd', pages if pages > 0 else 40)
    REAL_GUIDES['kennedy-poole-adhd'] = {'total_pages': get_source_page_count('kennedy-poole-adhd')}
    print(f"  kennedy-poole-adhd detected as real guide")

# Step B: Add all cases from project
sys.path.insert(0, '.')
try:
    from cases_data import CASES
except ImportError:
    print("ERROR: Cannot import cases_data. Run this script from the project root.")
    sys.exit(1)

print(f"\nStep B -- Creating sample previews for all cases without real PDFs...")
print(f"  Total cases: {len(CASES)}")

real_count = 0
sample_count = 0
skipped_count = 0
errors = []

for case in CASES:
    slug = case['slug']
    title = case['title']
    tags = case.get('tags', [])
    dest_dir = os.path.join(PREVIEWS_DIR, slug)

    # Skip if already has a real guide preview
    if slug in REAL_GUIDES:
        real_count += 1
        print(f"  [REAL]    {slug}")
        continue

    # Skip if folder already exists with images (previously processed)
    if os.path.isdir(dest_dir) and os.path.exists(os.path.join(dest_dir, 'page_1.png')):
        skipped_count += 1
        print(f"  [EXISTS]  {slug}")
        continue

    # Create sample preview
    source = get_sample_source(tags)
    success = copy_sample_preview(source, slug, title)

    if success:
        sample_count += 1
        print(f"  [SAMPLE]  {slug:<55} <- {source}")
    else:
        errors.append(slug)
        print(f"  [FAILED]  {slug}")

# ── Summary ────────────────────────────────────────────────────────
print(f"""
================================================
SUMMARY
================================================
  Real guide previews:     {real_count}
  Sample previews created: {sample_count}
  Already existed:         {skipped_count}
  Errors:                  {len(errors)}
  Total preview folders:   {real_count + sample_count + skipped_count}
""")

if errors:
    print("ERRORS -- these cases need manual attention:")
    for e in errors:
        print(f"  - {e}")

# Final check -- list all preview folders
all_folders = sorted(os.listdir(PREVIEWS_DIR))
print(f"All preview folders ({len(all_folders)}):")
for folder in all_folders:
    folder_path = os.path.join(PREVIEWS_DIR, folder)
    if os.path.isdir(folder_path):
        files = os.listdir(folder_path)
        pngs = [f for f in files if f.endswith('.png')]
        has_meta = 'meta.json' in files
        print(f"  {folder:<55} {len(pngs)} pages  meta:{'Y' if has_meta else 'N'}")
