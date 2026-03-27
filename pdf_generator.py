"""
pdf_generator.py

Generates two PDFs:
  1. Score cards — one per 3"x5" page, for printing on index cards.
  2. Answer key — letter-size pages with a table of all courses.
"""

from datetime import datetime
from reportlab.lib.pagesizes import letter, inch
from reportlab.lib.units import inch as rl_inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas


# -- Score Cards (3x5 index cards) ------------------------------------------

# Card dimensions: 3" wide x 5" tall (portrait orientation for an index card)
CARD_W = 3 * rl_inch
CARD_H = 5 * rl_inch


def generate_score_cards(courses, output_path, timestamp=None):
    """
    Create a PDF with one 3x5 page per course.
    Each page is a single score card.
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    c = canvas.Canvas(str(output_path), pagesize=(CARD_W, CARD_H))

    for course in courses:
        _draw_score_card(c, course, timestamp)
        c.showPage()

    c.save()


def _draw_score_card(c, course, timestamp):
    """Draw a single score card on the current 3x5 page."""
    margin = 0.25 * rl_inch
    usable_w = CARD_W - 2 * margin

    # Current y position, starting from top
    y = CARD_H - margin

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(CARD_W / 2, y - 14, "SCORE CARD")
    y -= 28

    # Course label and starting point
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y - 11,
                 f"Course {course.label} — Starting Point No. {course.start_station}")
    y -= 22

    # Separator line
    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.5)
    c.line(margin, y, CARD_W - margin, y)
    y -= 12

    # Leg instructions
    c.setFont("Helvetica", 10)
    for i, leg in enumerate(course.legs):
        if i == 0:
            text = f"Head {leg.azimuth}\u00b0 for {leg.distance} feet"
        else:
            text = f"Then {leg.azimuth}\u00b0 for {leg.distance} feet"
        c.drawString(margin, y - 10, text)
        y -= 16

    # Spacer before fill-in section
    y -= 10

    # Separator line
    c.line(margin, y, CARD_W - margin, y)
    y -= 18

    # Fill-in fields
    c.setFont("Helvetica", 10)
    fields = [
        "MY DESTINATION: ________",
        "CORRECT DESTINATION: ________",
        "SCORE: ________",
    ]
    for field_text in fields:
        c.drawRightString(CARD_W - margin, y - 10, field_text)
        y -= 18

    # Timestamp at the bottom
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.grey)
    c.drawRightString(CARD_W - margin, margin, f"Generated: {timestamp}")
    c.setFillColor(colors.black)


# -- Answer Key (letter-size) -----------------------------------------------

def generate_answer_key(courses, num_legs, output_path, timestamp=None):
    """
    Create a letter-size PDF with a table showing all courses and answers.
    Columns: Course, Start, Leg 1, Leg 2, ..., Leg N, Destination
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    styles = getSampleStyleSheet()

    # Custom styles for the table cells
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
    )
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=12,
    )
    ts_style = ParagraphStyle(
        'TimestampStyle',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.grey,
        alignment=2,  # right-aligned
    )

    # Build table data
    header_row = ["Course", "Start"]
    for i in range(1, num_legs + 1):
        header_row.append(f"Leg {i}")
    header_row.append("Dest.")
    header_row = [Paragraph(f"<b>{h}</b>", header_style) for h in header_row]

    data = [header_row]
    for course in courses:
        row = [
            Paragraph(course.label, cell_style),
            Paragraph(str(course.start_station), cell_style),
        ]
        for leg in course.legs:
            row.append(Paragraph(f"{leg.azimuth}\u00b0 / {leg.distance}'", cell_style))
        row.append(Paragraph(f"<b>{course.destination}</b>", cell_style))
        data.append(row)

    # Calculate column widths
    # Available width on letter paper with margins
    page_w = letter[0]
    margin = 0.6 * rl_inch
    usable_w = page_w - 2 * margin

    # Fixed columns: Course (0.5"), Start (0.4"), Dest (0.4")
    fixed = 0.5 * rl_inch + 0.4 * rl_inch + 0.4 * rl_inch
    leg_col_w = (usable_w - fixed) / num_legs

    col_widths = [0.5 * rl_inch, 0.4 * rl_inch]
    col_widths += [leg_col_w] * num_legs
    col_widths += [0.4 * rl_inch]

    table = Table(data, colWidths=col_widths, repeatRows=1)

    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#333333")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f0f0f0")]),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

        # Alignment
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))

    # Build the document
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=0.5 * rl_inch,
        bottomMargin=0.5 * rl_inch,
    )

    elements = [
        Paragraph("COMPASS GAME — ANSWER KEY", title_style),
        table,
        Spacer(1, 12),
        Paragraph(f"Generated: {timestamp}", ts_style),
    ]

    doc.build(elements)
