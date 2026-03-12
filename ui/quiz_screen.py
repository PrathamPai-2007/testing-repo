import html

import streamlit as st  # type: ignore
import streamlit.components.v1 as components  # type: ignore

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


def _render_scroll_to_top() -> None:
    components.html(
        """
        <script>
        const scrollToTop = () => {
          const parentWindow = window.parent;
          if (!parentWindow) {
            window.scrollTo(0, 0);
            return;
          }

          try {
            parentWindow.scrollTo({ top: 0, left: 0, behavior: "auto" });
          } catch (error) {
            parentWindow.scrollTo(0, 0);
          }

          const selectors = [
            '[data-testid="stAppScrollToTopContainer"]',
            '[data-testid="stAppViewContainer"]',
            '.main',
            'section.main'
          ];

          selectors.forEach((selector) => {
            const element = parentWindow.document.querySelector(selector);
            if (element) {
              element.scrollTo({ top: 0, left: 0, behavior: "auto" });
            }
          });
        };

        scrollToTop();
        requestAnimationFrame(scrollToTop);
        setTimeout(scrollToTop, 50);
        </script>
        """,
        height=0,
    )


def render_quiz_ui() -> None:
    key_is_configured = has_gemini_api_key()
    questions = st.session_state.questions
    sync_current_question_state()

    if st.session_state.get("scroll_to_top"):
        _render_scroll_to_top()
        st.session_state.scroll_to_top = False

    if not questions:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.write("**Question 0 of 0**")
        with col_b:
            st.write(f"**Score:** {st.session_state.score}")

        st.markdown('<div class="question-box">No question present</div>', unsafe_allow_html=True)

        with st.container(key="option-grid"):
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
    question_text = html.escape(str(current_q["question"]))
    st.markdown(f'<div class="question-box">{question_text}</div>', unsafe_allow_html=True)

    options = current_q["options"][:4]
    while len(options) < 4:
        options.append("N/A")

    with st.container(key="option-grid"):
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

    with st.container(key="quiz-nav"):
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
