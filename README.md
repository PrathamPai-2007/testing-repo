# AI Quiz

Streamlit quiz app that generates multiple-choice questions with Gemini or loads them from JSON/CSV files.

## Run

From this folder:

```powershell
streamlit run main.py
```

## Secrets

Create this file locally:

`Python/AI_Quiz/.streamlit/secrets.toml`

Put your Gemini key inside:

```toml
GEMINI_API_KEY = "your-real-key-here"
```

Notes:

- `.streamlit/secrets.toml` is ignored by Git on purpose.
- `.streamlit/secrets.toml.example` is only a template.

## Main Files

- `main.py`: app entrypoint and phase routing
- `state.py`: quiz/session state
- `models.py`: shared `Question` model
- `services/gemini_service.py`: Gemini API access
- `services/question_io.py`: validation plus JSON/CSV loading
- `services/quiz_service.py`: scoring and quiz actions
- `ui/`: Streamlit screens and styles

## Upload Formats

JSON:

```json
[
  {
    "question": "What is the capital of France?",
    "options": ["Berlin", "Madrid", "Paris", "Rome"],
    "correct_answer": "Paris"
  }
]
```

CSV columns:

```text
question,option1,option2,option3,option4,correct_answer
```

## Tests

Run the validation tests with:

```powershell
python -m unittest tests.test_question_io
```

## Deploy

Before deployment:

1. Add `GEMINI_API_KEY` in your deployment platform's secrets/settings.
2. Do not commit the real `secrets.toml`.
3. Launch the app with `main.py`.
