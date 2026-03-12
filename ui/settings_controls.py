import streamlit as st  # type: ignore

from constants import DIFFICULTY_DETAILS


def get_current_difficulty() -> str:
    difficulty = st.session_state.difficulty
    if difficulty in DIFFICULTY_DETAILS:
        return difficulty
    return "medium"


def get_current_difficulty_details() -> dict[str, str]:
    return DIFFICULTY_DETAILS[get_current_difficulty()]


def _sync_topic(widget_key: str) -> None:
    st.session_state.topic = st.session_state[widget_key]


def _sync_difficulty(widget_key: str) -> None:
    st.session_state.difficulty = st.session_state[widget_key]


def _sync_question_count(widget_key: str) -> None:
    st.session_state.questions_to_generate = int(st.session_state[widget_key])


def render_quiz_configuration_controls(
    container,
    topic_key: str,
    difficulty_key: str,
    question_count_key: str,
) -> None:
    current_difficulty = get_current_difficulty()
    st.session_state[topic_key] = st.session_state.topic
    st.session_state[difficulty_key] = current_difficulty
    st.session_state[question_count_key] = int(st.session_state.questions_to_generate)

    container.text_input(
        "Quiz topic",
        key=topic_key,
        on_change=_sync_topic,
        args=(topic_key,),
    )
    container.selectbox(
        "Difficulty",
        list(DIFFICULTY_DETAILS.keys()),
        key=difficulty_key,
        format_func=lambda level: level,
        on_change=_sync_difficulty,
        args=(difficulty_key,),
    )
    container.number_input(
        "Questions to generate",
        min_value=1,
        max_value=5,
        step=1,
        key=question_count_key,
        on_change=_sync_question_count,
        args=(question_count_key,),
    )
