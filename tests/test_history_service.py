import unittest
from unittest.mock import patch

from services.auth_service import create_user
from services.history_service import build_user_history_summary, delete_quiz_attempt, fetch_user_quiz_history, record_quiz_attempt
from services.quiz_engine import QuizSummary
from tests.fake_supabase import FakeSupabaseClient


def _build_summary(score: int, correct_answers: int, total_questions: int, answered_questions: int) -> QuizSummary:
    accuracy = (correct_answers / total_questions * 100) if total_questions else 0.0
    return QuizSummary(
        total_questions=total_questions,
        answered_questions=answered_questions,
        correct_answers=correct_answers,
        accuracy=accuracy,
        score=score,
        review_items=[],
    )


class HistoryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeSupabaseClient()
        self.create_client_patch = patch("services.auth_service.create_supabase_client", return_value=self.fake_client)
        self.create_client_patch.start()
        self.primary_user = create_user(
            email="history_user@example.com",
            password="Password123",
        )
        self.other_user = create_user(
            email="other_user@example.com",
            password="Password123",
        )

    def tearDown(self) -> None:
        self.create_client_patch.stop()

    def test_record_quiz_attempt_and_fetch_history(self) -> None:
        record_quiz_attempt(
            user_id=self.primary_user.id,
            access_token=self.primary_user.access_token,
            refresh_token=self.primary_user.refresh_token,
            topic="fractions",
            difficulty="medium",
            summary=_build_summary(score=7, correct_answers=2, total_questions=3, answered_questions=3),
        )
        record_quiz_attempt(
            user_id=self.primary_user.id,
            access_token=self.primary_user.access_token,
            refresh_token=self.primary_user.refresh_token,
            topic="physics",
            difficulty="hard",
            summary=_build_summary(score=11, correct_answers=3, total_questions=3, answered_questions=3),
        )

        attempts = fetch_user_quiz_history(
            user_id=self.primary_user.id,
            access_token=self.primary_user.access_token,
            refresh_token=self.primary_user.refresh_token,
        )

        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0].topic, "physics")
        self.assertEqual(attempts[0].score, 11)
        self.assertEqual(attempts[1].topic, "fractions")

    def test_history_summary_aggregates_attempts(self) -> None:
        record_quiz_attempt(
            user_id=self.primary_user.id,
            access_token=self.primary_user.access_token,
            refresh_token=self.primary_user.refresh_token,
            topic="algebra",
            difficulty="easy",
            summary=_build_summary(score=8, correct_answers=2, total_questions=2, answered_questions=2),
        )
        record_quiz_attempt(
            user_id=self.primary_user.id,
            access_token=self.primary_user.access_token,
            refresh_token=self.primary_user.refresh_token,
            topic="geometry",
            difficulty="medium",
            summary=_build_summary(score=4, correct_answers=1, total_questions=2, answered_questions=2),
        )

        history_summary = build_user_history_summary(
            user_id=self.primary_user.id,
            access_token=self.primary_user.access_token,
            refresh_token=self.primary_user.refresh_token,
        )

        self.assertEqual(history_summary.total_attempts, 2)
        self.assertEqual(history_summary.best_score, 8)
        self.assertEqual(history_summary.average_accuracy, 75.0)

    def test_fetch_history_is_user_scoped(self) -> None:
        record_quiz_attempt(
            user_id=self.primary_user.id,
            access_token=self.primary_user.access_token,
            refresh_token=self.primary_user.refresh_token,
            topic="biology",
            difficulty="medium",
            summary=_build_summary(score=3, correct_answers=1, total_questions=2, answered_questions=2),
        )
        record_quiz_attempt(
            user_id=self.other_user.id,
            access_token=self.other_user.access_token,
            refresh_token=self.other_user.refresh_token,
            topic="chemistry",
            difficulty="hard",
            summary=_build_summary(score=7, correct_answers=2, total_questions=2, answered_questions=2),
        )

        attempts = fetch_user_quiz_history(
            user_id=self.primary_user.id,
            access_token=self.primary_user.access_token,
            refresh_token=self.primary_user.refresh_token,
        )

        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].topic, "biology")

    def test_user_can_delete_own_quiz_attempt(self) -> None:
        attempt = record_quiz_attempt(
            user_id=self.primary_user.id,
            access_token=self.primary_user.access_token,
            refresh_token=self.primary_user.refresh_token,
            topic="fractions",
            difficulty="medium",
            summary=_build_summary(score=7, correct_answers=2, total_questions=3, answered_questions=3),
        )

        deleted = delete_quiz_attempt(
            attempt_id=attempt.id,
            access_token=self.primary_user.access_token,
            refresh_token=self.primary_user.refresh_token,
        )

        attempts = fetch_user_quiz_history(
            user_id=self.primary_user.id,
            access_token=self.primary_user.access_token,
            refresh_token=self.primary_user.refresh_token,
        )
        self.assertTrue(deleted)
        self.assertEqual(attempts, [])

    def test_user_cannot_delete_someone_elses_quiz_attempt(self) -> None:
        other_attempt = record_quiz_attempt(
            user_id=self.other_user.id,
            access_token=self.other_user.access_token,
            refresh_token=self.other_user.refresh_token,
            topic="chemistry",
            difficulty="hard",
            summary=_build_summary(score=7, correct_answers=2, total_questions=2, answered_questions=2),
        )

        deleted = delete_quiz_attempt(
            attempt_id=other_attempt.id,
            access_token=self.primary_user.access_token,
            refresh_token=self.primary_user.refresh_token,
        )

        attempts = fetch_user_quiz_history(
            user_id=self.other_user.id,
            access_token=self.other_user.access_token,
            refresh_token=self.other_user.refresh_token,
        )
        self.assertFalse(deleted)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].id, other_attempt.id)


if __name__ == "__main__":
    unittest.main()
