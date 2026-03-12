import json
from io import BytesIO
from xml.sax.saxutils import escape

import streamlit as st  # type: ignore

from services.question_io import question_dicts_to_models

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
except ImportError:
    colors = None
    LETTER = None
    ParagraphStyle = None
    SimpleDocTemplate = None
    Spacer = None
    getSampleStyleSheet = None
    inch = None


def build_questions_download() -> str:
    return json.dumps(st.session_state.questions, indent=2, ensure_ascii=False)


def has_pdf_export_support() -> bool:
    return all(
        dependency is not None
        for dependency in (colors, LETTER, ParagraphStyle, SimpleDocTemplate, Spacer, getSampleStyleSheet, inch)
    )


def build_questions_pdf_download() -> bytes:
    if not has_pdf_export_support():
        raise RuntimeError("Missing dependency: install reportlab to enable PDF exports.")

    questions = question_dicts_to_models(st.session_state.questions)
    buffer = BytesIO()
    document = SimpleDocTemplate(  # type: ignore[operator]
        buffer,
        pagesize=LETTER,  # type: ignore[arg-type]
        leftMargin=0.75 * inch,  # type: ignore[operator]
        rightMargin=0.75 * inch,  # type: ignore[operator]
        topMargin=0.75 * inch,  # type: ignore[operator]
        bottomMargin=0.75 * inch,  # type: ignore[operator]
        title="Quiz Questions",
    )

    styles = getSampleStyleSheet()  # type: ignore[operator]
    title_style = ParagraphStyle(  # type: ignore[operator]
        "QuizTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#111827"),  # type: ignore[union-attr]
        spaceAfter=12,
    )
    meta_style = ParagraphStyle(  # type: ignore[operator]
        "QuizMeta",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#4B5563"),  # type: ignore[union-attr]
        spaceAfter=6,
    )
    question_style = ParagraphStyle(  # type: ignore[operator]
        "QuizQuestion",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#111827"),  # type: ignore[union-attr]
        spaceAfter=6,
    )
    option_style = ParagraphStyle(  # type: ignore[operator]
        "QuizOption",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1F2937"),  # type: ignore[union-attr]
        leftIndent=12,
        spaceAfter=4,
    )
    answer_style = ParagraphStyle(  # type: ignore[operator]
        "QuizAnswer",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#166534"),  # type: ignore[union-attr]
        spaceAfter=14,
    )

    story = [
        Paragraph("Quiz Questions", title_style),  # type: ignore[operator]
        Paragraph(f"Topic: {escape(st.session_state.topic or 'general knowledge')}", meta_style),  # type: ignore[operator]
        Paragraph(f"Difficulty: {escape(st.session_state.difficulty)}", meta_style),  # type: ignore[operator]
        Paragraph(f"Total questions: {len(questions)}", meta_style),  # type: ignore[operator]
        Spacer(1, 0.15 * inch),  # type: ignore[operator]
    ]

    for index, question in enumerate(questions, start=1):
        story.append(Paragraph(f"Q{index}. {escape(question.question)}", question_style))  # type: ignore[operator]
        for option_index, option in enumerate(question.options, start=1):
            option_label = chr(ord("A") + option_index - 1)
            story.append(Paragraph(f"{option_label}. {escape(option)}", option_style))  # type: ignore[operator]
        story.append(Paragraph(f"Correct answer: {escape(question.correct_answer)}", answer_style))  # type: ignore[operator]

    document.build(story)
    return buffer.getvalue()
