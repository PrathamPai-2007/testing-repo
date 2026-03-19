from datetime import datetime

import streamlit as st  # type: ignore

from constants import GEMINI_API_KEY_NAME
from services.export_service import build_questions_download, build_questions_pdf_download, has_pdf_export_support
from services.gemini_service import has_gemini_api_key
from services.question_io import load_questions_from_uploaded_file
from services.quiz_service import queue_generation, store_questions
from state import mark_quiz_ready
from ui.settings_controls import render_quiz_configuration_controls


def render_sidebar() -> None:
    key_is_configured = has_gemini_api_key()
    st.sidebar.title("Quiz Settings")
    st.sidebar.write("Generate quiz questions with Gemini.")
    if not key_is_configured:
        st.sidebar.warning(
            f"Gemini is not configured yet. Add `{GEMINI_API_KEY_NAME}` to Streamlit secrets before generating questions."
        )

    render_quiz_configuration_controls(
        st.sidebar,
        topic_key="sidebar_topic",
        difficulty_key="sidebar_difficulty",
        question_count_key="sidebar_question_count",
        model_key="sidebar_model",
    )

    feedback = st.session_state.pop("generation_feedback", None)
    if feedback:
        if feedback["type"] == "success":
            st.sidebar.success(feedback["message"])
        else:
            st.sidebar.error(feedback["message"])

    if st.sidebar.button("Generate from Scratch", disabled=not key_is_configured):
        try:
            queue_generation(
                count=st.session_state.questions_to_generate,
                jump_to="first_new",
                next_phase="ready",
                replace_existing=True,
            )
            st.rerun()
        except Exception as exc:
            st.sidebar.error(f"Could not generate question: {exc}")

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Active Gemini model: `{st.session_state.gemini_model}`")
    st.sidebar.write(f"**Total Questions Loaded:** {len(st.session_state.questions)}")
    pdf_download = None
    pdf_export_error = None
    if st.session_state.questions and has_pdf_export_support():
        try:
            pdf_download = build_questions_pdf_download()
        except Exception as exc:
            pdf_export_error = str(exc)
    st.sidebar.download_button(
        "Download Questions PDF",
        data=pdf_download or b"",
        file_name=f"quiz_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        disabled=not st.session_state.questions or pdf_download is None,
    )
    if not has_pdf_export_support():
        st.sidebar.caption("Install `reportlab` to enable PDF downloads.")
    elif pdf_export_error:
        st.sidebar.caption(f"PDF export unavailable: {pdf_export_error}")
    st.sidebar.download_button(
        "Download Questions JSON",
        data=build_questions_download(),
        file_name=f"quiz_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        disabled=not st.session_state.questions,
    )
    st.sidebar.write("Or upload your own questions.")
    uploaded_file = st.sidebar.file_uploader("Upload JSON or CSV", type=["json", "csv"])
    if uploaded_file is not None:
        st.sidebar.caption("JSON needs: question, options, correct_answer. CSV needs question, option1-4, correct_answer.")
        if st.sidebar.button("Load Uploaded Questions"):
            try:
                uploaded_questions = load_questions_from_uploaded_file(uploaded_file)
                store_questions(
                    questions=uploaded_questions,
                    jump_to="first_new",
                    replace_existing=True,
                )
                mark_quiz_ready()
                st.session_state.generation_feedback = {
                    "type": "success",
                    "message": f"Loaded {len(uploaded_questions)} question(s) from file.",
                }
                st.rerun()
            except Exception as exc:
                st.sidebar.error(f"Could not load file: {exc}")
