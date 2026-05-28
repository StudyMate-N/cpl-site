"""
Custom Flowables for the CPL cheat sheet PDFs.
Builds brand-consistent anatomical and mnemonic diagrams using ReportLab primitives.

Visual language:
- Stylized, not photorealistic
- Brand palette: teal-900, teal-500, lime-500, cream, ink
- Labeled, scannable, screenshot-worthy
"""

from reportlab.lib.colors import HexColor, Color, white
from reportlab.platypus.flowables import Flowable
from reportlab.lib.units import inch
import math

# Re-export the brand colors so this module is self-contained
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
WARM_BG = HexColor("#FFFCF5")
WARM_BORDER = HexColor("#E8B566")
TRAP_AMBER = HexColor("#946115")


# ═════════════════════════════════════════════════════════════════════
# CASE STAGE MAP — shown at the start of each volume
# Indicates where THIS volume fits in the overall iHuman case flow.
# ═════════════════════════════════════════════════════════════════════
class CaseStageMap(Flowable):
    """Horizontal flow chart showing the 4 iHuman case stages, with current highlighted."""
    STAGES = [
        ("HISTORY",          "~40%", "history"),
        ("PHYSICAL EXAM",    "~40%", "physical-exam"),
        ("KEY FINDINGS + DDx", "Graded", "ddx"),
        ("PLAN + SOAP",      "~20%",  "plan"),
    ]

    def __init__(self, width, active_id, font_body, font_body_bold, font_body_semi):
        Flowable.__init__(self)
        self.width = width
        self.height = 78
        self.active_id = active_id
        self.font_body = font_body
        self.font_body_bold = font_body_bold
        self.font_body_semi = font_body_semi

    def draw(self):
        c = self.canv
        c.saveState()

        n = len(self.STAGES)
        gap = 8
        box_w = (self.width - (n - 1) * gap) / n
        box_h = 52

        for i, (label, weight, stage_id) in enumerate(self.STAGES):
            x = i * (box_w + gap)
            y = self.height - box_h - 18
            is_active = stage_id == self.active_id

            if is_active:
                c.setFillColor(INK)
                c.setStrokeColor(LIME_500)
                c.setLineWidth(2)
            else:
                c.setFillColor(CREAM_2)
                c.setStrokeColor(BORDER_STRONG)
                c.setLineWidth(0.5)
            c.roundRect(x, y, box_w, box_h, 6, fill=1, stroke=1)

            # Stage number
            c.setFillColor(LIME_500 if is_active else MUTED)
            c.setFont(self.font_body_semi, 8)
            c.drawString(x + 8, y + box_h - 14, f"STAGE {i+1}")

            # Label
            c.setFillColor(CREAM if is_active else INK_2)
            c.setFont(self.font_body_bold, 9.5)
            # truncate if too long
            if c.stringWidth(label, self.font_body_bold, 9.5) > box_w - 14:
                # shrink
                c.setFont(self.font_body_bold, 8.5)
            c.drawString(x + 8, y + box_h - 28, label)

            # Weight
            c.setFillColor(LIME_400 if is_active else MUTED)
            c.setFont(self.font_body, 8)
            c.drawString(x + 8, y + 8, weight)

            # Arrow between boxes
            if i < n - 1:
                ax = x + box_w + 1
                ay = y + box_h / 2
                c.setStrokeColor(MUTED)
                c.setLineWidth(1)
                c.line(ax, ay, ax + gap - 2, ay)
                # Arrow head
                c.setFillColor(MUTED)
                p = c.beginPath()
                p.moveTo(ax + gap - 2, ay)
                p.lineTo(ax + gap - 5, ay - 2.5)
                p.lineTo(ax + gap - 5, ay + 2.5)
                p.close()
                c.drawPath(p, fill=1, stroke=0)

        # Caption above the boxes
        c.setFillColor(MUTED)
        c.setFont(self.font_body, 8.5)
        c.drawString(0, self.height - 10, "THE iHUMAN CASE FLOW  ·  You are here")

        c.restoreState()


# ═════════════════════════════════════════════════════════════════════
# SNOOP4 mnemonic — vertical card with each letter explained
# ═════════════════════════════════════════════════════════════════════
class SnoopMnemonic(Flowable):
    LETTERS = [
        ("S", "Systemic signs", "Fever, weight loss, immunocompromise"),
        ("N", "Neurologic deficits", "Focal weakness, CN abnormalities, ataxia"),
        ("O", "Onset sudden (thunderclap)", "Worst headache of life within seconds"),
        ("O", "Onset after age 50", "New headache pattern in older adults"),
        ("P", "Papilledema", "Optic disc swelling on fundoscopy"),
        ("P", "Postural worsening", "Worse lying down or with Valsalva"),
        ("P", "Precipitated by Valsalva", "Cough, sneeze, sex, exertion"),
        ("P", "Progressive / Pattern change", "New character, frequency, severity"),
    ]

    def __init__(self, width, font_body, font_body_bold, font_body_semi, font_display_semi):
        Flowable.__init__(self)
        self.width = width
        self.font_body = font_body
        self.font_body_bold = font_body_bold
        self.font_body_semi = font_body_semi
        self.font_display_semi = font_display_semi
        self.row_h = 24
        self.header_h = 48  # increased from 32 — gives subline more room
        self.padding = 14
        self.height = self.header_h + len(self.LETTERS) * self.row_h + self.padding + 8

    def draw(self):
        c = self.canv
        c.saveState()
        h = self.height

        # Outer box (warm callout) — use clipping to ensure accent stays within corners
        c.setFillColor(WARM_BG)
        c.setStrokeColor(WARM_BORDER)
        c.setLineWidth(0.7)
        c.roundRect(0, 0, self.width, h, 8, fill=1, stroke=1)

        # Left accent band — inset slightly to avoid corner overflow
        c.setFillColor(TRAP_AMBER)
        c.rect(0.5, 8, 3.5, h - 16, fill=1, stroke=0)

        # Title bar
        c.setFillColor(TRAP_AMBER)
        c.setFont(self.font_body_bold, 11)
        c.drawString(18, h - 22, "SNOOP4  ·  Headache Red Flag Mnemonic")
        c.setFillColor(MUTED)
        c.setFont(self.font_body, 8.5)
        c.drawString(18, h - 36, "If ANY are present → DO NOT manage as primary headache. Imaging indicated.")

        # Rows — start lower (more header padding)
        y_start = h - self.header_h - 4
        for i, (letter, short, detail) in enumerate(self.LETTERS):
            y = y_start - (i * self.row_h)
            # Letter badge
            c.setFillColor(TRAP_AMBER)
            c.circle(28, y, 9, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont(self.font_body_bold, 11)
            c.drawCentredString(28, y - 4, letter)
            # Short label
            c.setFillColor(INK)
            c.setFont(self.font_body_bold, 10)
            c.drawString(50, y + 1, short)
            # Detail
            c.setFillColor(MUTED)
            c.setFont(self.font_body, 8.5)
            c.drawString(50, y - 10, detail)
        c.restoreState()


# ═════════════════════════════════════════════════════════════════════
# Centor Criteria mnemonic — checklist box
# ═════════════════════════════════════════════════════════════════════
class CentorCriteria(Flowable):
    CRITERIA = [
        ("Tonsillar exudate", "1 point"),
        ("Tender anterior cervical lymphadenopathy", "1 point"),
        ("Fever (>38°C / 100.4°F)", "1 point"),
        ("Absence of cough", "1 point"),
        ("Age 3–14 (modified Centor)", "+1"),
        ("Age 15–44", "0"),
        ("Age ≥45", "−1"),
    ]
    INTERPRETATION = [
        ("0–1", "Low risk — no testing, no treatment", TEAL_700),
        ("2–3", "Test (rapid strep or culture). Treat if positive.", TRAP_AMBER),
        ("4–5", "High risk — empiric antibiotics may be appropriate", HexColor("#C44")),
    ]

    def __init__(self, width, font_body, font_body_bold, font_body_semi):
        Flowable.__init__(self)
        self.width = width
        self.font_body = font_body
        self.font_body_bold = font_body_bold
        self.font_body_semi = font_body_semi
        self.row_h = 16
        self.interp_h = 18
        self.header_h = 38
        self.height = self.header_h + len(self.CRITERIA) * self.row_h + len(self.INTERPRETATION) * self.interp_h + 36

    def draw(self):
        c = self.canv
        c.saveState()
        h = self.height
        # Outer box
        c.setFillColor(WARM_BG)
        c.setStrokeColor(BORDER_STRONG)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, self.width, h, 8, fill=1, stroke=1)
        c.setFillColor(TEAL_500)
        c.rect(0, 0, 4, h, fill=1, stroke=0)

        # Title
        c.setFillColor(TEAL_800)
        c.setFont(self.font_body_bold, 11)
        c.drawString(18, h - 22, "CENTOR CRITERIA  ·  GAS pharyngitis probability")
        c.setFillColor(MUTED)
        c.setFont(self.font_body, 8.5)
        c.drawString(18, h - 34, "One point per criterion present (plus age modifier)")

        # Criteria rows
        y = h - self.header_h - 10
        for label, points in self.CRITERIA:
            # checkbox
            c.setStrokeColor(MUTED)
            c.setLineWidth(0.7)
            c.rect(20, y - 6, 9, 9, fill=0, stroke=1)
            # Label
            c.setFillColor(INK_2)
            c.setFont(self.font_body, 9.5)
            c.drawString(36, y - 3, label)
            # Points
            c.setFillColor(TEAL_700)
            c.setFont(self.font_body_bold, 9)
            c.drawRightString(self.width - 16, y - 3, points)
            y -= self.row_h

        # Divider
        y -= 4
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        c.line(16, y, self.width - 16, y)
        y -= 10

        # Interpretation
        c.setFillColor(MUTED)
        c.setFont(self.font_body_bold, 8.5)
        c.drawString(20, y, "INTERPRETATION")
        y -= 14
        for score, action, color in self.INTERPRETATION:
            # Score badge
            c.setFillColor(color)
            c.roundRect(20, y - 6, 30, 13, 2, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont(self.font_body_bold, 9)
            c.drawCentredString(35, y - 3, score)
            # Action
            c.setFillColor(INK_2)
            c.setFont(self.font_body, 9)
            c.drawString(58, y - 3, action)
            y -= self.interp_h

        c.restoreState()


# ═════════════════════════════════════════════════════════════════════
# OLDCARTS visual mnemonic
# ═════════════════════════════════════════════════════════════════════
class OldcartsMnemonic(Flowable):
    LETTERS = [
        ("O", "Onset", "When did it start? Sudden or gradual?"),
        ("L", "Location", "Where exactly? Does it move?"),
        ("D", "Duration", "How long? Continuous or intermittent?"),
        ("C", "Character", "Sharp, dull, throbbing, burning?"),
        ("A", "Aggravating/Alleviating", "What makes it better or worse?"),
        ("R", "Radiation", "Does it spread anywhere?"),
        ("T", "Timing", "Time of day? Frequency?"),
        ("S", "Severity", "Rate 1–10. Impact on daily life?"),
    ]

    def __init__(self, width, font_body, font_body_bold, font_display_semi):
        Flowable.__init__(self)
        self.width = width
        self.font_body = font_body
        self.font_body_bold = font_body_bold
        self.font_display_semi = font_display_semi
        self.row_h = 22
        self.header_h = 32
        self.height = self.header_h + len(self.LETTERS) * self.row_h + 18

    def draw(self):
        c = self.canv
        c.saveState()
        h = self.height
        # Outer
        c.setFillColor(CREAM)
        c.setStrokeColor(BORDER_STRONG)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, self.width, h, 8, fill=1, stroke=1)
        c.setFillColor(TEAL_500)
        c.rect(0, 0, 4, h, fill=1, stroke=0)

        # Title
        c.setFillColor(TEAL_800)
        c.setFont(self.font_body_bold, 11)
        c.drawString(18, h - 22, "OLDCARTS  ·  The HPI mnemonic")

        # Rows
        y = h - self.header_h - 4
        for letter, label, detail in self.LETTERS:
            # Letter circle
            c.setFillColor(TEAL_600)
            c.circle(28, y - 2, 9, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont(self.font_body_bold, 11)
            c.drawCentredString(28, y - 6, letter)
            # Label
            c.setFillColor(INK)
            c.setFont(self.font_body_bold, 9.5)
            c.drawString(50, y, label)
            # Detail
            c.setFillColor(MUTED)
            c.setFont(self.font_body, 9)
            c.drawString(50, y - 11, detail)
            y -= self.row_h
        c.restoreState()


# ═════════════════════════════════════════════════════════════════════
# Cardiac auscultation diagram — stylized chest with 5 points
# ═════════════════════════════════════════════════════════════════════
class CardiacAuscultationDiagram(Flowable):
    """Stylized anterior chest with 5 auscultation points labeled."""

    POINTS = [
        # (label_short, name, position_x_norm, position_y_norm, sound_short)
        ("A",  "Aortic",        0.42, 0.78, "2nd ICS,\nR sternal border"),
        ("P",  "Pulmonic",      0.58, 0.78, "2nd ICS,\nL sternal border"),
        ("E",  "Erb's point",   0.50, 0.66, "3rd ICS,\nL sternal border"),
        ("T",  "Tricuspid",     0.50, 0.50, "4th ICS,\nL sternal border"),
        ("M",  "Mitral / Apex", 0.62, 0.35, "5th ICS, MCL\n— also PMI"),
    ]

    def __init__(self, width, font_body, font_body_bold, font_body_semi):
        Flowable.__init__(self)
        self.width = width
        self.diagram_h = 280  # chest area
        self.legend_h = 100   # labels below — increased for two-line sound text
        self.height = self.diagram_h + self.legend_h
        self.font_body = font_body
        self.font_body_bold = font_body_bold
        self.font_body_semi = font_body_semi

    def draw(self):
        c = self.canv
        c.saveState()

        # Background
        c.setFillColor(CREAM)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.4)
        c.roundRect(0, 0, self.width, self.height, 8, fill=1, stroke=1)

        # Title
        c.setFillColor(TEAL_800)
        c.setFont(self.font_body_bold, 11)
        c.drawString(14, self.height - 18, "5-POINT CARDIAC AUSCULTATION")
        c.setFillColor(MUTED)
        c.setFont(self.font_body, 8.5)
        c.drawString(14, self.height - 30, "Anterior chest, patient supine. Listen with diaphragm at each point.")

        # Compute chest drawing area
        diagram_top = self.height - 42
        diagram_bottom = self.legend_h + 4
        diagram_w = self.width - 28
        diagram_x = 14
        cx = diagram_x + diagram_w / 2
        cy = diagram_bottom + (diagram_top - diagram_bottom) / 2

        # Draw stylized chest outline — simple torso shape
        chest_w = min(diagram_w * 0.55, 180)
        chest_h = (diagram_top - diagram_bottom) * 0.85
        chest_left = cx - chest_w / 2
        chest_right = cx + chest_w / 2
        chest_bottom = cy - chest_h / 2
        chest_top = cy + chest_h / 2

        # Outline: rounded rectangle for torso
        c.setStrokeColor(TEAL_700)
        c.setLineWidth(1.5)
        c.setFillColor(white)
        # Slightly tapered torso (use path)
        p = c.beginPath()
        # Top - shoulders
        p.moveTo(chest_left - 6, chest_top - 12)
        # Neck notch
        p.curveTo(cx - 24, chest_top + 8, cx + 24, chest_top + 8, chest_right + 6, chest_top - 12)
        # Right side
        p.curveTo(chest_right + 4, cy + 10, chest_right - 6, cy - 20, chest_right - 8, chest_bottom + 8)
        # Bottom (waist)
        p.curveTo(chest_right - 12, chest_bottom - 6, chest_left + 12, chest_bottom - 6, chest_left + 8, chest_bottom + 8)
        # Left side
        p.curveTo(chest_left + 6, cy - 20, chest_left - 4, cy + 10, chest_left - 6, chest_top - 12)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

        # Sternum line
        c.setStrokeColor(BORDER_STRONG)
        c.setLineWidth(0.8)
        c.setDash(2, 2)
        c.line(cx, chest_top - 18, cx, chest_bottom + 14)
        c.setDash([])

        # Rib hints — subtle horizontal lines
        c.setStrokeColor(HexColor("#EAE0C8"))
        c.setLineWidth(0.5)
        for i in range(4):
            rib_y = chest_top - 30 - i * (chest_h * 0.13)
            # Left side rib curve
            c.line(chest_left + 6, rib_y, cx - 4, rib_y - 2)
            c.line(cx + 4, rib_y - 2, chest_right - 6, rib_y)

        # Heart shadow — subtle
        c.setFillColor(HexColor("#FBF5E8"))
        c.setStrokeColor(HexColor("#F0E6D0"))
        c.setLineWidth(0.4)
        heart_cx = cx + 4
        heart_cy = cy - 4
        # Heart shape via two circles + triangle
        c.circle(heart_cx - 14, heart_cy + 12, 16, fill=1, stroke=1)
        c.circle(heart_cx + 14, heart_cy + 12, 16, fill=1, stroke=1)
        p = c.beginPath()
        p.moveTo(heart_cx - 28, heart_cy + 14)
        p.lineTo(heart_cx + 28, heart_cy + 14)
        p.lineTo(heart_cx, heart_cy - 26)
        p.close()
        c.setFillColor(HexColor("#FBF5E8"))
        c.setStrokeColor(HexColor("#F0E6D0"))
        c.drawPath(p, fill=1, stroke=1)

        # Auscultation points as labeled circles
        # Position relative to chest box
        pts_drawn = []
        for label_short, name, nx, ny, sound in self.POINTS:
            px = chest_left + nx * chest_w
            py = chest_bottom + ny * chest_h
            # Point circle
            c.setFillColor(LIME_500)
            c.setStrokeColor(INK)
            c.setLineWidth(1.2)
            c.circle(px, py, 8.5, fill=1, stroke=1)
            c.setFillColor(INK)
            c.setFont(self.font_body_bold, 10)
            c.drawCentredString(px, py - 3.5, label_short)
            pts_drawn.append((label_short, px, py))

        # Legend below diagram (legend_h is the bottom band of the flowable)
        # Divider line at top of legend area
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.4)
        c.line(14, self.legend_h - 6, self.width - 14, self.legend_h - 6)

        # 5 legend entries in a row — each entry is a stacked column
        legend_cols = 5
        col_w = (self.width - 24) / legend_cols
        for i, (label_short, name, _, _, sound) in enumerate(self.POINTS):
            lx = 12 + i * col_w
            # Badge + name on top row
            c.setFillColor(LIME_500)
            c.setStrokeColor(INK)
            c.setLineWidth(0.8)
            c.circle(lx + 7, self.legend_h - 24, 6, fill=1, stroke=1)
            c.setFillColor(INK)
            c.setFont(self.font_body_bold, 7.5)
            c.drawCentredString(lx + 7, self.legend_h - 26.5, label_short)
            # Name
            c.setFillColor(INK_2)
            c.setFont(self.font_body_bold, 7.5)
            c.drawString(lx + 17, self.legend_h - 22, name)
            # Sound location — two lines, smaller font
            c.setFillColor(MUTED)
            c.setFont(self.font_body, 6.5)
            sound_lines = sound.split("\n")
            sy = self.legend_h - 36
            for sw in sound_lines[:2]:
                c.drawString(lx + 4, sy, sw.strip())
                sy -= 9

        c.restoreState()


# ═════════════════════════════════════════════════════════════════════
# Abdominal quadrants — labeled grid
# ═════════════════════════════════════════════════════════════════════
class AbdominalQuadrants(Flowable):
    QUADRANTS = [
        # (label, contents, position: row,col, watch_for_list)  row 0 = top
        ("RUQ", "Liver, gallbladder, R kidney,\nhead of pancreas, duodenum", 0, 0,
         ["Cholecystitis", "Hepatitis"]),
        ("LUQ", "Spleen, L kidney, stomach,\nbody/tail of pancreas", 0, 1,
         ["Splenomegaly", "Gastric ulcer"]),
        ("RLQ", "Appendix, R ovary, R ureter,\ncecum, R inguinal ring", 1, 0,
         ["Appendicitis", "Ectopic pregnancy"]),
        ("LLQ", "Sigmoid colon, L ovary,\nL ureter, L inguinal ring", 1, 1,
         ["Diverticulitis", "Ovarian cyst"]),
    ]

    def __init__(self, width, font_body, font_body_bold, font_body_semi):
        Flowable.__init__(self)
        self.width = width
        self.diagram_w = min(width, 360)
        self.quad_h = 90  # slightly taller — room for two-line watch-for
        self.height = self.quad_h * 2 + 80  # quadrants + header

        self.font_body = font_body
        self.font_body_bold = font_body_bold
        self.font_body_semi = font_body_semi

    def draw(self):
        c = self.canv
        c.saveState()
        # Background card
        c.setFillColor(CREAM)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.4)
        c.roundRect(0, 0, self.width, self.height, 8, fill=1, stroke=1)

        # Title
        c.setFillColor(TEAL_800)
        c.setFont(self.font_body_bold, 11)
        c.drawString(14, self.height - 18, "ABDOMINAL QUADRANTS  ·  Auscultate before palpating")
        c.setFillColor(MUTED)
        c.setFont(self.font_body, 8.5)
        c.drawString(14, self.height - 30, "Listen in all four. Document bowel sounds: normoactive / hyperactive / hypoactive / absent.")

        # Center the diagram
        diagram_left = (self.width - self.diagram_w) / 2
        diagram_top = self.height - 44
        diagram_bottom = 28
        quad_w = self.diagram_w / 2
        quad_h_actual = (diagram_top - diagram_bottom) / 2

        for label, organs, row, col, conds in self.QUADRANTS:
            x = diagram_left + col * quad_w
            y = diagram_top - (row + 1) * quad_h_actual

            # Quadrant cell
            c.setFillColor(WARM_BG)
            c.setStrokeColor(TEAL_500)
            c.setLineWidth(1.2)
            c.rect(x, y, quad_w, quad_h_actual, fill=1, stroke=1)

            # Label badge (corner)
            c.setFillColor(TEAL_700)
            badge_w = 36
            c.roundRect(x + 6, y + quad_h_actual - 20, badge_w, 14, 3, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont(self.font_body_bold, 9)
            c.drawCentredString(x + 6 + badge_w / 2, y + quad_h_actual - 16, label)

            # Organs
            c.setFillColor(INK_2)
            c.setFont(self.font_body, 7.8)
            text_y = y + quad_h_actual - 30
            for line in organs.split("\n"):
                c.drawString(x + 8, text_y, line.strip())
                text_y -= 9

            # "Watch for" section — two lines, one diagnosis per line
            c.setFillColor(TRAP_AMBER)
            c.setFont(self.font_body_bold, 7)
            c.drawString(x + 8, y + 24, "WATCH FOR")
            c.setFillColor(MUTED)
            c.setFont(self.font_body, 7.5)
            wfy = y + 14
            for cond in conds:
                c.drawString(x + 8, wfy, "• " + cond)
                wfy -= 9

        # Patient orientation note
        c.setFillColor(MUTED)
        c.setFont(self.font_body, 7.5)
        c.drawCentredString(self.width / 2, 14,
                            "Quadrants shown from clinician's view (patient's left appears on your right)")

        c.restoreState()


# ═════════════════════════════════════════════════════════════════════
# Lung field zones diagram
# ═════════════════════════════════════════════════════════════════════
class LungFieldsDiagram(Flowable):
    """Anterior/posterior lung field auscultation pattern."""

    POINTS_ANT = [
        # (x_norm, y_norm) — anterior chest, 6 points (3 levels × L+R)
        (0.38, 0.82), (0.62, 0.82),   # apices
        (0.38, 0.62), (0.62, 0.62),   # mid
        (0.38, 0.42), (0.62, 0.42),   # lower
    ]
    POINTS_POST = [
        (0.38, 0.78), (0.62, 0.78),
        (0.38, 0.55), (0.62, 0.55),
        (0.38, 0.32), (0.62, 0.32),
    ]

    def __init__(self, width, font_body, font_body_bold):
        Flowable.__init__(self)
        self.width = width
        self.height = 240
        self.font_body = font_body
        self.font_body_bold = font_body_bold

    def draw(self):
        c = self.canv
        c.saveState()
        # Background
        c.setFillColor(CREAM)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.4)
        c.roundRect(0, 0, self.width, self.height, 8, fill=1, stroke=1)
        # Title
        c.setFillColor(TEAL_800)
        c.setFont(self.font_body_bold, 11)
        c.drawString(14, self.height - 18, "LUNG FIELD AUSCULTATION  ·  6 anterior + 6 posterior")
        c.setFillColor(MUTED)
        c.setFont(self.font_body, 8.5)
        c.drawString(14, self.height - 30, "Compare side to side at each level. Posterior bases first — fluid collects there.")

        # Two panels: anterior + posterior
        panel_w = (self.width - 36) / 2
        panel_h = self.height - 56
        panel_y = 14

        for panel_idx, (label, points) in enumerate(
            [("ANTERIOR", self.POINTS_ANT), ("POSTERIOR", self.POINTS_POST)]
        ):
            px = 14 + panel_idx * (panel_w + 8)
            py = panel_y
            # Panel box
            c.setFillColor(white)
            c.setStrokeColor(BORDER)
            c.setLineWidth(0.5)
            c.roundRect(px, py, panel_w, panel_h, 6, fill=1, stroke=1)
            # Panel label
            c.setFillColor(TEAL_700)
            c.setFont(self.font_body_bold, 9)
            c.drawString(px + 8, py + panel_h - 14, label)

            # Torso outline
            cx = px + panel_w / 2
            tx_left = px + panel_w * 0.2
            tx_right = px + panel_w * 0.8
            tx_top = py + panel_h - 28
            tx_bottom = py + 18
            c.setStrokeColor(TEAL_700)
            c.setLineWidth(1.2)
            c.setFillColor(HexColor("#FBF8EF"))
            path = c.beginPath()
            path.moveTo(tx_left, tx_top - 8)
            path.curveTo(cx - 14, tx_top + 4, cx + 14, tx_top + 4, tx_right, tx_top - 8)
            path.curveTo(tx_right + 4, py + panel_h * 0.5, tx_right - 4, tx_bottom + 18, tx_right - 8, tx_bottom)
            path.curveTo(tx_right - 14, tx_bottom - 4, tx_left + 14, tx_bottom - 4, tx_left + 8, tx_bottom)
            path.curveTo(tx_left + 4, tx_bottom + 18, tx_left - 4, py + panel_h * 0.5, tx_left, tx_top - 8)
            path.close()
            c.drawPath(path, fill=1, stroke=1)

            # Centerline
            c.setStrokeColor(BORDER_STRONG)
            c.setLineWidth(0.6)
            c.setDash(2, 2)
            c.line(cx, tx_top - 12, cx, tx_bottom + 4)
            c.setDash([])

            # Numbered points
            for i, (nx, ny) in enumerate(points):
                ax = px + nx * panel_w
                ay = py + ny * panel_h
                c.setFillColor(LIME_500)
                c.setStrokeColor(INK)
                c.setLineWidth(0.8)
                c.circle(ax, ay, 7, fill=1, stroke=1)
                c.setFillColor(INK)
                c.setFont(self.font_body_bold, 8)
                c.drawCentredString(ax, ay - 2.5, str(i + 1))
        c.restoreState()


# ═════════════════════════════════════════════════════════════════════
# Problem statement structure diagram
# ═════════════════════════════════════════════════════════════════════
class ProblemStatementStructure(Flowable):
    def __init__(self, width, font_body, font_body_bold, font_body_semi, font_display_italic):
        Flowable.__init__(self)
        self.width = width
        self.font_body = font_body
        self.font_body_bold = font_body_bold
        self.font_body_semi = font_body_semi
        self.font_display_italic = font_display_italic
        self.row_h = 78
        self.header_h = 32
        self.height = self.header_h + self.row_h * 3 + 14

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(CREAM)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.4)
        c.roundRect(0, 0, self.width, self.height, 8, fill=1, stroke=1)
        # Title
        c.setFillColor(TEAL_800)
        c.setFont(self.font_body_bold, 11)
        c.drawString(14, self.height - 18, "PROBLEM STATEMENT  ·  3-sentence structure")
        c.setFillColor(MUTED)
        c.setFont(self.font_body, 8.5)
        c.drawString(14, self.height - 30, "Faculty-scored. Clinical language only. Brevity wins.")

        sentences = [
            ("S1", "Who + CC + Duration",
             "H.H. is a 57-year-old Hispanic male who presents with elevated blood pressure noted at a community health fair, with no previous follow-up.",
             TEAL_600),
            ("S2", "Key positives + Risk factors",
             "Examination reveals BP 172/94 (L) and 178/98 (R), AV nicking on fundoscopy, and laterally displaced PMI; risk factors include 35-pack-year smoking, family history of premature CVD, and high-sodium diet.",
             LIME_500),
            ("S3", "Diagnostic impression + Must-not-miss",
             "Findings are consistent with Stage 2 essential hypertension with target organ damage; OSA is a must-not-miss given snoring, obesity, and HTN.",
             TEAL_800),
        ]
        y_start = self.height - self.header_h - 8
        for i, (tag, label, text, color) in enumerate(sentences):
            y = y_start - i * self.row_h
            # Tag badge
            c.setFillColor(color)
            c.roundRect(14, y - 24, 30, 18, 3, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont(self.font_body_bold, 9)
            c.drawCentredString(29, y - 18, tag)
            # Label
            c.setFillColor(INK)
            c.setFont(self.font_body_bold, 9.5)
            c.drawString(52, y - 4, label)
            # Example
            c.setFillColor(INK_2)
            c.setFont(self.font_display_italic, 8.5)
            # Word wrap the text manually
            words = text.split()
            max_w = self.width - 60
            line = ""
            ty = y - 18
            for word in words:
                test = (line + " " + word).strip()
                if c.stringWidth(test, self.font_display_italic, 8.5) > max_w:
                    c.drawString(52, ty, line)
                    line = word
                    ty -= 11
                else:
                    line = test
            if line:
                c.drawString(52, ty, line)
        c.restoreState()


# ═════════════════════════════════════════════════════════════════════
# Mid-document CTA box — promotes paid case guides
# ═════════════════════════════════════════════════════════════════════
class CTABox(Flowable):
    """A "Need case-specific help?" promo box, mid-document."""

    def __init__(self, width, font_body, font_body_bold, font_body_semi, font_display_semi, font_display_italic,
                 size="medium"):
        Flowable.__init__(self)
        self.width = width
        self.font_body = font_body
        self.font_body_bold = font_body_bold
        self.font_body_semi = font_body_semi
        self.font_display_semi = font_display_semi
        self.font_display_italic = font_display_italic
        self.size = size
        self.height = 96 if size == "medium" else 130

    def draw(self):
        c = self.canv
        c.saveState()
        h = self.height
        # Dark ink background with subtle teal gradient via overlay
        c.setFillColor(INK)
        c.roundRect(0, 0, self.width, h, 10, fill=1, stroke=0)
        # Lime accent rule on left
        c.setFillColor(LIME_500)
        c.rect(0, 0, 5, h, fill=1, stroke=0)

        # Eyebrow
        c.setFillColor(LIME_400)
        c.setFont(self.font_body_bold, 8)
        c.drawString(22, h - 18, "WHEN THE CHEAT SHEET ISN'T ENOUGH")

        # Headline
        c.setFillColor(CREAM)
        c.setFont(self.font_display_semi, 16)
        c.drawString(22, h - 42, "Get the case-specific guide.")

        # Subline
        c.setFillColor(Color(0.85, 0.83, 0.74))
        c.setFont(self.font_body, 9.5)
        c.drawString(22, h - 58, "Every history question, every PE finding, every scored item")
        c.drawString(22, h - 70, "for your exact case. Word + PDF, delivered same day.")

        # CTA "button" — right side
        btn_w = 130
        btn_x = self.width - btn_w - 18
        btn_y = h / 2 - 14
        c.setFillColor(LIME_500)
        c.roundRect(btn_x, btn_y, btn_w, 28, 14, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont(self.font_body_bold, 10)
        c.drawCentredString(btn_x + btn_w / 2, btn_y + 10, "Browse all cases →")

        # Price hint
        if self.size == "medium":
            c.setFillColor(MUTED)
            c.setFont(self.font_body, 8)
            c.drawString(22, 14, "From $150 single  ·  $390 3-bundle (save $60)  ·  $540 5-bundle (save $210)")

        c.restoreState()


# ═════════════════════════════════════════════════════════════════════
# Final-page strong CTA card — with discount code
# ═════════════════════════════════════════════════════════════════════
class FinalCTACard(Flowable):
    def __init__(self, width, font_body, font_body_bold, font_body_semi, font_display_semi):
        Flowable.__init__(self)
        self.width = width
        self.font_body = font_body
        self.font_body_bold = font_body_bold
        self.font_body_semi = font_body_semi
        self.font_display_semi = font_display_semi
        self.height = 230

    def draw(self):
        c = self.canv
        c.saveState()
        h = self.height

        # Single dark card with rounded corners
        c.setFillColor(INK)
        c.roundRect(0, 0, self.width, h, 12, fill=1, stroke=0)

        # Lime accent rule down the left edge
        c.setFillColor(LIME_500)
        c.rect(0, 12, 5, h - 24, fill=1, stroke=0)

        # ── UPPER SECTION (dark, content) ───────────────────
        # Eyebrow
        c.setFillColor(LIME_400)
        c.setFont(self.font_body_bold, 9)
        c.drawString(28, h - 28, "READY FOR THE FULL GUIDE?")

        # Headline (two lines, large display serif)
        c.setFillColor(CREAM)
        c.setFont(self.font_display_semi, 22)
        c.drawString(28, h - 60, "Walk into your case with")
        c.drawString(28, h - 86, "the answer key.")

        # Subline body copy
        c.setFillColor(Color(0.85, 0.83, 0.74))
        c.setFont(self.font_body, 9.5)
        c.drawString(28, h - 108, "Submission-ready iHuman case guides — every section walked through,")
        c.drawString(28, h - 122, "every scoring trap mapped, every test, EHR phrase, and management plan.")

        # ── DISCOUNT BANNER (inset lime panel) ──────────────
        # Banner sits inside the card with margin on all sides
        banner_x = 16
        banner_w = self.width - 32
        banner_h = 44
        banner_y = 22  # margin from bottom of card

        c.setFillColor(LIME_500)
        c.roundRect(banner_x, banner_y, banner_w, banner_h, 8, fill=1, stroke=0)

        # Discount code text — left side of banner
        c.setFillColor(INK)
        c.setFont(self.font_body_bold, 11)
        c.drawString(banner_x + 16, banner_y + banner_h - 18, "USE CODE  CPLFIRST15")
        c.setFillColor(HexColor("#3A4D2A"))
        c.setFont(self.font_body, 8.5)
        c.drawString(banner_x + 16, banner_y + banner_h - 30, "15% off your first single case  ·  bundles already discounted")

        # CTA "button" — right side of banner
        btn_w = 150
        btn_h = 28
        btn_x = banner_x + banner_w - btn_w - 12
        btn_y = banner_y + (banner_h - btn_h) / 2
        c.setFillColor(INK)
        c.roundRect(btn_x, btn_y, btn_w, btn_h, 14, fill=1, stroke=0)
        c.setFillColor(LIME_500)
        c.setFont(self.font_body_bold, 10.5)
        c.drawCentredString(btn_x + btn_w / 2, btn_y + 10, "Browse the catalog →")

        # URL footer (above banner, in the dark area)
        c.setFillColor(MUTED)
        c.setFont(self.font_body, 8)
        c.drawString(28, banner_y + banner_h + 8, "cpl-site.vercel.app")

        c.restoreState()


# ═════════════════════════════════════════════════════════════════════
# Medication dosing reference card — iHuman-framed, with disclaimer
# ═════════════════════════════════════════════════════════════════════
class MedDosingCard(Flowable):
    """A reference card for the most-recurring iHuman medications.

    Framed explicitly as "answer key" content, not clinical prescribing reference.
    """
    MEDS = [
        # (case_type, drug, full_order, notes)
        ("Stage 2 HTN (Harvey/Felipe/Herbie/Anselmo)",
         "Lisinopril 10 mg + Hydrochlorothiazide 25 mg",
         "PO daily, dispense #30, 2 refills (each)",
         "Two-drug therapy required per ACC/AHA 2017"),
        ("GAS Pharyngitis (Amanda Wheaton, et al.)",
         "Penicillin V 500 mg",
         "PO BID × 10 days, dispense #20, 0 refills",
         "10-day course mandatory. Amoxicillin 500mg BID acceptable alt."),
        ("Migraine acute (Bebe/Marta/Jessica/Mabel)",
         "Sumatriptan 50 mg",
         "PO at onset, may repeat × 1 after 2h; dispense #9, 0 refills",
         "Max 200 mg/day. ≤10 days/month. Hold if pregnant."),
        ("Migraine adjunct nausea",
         "Metoclopramide 10 mg",
         "PO PRN nausea, max 45 mg/day; dispense #20, 0 refills",
         "Often paired with Sumatriptan."),
        ("Migraine NSAID option",
         "Naproxen sodium 500 mg",
         "PO once, may repeat once; dispense #18, 0 refills",
         "Max 1000 mg/day. Alternative to triptan."),
        ("Hyperlipidemia (Cynthia Francis)",
         "Atorvastatin 20 mg",
         "PO at bedtime, dispense #30, 2 refills",
         "Continue thyroid hormone replacement concurrently."),
        ("ADHD inattentive (Kennedy Poole)",
         "Methylphenidate ER 18 mg",
         "PO morning, dispense #30, 0 refills, Schedule II",
         "Baseline ECG before start. Titrate q2 weeks."),
        ("Pediatric viral GE (Samantha/Courtney)",
         "Oral rehydration solution (Pedialyte)",
         "Small frequent sips, replace fluid losses",
         "No antiemetics in mild dehydration. Return for any worsening."),
    ]

    def __init__(self, width, font_body, font_body_bold, font_body_semi, font_display_semi):
        Flowable.__init__(self)
        self.width = width
        self.font_body = font_body
        self.font_body_bold = font_body_bold
        self.font_body_semi = font_body_semi
        self.font_display_semi = font_display_semi
        self.row_h = 46
        self.title_h = 24       # title bar
        self.disclaimer_h = 26  # warning banner
        self.header_total = self.title_h + self.disclaimer_h + 12  # padding
        self.bottom_pad = 22
        self.height = self.header_total + self.row_h * len(self.MEDS) + self.bottom_pad

    def draw(self):
        c = self.canv
        c.saveState()
        h = self.height
        # Outer
        c.setFillColor(CREAM)
        c.setStrokeColor(BORDER_STRONG)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, self.width, h, 8, fill=1, stroke=1)
        c.setFillColor(TEAL_500)
        c.rect(0.5, 8, 3.5, h - 16, fill=1, stroke=0)

        # Title
        c.setFillColor(TEAL_800)
        c.setFont(self.font_body_bold, 12)
        c.drawString(18, h - 20, "iHUMAN MEDICATION ANSWERS  ·  by case template")

        # Disclaimer banner — positioned BELOW the title with clear separation
        disclaimer_y = h - self.title_h - self.disclaimer_h - 2
        c.setFillColor(HexColor("#FFF6E8"))
        c.setStrokeColor(WARM_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(18, disclaimer_y, self.width - 36, self.disclaimer_h - 4, 3, fill=1, stroke=1)
        c.setFillColor(TRAP_AMBER)
        c.setFont(self.font_body_bold, 8)
        c.drawString(26, disclaimer_y + 11, "⚠ FOR iHUMAN CASE DOCUMENTATION ONLY")
        c.setFillColor(MUTED)
        c.setFont(self.font_body, 7.5)
        c.drawString(26, disclaimer_y + 2, "Verify all dosing with current Epocrates/UpToDate before any clinical application.")

        # Rows — start below the disclaimer banner
        y_start = disclaimer_y - 6
        for i, (case_type, drug, order, notes) in enumerate(self.MEDS):
            y_top = y_start - i * self.row_h
            y_bottom = y_top - self.row_h
            # Row separator
            if i > 0:
                c.setStrokeColor(BORDER)
                c.setLineWidth(0.3)
                c.line(14, y_top, self.width - 14, y_top)
            # Case type
            c.setFillColor(TEAL_700)
            c.setFont(self.font_body_bold, 8)
            c.drawString(18, y_top - 12, case_type.upper())
            # Drug
            c.setFillColor(INK)
            c.setFont(self.font_body_bold, 10)
            c.drawString(18, y_top - 24, drug)
            # Order
            c.setFillColor(INK_2)
            c.setFont(self.font_body, 9)
            c.drawString(18, y_top - 34, order)
            # Notes
            c.setFillColor(MUTED)
            c.setFont(self.font_body, 8)
            c.drawString(18, y_top - 43, notes)

        # Bottom disclaimer
        c.setFillColor(MUTED)
        c.setFont(self.font_body, 7)
        c.drawCentredString(self.width / 2, 10,
                            "Doses reflect what the iHuman platform expects on listed case templates. Not for clinical use.")
        c.restoreState()


# ═════════════════════════════════════════════════════════════════════
# 6-part Management Plan visual
# ═════════════════════════════════════════════════════════════════════
class SixPartPlanVisual(Flowable):
    PARTS = [
        ("Dx", "DIAGNOSTICS", "Tests ordered — or 'no tests needed' with rationale"),
        ("Rx", "PHARMACOLOGIC", "Name, dose, route, frequency, duration, dispense qty, refills"),
        ("Non-Rx", "NON-PHARM", "Lifestyle, diet, exercise, sleep, behavior change"),
        ("Ref", "REFERRALS", "Specialty, urgency, reason"),
        ("Edu", "EDUCATION", "Disease process, warning signs, when to return"),
        ("F/U", "FOLLOW-UP", "When + monitoring parameters + ER return precautions"),
    ]

    def __init__(self, width, font_body, font_body_bold, font_body_semi):
        Flowable.__init__(self)
        self.width = width
        self.font_body = font_body
        self.font_body_bold = font_body_bold
        self.font_body_semi = font_body_semi
        n = len(self.PARTS)
        # 2 columns × 3 rows
        self.cols = 2
        self.rows = math.ceil(n / self.cols)
        self.cell_h = 56
        self.header_h = 28
        self.height = self.header_h + self.rows * self.cell_h + 10

    def draw(self):
        c = self.canv
        c.saveState()
        h = self.height
        c.setFillColor(CREAM)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.4)
        c.roundRect(0, 0, self.width, h, 8, fill=1, stroke=1)
        c.setFillColor(TEAL_800)
        c.setFont(self.font_body_bold, 11)
        c.drawString(14, h - 18, "THE 6-PART MANAGEMENT PLAN  ·  Faculty look for all six")

        cell_w = (self.width - 28) / self.cols
        for i, (tag, label, detail) in enumerate(self.PARTS):
            row = i // self.cols
            col = i % self.cols
            x = 14 + col * cell_w
            y = h - self.header_h - (row + 1) * self.cell_h + 6

            c.setFillColor(WARM_BG)
            c.setStrokeColor(TEAL_500)
            c.setLineWidth(0.9)
            c.roundRect(x + 2, y, cell_w - 4, self.cell_h - 6, 5, fill=1, stroke=1)

            # Tag badge
            c.setFillColor(TEAL_700)
            badge_w = 50
            c.roundRect(x + 8, y + self.cell_h - 22, badge_w, 14, 3, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont(self.font_body_bold, 8.5)
            c.drawCentredString(x + 8 + badge_w / 2, y + self.cell_h - 18, tag)

            # Label
            c.setFillColor(INK)
            c.setFont(self.font_body_bold, 9.5)
            c.drawString(x + 64, y + self.cell_h - 18, label)

            # Detail
            c.setFillColor(MUTED)
            c.setFont(self.font_body, 8)
            # Word wrap to fit cell_w - 16
            max_w = cell_w - 22
            words = detail.split()
            lines = []
            cur = ""
            for word in words:
                test = (cur + " " + word).strip()
                if c.stringWidth(test, self.font_body, 8) > max_w and cur:
                    lines.append(cur)
                    cur = word
                else:
                    cur = test
            if cur:
                lines.append(cur)
            ty = y + self.cell_h - 34
            for line in lines[:2]:
                c.drawString(x + 10, ty, line)
                ty -= 10

        c.restoreState()
