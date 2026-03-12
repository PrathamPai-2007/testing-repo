import streamlit as st  # type: ignore

from constants import DIFFICULTY_DETAILS, GEMINI_API_KEY_NAME
from services.gemini_service import has_gemini_api_key
from services.quiz_service import queue_generation
from state import start_quiz
from ui.settings_controls import get_current_difficulty_details, render_quiz_configuration_controls


def render_setup_screen() -> None:
    key_is_configured = has_gemini_api_key()
    difficulty_details = get_current_difficulty_details()
    st.title("Gemini Quiz Generator")
    st.write("Set a topic and difficulty here or in the sidebar. Both stay in sync.")
    if not key_is_configured:
        st.info(
            f"To generate new quiz questions, add `{GEMINI_API_KEY_NAME}` to your Streamlit secrets first."
        )

    with st.container():
        render_quiz_configuration_controls(
            st,
            topic_key="setup_topic",
            difficulty_key="setup_difficulty",
            question_count_key="setup_question_count",
        )

    st.caption(
        "Difficulty guide: "
        + " | ".join(
            f"{level}: {details['description']}"
            for level, details in DIFFICULTY_DETAILS.items()
        )
    )

    if st.session_state.questions:
        st.subheader("Quiz Ready")
        st.write(
            f"{len(st.session_state.questions)} question(s) prepared for "
            f"`{st.session_state.topic or 'general knowledge'}` at "
            f"`{difficulty_details['label']}` difficulty."
        )
        start_col, regen_col = st.columns(2)
        with start_col:
            if st.button("Start Quiz", type="primary"):
                start_quiz()
                st.rerun()
        with regen_col:
            if st.button("Generate from Scratch", disabled=not key_is_configured):
                queue_generation(
                    count=st.session_state.questions_to_generate,
                    jump_to="first_new",
                    next_phase="ready",
                    replace_existing=True,
                )
                st.rerun()
        st.info("Use either this screen or the sidebar to adjust topic and difficulty before starting.")
        return

    st.subheader("No Questions Yet")
    st.write(
        f"Current settings: topic `{st.session_state.topic or 'general knowledge'}`, "
        f"difficulty `{difficulty_details['label']}`, "
        f"{int(st.session_state.questions_to_generate)} question(s)."
    )
    if st.button("Generate from Scratch", type="primary", disabled=not key_is_configured):
        queue_generation(
            count=st.session_state.questions_to_generate,
            jump_to="first_new",
            next_phase="ready",
            replace_existing=True,
        )
        st.rerun()
