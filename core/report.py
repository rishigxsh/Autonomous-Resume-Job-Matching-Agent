"""PDF report generator for the Resume–Job Matching Agent.

Deterministic, LLM-free. Produces a clean white PDF from a MatchReportJSON
and FeedbackResponse using reportlab.
"""

from __future__ import annotations

import io
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from api.response_models import FeedbackResponse
from schemas.models import MatchReportJSON

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

_styles = getSampleStyleSheet()

_TITLE_STYLE = ParagraphStyle(
    "ReportTitle",
    parent=_styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=20,
    alignment=1,  # center
    spaceAfter=4,
)

_SUBTITLE_STYLE = ParagraphStyle(
    "ReportSubtitle",
    parent=_styles["Normal"],
    fontName="Helvetica",
    fontSize=11,
    alignment=1,
    textColor=colors.HexColor("#555555"),
    spaceAfter=12,
)

_SECTION_STYLE = ParagraphStyle(
    "SectionHeading",
    parent=_styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=13,
    spaceBefore=16,
    spaceAfter=6,
    textColor=colors.HexColor("#222222"),
)

_BODY_STYLE = ParagraphStyle(
    "BodyText",
    parent=_styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=14,
    spaceAfter=4,
)

_BULLET_STYLE = ParagraphStyle(
    "BulletText",
    parent=_BODY_STYLE,
    leftIndent=16,
    bulletIndent=6,
)

_EVIDENCE_STYLE = ParagraphStyle(
    "EvidenceText",
    parent=_BODY_STYLE,
    fontName="Helvetica-Oblique",
    fontSize=9,
    leftIndent=28,
    textColor=colors.HexColor("#555555"),
)

_SCORE_STYLE = ParagraphStyle(
    "BigScore",
    parent=_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=28,
    alignment=1,
    spaceAfter=8,
)

_HR = HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"),
                  spaceAfter=8, spaceBefore=8)


# ---------------------------------------------------------------------------
# Component labels/weights
# ---------------------------------------------------------------------------

_COMPONENTS = [
    ("required_skills_score", "Required Skills", 35),
    ("preferred_skills_score", "Preferred Skills", 15),
    ("experience_score", "Experience", 25),
    ("responsibilities_score", "Responsibilities", 15),
    ("education_score", "Education", 10),
]


def _escape(text: str) -> str:
    """Escape XML special characters for reportlab Paragraphs."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_pdf_report(
    match_report: MatchReportJSON,
    feedback: FeedbackResponse,
) -> bytes:
    """Generate a structured PDF report and return raw bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    story: List = []

    # --- Section 1: Header ---
    story.append(Paragraph("Resume–Job Match Report", _TITLE_STYLE))
    story.append(Paragraph(
        f"{_escape(match_report.resume_name)}  ·  {_escape(match_report.job_title)}",
        _SUBTITLE_STYLE,
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#333333"),
                             spaceAfter=12))

    # --- Section 2: Score overview ---
    story.append(Paragraph(f"{match_report.overall_score} / 100", _SCORE_STYLE))
    story.append(Spacer(1, 4))

    # Component table
    table_data = [["Category", "Score", "Weight"]]
    cs = match_report.component_scores
    for attr, label, weight in _COMPONENTS:
        table_data.append([label, str(getattr(cs, attr)), f"{weight}%"])

    table = Table(table_data, colWidths=[3 * inch, 1.2 * inch, 1 * inch])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F0F0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1, 8))

    # Rationale
    story.append(Paragraph(_escape(match_report.rationale), _BODY_STYLE))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"),
                             spaceAfter=8, spaceBefore=12))

    # --- Section 3: Matched Skills ---
    story.append(Paragraph("Matched Skills", _SECTION_STYLE))
    if match_report.matched_skills:
        for se in match_report.matched_skills:
            story.append(Paragraph(f"<b>{_escape(se.skill)}</b>", _BODY_STYLE))
            for snippet in se.evidence:
                story.append(Paragraph(f"• {_escape(snippet)}", _EVIDENCE_STYLE))
    else:
        story.append(Paragraph("None", _BODY_STYLE))
    story.append(Spacer(1, 6))

    # --- Section 4: Missing Skills ---
    story.append(Paragraph("Missing Skills", _SECTION_STYLE))
    if match_report.missing_skills:
        missing_text = ", ".join(se.skill for se in match_report.missing_skills)
        story.append(Paragraph(_escape(missing_text), _BODY_STYLE))
    else:
        story.append(Paragraph("All required skills matched.", _BODY_STYLE))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"),
                             spaceAfter=8, spaceBefore=12))

    # --- Section 5: Top Suggestions ---
    story.append(Paragraph("Top Suggestions", _SECTION_STYLE))
    for i, suggestion in enumerate(feedback.suggestions, 1):
        story.append(Paragraph(f"{i}. {_escape(suggestion)}", _BULLET_STYLE))
    story.append(Spacer(1, 6))

    # --- Section 6: Rewritten Bullets ---
    story.append(Paragraph("Rewritten Resume Bullets", _SECTION_STYLE))
    for bullet in feedback.rewritten_bullets:
        story.append(Paragraph(f"• {_escape(bullet)}", _BULLET_STYLE))

    doc.build(story)
    return buf.getvalue()
