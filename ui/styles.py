import streamlit as st  # type: ignore
import streamlit.components.v1 as components  # type: ignore


APP_STYLES = """
<style>
:root {
    --option-height: 132px;
    --option-font-size: 18px;
    --option-padding-y: 12px;
    --option-padding-x: 14px;
    --option-row-gap: 14px;
    --option-neutral-bg: #565656;
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
    transition: background-color 0.15s ease;
}

/* Fix: stElementContainer and all descendants need explicit 100% width to override Streamlit's fit-content */
.st-key-answer_0,
.st-key-answer_1,
.st-key-answer_2,
.st-key-answer_3,
.st-key-empty_answer_0,
.st-key-empty_answer_1,
.st-key-empty_answer_2,
.st-key-empty_answer_3,
.st-key-answer_0 .stButton,
.st-key-answer_1 .stButton,
.st-key-answer_2 .stButton,
.st-key-answer_3 .stButton,
.st-key-empty_answer_0 .stButton,
.st-key-empty_answer_1 .stButton,
.st-key-empty_answer_2 .stButton,
.st-key-empty_answer_3 .stButton,
.st-key-answer_0 button,
.st-key-answer_1 button,
.st-key-answer_2 button,
.st-key-answer_3 button,
.st-key-empty_answer_0 button,
.st-key-empty_answer_1 button,
.st-key-empty_answer_2 button,
.st-key-empty_answer_3 button,
.st-key-answer_0 button > div,
.st-key-answer_1 button > div,
.st-key-answer_2 button > div,
.st-key-answer_3 button > div,
.st-key-empty_answer_0 button > div,
.st-key-empty_answer_1 button > div,
.st-key-empty_answer_2 button > div,
.st-key-empty_answer_3 button > div {
    width: 100% !important;
}

.st-key-option_row_1 {
    margin-bottom: var(--option-row-gap);
}

.st-key-answer_0 .stButton>button,
.st-key-answer_1 .stButton>button,
.st-key-answer_2 .stButton>button,
.st-key-answer_3 .stButton>button,
.st-key-empty_answer_0 .stButton>button,
.st-key-empty_answer_1 .stButton>button,
.st-key-empty_answer_2 .stButton>button,
.st-key-empty_answer_3 .stButton>button {
    height: var(--option-height);
    padding: var(--option-padding-y) var(--option-padding-x);
    font-size: var(--option-font-size);
    font-weight: bold;
    color: white;
    white-space: normal;
    word-wrap: break-word;
    line-height: 1.2;
    display: block;
    text-align: center;
    box-shadow: none;
    overflow: hidden;
}

.st-key-answer_0 .stButton>button p,
.st-key-answer_0 .stButton>button span,
.st-key-answer_1 .stButton>button p,
.st-key-answer_1 .stButton>button span,
.st-key-answer_2 .stButton>button p,
.st-key-answer_2 .stButton>button span,
.st-key-answer_3 .stButton>button p,
.st-key-answer_3 .stButton>button span,
.st-key-empty_answer_0 .stButton>button p,
.st-key-empty_answer_0 .stButton>button span,
.st-key-empty_answer_1 .stButton>button p,
.st-key-empty_answer_1 .stButton>button span,
.st-key-empty_answer_2 .stButton>button p,
.st-key-empty_answer_2 .stButton>button span,
.st-key-empty_answer_3 .stButton>button p,
.st-key-empty_answer_3 .stButton>button span {
    font-size: inherit;
    line-height: inherit;
    margin: 0;
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

.st-key-answer_0 .stButton>button,
.st-key-answer_1 .stButton>button,
.st-key-answer_2 .stButton>button,
.st-key-answer_3 .stButton>button,
.st-key-empty_answer_0 .stButton>button,
.st-key-empty_answer_1 .stButton>button,
.st-key-empty_answer_2 .stButton>button,
.st-key-empty_answer_3 .stButton>button {
    background-color: var(--option-neutral-bg);
}

.st-key-answer_0 .stButton>button:hover,
.st-key-answer_1 .stButton>button:hover,
.st-key-answer_2 .stButton>button:hover,
.st-key-answer_3 .stButton>button:hover {
    background-color: #616161;
}

.st-key-quiz_back .stButton>button,
.st-key-quiz_next .stButton>button,
.st-key-quiz_generate .stButton>button {
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
    padding: var(--option-padding-y) var(--option-padding-x);
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
    box-shadow: none;
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


def render_close_sidebar_once() -> None:
    components.html(
        """
        <script>
        const closeSidebar = () => {
          const parentWindow = window.parent;
          if (!parentWindow) {
            return;
          }

          const sidebar = parentWindow.document.querySelector('[data-testid="stSidebar"]');
          if (!sidebar || sidebar.getAttribute('aria-expanded') !== 'true') {
            return;
          }

          const collapseButton = parentWindow.document.querySelector(
            '[data-testid="stSidebarCollapseButton"] button, button[aria-label="Close sidebar"]'
          );
          if (collapseButton) {
            collapseButton.click();
          }
        };

        requestAnimationFrame(closeSidebar);
        setTimeout(closeSidebar, 150);
        </script>
        """,
        height=0,
    )
