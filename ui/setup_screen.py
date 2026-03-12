import streamlit as st  # type: ignore

from constants import GEMINI_API_KEY_NAME
from services.gemini_service import has_gemini_api_key
from services.quiz_service import queue_generation
from state import start_quiz


def render_setup_screen() -> None:
    key_is_configured = has_gemini_api_key()
    st.title("Gemini Quiz Generator")
    st.write("Set a topic, difficulty, and question count in the sidebar, then generate a quiz.")
    if not key_is_configured:
        st.info(
            f"To generate new quiz questions, add `{GEMINI_API_KEY_NAME}` to your Streamlit secrets first."
        )

    if st.session_state.questions:
        st.subheader("Quiz Ready")
        st.write(
            f"{len(st.session_state.questions)} question(s) prepared for "
            f"`{st.session_state.topic or 'general knowledge'}` at "
            f"`{st.session_state.difficulty}` difficulty."
        )
        start_col, regen_col = st.columns(2)
        with start_col:
            if st.button("Start Quiz", type="primary"):
                start_quiz()
                st.rerun()
        with regen_col:
            if st.button("Generate Fresh Quiz", disabled=not key_is_configured):
                queue_generation(
                    count=st.session_state.questions_to_generate,
                    jump_to="first_new",
                    next_phase="ready",
                    replace_existing=True,
                )
                st.rerun()
        st.info("Use the sidebar to change the topic or difficulty before starting.")
        return

    st.subheader("No Questions Yet")
    st.write(
        f"Current settings: topic `{st.session_state.topic or 'general knowledge'}`, "
        f"difficulty `{st.session_state.difficulty}`, "
        f"{int(st.session_state.questions_to_generate)} question(s)."
    )
    if st.button("Generate Quiz", type="primary", disabled=not key_is_configured):
        queue_generation(
            count=st.session_state.questions_to_generate,
            jump_to="first_new",
            next_phase="ready",
            replace_existing=True,
        )
        st.rerun()
