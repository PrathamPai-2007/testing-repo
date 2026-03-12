import json
import os
import re

import streamlit as st  # type: ignore

from constants import GEMINI_API_KEY_NAME
from models import Question
from services.question_io import validate_questions

try:
    from google import genai
except ImportError:
    genai = None


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


def generate_gemini_questions(topic: str, difficulty: str, count: int) -> list[Question]:
    client = get_gemini_client()
    normalized_topic = topic.strip() or "general knowledge"
    prompt = f"""
Generate exactly {count} unique {difficulty} multiple-choice quiz questions about "{normalized_topic}".
Requirements:
- Each question must have exactly 4 options.
- Exactly 1 option must be clearly correct.
- Keep the wording concise and natural.
- Keep answer options short and plausible.
- Avoid duplicate questions, trick wording, and "all/none of the above".
Return ONLY valid JSON as an array of objects in this format:
[
  {{
    "question": "Question text",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "correct_answer": "One of the option strings exactly"
  }}
]
No markdown. No commentary.
"""
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
    )
    response_text = getattr(response, "text", None)
    if not response_text:
        raise RuntimeError("Gemini returned an empty response.")

    try:
        payload = _extract_json_payload(str(response_text))
        raw_questions = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Gemini returned invalid JSON for quiz generation.") from exc

    return validate_questions(raw_questions, expected_count=count)


def build_questions_download() -> str:
    return json.dumps(st.session_state.questions, indent=2, ensure_ascii=False)
