import streamlit as st  # type: ignore

from models import Question
from services.gemini_service import generate_gemini_questions
from services.quiz_engine import (
    go_to_next_question as advance_quiz_question,
    go_to_previous_question as return_to_previous_quiz_question,
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
