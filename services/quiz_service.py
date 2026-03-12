import streamlit as st  # type: ignore

from models import Question
from services.gemini_service import generate_gemini_questions
from services.question_io import questions_to_dicts
from state import ensure_answer_slots, mark_quiz_completed, mark_quiz_ready, set_phase, sync_current_question_state


def add_generated_questions(
    topic: str,
    difficulty: str,
    count: int,
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
    )
    return store_questions(
        questions=generated_questions,
        jump_to=jump_to,
        replace_existing=replace_existing,
    )


def store_questions(questions: list[Question], jump_to: str = "first_new", replace_existing: bool = True) -> int:
    if jump_to not in {"first_new", "latest"}:
        raise ValueError("Unsupported jump target for stored questions.")

    starting_index = 0 if replace_existing else len(st.session_state.questions)
    generated_questions = questions_to_dicts(questions)
    if replace_existing:
        st.session_state.questions = generated_questions
        st.session_state.score = 0
        st.session_state.answers = [None] * len(generated_questions)
        st.session_state.selected_option = None
        st.session_state.submitted = False
    else:
        st.session_state.questions.extend(generated_questions)

    ensure_answer_slots()
    if jump_to == "first_new":
        st.session_state.question_index = starting_index
    else:
        st.session_state.question_index = len(st.session_state.questions) - 1
    sync_current_question_state()
    return len(generated_questions)


def submit_answer(selected_option: str) -> None:
    question_index = st.session_state.question_index
    if st.session_state.answers[question_index] is not None:
        return

    current_question = st.session_state.questions[question_index]
    st.session_state.selected_option = selected_option
    st.session_state.submitted = True
    st.session_state.answers[question_index] = selected_option

    if selected_option == current_question["correct_answer"]:
        st.session_state.score += 10
    else:
        st.session_state.score -= 1


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
    if st.session_state.question_index > 0:
        st.session_state.question_index -= 1
        st.session_state.scroll_to_top = True
    sync_current_question_state()


def go_to_next_question() -> None:
    if st.session_state.question_index < len(st.session_state.questions) - 1:
        st.session_state.question_index += 1
        st.session_state.scroll_to_top = True
        sync_current_question_state()
        return

    mark_quiz_completed()
