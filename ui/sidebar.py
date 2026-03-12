from datetime import datetime

import streamlit as st  # type: ignore

from constants import GEMINI_API_KEY_NAME
from services.gemini_service import build_questions_download, has_gemini_api_key
from services.question_io import load_questions_from_uploaded_file
from services.quiz_service import queue_generation, store_questions
from state import mark_quiz_ready, reset_quiz


def render_sidebar() -> None:
    key_is_configured = has_gemini_api_key()
    st.sidebar.title("Quiz Settings")
    st.sidebar.write("Generate quiz questions with Gemini.")
    st.sidebar.caption(f"Phase: `{st.session_state.phase}`")
    if not key_is_configured:
        st.sidebar.warning(
            f"Gemini is not configured yet. Add `{GEMINI_API_KEY_NAME}` to Streamlit secrets before generating questions."
        )

    topic = st.sidebar.text_input("Quiz topic", value=st.session_state.topic)
    difficulty_options = ["easy", "medium", "hard"]
    difficulty = st.sidebar.selectbox(
        "Difficulty",
        difficulty_options,
        index=difficulty_options.index(st.session_state.difficulty),
    )
    st.session_state.topic = topic
    st.session_state.difficulty = difficulty
    questions_to_generate = st.sidebar.number_input(
        "Questions to generate",
        min_value=1,
        max_value=5,
        value=int(st.session_state.questions_to_generate),
        step=1,
    )
    st.session_state.questions_to_generate = int(questions_to_generate)

    feedback = st.session_state.pop("generation_feedback", None)
    if feedback:
        if feedback["type"] == "success":
            st.sidebar.success(feedback["message"])
        else:
            st.sidebar.error(feedback["message"])

    if st.sidebar.button("Generate Questions", disabled=not key_is_configured):
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

    st.sidebar.markdown("---")
    st.sidebar.write(f"**Total Questions Loaded:** {len(st.session_state.questions)}")
    st.sidebar.download_button(
        "Download Questions JSON",
        data=build_questions_download(),
        file_name=f"quiz_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        disabled=not st.session_state.questions,
    )
    if st.sidebar.button("Reset Progress"):
        if st.session_state.questions:
            reset_quiz(phase="ready")
            mark_quiz_ready()
        else:
            reset_quiz()
        st.rerun()
