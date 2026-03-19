GEMINI_API_KEY_NAME = "GEMINI_API_KEY"
GEMINI_MODEL_OPTIONS = (
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
)
HINT_GEMINI_MODEL = "gemini-2.5-flash-lite"
DEFAULT_GEMINI_MODEL = GEMINI_MODEL_OPTIONS[0]

DEFAULT_QUESTIONS: list[dict] = []

DIFFICULTY_DETAILS = {
    "easy": {
        "label": "Easy",
        "description": "Grade 5 level kid",
        "prompt_guidance": (
            "Target a grade 5 student. Use simple vocabulary, direct wording, and foundational concepts."
        ),
    },
    "medium": {
        "label": "Medium",
        "description": "Grade 10 level kid",
        "prompt_guidance": (
            "Target a grade 10 student. Use standard high-school difficulty with moderate reasoning."
        ),
    },
    "hard": {
        "label": "Hard",
        "description": "College-going kid",
        "prompt_guidance": (
            "Target a college student. Use deeper conceptual understanding, multi-step reasoning, or stronger subject detail."
        ),
    },
    "insane": {
        "label": "Insane",
        "description": "Some of the hardest possible questions",
        "prompt_guidance": (
            "Make the questions exceptionally challenging, near the upper limit of what a strong specialist or advanced college student could handle."
        ),
    },
}
