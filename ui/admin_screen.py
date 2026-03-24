import streamlit as st  # type: ignore

from services.admin_service import fetch_all_user_overviews
from services.time_service import format_timestamp_local


def render_admin_screen() -> None:
    if not st.session_state.get("auth_is_admin"):
        st.error("Admin access is required to view this dashboard.")
        return

    user_overviews = fetch_all_user_overviews(
        access_token=str(st.session_state.get("auth_access_token") or ""),
        refresh_token=str(st.session_state.get("auth_refresh_token") or ""),
    )
    st.title("Admin Dashboard")
    st.write("All registered users, their quiz generation counts, and their latest recorded activity are shown here.")

    total_users = len(user_overviews)
    admin_count = sum(1 for user in user_overviews if user.is_admin)
    total_generated_quizzes = sum(user.generated_quiz_count for user in user_overviews)

    summary_col_a, summary_col_b, summary_col_c = st.columns(3)
    with summary_col_a:
        st.metric("Users", total_users)
    with summary_col_b:
        st.metric("Admins", admin_count)
    with summary_col_c:
        st.metric("Generated Quizzes", total_generated_quizzes)

    if not user_overviews:
        st.info("No users have signed up yet.")
        return

    st.dataframe(
        [
            {
                "Email": user.email,
                "Role": "Admin" if user.is_admin else "User",
                "Generated Quizzes": user.generated_quiz_count,
                "Last Online": format_timestamp_local(user.last_online_at_iso),
                "Joined": format_timestamp_local(user.created_at_iso),
            }
            for user in user_overviews
        ],
        use_container_width=True,
        hide_index=True,
    )
