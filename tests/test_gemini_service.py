import unittest
from unittest.mock import patch

from google.genai.errors import ServerError

from models import Question
from services.gemini_service import (
    _generate_content_with_retries,
    build_hint_prompt,
    build_generation_prompt,
    normalize_gemini_model,
)


class _FakeModels:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0
        self.last_model = None

    def generate_content(self, *, model, contents):
        self.calls += 1
        self.last_model = model
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _FakeClient:
    def __init__(self, responses):
        self.models = _FakeModels(responses)


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class GeminiRetryTests(unittest.TestCase):
    def test_retries_temporary_server_error_then_succeeds(self) -> None:
        client = _FakeClient(
            [
                ServerError(503, {"error": {"code": 503, "message": "busy", "status": "UNAVAILABLE"}}),
                _FakeResponse("[]"),
            ]
        )

        with patch("services.gemini_service.time.sleep") as sleep_mock:
            response = _generate_content_with_retries(client, "prompt", "gemini-3-flash-preview")

        self.assertEqual(response.text, "[]")
        self.assertEqual(client.models.calls, 2)
        self.assertEqual(client.models.last_model, "gemini-3-flash-preview")
        sleep_mock.assert_called_once_with(1.0)

    def test_returns_clean_message_after_retry_exhaustion(self) -> None:
        client = _FakeClient(
            [
                ServerError(503, {"error": {"code": 503, "message": "busy", "status": "UNAVAILABLE"}}),
                ServerError(503, {"error": {"code": 503, "message": "busy", "status": "UNAVAILABLE"}}),
                ServerError(503, {"error": {"code": 503, "message": "busy", "status": "UNAVAILABLE"}}),
            ]
        )

        with patch("services.gemini_service.time.sleep") as sleep_mock:
            with self.assertRaisesRegex(RuntimeError, "temporarily unavailable"):
                _generate_content_with_retries(client, "prompt", "gemini-2.5-flash")

        self.assertEqual(client.models.calls, 3)
        self.assertEqual(sleep_mock.call_count, 2)


class GeminiPromptTests(unittest.TestCase):
    def test_build_generation_prompt_uses_grade_based_easy_guidance(self) -> None:
        prompt = build_generation_prompt(topic="fractions", difficulty="easy", count=3)

        self.assertIn('about "fractions"', prompt)
        self.assertIn("Difficulty level: Easy (Grade 5 level kid).", prompt)
        self.assertIn("Target a grade 5 student.", prompt)

    def test_build_generation_prompt_supports_insane_difficulty(self) -> None:
        prompt = build_generation_prompt(topic="physics", difficulty="insane", count=2)

        self.assertIn("Difficulty level: Insane (Some of the hardest possible questions).", prompt)
        self.assertIn("exceptionally challenging", prompt)

    def test_build_hint_prompt_requests_short_non_revealing_hint(self) -> None:
        prompt = build_hint_prompt(
            topic="fractions",
            difficulty="medium",
            question=Question(
                question="Which fraction is the largest?",
                options=["1/2", "2/3", "3/8", "1/4"],
                correct_answer="2/3",
            ),
        )

        self.assertIn("Write exactly one short hint in 1 or 2 sentences.", prompt)
        self.assertIn("Do not quote the correct option verbatim.", prompt)
        self.assertIn("A. 1/2", prompt)
        self.assertIn("B. 2/3", prompt)


class GeminiModelTests(unittest.TestCase):
    def test_known_preview_lite_model_is_accepted(self) -> None:
        self.assertEqual(normalize_gemini_model("gemini-3.1-flash-lite-preview"), "gemini-3.1-flash-lite-preview")

    def test_hint_model_is_accepted(self) -> None:
        self.assertEqual(normalize_gemini_model("gemini-2.5-flash-lite"), "gemini-2.5-flash-lite")

    def test_invalid_model_name_falls_back_to_default(self) -> None:
        self.assertEqual(normalize_gemini_model("not-a-real-model"), "gemini-2.5-flash")


if __name__ == "__main__":
    unittest.main()
