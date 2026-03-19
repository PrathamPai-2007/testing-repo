import io
import unittest

from services.gemini_service import _extract_json_payload
from services.question_io import (
    load_questions_from_csv_file,
    load_questions_from_json_file,
    validate_questions,
)


class NamedBytesIO(io.BytesIO):
    def __init__(self, content: bytes, name: str) -> None:
        super().__init__(content)
        self.name = name


class ValidateQuestionsTests(unittest.TestCase):
    def test_valid_questions_pass_validation(self) -> None:
        raw_questions = [
            {
                "question": "Capital of France?",
                "options": ["Berlin", "Madrid", "Paris", "Rome"],
                "correct_answer": "Paris",
            }
        ]

        questions = validate_questions(raw_questions)

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].correct_answer, "Paris")

    def test_question_with_three_options_fails(self) -> None:
        raw_questions = [
            {
                "question": "Capital of France?",
                "options": ["Berlin", "Paris", "Rome"],
                "correct_answer": "Paris",
            }
        ]

        with self.assertRaisesRegex(ValueError, "exactly 4 options"):
            validate_questions(raw_questions)

    def test_question_with_wrong_correct_answer_fails(self) -> None:
        raw_questions = [
            {
                "question": "2 + 2 = ?",
                "options": ["1", "2", "3", "4"],
                "correct_answer": "5",
            }
        ]

        with self.assertRaisesRegex(ValueError, "must match one of the options"):
            validate_questions(raw_questions)

    def test_question_with_duplicate_options_fails(self) -> None:
        raw_questions = [
            {
                "question": "Pick the even number",
                "options": ["2", "2", "3", "5"],
                "correct_answer": "2",
            }
        ]

        with self.assertRaisesRegex(ValueError, "duplicate options"):
            validate_questions(raw_questions)

    def test_duplicate_questions_fail_validation(self) -> None:
        raw_questions = [
            {
                "question": "Capital of France?",
                "options": ["Berlin", "Madrid", "Paris", "Rome"],
                "correct_answer": "Paris",
            },
            {
                "question": "capital of france?",
                "options": ["Paris", "Lyon", "Nice", "Lille"],
                "correct_answer": "Paris",
            },
        ]

        with self.assertRaisesRegex(ValueError, "duplicated"):
            validate_questions(raw_questions)


class UploadLoaderTests(unittest.TestCase):
    def test_json_upload_loader_accepts_valid_file(self) -> None:
        uploaded_file = NamedBytesIO(
            b'[{"question":"Largest planet?","options":["Earth","Mars","Jupiter","Venus"],"correct_answer":"Jupiter"}]',
            "questions.json",
        )

        questions = load_questions_from_json_file(uploaded_file)

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].question, "Largest planet?")

    def test_csv_upload_loader_rejects_missing_column(self) -> None:
        uploaded_file = NamedBytesIO(
            (
                "question,option1,option2,option3,correct_answer\n"
                "Capital of France?,Berlin,Madrid,Paris,Paris\n"
            ).encode("utf-8"),
            "questions.csv",
        )

        with self.assertRaisesRegex(ValueError, "missing columns"):
            load_questions_from_csv_file(uploaded_file)

    def test_csv_upload_loader_rejects_empty_question(self) -> None:
        uploaded_file = NamedBytesIO(
            (
                "question,option1,option2,option3,option4,correct_answer\n"
                ",Berlin,Madrid,Paris,Rome,Paris\n"
            ).encode("utf-8"),
            "questions.csv",
        )

        with self.assertRaisesRegex(ValueError, "missing question text"):
            load_questions_from_csv_file(uploaded_file)


class GeminiParsingTests(unittest.TestCase):
    def test_extract_json_payload_from_code_fence(self) -> None:
        response_text = """
        ```json
        [{"question":"Largest planet?","options":["Earth","Mars","Jupiter","Venus"],"correct_answer":"Jupiter"}]
        ```
        """

        payload = _extract_json_payload(response_text)

        self.assertEqual(
            payload,
            '[{"question":"Largest planet?","options":["Earth","Mars","Jupiter","Venus"],"correct_answer":"Jupiter"}]',
        )

    def test_extract_json_payload_from_wrapped_text(self) -> None:
        response_text = (
            'Here is the quiz:\n'
            '[{"question":"Largest planet?","options":["Earth","Mars","Jupiter","Venus"],"correct_answer":"Jupiter"}]\n'
            "Use it directly."
        )

        payload = _extract_json_payload(response_text)

        self.assertEqual(
            payload,
            '[{"question":"Largest planet?","options":["Earth","Mars","Jupiter","Venus"],"correct_answer":"Jupiter"}]',
        )


if __name__ == "__main__":
    unittest.main()
