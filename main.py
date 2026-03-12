import streamlit as st  # type: ignore

from services.quiz_service import process_pending_generation
from state import initialize_state
from ui.completed_screen import render_completed_screen
from ui.quiz_screen import render_quiz_ui
from ui.setup_screen import render_setup_screen
from ui.sidebar import render_sidebar
from ui.styles import render_close_sidebar_once, render_generating_overlay, render_styles


def main() -> None:
    st.set_page_config(
        page_title="Gemini Quiz Generator",
        page_icon="💀",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    render_styles()
    initialize_state()
    if not st.session_state.get("sidebar_default_applied"):
        render_close_sidebar_once()
        st.session_state.sidebar_default_applied = True
    render_sidebar()

    if st.session_state.is_generating:
        render_generating_overlay()
        process_pending_generation()
        return

    phase = st.session_state.phase
    if phase in {"setup", "ready"}:
        render_setup_screen()
    elif phase == "in_progress":
        render_quiz_ui()
    elif phase == "completed":
        render_completed_screen()
    else:
        st.error(f"Unknown phase: {phase}")


if __name__ == "__main__":
    main()
