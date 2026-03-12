import streamlit as st  # type: ignore


APP_STYLES = """
<style>
:root {
    --option-height: 250px;
    --option-font-size: clamp(20px, 2.2vw, 30px);
}

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

.st-key-option-grid div[data-testid="column"] .stButton>button {
    height: var(--option-height);
    padding: 20px;
    font-size: var(--option-font-size);
    font-weight: bold;
    color: white;
    white-space: normal;
    word-wrap: break-word;
    line-height: 1.2;
}

.st-key-option-grid div[data-testid="column"] .stButton>button p,
.st-key-option-grid div[data-testid="column"] .stButton>button span {
    font-size: inherit;
    line-height: inherit;
    margin: 0;
}

.stButton>button:hover {
    transform: scale(1.02);
    box-shadow: 0px 5px 15px rgba(0,0,0,0.2);
}

.stButton>button[kind="primary"] {
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #D9D9D9;
}

.stButton>button[kind="primary"]:hover {
    background-color: #F3F3F3;
    color: #000000;
}

.st-key-option-grid div[data-testid="column"]:nth-of-type(1) .stButton>button { background-color: #E21B3C; }
.st-key-option-grid div[data-testid="column"]:nth-of-type(2) .stButton>button { background-color: #1368CE; }
.st-key-option-grid div[data-testid="column"]:nth-of-type(3) .stButton>button { background-color: #D89E00; }
.st-key-option-grid div[data-testid="column"]:nth-of-type(4) .stButton>button { background-color: #26890C; }

.st-key-quiz-nav .stButton>button {
    height: 60px;
    font-size: 20px;
    margin-top: 20px;
    padding: 10px;
}

.option-feedback {
    height: var(--option-height);
    width: 100%;
    box-sizing: border-box;
    border-radius: 8px;
    padding: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    overflow: hidden;
    font-size: var(--option-font-size);
    font-weight: bold;
    color: #FFFFFF;
    line-height: 1.2;
    word-break: break-word;
    box-shadow: 0px 5px 15px rgba(0,0,0,0.18);
}

.option-feedback__label {
    display: block;
    width: 100%;
    margin: 0;
}

.option-feedback--neutral {
    background-color: #4A4A4A;
}

.option-feedback--correct {
    background-color: #1F8B24;
}

.option-feedback--wrong {
    background-color: #C62828;
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
"""


def render_styles() -> None:
    st.markdown(APP_STYLES, unsafe_allow_html=True)


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
