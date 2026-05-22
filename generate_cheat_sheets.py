"""
Generates the four CPL cheat sheet PDFs from cheat_sheet_content.py.
Premium typography (Fraunces + Inter), brand-consistent (CPL teal/lime),
designed to be screenshot-worthy and shareable.

Usage:
    python3 generate_cheat_sheets.py
    → Outputs to ./public/cheat-sheets/
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, HRFlowable, ListFlowable, ListItem, Image as RLImage
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from cheat_sheet_content import ALL_VOLUMES, VOLUME_META
from cheat_sheet_flowables import (
    CaseStageMap, SnoopMnemonic, CentorCriteria, OldcartsMnemonic,
    CardiacAuscultationDiagram, AbdominalQuadrants, LungFieldsDiagram,
    ProblemStatementStructure, CTABox, FinalCTACard, MedDosingCard,
    SixPartPlanVisual,
)

# ─── Output directory ─────────────────────────────────────────────────
OUT_DIR = os.path.join(os.path.dirname(__file__), "public", "cheat-sheets")
os.makedirs(OUT_DIR, exist_ok=True)

# ─── Brand colors ─────────────────────────────────────────────────────
TEAL_900 = HexColor("#064E45")
TEAL_800 = HexColor("#0A6358")
TEAL_700 = HexColor("#0F7A6B")
TEAL_600 = HexColor("#0D9E85")
TEAL_500 = HexColor("#14B896")
LIME_500 = HexColor("#B7E04E")
LIME_400 = HexColor("#C7E96B")
CREAM = HexColor("#FAF7F0")
CREAM_2 = HexColor("#F4EFE2")
INK = HexColor("#0B1F1B")
INK_2 = HexColor("#1F3530")
MUTED = HexColor("#5C6E69")
BORDER = HexColor("#E4DCC8")
BORDER_STRONG = HexColor("#D2C7A8")
TRAP_RED = HexColor("#C44")
TRAP_AMBER = HexColor("#946115")
WARM_BG = HexColor("#FFFCF5")
WHITE = HexColor("#FFFFFF")

# ─── Try to register Fraunces + Inter; fall back to built-in if not available ──
USE_CUSTOM_FONTS = False
try:
    import urllib.request

    # Download Inter if not already cached
    font_cache = os.path.join(os.path.dirname(__file__), ".fonts")
    os.makedirs(font_cache, exist_ok=True)

    # Direct TTF URLs from Google Fonts CDN (resolved from CSS, May 2026)
    fonts_to_get = {
        "Inter-Regular.ttf":   "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfMZg.ttf",
        "Inter-SemiBold.ttf":  "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuI6fMZg.ttf",
        "Inter-Bold.ttf":      "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuFuYMZg.ttf",
        "Inter-Italic.ttf":    "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfMZg.ttf",  # fallback to Regular if no italic available
        "Fraunces-Regular.ttf":  "https://fonts.gstatic.com/s/fraunces/v38/6NUh8FyLNQOQZAnv9bYEvDiIdE9Ea92uemAk_WBq8U_9v0c2Wa0K7iN7hzFUPJH58nib1603gg7S2nfgRYIctxujDg.ttf",
        "Fraunces-SemiBold.ttf": "https://fonts.gstatic.com/s/fraunces/v38/6NUh8FyLNQOQZAnv9bYEvDiIdE9Ea92uemAk_WBq8U_9v0c2Wa0K7iN7hzFUPJH58nib1603gg7S2nfgRYIcaRyjDg.ttf",
        "Fraunces-Italic.ttf":   "https://fonts.gstatic.com/s/fraunces/v38/6NUh8FyLNQOQZAnv9bYEvDiIdE9Ea92uemAk_WBq8U_9v0c2Wa0K7iN7hzFUPJH58nib1603gg7S2nfgRYIctxujDg.ttf",  # fallback
    }
    for fname, url in fonts_to_get.items():
        path = os.path.join(font_cache, fname)
        if not os.path.exists(path):
            try:
                urllib.request.urlretrieve(url, path)
            except Exception as e:
                print(f"  ⚠ Could not fetch {fname}: {e}")

    # Register if all downloaded successfully
    all_present = all(os.path.exists(os.path.join(font_cache, f)) for f in fonts_to_get)
    if all_present:
        pdfmetrics.registerFont(TTFont("Inter", os.path.join(font_cache, "Inter-Regular.ttf")))
        pdfmetrics.registerFont(TTFont("Inter-Bold", os.path.join(font_cache, "Inter-Bold.ttf")))
        pdfmetrics.registerFont(TTFont("Inter-SemiBold", os.path.join(font_cache, "Inter-SemiBold.ttf")))
        pdfmetrics.registerFont(TTFont("Inter-Italic", os.path.join(font_cache, "Inter-Italic.ttf")))
        pdfmetrics.registerFont(TTFont("Fraunces", os.path.join(font_cache, "Fraunces-Regular.ttf")))
        pdfmetrics.registerFont(TTFont("Fraunces-SemiBold", os.path.join(font_cache, "Fraunces-SemiBold.ttf")))
        pdfmetrics.registerFont(TTFont("Fraunces-Italic", os.path.join(font_cache, "Fraunces-Italic.ttf")))
        # Map italic/bold variants for inline formatting
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        registerFontFamily(
            "Inter",
            normal="Inter",
            bold="Inter-Bold",
            italic="Inter-Italic",
            boldItalic="Inter-Bold",
        )
        registerFontFamily(
            "Fraunces",
            normal="Fraunces",
            bold="Fraunces-SemiBold",
            italic="Fraunces-Italic",
            boldItalic="Fraunces-SemiBold",
        )
        USE_CUSTOM_FONTS = True
        print("  ✓ Custom fonts registered (Inter + Fraunces)")
except Exception as e:
    print(f"  ⚠ Custom fonts unavailable, using fallback: {e}")

# Font name shortcuts
FONT_BODY = "Inter" if USE_CUSTOM_FONTS else "Helvetica"
FONT_BODY_BOLD = "Inter-Bold" if USE_CUSTOM_FONTS else "Helvetica-Bold"
FONT_BODY_SEMI = "Inter-SemiBold" if USE_CUSTOM_FONTS else "Helvetica-Bold"
FONT_BODY_ITALIC = "Inter-Italic" if USE_CUSTOM_FONTS else "Helvetica-Oblique"
FONT_DISPLAY = "Fraunces" if USE_CUSTOM_FONTS else "Times-Roman"
FONT_DISPLAY_SEMI = "Fraunces-SemiBold" if USE_CUSTOM_FONTS else "Times-Bold"
FONT_DISPLAY_ITALIC = "Fraunces-Italic" if USE_CUSTOM_FONTS else "Times-Italic"
import re

def md_to_html(text):
    """Convert minimal markdown to ReportLab HTML.
    **bold** → <b>bold</b>
    *italic* → <i>italic</i>  (only when not adjacent to ** patterns)
    [link text] → strip brackets
    """
    if text is None:
        return ""
    # Bold first (paired **)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic (single *, but not inside already-converted tags)
    # Use a simple approach: match *...* that's not adjacent to <
    text = re.sub(r'(?<![<*])\*([^*\n]+?)\*(?![*>])', r'<i>\1</i>', text)
    # Strip outer brackets from inline link text [example.com]
    text = re.sub(r'\[([^\]]+)\]', r'<font color="#0F7A6B"><b>\1</b></font>', text)
    return text



def get_styles():
    """Build paragraph styles using brand typography."""
    styles = getSampleStyleSheet()

    # Volume label (e.g. "Vol I of IV")
    s_volume = ParagraphStyle(
        "Volume", parent=styles["Normal"],
        fontName=FONT_BODY_SEMI, fontSize=9.5, textColor=TEAL_700,
        leading=12, alignment=TA_LEFT, spaceAfter=4, letterSpacing=2.0
    )
    # Main title (big)
    s_title = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontName=FONT_DISPLAY_SEMI, fontSize=32, textColor=INK,
        leading=36, alignment=TA_LEFT, spaceAfter=10
    )
    # Subtitle below title
    s_subtitle = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontName=FONT_BODY, fontSize=14, textColor=INK_2,
        leading=20, alignment=TA_LEFT, spaceAfter=18
    )
    # Big intro paragraph
    s_tagline = ParagraphStyle(
        "Tagline", parent=styles["Normal"],
        fontName=FONT_DISPLAY_ITALIC, fontSize=15, textColor=TEAL_800,
        leading=22, alignment=TA_LEFT, spaceAfter=22,
        borderColor=TEAL_500, borderWidth=0,
        leftIndent=14, rightIndent=14,
        spaceBefore=8,
    )
    # Conversational intro block
    s_intro_lead = ParagraphStyle(
        "IntroLead", parent=styles["Normal"],
        fontName=FONT_DISPLAY_SEMI, fontSize=12.5, textColor=TEAL_900,
        leading=18, alignment=TA_LEFT, spaceAfter=6,
    )
    s_intro_body = ParagraphStyle(
        "IntroBody", parent=styles["Normal"],
        fontName=FONT_BODY, fontSize=11, textColor=INK_2,
        leading=17, alignment=TA_LEFT, spaceAfter=14,
    )

    # Section header
    s_section_head = ParagraphStyle(
        "SectionHead", parent=styles["Heading2"],
        fontName=FONT_DISPLAY_SEMI, fontSize=18, textColor=INK,
        leading=22, alignment=TA_LEFT, spaceBefore=16, spaceAfter=10,
    )
    # Body paragraph
    s_body = ParagraphStyle(
        "Body", parent=styles["BodyText"],
        fontName=FONT_BODY, fontSize=10.5, textColor=INK_2,
        leading=16, alignment=TA_LEFT, spaceAfter=6,
    )
    # Checklist item
    s_check = ParagraphStyle(
        "Check", parent=styles["Normal"],
        fontName=FONT_BODY, fontSize=10.5, textColor=INK_2,
        leading=16, alignment=TA_LEFT, leftIndent=18, spaceAfter=5,
        bulletIndent=4,
    )
    # Trap callout (warm background)
    s_trap_title = ParagraphStyle(
        "TrapTitle", parent=styles["Normal"],
        fontName=FONT_BODY_BOLD, fontSize=11, textColor=TRAP_AMBER,
        leading=14, alignment=TA_LEFT, spaceAfter=2,
    )
    s_trap_body = ParagraphStyle(
        "TrapBody", parent=styles["Normal"],
        fontName=FONT_BODY, fontSize=10, textColor=INK_2,
        leading=14, alignment=TA_LEFT, spaceAfter=8,
    )
    # Outro / closing
    s_outro = ParagraphStyle(
        "Outro", parent=styles["Normal"],
        fontName=FONT_BODY, fontSize=10.5, textColor=INK_2,
        leading=17, alignment=TA_LEFT, spaceAfter=8,
    )
    # Footer page numbers
    s_footer = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontName=FONT_BODY, fontSize=8, textColor=MUTED,
        leading=10, alignment=TA_CENTER,
    )

    return dict(
        volume=s_volume,
        title=s_title,
        subtitle=s_subtitle,
        tagline=s_tagline,
        intro_lead=s_intro_lead,
        intro_body=s_intro_body,
        section_head=s_section_head,
        body=s_body,
        check=s_check,
        trap_title=s_trap_title,
        trap_body=s_trap_body,
        outro=s_outro,
        footer=s_footer,
    )


# ═════════════════════════════════════════════════════════════════════
# CUSTOM FLOWABLES
# ═════════════════════════════════════════════════════════════════════
class BrandHeader(Flowable):
    """Top-of-page branded header bar (logo + brand name)"""
    def __init__(self, width):
        Flowable.__init__(self)
        self.width = width
        self.height = 28
    def draw(self):
        # Brand circle
        self.canv.saveState()
        self.canv.setFillColor(TEAL_600)
        self.canv.circle(8, self.height - 14, 8, fill=1, stroke=0)
        # Lime accent dot
        self.canv.setFillColor(LIME_500)
        self.canv.circle(11.5, self.height - 12, 2.5, fill=1, stroke=0)
        # "CPL" text inside circle is hard to do legibly at this size — use brand text next to it instead
        self.canv.setFillColor(INK)
        self.canv.setFont(FONT_BODY_BOLD, 10)
        self.canv.drawString(22, self.height - 16, "Clinical Performance Lab")
        # Right side: tiny tag
        self.canv.setFillColor(MUTED)
        self.canv.setFont(FONT_BODY, 8)
        self.canv.drawRightString(self.width, self.height - 16, "clinicalperformancelab.vercel.app")
        # Thin underline
        self.canv.setStrokeColor(BORDER)
        self.canv.setLineWidth(0.5)
        self.canv.line(0, 0, self.width, 0)
        self.canv.restoreState()


class CalloutBox(Flowable):
    """Warm-background callout box for tips, traps, frameworks."""
    def __init__(self, content, width, bg=WARM_BG, border=BORDER_STRONG, accent=TEAL_500, padding=14):
        Flowable.__init__(self)
        self.content = content  # list of (style_name, text) tuples
        self.width = width
        self.bg = bg
        self.border = border
        self.accent = accent
        self.padding = padding
        self.styles = get_styles()
        # Pre-compute height
        from reportlab.platypus import Paragraph
        self._paras = []
        for style_name, text in content:
            p = Paragraph(text, self.styles[style_name])
            self._paras.append(p)

        # Wrap each paragraph to determine height
        avail_w = width - 2 * padding - 4
        total_h = padding
        for p in self._paras:
            w, h = p.wrap(avail_w, 1000)
            total_h += h + 4
        self.height = total_h + padding

    def draw(self):
        c = self.canv
        c.saveState()
        # Background
        c.setFillColor(self.bg)
        c.setStrokeColor(self.border)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=1)
        # Left accent bar
        c.setFillColor(self.accent)
        c.rect(0, 0, 3, self.height, fill=1, stroke=0)
        # Draw each paragraph
        y_cursor = self.height - self.padding
        avail_w = self.width - 2 * self.padding - 4
        for p in self._paras:
            w, h = p.wrap(avail_w, 1000)
            p.drawOn(c, self.padding + 4, y_cursor - h)
            y_cursor -= (h + 4)
        c.restoreState()


def draw_cover(canvas_obj, doc, volume):
    """Draw the full-bleed cover page directly on the canvas. Called via onFirstPage."""
    c = canvas_obj
    w, h = letter
    c.saveState()
    # Solid dark background
    c.setFillColor(INK)
    c.rect(0, 0, w, h, fill=1, stroke=0)
    # Upper teal band
    c.setFillColor(TEAL_900)
    c.rect(0, h * 0.4, w, h * 0.6, fill=1, stroke=0)
    # Top brand mark
    c.setFillColor(LIME_500)
    c.circle(56, h - 56, 22, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont(FONT_BODY_BOLD, 16)
    c.drawCentredString(56, h - 62, "CPL")
    # Brand text
    c.setFillColor(CREAM)
    c.setFont(FONT_BODY_SEMI, 12)
    c.drawString(90, h - 55, "CLINICAL PERFORMANCE LAB")
    c.setFillColor(LIME_400)
    c.setFont(FONT_BODY, 9)
    c.drawString(90, h - 68, "The Cheat Sheet Library")

    # Volume label
    c.setFillColor(LIME_500)
    c.setFont(FONT_BODY_SEMI, 11)
    c.drawString(56, h * 0.55 + 90, volume["volume_label"].upper())

    # Title (auto-shrink if too long, then wrap if needed)
    title = volume["title"]
    c.setFillColor(CREAM)

    # Try font sizes 40 → 28 to find one that fits
    title_max_width = w - 112  # left margin + right margin = 56 + 56
    title_size = 40
    for try_size in (40, 36, 32, 28):
        c.setFont(FONT_DISPLAY_SEMI, try_size)
        if c.stringWidth(title, FONT_DISPLAY_SEMI, try_size) <= title_max_width:
            title_size = try_size
            break
        title_size = try_size

    c.setFont(FONT_DISPLAY_SEMI, title_size)
    if c.stringWidth(title, FONT_DISPLAY_SEMI, title_size) <= title_max_width:
        # Single line fits
        c.drawString(56, h * 0.55 + 20, title)
    else:
        # Wrap to two lines
        title_words = title.split()
        # Find best break point
        best_break = len(title_words) // 2 + 1
        line1 = " ".join(title_words[:best_break])
        line2 = " ".join(title_words[best_break:])
        # Walk in if line1 still too long
        while c.stringWidth(line1, FONT_DISPLAY_SEMI, title_size) > title_max_width and best_break > 1:
            best_break -= 1
            line1 = " ".join(title_words[:best_break])
            line2 = " ".join(title_words[best_break:])
        line_height = title_size + 4
        c.drawString(56, h * 0.55 + line_height / 2 + 12, line1)
        c.drawString(56, h * 0.55 - line_height / 2 + 12, line2)

    # Subtitle
    c.setFillColor(Color(0.85, 0.83, 0.74))
    c.setFont(FONT_BODY, 13)
    subtitle = volume["subtitle"]
    if len(subtitle) > 55:
        sub_words = subtitle.split()
        # Find break point under 55 chars
        break_idx = len(sub_words) // 2 + 1
        sub1 = " ".join(sub_words[:break_idx])
        sub2 = " ".join(sub_words[break_idx:])
        c.drawString(56, h * 0.55 - 40, sub1)
        c.drawString(56, h * 0.55 - 56, sub2)
    else:
        c.drawString(56, h * 0.55 - 40, subtitle)

    # Lime accent rule
    c.setFillColor(LIME_500)
    c.rect(56, h * 0.4 + 16, 80, 3, fill=1, stroke=0)

    # Tagline (italic, in lower section)
    c.setFillColor(CREAM)
    c.setFont(FONT_DISPLAY_ITALIC, 13)
    tagline = volume["tagline"]
    max_chars = 70
    words = tagline.split()
    lines, cur, cur_len = [], [], 0
    for word in words:
        if cur_len + len(word) + 1 > max_chars:
            lines.append(" ".join(cur))
            cur = [word]; cur_len = len(word)
        else:
            cur.append(word); cur_len += len(word) + 1
    if cur: lines.append(" ".join(cur))
    y = h * 0.4 - 16
    for line in lines:
        c.drawString(56, y, line)
        y -= 18

    # Bottom panel
    c.setFillColor(LIME_400)
    c.setFont(FONT_BODY_SEMI, 9)
    c.drawString(56, 70, "FREE RESOURCE")
    c.setFillColor(Color(0.85, 0.83, 0.74))
    c.setFont(FONT_BODY, 9.5)
    c.drawString(56, 52, "clinicalperformancelab.vercel.app")
    c.drawString(56, 36, "Built by clinicians. Verified against live platform data.")
    c.restoreState()


# ═════════════════════════════════════════════════════════════════════
# PAGE TEMPLATE
# ═════════════════════════════════════════════════════════════════════
def make_page_template(volume):
    """Returns header/footer callback for a given volume."""
    label = volume["volume_label"]
    title = volume["title"]
    def on_page(canvas_obj, doc):
        if doc.page == 1:
            return  # cover page handles its own design
        canvas_obj.saveState()
        # Header
        w, h = letter
        # Brand text
        canvas_obj.setFillColor(MUTED)
        canvas_obj.setFont(FONT_BODY, 8.5)
        canvas_obj.drawString(0.6 * inch, h - 0.42 * inch, f"CPL CHEAT SHEET LIBRARY  ·  {label.upper()}")
        canvas_obj.drawRightString(w - 0.6 * inch, h - 0.42 * inch, title)
        # Underline
        canvas_obj.setStrokeColor(BORDER)
        canvas_obj.setLineWidth(0.4)
        canvas_obj.line(0.6 * inch, h - 0.5 * inch, w - 0.6 * inch, h - 0.5 * inch)
        # Footer
        canvas_obj.setFillColor(MUTED)
        canvas_obj.setFont(FONT_BODY, 8)
        canvas_obj.drawCentredString(w / 2, 0.3 * inch, f"Page {doc.page}")
        canvas_obj.drawString(0.6 * inch, 0.3 * inch, "clinicalperformancelab.vercel.app")
        canvas_obj.setFont(FONT_BODY, 7.5)
        canvas_obj.drawRightString(w - 0.6 * inch, 0.3 * inch, "© 2026 CPL  •  For personal study use")
        canvas_obj.restoreState()
    return on_page


# ═════════════════════════════════════════════════════════════════════
# RENDER A SECTION (heterogeneous content types)
# ═════════════════════════════════════════════════════════════════════
def make_flowable(name, width):
    """Dispatch by name. All flowables receive the brand-color palette and font names."""
    if name == "oldcarts_mnemonic":
        return OldcartsMnemonic(width, FONT_BODY, FONT_BODY_BOLD, FONT_DISPLAY_SEMI)
    if name == "snoop_mnemonic":
        return SnoopMnemonic(width, FONT_BODY, FONT_BODY_BOLD, FONT_BODY_SEMI, FONT_DISPLAY_SEMI)
    if name == "centor_criteria":
        return CentorCriteria(width, FONT_BODY, FONT_BODY_BOLD, FONT_BODY_SEMI)
    if name == "cardiac_diagram":
        return CardiacAuscultationDiagram(width, FONT_BODY, FONT_BODY_BOLD, FONT_BODY_SEMI)
    if name == "abdominal_quadrants":
        return AbdominalQuadrants(width, FONT_BODY, FONT_BODY_BOLD, FONT_BODY_SEMI)
    if name == "lung_fields":
        return LungFieldsDiagram(width, FONT_BODY, FONT_BODY_BOLD)
    if name == "problem_statement":
        return ProblemStatementStructure(width, FONT_BODY, FONT_BODY_BOLD,
                                         FONT_BODY_SEMI, FONT_DISPLAY_ITALIC)
    if name == "med_dosing":
        return MedDosingCard(width, FONT_BODY, FONT_BODY_BOLD,
                             FONT_BODY_SEMI, FONT_DISPLAY_SEMI)
    if name == "six_part_plan":
        return SixPartPlanVisual(width, FONT_BODY, FONT_BODY_BOLD, FONT_BODY_SEMI)
    raise ValueError(f"Unknown flowable: {name}")


def render_section(section, styles, content_width):
    """Convert a section dict into a list of flowables."""
    out = []
    kind = section.get("kind", "framework")

    # mid_cta and flowable sections may or may not have a title
    if section.get("title"):
        out.append(Paragraph(md_to_html(section["title"]), styles["section_head"]))

    if kind == "flowable":
        flowable_name = section.get("flowable")
        out.append(make_flowable(flowable_name, content_width))

    elif kind == "mid_cta":
        out.append(Spacer(1, 6))
        out.append(CTABox(content_width, FONT_BODY, FONT_BODY_BOLD,
                          FONT_BODY_SEMI, FONT_DISPLAY_SEMI, FONT_DISPLAY_ITALIC))
        out.append(Spacer(1, 6))

    elif kind == "framework":
        for line in section.get("body", []):
            if line == "":
                out.append(Spacer(1, 4))
            else:
                out.append(Paragraph(md_to_html(line), styles["body"]))

    elif kind == "checklist":
        starred = section.get("starred", False)
        bullet = "★" if starred else "✓"
        items_data = []
        for item in section["items"]:
            items_data.append(Paragraph(
                f"<font color='#0D9E85'>{bullet}</font>&nbsp;&nbsp;{md_to_html(item)}",
                styles["check"]))
        out.extend(items_data)

    elif kind == "translation":
        for line in section.get("body", []):
            out.append(Paragraph(md_to_html(line), styles["body"]))
        out.append(Spacer(1, 6))
        # Two-column table
        rows = [[Paragraph(f"<i>{md_to_html(lay)}</i>", styles["body"]),
                 Paragraph(f"<b>{md_to_html(clinical)}</b>", styles["body"])]
                for lay, clinical in section["translations"]]
        col_w = (content_width / 2) - 2
        t = Table(rows, colWidths=[col_w, col_w])
        t.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), FONT_BODY),
            ("FONTSIZE", (0,0), (-1,-1), 9.5),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [WARM_BG, CREAM_2]),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
            ("TOPPADDING", (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LINEBELOW", (0,0), (-1,-1), 0.25, BORDER),
        ]))
        out.append(t)

    elif kind == "traps":
        for label, explanation in section["items"]:
            content_for_box = [
                ("trap_title", f"⚠️ {md_to_html(label)}"),
                ("trap_body", md_to_html(explanation)),
            ]
            out.append(CalloutBox(content_for_box, content_width,
                                  bg=WARM_BG, border=BORDER_STRONG, accent=TRAP_AMBER, padding=10))
            out.append(Spacer(1, 6))

    elif kind == "trap_callout":
        content_for_box = []
        content_for_box.append(("trap_title", "⚠️ Critical Scoring Trap"))
        for line in section.get("body", []):
            if line == "":
                continue
            content_for_box.append(("trap_body", md_to_html(line)))
        out.append(CalloutBox(content_for_box, content_width,
                              bg=HexColor("#FFF6E8"), border=HexColor("#E8B566"), accent=TRAP_AMBER, padding=14))

    out.append(Spacer(1, 10))
    return out


# ═════════════════════════════════════════════════════════════════════
# BUILD ONE VOLUME PDF
# ═════════════════════════════════════════════════════════════════════
def build_volume_pdf(volume, meta):
    out_path = os.path.join(OUT_DIR, meta["filename"])
    doc = SimpleDocTemplate(
        out_path,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.85 * inch,   # leaves room for header
        bottomMargin=0.6 * inch,
        title=f"CPL — {volume['title']}",
        author="Clinical Performance Lab",
        subject="Clinical reasoning cheat sheet for nursing students",
    )

    styles = get_styles()
    content_w = letter[0] - 1.2 * inch  # available text width

    story = []

    # ─── Page 1 is the cover (drawn directly on canvas via onFirstPage) ───
    # Story begins with a spacer + PageBreak so doc.build's first flowable
    # forces a page break, then the content frame starts on page 2.
    story.append(Spacer(1, 1))  # tiny seed so the first page exists
    story.append(PageBreak())

    # ─── Introduction (conversational voice) ────────────
    story.append(Paragraph(volume["volume_label"], styles["volume"]))
    story.append(Paragraph(volume["title"], styles["title"]))
    story.append(Paragraph(volume["subtitle"], styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=LIME_500, spaceBefore=4, spaceAfter=18))

    for lead, body in volume["intro_voice"]:
        story.append(Paragraph(md_to_html(lead), styles["intro_lead"]))
        story.append(Paragraph(md_to_html(body), styles["intro_body"]))

    # ─── Case Stage Map ────────────────────────────────
    stage_id = volume.get("stage_id", "history")
    story.append(Spacer(1, 8))
    story.append(CaseStageMap(content_w, stage_id, FONT_BODY, FONT_BODY_BOLD, FONT_BODY_SEMI))
    story.append(Spacer(1, 12))

    # ─── Sections ──────────────────────────────────────
    for section in volume["sections"]:
        section_flowables = render_section(section, styles, content_w)
        # Try to keep section title with first 1-2 lines together
        if len(section_flowables) > 2:
            story.append(KeepTogether(section_flowables[:2]))
            story.extend(section_flowables[2:])
        else:
            story.extend(section_flowables)

    # ─── Outro ─────────────────────────────────────────
    story.append(Spacer(1, 18))
    story.append(HRFlowable(width="100%", thickness=1.5, color=TEAL_500, spaceAfter=14))
    story.append(Paragraph("Next steps", styles["section_head"]))
    for line in volume["outro"]:
        if line == "":
            story.append(Spacer(1, 4))
        else:
            story.append(Paragraph(md_to_html(line), styles["outro"]))

    # ─── Final CTA card (strong) ──────────────────────
    story.append(Spacer(1, 16))
    story.append(FinalCTACard(content_w, FONT_BODY, FONT_BODY_BOLD,
                              FONT_BODY_SEMI, FONT_DISPLAY_SEMI))

    # ─── Final brand strip ─────────────────────────────
    story.append(Spacer(1, 18))
    story.append(HRFlowable(width="40%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 6))
    brand_strip = Paragraph(
        f'<font name="{FONT_BODY_SEMI}" color="#0F7A6B">CLINICAL PERFORMANCE LAB</font>  '
        '<font color="#5C6E69">·  Submission-ready clinical reasoning resources</font><br/>'
        '<font color="#5C6E69" size="8">Built from 200+ verified student submissions across NR509, NR511, NR602, NURS 6512, NRNP 6541.<br/>'
        'clinicalperformancelab.vercel.app  ·  Tutorspot98@gmail.com</font>',
        styles["body"]
    )
    story.append(brand_strip)

    # Build with proper callbacks: cover on page 1, header/footer from page 2 onward
    on_page = make_page_template(volume)
    first_page = lambda c, d: draw_cover(c, d, volume)
    doc.build(story, onFirstPage=first_page, onLaterPages=on_page)
    return out_path


# ═════════════════════════════════════════════════════════════════════
# BUILD ALL
# ═════════════════════════════════════════════════════════════════════
def build_all():
    print("Generating CPL Cheat Sheet Library...")
    paths = []
    for volume, meta in zip(ALL_VOLUMES, VOLUME_META):
        path = build_volume_pdf(volume, meta)
        size_kb = os.path.getsize(path) / 1024
        print(f"  ✓ {meta['filename']:38} ({size_kb:.0f} KB)")
        paths.append(path)
    return paths


if __name__ == "__main__":
    paths = build_all()
    print(f"\n✓ Built {len(paths)} PDFs into {OUT_DIR}/")
