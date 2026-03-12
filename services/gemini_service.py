import json
import os
import re
import time

import streamlit as st  # type: ignore

from constants import DEFAULT_GEMINI_MODEL, DIFFICULTY_DETAILS, GEMINI_API_KEY_NAME, GEMINI_MODEL_OPTIONS
from models import Question
from services.question_io import validate_questions

try:
    from google import genai
    from google.genai.errors import APIError
except ImportError:
    genai = None
    APIError = None


RETRYABLE_GEMINI_ERROR_CODES = {429, 500, 502, 503, 504}
GEMINI_RETRY_DELAYS_SECONDS = (1.0, 2.0)


def normalize_gemini_model(model_name: str) -> str:
    normalized_model = str(model_name).strip()
    if normalized_model in GEMINI_MODEL_OPTIONS:
        return normalized_model
    return DEFAULT_GEMINI_MODEL


def get_gemini_api_key() -> str | None:
    secret_key = None
    try:
        secret_key = st.secrets.get(GEMINI_API_KEY_NAME)
    except Exception:
        secret_key = None

    env_key = os.getenv(GEMINI_API_KEY_NAME)
    api_key = secret_key or env_key
    if api_key:
        api_key = str(api_key).strip()
    return api_key or None


def has_gemini_api_key() -> bool:
    return bool(get_gemini_api_key())


def get_gemini_client():
    api_key = get_gemini_api_key()
    if genai is None:
        raise RuntimeError("Missing dependency: install the Google GenAI SDK first.")
    if not api_key:
        raise RuntimeError(
            "Missing Gemini API key. Set GEMINI_API_KEY in .streamlit/secrets.toml or as an environment variable."
        )
    return genai.Client(api_key=api_key)


def _extract_json_payload(response_text: str) -> str:
    text = response_text.strip()
    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced_match:
        text = fenced_match.group(1).strip()

    for opener, closer in (("[", "]"), ("{", "}")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end != -1 and start < end:
            return text[start : end + 1]

    return text


def _is_retryable_gemini_error(exc: Exception) -> bool:
    return bool(APIError is not None and isinstance(exc, APIError) and getattr(exc, "code", None) in RETRYABLE_GEMINI_ERROR_CODES)


def _build_generation_error(exc: Exception) -> RuntimeError:
    if APIError is not None and isinstance(exc, APIError):
        code = getattr(exc, "code", None)
        message = (getattr(exc, "message", None) or "The Gemini API request failed.").strip()
        if code in RETRYABLE_GEMINI_ERROR_CODES:
            return RuntimeError(f"Gemini is temporarily unavailable ({code}). Please try again in a moment.")
        return RuntimeError(f"Gemini request failed ({code}): {message}")

    return RuntimeError(f"Gemini request failed: {exc}")


def _generate_content_with_retries(client, prompt: str, model_name: str):
    last_exc: Exception | None = None
    normalized_model = normalize_gemini_model(model_name)
    for attempt in range(len(GEMINI_RETRY_DELAYS_SECONDS) + 1):
        try:
            return client.models.generate_content(
                model=normalized_model,
                contents=prompt,
            )
        except Exception as exc:
            last_exc = exc
            if not _is_retryable_gemini_error(exc) or attempt >= len(GEMINI_RETRY_DELAYS_SECONDS):
                raise _build_generation_error(exc) from exc
            time.sleep(GEMINI_RETRY_DELAYS_SECONDS[attempt])

    if last_exc is not None:
        raise _build_generation_error(last_exc) from last_exc
    raise RuntimeError("Gemini request failed before a response was received.")


def build_generation_prompt(topic: str, difficulty: str, count: int) -> str:
    normalized_topic = topic.strip() or "general knowledge"
    difficulty_key = difficulty if difficulty in DIFFICULTY_DETAILS else "medium"
    difficulty_details = DIFFICULTY_DETAILS[difficulty_key]
    difficulty_label = difficulty_details["label"]
    difficulty_description = difficulty_details["description"]
    prompt_guidance = difficulty_details["prompt_guidance"]

    return f"""
Generate exactly {count} unique multiple-choice quiz questions about "{normalized_topic}".
Difficulty level: {difficulty_label} ({difficulty_description}).
Audience guidance: {prompt_guidance}
Requirements:
- Match the requested difficulty consistently across every question.
- Each question must have exactly 4 options.
- Exactly 1 option must be clearly correct.
- Keep the wording concise and natural for the intended learner level.
- Keep answer options short, plausible, and clearly distinct.
- Avoid duplicate questions, trick wording, and "all/none of the above".
- Prefer questions that test understanding, not random trivia, unless the topic naturally requires factual recall.
Return ONLY valid JSON as an array of objects in this format:
[
  {{
    "question": "Question text",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "correct_answer": "One of the option strings exactly"
  }}
]
No markdown. No commentary.
""".strip()


def generate_gemini_questions(topic: str, difficulty: str, count: int, model_name: str = DEFAULT_GEMINI_MODEL) -> list[Question]:
    client = get_gemini_client()
    prompt = build_generation_prompt(topic=topic, difficulty=difficulty, count=count)
    response = _generate_content_with_retries(client, prompt, model_name=model_name)
    response_text = getattr(response, "text", None)
    if not response_text:
        raise RuntimeError("Gemini returned an empty response.")

    try:
        payload = _extract_json_payload(str(response_text))
        raw_questions = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Gemini returned invalid JSON for quiz generation.") from exc

    return validate_questions(raw_questions, expected_count=count)
