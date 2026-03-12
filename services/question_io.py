import csv
import io
import json

from models import Question


def _normalize_correct_answer(correct_answer: str, options: list[str]) -> str:
    normalized_answer = correct_answer.strip()
    if normalized_answer in {"A", "B", "C", "D"}:
        normalized_answer = options["ABCD".index(normalized_answer)]
    return normalized_answer


def validate_questions(raw_questions: object, expected_count: int | None = None) -> list[Question]:
    if isinstance(raw_questions, dict):
        raw_questions = [raw_questions]

    if not isinstance(raw_questions, list):
        raise ValueError("Questions must be provided as a list.")
    if not raw_questions:
        raise ValueError("No questions were provided.")

    normalized_questions: list[Question] = []
    seen_questions: set[str] = set()
    for index, item in enumerate(raw_questions, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Question {index} must be a JSON object.")

        question_text = str(item.get("question", "")).strip()
        raw_options = item.get("options", [])
        raw_correct_answer = str(item.get("correct_answer", "")).strip()

        if not question_text:
            raise ValueError(f"Question {index} is missing question text.")
        if not isinstance(raw_options, list):
            raise ValueError(f"Question {index} options must be a list.")

        options = [str(option).strip() for option in raw_options]
        if len(options) != 4:
            raise ValueError(f"Question {index} must have exactly 4 options.")
        if any(not option for option in options):
            raise ValueError(f"Question {index} has an empty option.")
        normalized_options = [option.casefold() for option in options]
        if len(set(normalized_options)) != len(options):
            raise ValueError(f"Question {index} must not contain duplicate options.")

        correct_answer = _normalize_correct_answer(raw_correct_answer, options)
        if not correct_answer:
            raise ValueError(f"Question {index} is missing a correct answer.")
        if correct_answer not in options:
            raise ValueError(f"Question {index} correct answer must match one of the options.")
        normalized_question = question_text.casefold()
        if normalized_question in seen_questions:
            raise ValueError(f"Question {index} is duplicated.")
        seen_questions.add(normalized_question)

        normalized_questions.append(
            Question(
                question=question_text,
                options=options,
                correct_answer=correct_answer,
            )
        )

    if expected_count is not None and len(normalized_questions) != expected_count:
        raise ValueError(
            f"Received {len(normalized_questions)} question(s); expected {expected_count}."
        )

    return normalized_questions


def questions_to_dicts(questions: list[Question]) -> list[dict]:
    return [question.to_dict() for question in questions]


def question_dicts_to_models(raw_questions: list[dict]) -> list[Question]:
    # Reuse the shared validator so session data and uploaded data follow the same rules.
    return validate_questions(raw_questions)


def load_questions_from_json_file(uploaded_file) -> list[Question]:
    try:
        raw_questions = json.load(uploaded_file)
    finally:
        uploaded_file.seek(0)
    return validate_questions(raw_questions)


def load_questions_from_csv_file(uploaded_file) -> list[Question]:
    required_columns = ["question", "option1", "option2", "option3", "option4", "correct_answer"]
    try:
        csv_text = uploaded_file.getvalue().decode("utf-8")
    finally:
        uploaded_file.seek(0)

    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise ValueError("CSV file is empty.")

    missing_columns = [column for column in required_columns if column not in reader.fieldnames]
    if missing_columns:
        raise ValueError(f"CSV is missing columns: {', '.join(missing_columns)}")

    raw_questions = []
    for row in reader:
        raw_questions.append(
            {
                "question": row.get("question", ""),
                "options": [
                    row.get("option1", ""),
                    row.get("option2", ""),
                    row.get("option3", ""),
                    row.get("option4", ""),
                ],
                "correct_answer": row.get("correct_answer", ""),
            }
        )

    return validate_questions(raw_questions)


def load_questions_from_uploaded_file(uploaded_file) -> list[Question]:
    file_name = uploaded_file.name.lower()
    if file_name.endswith(".json"):
        return load_questions_from_json_file(uploaded_file)
    if file_name.endswith(".csv"):
        return load_questions_from_csv_file(uploaded_file)
    raise ValueError("Unsupported file type. Use JSON or CSV.")
