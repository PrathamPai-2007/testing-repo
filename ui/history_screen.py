import streamlit as st  # type: ignore

from services.history_service import build_user_history_summary, delete_quiz_attempt, fetch_user_quiz_history
from services.time_service import format_timestamp_local


def render_history_screen() -> None:
    user_id = st.session_state.get("auth_user_id")
    access_token = st.session_state.get("auth_access_token")
    refresh_token = st.session_state.get("auth_refresh_token")
    if not user_id or not access_token or not refresh_token:
        st.error("You need to be signed in to view quiz history.")
        return

    history_summary = build_user_history_summary(
        user_id=str(user_id),
        access_token=str(access_token),
        refresh_token=str(refresh_token),
    )
    attempts = fetch_user_quiz_history(
        user_id=str(user_id),
        access_token=str(access_token),
        refresh_token=str(refresh_token),
        limit=25,
    )

    st.title("Quiz History")
    st.write("Your completed quiz attempts and saved score history appear here.")

    summary_col_a, summary_col_b, summary_col_c = st.columns(3)
    with summary_col_a:
        st.metric("Attempts", history_summary.total_attempts)
    with summary_col_b:
        st.metric("Best Score", history_summary.best_score)
    with summary_col_c:
        st.metric("Average Accuracy", f"{history_summary.average_accuracy:.0f}%")

    if not attempts:
        st.info("No completed quizzes yet. Finish a quiz and it will appear here.")
        return

    for attempt in attempts:
        details_col, action_col = st.columns([6, 1])
        with details_col:
            st.markdown(
                f"""
**{attempt.topic}**  
Difficulty: `{attempt.difficulty}`  
Score: `{attempt.score}` | Correct: `{attempt.correct_answers}/{attempt.total_questions}` | Accuracy: `{attempt.accuracy:.0f}%`  
Answered: `{attempt.answered_questions}`  
Completed: `{format_timestamp_local(attempt.created_at_iso)}`
"""
            )
        with action_col:
            if st.button("Delete", key=f"delete_attempt_{attempt.id}", use_container_width=True):
                try:
                    deleted = delete_quiz_attempt(
                        attempt_id=attempt.id,
                        access_token=str(access_token),
                        refresh_token=str(refresh_token),
                    )
                except RuntimeError as exc:
                    st.error(str(exc))
                else:
                    if deleted:
                        st.success("Quiz attempt deleted.")
                    else:
                        st.info("That quiz attempt was already removed.")
                    st.rerun()
        st.markdown("---")
