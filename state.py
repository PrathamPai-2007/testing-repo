import streamlit as st  # type: ignore

from constants import DEFAULT_QUESTIONS


QUIZ_PHASES = ("setup", "generating", "ready", "in_progress", "completed")


def set_phase(phase: str) -> None:
    if phase not in QUIZ_PHASES:
        raise ValueError(f"Unsupported quiz phase: {phase}")
    st.session_state.phase = phase


def reset_quiz(phase: str = "setup") -> None:
    st.session_state.question_index = 0
    st.session_state.selected_option = None
    st.session_state.submitted = False
    st.session_state.score = 0
    st.session_state.answers = [None] * len(st.session_state.get("questions", []))
    set_phase(phase)


def start_quiz() -> None:
    reset_quiz(phase="in_progress")


def mark_quiz_ready() -> None:
    set_phase("ready" if st.session_state.get("questions") else "setup")


def mark_quiz_completed() -> None:
    set_phase("completed")


def ensure_answer_slots() -> None:
    questions = st.session_state.get("questions", [])
    answers = st.session_state.get("answers")

    if answers is None:
        st.session_state.answers = [None] * len(questions)
        return

    if len(answers) < len(questions):
        answers.extend([None] * (len(questions) - len(answers)))
    elif len(answers) > len(questions):
        del answers[len(questions) :]


def sync_current_question_state() -> None:
    questions = st.session_state.get("questions", [])
    ensure_answer_slots()

    if not questions:
        st.session_state.question_index = 0
        st.session_state.selected_option = None
        st.session_state.submitted = False
        return

    st.session_state.question_index = min(st.session_state.question_index, len(questions) - 1)
    selected_option = st.session_state.answers[st.session_state.question_index]
    st.session_state.selected_option = selected_option
    st.session_state.submitted = selected_option is not None


def initialize_state() -> None:
    if "question_index" not in st.session_state:
        st.session_state.question_index = 0
    if "selected_option" not in st.session_state:
        st.session_state.selected_option = None
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "questions" not in st.session_state:
        st.session_state.questions = DEFAULT_QUESTIONS.copy()
    if "answers" not in st.session_state:
        st.session_state.answers = [None] * len(st.session_state.questions)
    if "topic" not in st.session_state:
        st.session_state.topic = "math"
    if "difficulty" not in st.session_state:
        st.session_state.difficulty = "medium"
    if "questions_to_generate" not in st.session_state:
        st.session_state.questions_to_generate = 1
    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False
    if "pending_generation" not in st.session_state:
        st.session_state.pending_generation = None
    if "generation_feedback" not in st.session_state:
        st.session_state.generation_feedback = None
    if "phase" not in st.session_state:
        st.session_state.phase = "setup"
    if "scroll_to_top" not in st.session_state:
        st.session_state.scroll_to_top = False

    ensure_answer_slots()
    sync_current_question_state()
    if not st.session_state.questions and st.session_state.phase != "generating":
        st.session_state.phase = "setup"
