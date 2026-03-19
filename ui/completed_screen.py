import streamlit as st  # type: ignore

from services.quiz_engine import build_quiz_summary
from state import read_quiz_session
from state import reset_to_initial_state, start_quiz


def render_completed_screen() -> None:
    summary = build_quiz_summary(read_quiz_session())

    st.title("Quiz Completed")
    st.markdown(
        f"""
        <div class="score-display">
            Score: {summary.score} | Correct: {summary.correct_answers}/{summary.total_questions} | Accuracy: {summary.accuracy:.0f}%
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write(f"You answered {summary.answered_questions} question(s). Review the results below or start another round.")

    for index, item in enumerate(summary.review_items, start=1):
        result_label = "Correct" if item.is_correct else "Incorrect"
        st.markdown(f"**Q{index}.** {item.question.question}")
        st.write(f"Your answer: {item.selected_answer or 'Not answered'}")
        st.write(f"Correct answer: {item.question.correct_answer}")
        st.caption(result_label)
        st.markdown("---")

    regenerate_col, setup_col = st.columns(2)
    with regenerate_col:
        if st.button("Restart Current Quiz"):
            start_quiz()
            st.rerun()
    with setup_col:
        if st.button("Start from Scratch"):
            reset_to_initial_state()
            st.rerun()
