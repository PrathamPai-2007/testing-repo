import unittest

from models import Question
from services.quiz_engine import (
    QuizSession,
    build_quiz_summary,
    go_to_next_question,
    go_to_previous_question,
    reset_quiz_progress,
    store_question_hint,
    store_questions_in_session,
    submit_answer_selection,
)


def _sample_questions() -> list[Question]:
    return [
        Question(
            question="2 + 2 = ?",
            options=["1", "2", "3", "4"],
            correct_answer="4",
        ),
        Question(
            question="Capital of France?",
            options=["Berlin", "Madrid", "Paris", "Rome"],
            correct_answer="Paris",
        ),
    ]


class QuizEngineTests(unittest.TestCase):
    def test_store_questions_replace_resets_progress_and_jumps_to_first_new(self) -> None:
        session = QuizSession(
            questions=_sample_questions(),
            answers=["4", None],
            question_index=1,
            selected_option="Paris",
            submitted=True,
            score=4,
            phase="in_progress",
        )

        stored_count = store_questions_in_session(
            session,
            questions=[_sample_questions()[1]],
            jump_to="first_new",
            replace_existing=True,
        )

        self.assertEqual(stored_count, 1)
        self.assertEqual(len(session.questions), 1)
        self.assertEqual(session.answers, [None])
        self.assertEqual(session.question_index, 0)
        self.assertIsNone(session.selected_option)
        self.assertFalse(session.submitted)
        self.assertEqual(session.score, 0)

    def test_store_questions_append_can_jump_to_latest(self) -> None:
        session = QuizSession(
            questions=[_sample_questions()[0]],
            answers=["4"],
            hints=["Use addition facts."],
            question_index=0,
            selected_option="4",
            submitted=True,
            score=4,
            phase="in_progress",
        )

        stored_count = store_questions_in_session(
            session,
            questions=[_sample_questions()[1]],
            jump_to="latest",
            replace_existing=False,
        )

        self.assertEqual(stored_count, 1)
        self.assertEqual(len(session.questions), 2)
        self.assertEqual(session.answers, ["4", None])
        self.assertEqual(session.hints, ["Use addition facts.", None])
        self.assertEqual(session.question_index, 1)
        self.assertIsNone(session.selected_option)
        self.assertFalse(session.submitted)
        self.assertEqual(session.score, 4)

    def test_store_question_hint_updates_matching_question_slot(self) -> None:
        session = QuizSession(
            questions=_sample_questions(),
            hints=[None, None],
            phase="in_progress",
        )

        store_question_hint(session, 1, "Think about famous European capitals.")

        self.assertEqual(session.hints, [None, "Think about famous European capitals."])

    def test_submit_answer_selection_scores_once(self) -> None:
        session = QuizSession(questions=_sample_questions(), phase="in_progress")

        first_submit = submit_answer_selection(session, "4")
        second_submit = submit_answer_selection(session, "1")

        self.assertTrue(first_submit)
        self.assertFalse(second_submit)
        self.assertEqual(session.answers, ["4", None])
        self.assertEqual(session.score, 4)
        self.assertTrue(session.submitted)

    def test_go_to_next_question_marks_completed_on_last_question(self) -> None:
        session = QuizSession(
            questions=_sample_questions(),
            answers=["4", None],
            question_index=1,
            selected_option=None,
            submitted=False,
            score=4,
            phase="in_progress",
        )

        moved = go_to_next_question(session)

        self.assertFalse(moved)
        self.assertEqual(session.phase, "completed")
        self.assertEqual(session.question_index, 1)

    def test_go_to_previous_question_syncs_selected_answer(self) -> None:
        session = QuizSession(
            questions=_sample_questions(),
            answers=["4", None],
            question_index=1,
            selected_option=None,
            submitted=False,
            score=4,
            phase="in_progress",
        )

        moved = go_to_previous_question(session)

        self.assertTrue(moved)
        self.assertEqual(session.question_index, 0)
        self.assertEqual(session.selected_option, "4")
        self.assertTrue(session.submitted)

    def test_reset_quiz_progress_clears_answers_and_score(self) -> None:
        session = QuizSession(
            questions=_sample_questions(),
            answers=["4", "Paris"],
            question_index=1,
            selected_option="Paris",
            submitted=True,
            score=8,
            phase="completed",
        )

        reset_quiz_progress(session, phase="in_progress")

        self.assertEqual(session.answers, [None, None])
        self.assertEqual(session.question_index, 0)
        self.assertIsNone(session.selected_option)
        self.assertFalse(session.submitted)
        self.assertEqual(session.score, 0)
        self.assertEqual(session.phase, "in_progress")

    def test_build_quiz_summary_reports_review_metrics(self) -> None:
        session = QuizSession(
            questions=_sample_questions(),
            answers=["4", None],
            score=4,
            phase="completed",
        )

        summary = build_quiz_summary(session)

        self.assertEqual(summary.total_questions, 2)
        self.assertEqual(summary.answered_questions, 1)
        self.assertEqual(summary.correct_answers, 1)
        self.assertEqual(summary.accuracy, 50.0)
        self.assertEqual(summary.review_items[0].selected_answer, "4")
        self.assertEqual(summary.review_items[1].selected_answer, None)


if __name__ == "__main__":
    unittest.main()
