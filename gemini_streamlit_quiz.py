import json
import os

import streamlit as st

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
    if "topic" not in st.session_state:
        st.session_state.topic = "math"
    if "difficulty" not in st.session_state:
        st.session_state.difficulty = "medium"


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


def generate_gemini_question(topic: str, difficulty: str) -> dict:
    client = get_gemini_client()
    prompt = f"""
Generate one {difficulty} multiple-choice quiz question about {topic}.
Return ONLY valid JSON with this exact structure:
{{
  "question": "Question text",
  "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
  "correct_answer": "One of the option strings exactly"
}}
Do not include markdown fences, explanations, or extra text.
"""
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
    )
    response_text = getattr(response, "text", None)
    if not response_text:
        raise RuntimeError("Gemini returned an empty response.")
    return normalize_generated_question(json.loads(response_text))


def add_generated_question(topic: str, difficulty: str) -> None:
    generated_question = generate_gemini_question(topic=topic, difficulty=difficulty)
    st.session_state.questions.append(generated_question)
    st.session_state.question_index = len(st.session_state.questions) - 1
    st.session_state.selected_option = None
    st.session_state.submitted = False


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

    if st.sidebar.button("Generate Question"):
        try:
            add_generated_question(topic=topic, difficulty=difficulty)
            st.sidebar.success("New Gemini question added to the quiz.")
            st.rerun()
        except Exception as exc:
            st.sidebar.error(f"Could not generate question: {exc}")

    st.sidebar.markdown("---")
    st.sidebar.write(f"**Total Questions Loaded:** {len(st.session_state.questions)}")
    if st.sidebar.button("Restart Quiz"):
        reset_quiz()
        st.rerun()


def render_quiz_ui() -> None:
    questions = st.session_state.questions

    if not questions:
        _, col_b = st.columns([3, 1])
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

        st.info("Generate a question from the sidebar or upload a question set to begin.")
        return

    _, col_b = st.columns([3, 1])
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
                st.session_state.selected_option = option
                st.session_state.submitted = True

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
        if st.button("Generate a New Question"):
            try:
                add_generated_question(
                    topic=st.session_state.topic,
                    difficulty=st.session_state.difficulty,
                )
                st.rerun()
            except Exception as exc:
                st.error(f"Could not generate question: {exc}")
        st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="Gemini Quiz Generator", page_icon="📝", layout="centered")
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
    </style>
    """,
        unsafe_allow_html=True,
    )

    initialize_state()
    render_sidebar()
    render_quiz_ui()


if __name__ == "__main__":
    main()
