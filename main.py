import streamlit as st  # type: ignore

from services.auth_service import restore_authenticated_user, touch_user_last_online
from services.quiz_service import process_pending_generation
from state import clear_auth_state, has_app_access, initialize_state, is_authenticated, is_guest_user, sync_authenticated_user
from ui.admin_screen import render_admin_screen
from ui.auth_screen import render_auth_screen
from ui.completed_screen import render_completed_screen
from ui.history_screen import render_history_screen
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

    restored_user = restore_authenticated_user(
        access_token=str(st.session_state.get("auth_access_token") or ""),
        refresh_token=str(st.session_state.get("auth_refresh_token") or ""),
    )
    if restored_user is None:
        if st.session_state.get("auth_access_token") or st.session_state.get("auth_refresh_token"):
            clear_auth_state()
    else:
        sync_authenticated_user(restored_user)

    if not has_app_access():
        render_auth_screen()
        return

    if is_authenticated():
        try:
            touch_user_last_online(
                user_id=str(st.session_state.auth_user_id),
                access_token=str(st.session_state.auth_access_token),
                refresh_token=str(st.session_state.auth_refresh_token),
            )
        except RuntimeError:
            clear_auth_state()
            st.rerun()
    elif is_guest_user() and st.session_state.get("app_screen") in {"history", "admin"}:
        st.session_state.app_screen = "quiz"

    if not st.session_state.get("sidebar_default_applied"):
        render_close_sidebar_once()
        st.session_state.sidebar_default_applied = True
    render_sidebar()

    if st.session_state.get("app_screen") == "admin":
        render_admin_screen()
        return
    if st.session_state.get("app_screen") == "history":
        render_history_screen()
        return

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
