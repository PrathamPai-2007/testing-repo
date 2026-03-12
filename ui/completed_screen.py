import streamlit as st  # type: ignore

from services.question_io import question_dicts_to_models
from state import reset_to_initial_state, start_quiz


def render_completed_screen() -> None:
    questions = question_dicts_to_models(st.session_state.questions)
    total_questions = len(questions)
    answered_questions = sum(1 for answer in st.session_state.answers if answer is not None)
    correct_answers = sum(
        1
        for index, answer in enumerate(st.session_state.answers)
        if answer is not None and answer == questions[index].correct_answer
    )
    accuracy = (correct_answers / total_questions * 100) if total_questions else 0

    st.title("Quiz Completed")
    st.markdown(
        f"""
        <div class="score-display">
            Score: {st.session_state.score} | Correct: {correct_answers}/{total_questions} | Accuracy: {accuracy:.0f}%
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write(f"You answered {answered_questions} question(s). Review the results below or start another round.")

    for index, question in enumerate(questions, start=1):
        selected_answer = st.session_state.answers[index - 1]
        correct_answer = question.correct_answer
        result_label = "Correct" if selected_answer == correct_answer else "Incorrect"
        st.markdown(f"**Q{index}.** {question.question}")
        st.write(f"Your answer: {selected_answer or 'Not answered'}")
        st.write(f"Correct answer: {correct_answer}")
        st.caption(result_label)
        st.markdown("---")

    play_again_col, regenerate_col, setup_col = st.columns(3)
    with play_again_col:
        st.button("Give an AI Summary")
    with regenerate_col:
        if st.button("Restart Current Quiz"):
            start_quiz()
            st.rerun()
    with setup_col:
        if st.button("Start from Scratch"):
            reset_to_initial_state()
            st.rerun()
