import streamlit as st  # type: ignore

from models import Question
from services.auth_service import increment_generated_quiz_count
from services.gemini_service import generate_gemini_questions, generate_question_hint
from services.quiz_engine import (
    go_to_next_question as advance_quiz_question,
    go_to_previous_question as return_to_previous_quiz_question,
    store_question_hint,
    store_questions_in_session,
    submit_answer_selection,
)
from state import mark_quiz_ready, read_quiz_session, set_phase, write_quiz_session


def add_generated_questions(
    topic: str,
    difficulty: str,
    count: int,
    model_name: str,
    jump_to: str = "first_new",
    replace_existing: bool = False,
) -> int:
    generated_count = max(1, min(int(count), 5))
    if jump_to not in {"first_new", "latest"}:
        raise ValueError("Unsupported jump target for generated questions.")

    generated_questions = generate_gemini_questions(
        topic=topic,
        difficulty=difficulty,
        count=generated_count,
        model_name=model_name,
    )
    return store_questions(
        questions=generated_questions,
        jump_to=jump_to,
        replace_existing=replace_existing,
    )


def store_questions(questions: list[Question], jump_to: str = "first_new", replace_existing: bool = True) -> int:
    session = read_quiz_session()
    stored_count = store_questions_in_session(
        session,
        questions=questions,
        jump_to=jump_to,
        replace_existing=replace_existing,
    )
    write_quiz_session(session)
    return stored_count


def submit_answer(selected_option: str) -> None:
    session = read_quiz_session()
    submit_answer_selection(session, selected_option)
    write_quiz_session(session)


def queue_generation(
    count: int,
    jump_to: str,
    next_phase: str = "ready",
    replace_existing: bool = False,
) -> None:
    st.session_state.pending_generation = {
        "count": max(1, min(int(count), 5)),
        "jump_to": jump_to,
        "topic": st.session_state.topic,
        "difficulty": st.session_state.difficulty,
        "model_name": st.session_state.gemini_model,
        "next_phase": next_phase,
        "replace_existing": replace_existing,
    }
    st.session_state.is_generating = True
    set_phase("generating")


def process_pending_generation() -> None:
    pending_generation = st.session_state.get("pending_generation")
    if not pending_generation:
        return

    try:
        generated_count = add_generated_questions(
            topic=pending_generation["topic"],
            difficulty=pending_generation["difficulty"],
            count=pending_generation["count"],
            model_name=pending_generation.get("model_name", st.session_state.gemini_model),
            jump_to=pending_generation["jump_to"],
            replace_existing=bool(pending_generation.get("replace_existing")),
        )
        st.session_state.generation_feedback = {
            "type": "success",
            "message": f"{generated_count} Gemini question(s) added to the quiz.",
        }
        auth_user_id = st.session_state.get("auth_user_id")
        auth_access_token = st.session_state.get("auth_access_token")
        auth_refresh_token = st.session_state.get("auth_refresh_token")
        if auth_user_id and auth_access_token and auth_refresh_token:
            increment_generated_quiz_count(
                access_token=str(auth_access_token),
                refresh_token=str(auth_refresh_token),
            )
        next_phase = pending_generation.get("next_phase", "ready")
        if next_phase == "ready":
            mark_quiz_ready()
        else:
            set_phase(next_phase)
    except Exception as exc:
        st.session_state.generation_feedback = {
            "type": "error",
            "message": f"Could not generate question: {exc}",
        }
        mark_quiz_ready()
    finally:
        st.session_state.pending_generation = None
        st.session_state.is_generating = False

    st.rerun()


def queue_hint_generation() -> None:
    question_index = int(st.session_state.get("question_index", 0))
    st.session_state.pending_hint_generation = {
        "question_index": question_index,
        "topic": st.session_state.topic,
        "difficulty": st.session_state.difficulty,
    }
    st.session_state.hint_feedback = None
    st.session_state.is_generating_hint = True


def process_pending_hint_generation() -> None:
    pending_hint_generation = st.session_state.get("pending_hint_generation")
    if not pending_hint_generation:
        return

    try:
        session = read_quiz_session()
        question_index = int(pending_hint_generation["question_index"])
        question = session.questions[question_index]
        hint_text = generate_question_hint(
            topic=pending_hint_generation["topic"],
            difficulty=pending_hint_generation["difficulty"],
            question=question,
        )
        store_question_hint(session, question_index, hint_text)
        write_quiz_session(session)
        st.session_state.hint_feedback = {
            "type": "success",
            "message": "Hint ready.",
        }
    except Exception as exc:
        st.session_state.hint_feedback = {
            "type": "error",
            "message": f"Could not generate hint: {exc}",
        }
    finally:
        st.session_state.pending_hint_generation = None
        st.session_state.is_generating_hint = False

    st.rerun()


def go_to_previous_question() -> None:
    session = read_quiz_session()
    moved = return_to_previous_quiz_question(session)
    write_quiz_session(session)
    if moved:
        st.session_state.scroll_to_top = True


def go_to_next_question() -> None:
    session = read_quiz_session()
    moved = advance_quiz_question(session)
    write_quiz_session(session)
    if moved:
        st.session_state.scroll_to_top = True
