import streamlit as st  # type: ignore

from constants import DEFAULT_GEMINI_MODEL, DEFAULT_QUESTIONS
from models import Question
from services.quiz_engine import (
    QUIZ_PHASES,
    QuizSession,
    clear_quiz_session,
    ensure_answer_slots as ensure_answer_slots_in_session,
    mark_quiz_completed as mark_session_completed,
    mark_quiz_ready as mark_session_ready,
    reset_quiz_progress,
    sync_current_question_state as sync_quiz_session,
    validate_phase,
)


def read_quiz_session() -> QuizSession:
    raw_questions = st.session_state.get("questions", [])
    return QuizSession(
        questions=[Question.from_dict(question) for question in raw_questions],
        answers=list(st.session_state.get("answers", [])),
        hints=list(st.session_state.get("hints", [])),
        question_index=int(st.session_state.get("question_index", 0)),
        selected_option=st.session_state.get("selected_option"),
        submitted=bool(st.session_state.get("submitted", False)),
        score=int(st.session_state.get("score", 0)),
        phase=str(st.session_state.get("phase", "setup")),
    )


def write_quiz_session(session: QuizSession) -> None:
    st.session_state.questions = [question.to_dict() for question in session.questions]
    st.session_state.answers = list(session.answers)
    st.session_state.hints = list(session.hints)
    st.session_state.question_index = session.question_index
    st.session_state.selected_option = session.selected_option
    st.session_state.submitted = session.submitted
    st.session_state.score = session.score
    st.session_state.phase = session.phase


def set_phase(phase: str) -> None:
    st.session_state.phase = validate_phase(phase)


def reset_quiz(phase: str = "setup") -> None:
    session = read_quiz_session()
    reset_quiz_progress(session, phase=phase)
    write_quiz_session(session)


def reset_to_initial_state() -> None:
    session = read_quiz_session()
    clear_quiz_session(session)
    write_quiz_session(session)


def start_quiz() -> None:
    reset_quiz(phase="in_progress")


def mark_quiz_ready() -> None:
    session = read_quiz_session()
    mark_session_ready(session)
    write_quiz_session(session)


def mark_quiz_completed() -> None:
    session = read_quiz_session()
    mark_session_completed(session)
    write_quiz_session(session)


def ensure_answer_slots() -> None:
    session = read_quiz_session()
    ensure_answer_slots_in_session(session)
    write_quiz_session(session)


def sync_current_question_state() -> None:
    session = read_quiz_session()
    sync_quiz_session(session)
    write_quiz_session(session)


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
    if "hints" not in st.session_state:
        st.session_state.hints = [None] * len(st.session_state.questions)
    if "topic" not in st.session_state:
        st.session_state.topic = "math"
    if "difficulty" not in st.session_state:
        st.session_state.difficulty = "medium"
    if "questions_to_generate" not in st.session_state:
        st.session_state.questions_to_generate = 1
    if "gemini_model" not in st.session_state:
        st.session_state.gemini_model = DEFAULT_GEMINI_MODEL
    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False
    if "pending_generation" not in st.session_state:
        st.session_state.pending_generation = None
    if "generation_feedback" not in st.session_state:
        st.session_state.generation_feedback = None
    if "is_generating_hint" not in st.session_state:
        st.session_state.is_generating_hint = False
    if "pending_hint_generation" not in st.session_state:
        st.session_state.pending_hint_generation = None
    if "hint_feedback" not in st.session_state:
        st.session_state.hint_feedback = None
    if "phase" not in st.session_state:
        st.session_state.phase = "setup"
    if "scroll_to_top" not in st.session_state:
        st.session_state.scroll_to_top = False
    if "sidebar_default_applied" not in st.session_state:
        st.session_state.sidebar_default_applied = False

    session = read_quiz_session()
    ensure_answer_slots_in_session(session)
    sync_quiz_session(session)
    if not session.questions and session.phase != "generating":
        session.phase = "setup"
    write_quiz_session(session)
