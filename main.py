import time

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


LAST_ONLINE_SYNC_INTERVAL_SECONDS = 300.0


def build_auth_token_key(access_token: str | None, refresh_token: str | None) -> str | None:
    normalized_access_token = str(access_token).strip() if access_token else None
    normalized_refresh_token = str(refresh_token).strip() if refresh_token else None
    if not normalized_access_token or not normalized_refresh_token:
        return None
    return f"{normalized_access_token}:{normalized_refresh_token}"


def should_restore_authenticated_user(
    *,
    token_key: str | None,
    restored_token_key: str | None,
    is_authenticated_user: bool,
) -> bool:
    return bool(token_key) and (token_key != restored_token_key or not is_authenticated_user)


def should_touch_last_online(
    *,
    token_key: str | None,
    last_synced_token_key: str | None,
    last_synced_at: float | None,
    now_ts: float,
    min_interval_seconds: float = LAST_ONLINE_SYNC_INTERVAL_SECONDS,
) -> bool:
    if not token_key:
        return False
    if last_synced_token_key != token_key or last_synced_at is None:
        return True
    return (now_ts - float(last_synced_at)) >= min_interval_seconds


def main() -> None:
    st.set_page_config(
        page_title="Gemini Quiz Generator",
        page_icon="💀",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    render_styles()
    initialize_state()

    token_key = build_auth_token_key(
        access_token=st.session_state.get("auth_access_token"),
        refresh_token=st.session_state.get("auth_refresh_token"),
    )
    has_stored_tokens = bool(token_key)
    restore_error_message = None
    restored_user = None
    if should_restore_authenticated_user(
        token_key=token_key,
        restored_token_key=st.session_state.get("auth_restored_token_key"),
        is_authenticated_user=is_authenticated(),
    ):
        try:
            restored_user = restore_authenticated_user(
                access_token=str(st.session_state.get("auth_access_token") or ""),
                refresh_token=str(st.session_state.get("auth_refresh_token") or ""),
            )
        except RuntimeError as exc:
            if has_stored_tokens:
                restore_error_message = str(exc)
        if restored_user is None:
            if has_stored_tokens:
                st.session_state.auth_status_message = restore_error_message or "Your session expired. Please sign in again."
                clear_auth_state()
        else:
            sync_authenticated_user(restored_user)

    if not has_app_access():
        render_auth_screen()
        return

    if is_authenticated():
        current_token_key = build_auth_token_key(
            access_token=st.session_state.get("auth_access_token"),
            refresh_token=st.session_state.get("auth_refresh_token"),
        )
        current_time = time.time()
        if should_touch_last_online(
            token_key=current_token_key,
            last_synced_token_key=st.session_state.get("auth_last_online_token_key"),
            last_synced_at=st.session_state.get("auth_last_online_synced_at"),
            now_ts=current_time,
        ):
            try:
                touch_user_last_online(
                    access_token=str(st.session_state.auth_access_token),
                    refresh_token=str(st.session_state.auth_refresh_token),
                )
                st.session_state.auth_last_online_token_key = current_token_key
                st.session_state.auth_last_online_synced_at = current_time
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
