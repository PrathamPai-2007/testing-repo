import json
import os
from datetime import datetime

import streamlit as st # type: ignore

try:
    from google import genai
except ImportError:
    genai = None


GEMINI_API_KEY = "AIzaSyDFBFX5aCAqNhIn_tuo4bemFTyKrl0x3nM"


DEFAULT_QUESTIONS = []


def reset_quiz() -> None:
    st.session_state.question_index = 0
    st.session_state.selected_option = None
    st.session_state.submitted = False
    st.session_state.score = 0
    st.session_state.answers = [None] * len(st.session_state.get("questions", []))


def ensure_answer_slots() -> None:
    questions = st.session_state.get("questions", [])
    answers = st.session_state.get("answers")

    if answers is None:
        st.session_state.answers = [None] * len(questions)
        return

    if len(answers) < len(questions):
        answers.extend([None] * (len(questions) - len(answers)))
    elif len(answers) > len(questions):
        del answers[len(questions) :]


def sync_current_question_state() -> None:
    questions = st.session_state.get("questions", [])
    ensure_answer_slots()

    if not questions:
        st.session_state.question_index = 0
        st.session_state.selected_option = None
        st.session_state.submitted = False
        return

    st.session_state.question_index = min(st.session_state.question_index, len(questions) - 1)
    selected_option = st.session_state.answers[st.session_state.question_index]
    st.session_state.selected_option = selected_option
    st.session_state.submitted = selected_option is not None


def initialize_state() -> None:
    if "question_index" not in st.session_state:
        st.session_state.question_index = 0
    if "selected_option" not in st.session_state:
        st.session_state.selected_option = None
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "questions" not in st.session_state:
        st.session_state.questions = DEFAULT_QUESTIONS.copy()
    if "answers" not in st.session_state:
        st.session_state.answers = [None] * len(st.session_state.questions)
    if "topic" not in st.session_state:
        st.session_state.topic = "math"
    if "difficulty" not in st.session_state:
        st.session_state.difficulty = "medium"
    if "questions_to_generate" not in st.session_state:
        st.session_state.questions_to_generate = 1
    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False
    if "pending_generation" not in st.session_state:
        st.session_state.pending_generation = None
    if "generation_feedback" not in st.session_state:
        st.session_state.generation_feedback = None
    ensure_answer_slots()
    sync_current_question_state()


def get_gemini_api_key() -> str | None:
    if GEMINI_API_KEY.strip():
        return GEMINI_API_KEY.strip()

    secret_key = None
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        secret_key = None
    return secret_key or os.getenv("GEMINI_API_KEY")


def get_gemini_client():
    api_key = get_gemini_api_key()
    if genai is None:
        raise RuntimeError("Missing dependency: install the Google GenAI SDK first.")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY in Streamlit secrets or environment variables.")
    return genai.Client(api_key=api_key)


def normalize_generated_question(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Gemini did not return a JSON object.")

    question = str(data.get("question", "")).strip()
    options = data.get("options", [])
    correct_answer = str(data.get("correct_answer", "")).strip()

    if not question:
        raise ValueError("Generated question is missing the question text.")
    if not isinstance(options, list) or len(options) != 4:
        raise ValueError("Generated question must include exactly 4 options.")

    options = [str(option).strip() for option in options]

    if correct_answer in {"A", "B", "C", "D"}:
        correct_answer = options["ABCD".index(correct_answer)]

    if correct_answer not in options:
        raise ValueError("The correct answer must match one of the generated options.")

    return {
        "question": question,
        "options": options,
        "correct_answer": correct_answer,
    }


def normalize_generated_questions(data: object, expected_count: int) -> list[dict]:
    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list):
        raise ValueError("Gemini did not return a JSON array of questions.")

    normalized_questions = [normalize_generated_question(item) for item in data]

    if len(normalized_questions) != expected_count:
        raise ValueError(
            f"Gemini returned {len(normalized_questions)} question(s); expected {expected_count}."
        )

    return normalized_questions


def generate_gemini_questions(topic: str, difficulty: str, count: int) -> list[dict]:
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
    return normalize_generated_questions(json.loads(response_text), expected_count=count)


def add_generated_question(topic: str, difficulty: str) -> None:
    add_generated_questions(topic=topic, difficulty=difficulty, count=1, jump_to="latest")


def add_generated_questions(topic: str, difficulty: str, count: int, jump_to: str = "first_new") -> int:
    generated_count = max(1, min(int(count), 5))
    if jump_to not in {"first_new", "latest"}:
        raise ValueError("Unsupported jump target for generated questions.")

    starting_index = len(st.session_state.questions)
    generated_questions = generate_gemini_questions(
        topic=topic,
        difficulty=difficulty,
        count=generated_count,
    )
    st.session_state.questions.extend(generated_questions)

    ensure_answer_slots()
    if jump_to == "first_new":
        st.session_state.question_index = starting_index
    else:
        st.session_state.question_index = len(st.session_state.questions) - 1
    sync_current_question_state()
    return generated_count


def build_questions_download() -> str:
    return json.dumps(st.session_state.questions, indent=2, ensure_ascii=False)


def queue_generation(count: int, jump_to: str) -> None:
    st.session_state.pending_generation = {
        "count": max(1, min(int(count), 5)),
        "jump_to": jump_to,
        "topic": st.session_state.topic,
        "difficulty": st.session_state.difficulty,
    }
    st.session_state.is_generating = True


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
        )
        st.session_state.generation_feedback = {
            "type": "success",
            "message": f"{generated_count} Gemini question(s) added to the quiz.",
        }
    except Exception as exc:
        st.session_state.generation_feedback = {
            "type": "error",
            "message": f"Could not generate question: {exc}",
        }
    finally:
        st.session_state.pending_generation = None
        st.session_state.is_generating = False

    st.rerun()


def render_generating_overlay() -> None:
    st.markdown(
        """
        <div class="generation-overlay">
            <div class="generation-overlay__panel">
                <div class="generation-overlay__title">Generating questions</div>
                <div class="generation-overlay__subtitle">Please wait...</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def go_to_previous_question() -> None:
    if st.session_state.question_index > 0:
        st.session_state.question_index -= 1
    sync_current_question_state()


def go_to_next_question() -> None:
    if st.session_state.question_index < len(st.session_state.questions) - 1:
        st.session_state.question_index += 1
        sync_current_question_state()
        return

    queue_generation(count=1, jump_to="latest")


def render_sidebar() -> None:
    st.sidebar.title("Quiz Settings")
    st.sidebar.write("Generate quiz questions with Gemini.")

    topic = st.sidebar.text_input("Quiz topic", value=st.session_state.topic)
    difficulty_options = ["easy", "medium", "hard"]
    difficulty = st.sidebar.selectbox(
        "Difficulty",
        difficulty_options,
        index=difficulty_options.index(st.session_state.difficulty),
    )
    st.session_state.topic = topic
    st.session_state.difficulty = difficulty
    questions_to_generate = st.sidebar.number_input(
        "Questions to generate",
        min_value=1,
        max_value=5,
        value=int(st.session_state.questions_to_generate),
        step=1,
    )
    st.session_state.questions_to_generate = int(questions_to_generate)

    feedback = st.session_state.pop("generation_feedback", None)
    if feedback:
        if feedback["type"] == "success":
            st.sidebar.success(feedback["message"])
        else:
            st.sidebar.error(feedback["message"])

    if st.sidebar.button("Generate Questions"):
        try:
            queue_generation(
                count=st.session_state.questions_to_generate,
                jump_to="first_new",
            )
            st.rerun()
        except Exception as exc:
            st.sidebar.error(f"Could not generate question: {exc}")

    st.sidebar.markdown("---")
    st.sidebar.write(f"**Total Questions Loaded:** {len(st.session_state.questions)}")
    st.sidebar.download_button(
        "Download Questions JSON",
        data=build_questions_download(),
        file_name=f"quiz_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        disabled=not st.session_state.questions,
    )
    if st.sidebar.button("Restart From Beginning"):
        reset_quiz()
        st.rerun()


def render_quiz_ui() -> None:
    questions = st.session_state.questions
    sync_current_question_state()

    if not questions:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.write("**Question 0 of 0**")
        with col_b:
            st.write(f"**Score:** {st.session_state.score}")

        st.markdown('<div class="question-box">No question present</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        columns = [col1, col2, col3, col4]

        for i in range(4):
            with columns[i]:
                st.button(
                    " ",
                    key=f"empty_btn_{i}",
                    disabled=True,
                )

        st.info("Generate a question from the sidebar to begin.")
        return

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.write(f"**Question {st.session_state.question_index + 1} of {len(questions)}**")
    with col_b:
        st.write(f"**Score:** {st.session_state.score}")

    current_q = questions[st.session_state.question_index]
    st.markdown(f'<div class="question-box">{current_q["question"]}</div>', unsafe_allow_html=True)

    options = current_q["options"][:4]
    while len(options) < 4:
        options.append("N/A")

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    columns = [col1, col2, col3, col4]

    for i, option in enumerate(options):
        with columns[i]:
            if st.button(
                option,
                key=f"btn_{st.session_state.question_index}_{i}",
                disabled=st.session_state.submitted,
            ):
                if st.session_state.answers[st.session_state.question_index] is not None:
                    st.rerun()

                st.session_state.selected_option = option
                st.session_state.submitted = True
                st.session_state.answers[st.session_state.question_index] = option

                if option == current_q["correct_answer"]:
                    st.session_state.score += 10
                else:
                    st.session_state.score -= 1

                st.rerun()

    if st.session_state.submitted:
        st.markdown("---")
        is_correct = st.session_state.selected_option == current_q["correct_answer"]

        if is_correct:
            st.success("Correct! Great job.")
        else:
            st.error(f"Incorrect! The correct answer was **{current_q['correct_answer']}**.")

    st.markdown('<div class="next-container">', unsafe_allow_html=True)
    back_col, next_col, generate_col = st.columns(3)

    with back_col:
        if st.button("Back", disabled=st.session_state.question_index == 0):
            go_to_previous_question()
            st.rerun()

    with next_col:
        if st.button("Next"):
            try:
                go_to_next_question()
                st.rerun()
            except Exception as exc:
                st.error(f"Could not load the next question: {exc}")

    with generate_col:
        if st.button("Generate a New Question"):
            try:
                queue_generation(count=1, jump_to="latest")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not generate question: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="Gemini Quiz Generator", page_icon="💀", layout="centered")
    st.markdown(
        """
    <style>
    .question-box {
        background-color: #000000;
        padding: 40px;
        border-radius: 8px;
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 30px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        color: white;
    }

    .stButton>button {
        width: 100%;
        border-radius: 8px;
        border: none;
        padding: 10px 15px;
        font-size: 16px;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    div[data-testid="column"] .stButton>button {
        height: 250px;
        padding: 20px;
        font-size: clamp(24px, 4vw, 50px);
        font-weight: bold;
        color: white;
        white-space: normal;
        word-wrap: break-word;
        line-height: 1.2;
    }

    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0px 5px 15px rgba(0,0,0,0.2);
    }

    div[data-testid="column"]:nth-of-type(1) .stButton>button { background-color: #E21B3C; }
    div[data-testid="column"]:nth-of-type(2) .stButton>button { background-color: #1368CE; }
    div[data-testid="column"]:nth-of-type(3) .stButton>button { background-color: #D89E00; }
    div[data-testid="column"]:nth-of-type(4) .stButton>button { background-color: #26890C; }

    .submit-container .stButton>button, .next-container .stButton>button {
        background-color: #333333 !important;
        height: 60px;
        font-size: 20px;
        margin-top: 20px;
        padding: 10px;
        color: white;
    }

    .score-display {
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
        padding: 10px;
        background-color: #E8F0FE;
        border-radius: 10px;
        color: #1A73E8;
    }

    .generation-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.88);
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(6px);
    }

    .generation-overlay__panel {
        text-align: center;
        padding: 32px 40px;
        border-radius: 16px;
        background: rgba(22, 22, 22, 0.92);
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
    }

    .generation-overlay__title {
        color: #FFFFFF;
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .generation-overlay__subtitle {
        color: #D0D0D0;
        font-size: 18px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    initialize_state()
    render_sidebar()
    if st.session_state.is_generating:
        render_generating_overlay()
        process_pending_generation()
    render_quiz_ui()


if __name__ == "__main__":
    main()
