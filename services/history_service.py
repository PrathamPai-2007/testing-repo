from __future__ import annotations

from dataclasses import dataclass

from services.auth_service import _read_attr, _create_authenticated_supabase_client
from services.quiz_engine import QuizSummary


@dataclass(frozen=True, slots=True)
class QuizAttemptRecord:
    id: int
    topic: str
    difficulty: str
    total_questions: int
    answered_questions: int
    correct_answers: int
    accuracy: float
    score: int
    created_at_iso: str


@dataclass(frozen=True, slots=True)
class QuizHistorySummary:
    total_attempts: int
    best_score: int
    average_accuracy: float


def _normalize_attempt_row(row: dict) -> QuizAttemptRecord:
    return QuizAttemptRecord(
        id=int(row["id"]),
        topic=str(row["topic"]),
        difficulty=str(row["difficulty"]),
        total_questions=int(row["total_questions"]),
        answered_questions=int(row["answered_questions"]),
        correct_answers=int(row["correct_answers"]),
        accuracy=float(row["accuracy"]),
        score=int(row["score"]),
        created_at_iso=str(row["created_at"]),
    )


def record_quiz_attempt(
    *,
    user_id: str,
    access_token: str,
    refresh_token: str,
    topic: str,
    difficulty: str,
    summary: QuizSummary,
) -> QuizAttemptRecord:
    normalized_topic = str(topic).strip() or "general knowledge"
    normalized_difficulty = str(difficulty).strip() or "medium"
    client, _, _, _ = _create_authenticated_supabase_client(
        access_token=access_token,
        refresh_token=refresh_token,
    )

    response = (
        client.table("quiz_attempts")
        .insert(
            {
                "user_id": str(user_id).strip(),
                "topic": normalized_topic,
                "difficulty": normalized_difficulty,
                "total_questions": int(summary.total_questions),
                "answered_questions": int(summary.answered_questions),
                "correct_answers": int(summary.correct_answers),
                "accuracy": float(summary.accuracy),
                "score": int(summary.score),
            }
        )
        .execute()
    )
    rows = list(_read_attr(response, "data", []) or [])
    if not rows:
        raise RuntimeError("Could not save your quiz attempt.")
    return _normalize_attempt_row(dict(rows[0]))


def fetch_user_quiz_history(*, user_id: str, access_token: str, refresh_token: str, limit: int = 20) -> list[QuizAttemptRecord]:
    client, _, _, _ = _create_authenticated_supabase_client(
        access_token=access_token,
        refresh_token=refresh_token,
    )
    response = (
        client.table("quiz_attempts")
        .select("*")
        .eq("user_id", str(user_id).strip())
        .execute()
    )
    rows = [dict(row) for row in list(_read_attr(response, "data", []) or [])]
    rows.sort(key=lambda row: (str(row.get("created_at") or ""), int(row.get("id") or 0)), reverse=True)
    return [_normalize_attempt_row(row) for row in rows[: max(1, int(limit))]]


def build_user_history_summary(*, user_id: str, access_token: str, refresh_token: str) -> QuizHistorySummary:
    attempts = fetch_user_quiz_history(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        limit=500,
    )
    if not attempts:
        return QuizHistorySummary(
            total_attempts=0,
            best_score=0,
            average_accuracy=0.0,
        )

    return QuizHistorySummary(
        total_attempts=len(attempts),
        best_score=max(attempt.score for attempt in attempts),
        average_accuracy=sum(attempt.accuracy for attempt in attempts) / len(attempts),
    )
