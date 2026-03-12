import html

import streamlit as st  # type: ignore

from constants import GEMINI_API_KEY_NAME
from services.gemini_service import has_gemini_api_key
from services.quiz_service import go_to_next_question, go_to_previous_question, queue_generation, submit_answer
from state import sync_current_question_state


def _get_option_feedback_class(option: str, selected_option: str | None, correct_answer: str) -> str:
    if option == correct_answer:
        return "option-feedback--correct"
    if option == selected_option:
        return "option-feedback--wrong"
    return "option-feedback--neutral"


def _render_option_feedback(option: str, css_class: str) -> None:
    st.markdown(
        f'<div class="option-feedback {css_class}"><span class="option-feedback__label">{html.escape(option)}</span></div>',
        unsafe_allow_html=True,
    )


def render_quiz_ui() -> None:
    key_is_configured = has_gemini_api_key()
    questions = st.session_state.questions
    sync_current_question_state()

    if not questions:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.write("**Question 0 of 0**")
        with col_b:
            st.write(f"**Score:** {st.session_state.score}")

        st.markdown('<div class="question-box">No question present</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        columns = [col1, col2, col3, col4]

        for i in range(4):
            with columns[i]:
                st.button(
                    " ",
                    key=f"empty_btn_{i}",
                    disabled=True,
                )

        st.info("Generate a question from the sidebar to begin.")
        return

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.write(f"**Question {st.session_state.question_index + 1} of {len(questions)}**")
    with col_b:
        st.write(f"**Score:** {st.session_state.score}")

    current_q = questions[st.session_state.question_index]
    st.markdown(f'<div class="question-box">{current_q["question"]}</div>', unsafe_allow_html=True)

    options = current_q["options"][:4]
    while len(options) < 4:
        options.append("N/A")

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    columns = [col1, col2, col3, col4]

    if st.session_state.submitted:
        selected_option = st.session_state.selected_option
        correct_answer = current_q["correct_answer"]
        for i, option in enumerate(options):
            with columns[i]:
                css_class = _get_option_feedback_class(
                    option=option,
                    selected_option=selected_option,
                    correct_answer=correct_answer,
                )
                _render_option_feedback(option, css_class)
    else:
        for i, option in enumerate(options):
            with columns[i]:
                if st.button(
                    option,
                    key=f"btn_{st.session_state.question_index}_{i}",
                ):
                    submit_answer(option)
                    st.rerun()

    if st.session_state.submitted:
        st.markdown("---")
        is_correct = st.session_state.selected_option == current_q["correct_answer"]

        if is_correct:
            st.success("Correct! Great job.")
        else:
            st.error(f"Incorrect! The correct answer was **{current_q['correct_answer']}**.")

    st.markdown('<div class="next-container">', unsafe_allow_html=True)
    back_col, next_col, generate_col = st.columns(3)

    with back_col:
        if st.button("Back", disabled=st.session_state.question_index == 0, type="primary"):
            go_to_previous_question()
            st.rerun()

    with next_col:
        if st.button("Next", type="primary"):
            try:
                go_to_next_question()
                st.rerun()
            except Exception as exc:
                st.error(f"Could not load the next question: {exc}")

    with generate_col:
        if st.button("Generate a New Question", disabled=not key_is_configured):
            try:
                queue_generation(
                    count=1,
                    jump_to="latest",
                    next_phase="in_progress",
                    replace_existing=False,
                )
                st.rerun()
            except Exception as exc:
                st.error(f"Could not generate question: {exc}")
        if not key_is_configured:
            st.caption(f"Set `{GEMINI_API_KEY_NAME}` in secrets to enable this.")

    st.markdown("</div>", unsafe_allow_html=True)
