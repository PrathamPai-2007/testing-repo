import streamlit as st  # type: ignore

from constants import DEFAULT_GEMINI_MODEL, DEFAULT_QUESTIONS
from models import Question
from services.auth_service import AuthenticatedUser
from services.quiz_engine import (
    QuizSession,
    clear_quiz_session,
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
    st.session_state.quiz_attempt_recorded = False


def reset_to_initial_state() -> None:
    session = read_quiz_session()
    clear_quiz_session(session)
    write_quiz_session(session)
    st.session_state.quiz_attempt_recorded = False


def start_quiz() -> None:
    reset_quiz(phase="in_progress")


def mark_quiz_ready() -> None:
    session = read_quiz_session()
    mark_session_ready(session)
    write_quiz_session(session)


def sync_current_question_state() -> None:
    session = read_quiz_session()
    sync_quiz_session(session)
    write_quiz_session(session)


def is_authenticated() -> bool:
    return bool(
        st.session_state.get("auth_user_id")
        and st.session_state.get("auth_user_email")
        and st.session_state.get("auth_access_token")
        and st.session_state.get("auth_refresh_token")
    )


def is_guest_user() -> bool:
    return bool(st.session_state.get("auth_is_guest"))


def has_app_access() -> bool:
    return is_authenticated() or is_guest_user()


def _store_authenticated_user(user: AuthenticatedUser) -> None:
    st.session_state.auth_user_id = str(user.id)
    st.session_state.auth_user_email = str(user.email)
    st.session_state.auth_is_admin = bool(user.is_admin)
    st.session_state.auth_access_token = str(user.access_token)
    st.session_state.auth_refresh_token = str(user.refresh_token)
    st.session_state.auth_is_guest = False
    st.session_state.auth_view = "app"


def log_in_user(user: AuthenticatedUser) -> None:
    _store_authenticated_user(user)
    st.session_state.app_screen = "admin" if user.is_admin else "quiz"
    st.session_state.quiz_attempt_recorded = False
    st.session_state.sidebar_default_applied = False


def sync_authenticated_user(user: AuthenticatedUser) -> None:
    current_screen = st.session_state.get("app_screen", "quiz")
    _store_authenticated_user(user)
    if current_screen == "admin" and not user.is_admin:
        st.session_state.app_screen = "quiz"


def log_in_guest_user() -> None:
    st.session_state.auth_user_id = None
    st.session_state.auth_user_email = "Guest"
    st.session_state.auth_is_admin = False
    st.session_state.auth_access_token = None
    st.session_state.auth_refresh_token = None
    st.session_state.auth_is_guest = True
    st.session_state.auth_view = "app"
    st.session_state.app_screen = "quiz"
    st.session_state.quiz_attempt_recorded = False
    st.session_state.sidebar_default_applied = False


def clear_auth_state() -> None:
    st.session_state.auth_user_id = None
    st.session_state.auth_user_email = None
    st.session_state.auth_is_admin = False
    st.session_state.auth_access_token = None
    st.session_state.auth_refresh_token = None
    st.session_state.auth_is_guest = False
    st.session_state.auth_view = "login"
    if st.session_state.get("app_screen") in {"admin", "history"}:
        st.session_state.app_screen = "quiz"


def log_out_user() -> None:
    reset_to_initial_state()
    clear_auth_state()
    st.session_state.is_generating = False
    st.session_state.pending_generation = None
    st.session_state.generation_feedback = None
    st.session_state.is_generating_hint = False
    st.session_state.pending_hint_generation = None
    st.session_state.hint_feedback = None


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
    if "auth_user_id" not in st.session_state:
        st.session_state.auth_user_id = None
    if "auth_user_email" not in st.session_state:
        st.session_state.auth_user_email = None
    if "auth_is_admin" not in st.session_state:
        st.session_state.auth_is_admin = False
    if "auth_access_token" not in st.session_state:
        st.session_state.auth_access_token = None
    if "auth_refresh_token" not in st.session_state:
        st.session_state.auth_refresh_token = None
    if "auth_is_guest" not in st.session_state:
        st.session_state.auth_is_guest = False
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "login"
    if "app_screen" not in st.session_state:
        st.session_state.app_screen = "quiz"
    if "quiz_attempt_recorded" not in st.session_state:
        st.session_state.quiz_attempt_recorded = False

    session = read_quiz_session()
    sync_quiz_session(session)
    if not session.questions and session.phase != "generating":
        session.phase = "setup"
    write_quiz_session(session)
