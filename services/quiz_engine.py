from dataclasses import dataclass, field

from models import Question


QUIZ_PHASES = ("setup", "generating", "ready", "in_progress", "completed")


@dataclass(slots=True)
class QuizSession:
    questions: list[Question] = field(default_factory=list)
    answers: list[str | None] = field(default_factory=list)
    question_index: int = 0
    selected_option: str | None = None
    submitted: bool = False
    score: int = 0
    phase: str = "setup"


@dataclass(frozen=True, slots=True)
class QuizReviewItem:
    question: Question
    selected_answer: str | None
    is_correct: bool


@dataclass(frozen=True, slots=True)
class QuizSummary:
    total_questions: int
    answered_questions: int
    correct_answers: int
    accuracy: float
    score: int
    review_items: list[QuizReviewItem]


def validate_phase(phase: str) -> str:
    if phase not in QUIZ_PHASES:
        raise ValueError(f"Unsupported quiz phase: {phase}")
    return phase


def ensure_answer_slots(session: QuizSession) -> None:
    if len(session.answers) < len(session.questions):
        session.answers.extend([None] * (len(session.questions) - len(session.answers)))
    elif len(session.answers) > len(session.questions):
        del session.answers[len(session.questions) :]


def sync_current_question_state(session: QuizSession) -> None:
    ensure_answer_slots(session)

    if not session.questions:
        session.question_index = 0
        session.selected_option = None
        session.submitted = False
        return

    session.question_index = min(session.question_index, len(session.questions) - 1)
    session.selected_option = session.answers[session.question_index]
    session.submitted = session.selected_option is not None


def reset_quiz_progress(session: QuizSession, phase: str = "setup") -> None:
    session.question_index = 0
    session.selected_option = None
    session.submitted = False
    session.score = 0
    session.answers = [None] * len(session.questions)
    session.phase = validate_phase(phase)


def clear_quiz_session(session: QuizSession) -> None:
    session.questions = []
    session.answers = []
    session.question_index = 0
    session.selected_option = None
    session.submitted = False
    session.score = 0
    session.phase = "setup"


def mark_quiz_ready(session: QuizSession) -> None:
    session.phase = "ready" if session.questions else "setup"


def mark_quiz_completed(session: QuizSession) -> None:
    session.phase = "completed"


def store_questions_in_session(
    session: QuizSession,
    questions: list[Question],
    jump_to: str = "first_new",
    replace_existing: bool = True,
) -> int:
    if jump_to not in {"first_new", "latest"}:
        raise ValueError("Unsupported jump target for stored questions.")

    starting_index = 0 if replace_existing else len(session.questions)
    if replace_existing:
        session.questions = list(questions)
        session.score = 0
        session.answers = [None] * len(session.questions)
        session.selected_option = None
        session.submitted = False
    else:
        session.questions.extend(questions)

    ensure_answer_slots(session)
    if session.questions:
        session.question_index = starting_index if jump_to == "first_new" else len(session.questions) - 1
    else:
        session.question_index = 0
    sync_current_question_state(session)
    return len(questions)


def submit_answer_selection(session: QuizSession, selected_option: str) -> bool:
    if not session.questions:
        return False

    ensure_answer_slots(session)
    question_index = session.question_index
    if session.answers[question_index] is not None:
        return False

    current_question = session.questions[question_index]
    session.selected_option = selected_option
    session.submitted = True
    session.answers[question_index] = selected_option

    if selected_option == current_question.correct_answer:
        session.score += 4
    else:
        session.score -= 1
    return True


def go_to_previous_question(session: QuizSession) -> bool:
    if session.question_index <= 0:
        sync_current_question_state(session)
        return False

    session.question_index -= 1
    sync_current_question_state(session)
    return True


def go_to_next_question(session: QuizSession) -> bool:
    if session.question_index < len(session.questions) - 1:
        session.question_index += 1
        sync_current_question_state(session)
        return True

    mark_quiz_completed(session)
    return False


def build_quiz_summary(session: QuizSession) -> QuizSummary:
    ensure_answer_slots(session)
    answered_questions = sum(1 for answer in session.answers if answer is not None)
    review_items: list[QuizReviewItem] = []
    correct_answers = 0

    for index, question in enumerate(session.questions):
        selected_answer = session.answers[index]
        is_correct = selected_answer is not None and selected_answer == question.correct_answer
        if is_correct:
            correct_answers += 1
        review_items.append(
            QuizReviewItem(
                question=question,
                selected_answer=selected_answer,
                is_correct=is_correct,
            )
        )

    total_questions = len(session.questions)
    accuracy = (correct_answers / total_questions * 100) if total_questions else 0.0
    return QuizSummary(
        total_questions=total_questions,
        answered_questions=answered_questions,
        correct_answers=correct_answers,
        accuracy=accuracy,
        score=session.score,
        review_items=review_items,
    )
