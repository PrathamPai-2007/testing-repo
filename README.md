# AI Quiz

A Streamlit quiz app that can:

- generate multiple-choice quizzes with Gemini
- load quizzes from JSON or CSV files
- let users play through the quiz with live scoring
- export the current question set as PDF or JSON

The app is built around a simple quiz flow:

1. Configure topic, difficulty, and question count.
2. Generate a quiz from Gemini or upload your own questions.
3. Play through the questions one by one.
4. Review the final summary screen.
5. Restart the same quiz, clear everything, or export the questions.

## Current Feature Set

- Gemini-powered quiz generation
- Upload support for `JSON` and `CSV`
- Synced quiz settings on both the setup screen and sidebar
- Sidebar starts collapsed by default
- Four difficulty levels: `easy`, `medium`, `hard`, `insane`
- Scoring system:
  - correct answer: `+4`
  - incorrect answer: `-1`
  - unattempted answer: `0`
- End-of-quiz summary with:
  - total score
  - correct answers count
  - accuracy
  - per-question review
- "Restart Current Quiz" to replay the same loaded questions
- "Start from Scratch" to clear all loaded/generated questions and return to the initial setup state
- "Generate a New Question" during the quiz to append one extra Gemini-generated question
- Export the current quiz as:
  - `PDF`
  - `JSON`

## Difficulty Levels

The app uses these difficulty definitions throughout the UI and Gemini prompt generation:

- `easy`: grade 5 level kid
- `medium`: grade 10 level kid
- `hard`: college-going kid
- `insane`: some of the hardest possible questions

These definitions are not just labels. They are passed into the Gemini prompt so generation quality aligns with the selected learner level.

## Screens And User Flow

### 1. Setup Screen

The setup screen is the homepage of the app.

It includes:

- topic input
- difficulty selector
- number-of-questions selector
- difficulty guide
- "Generate from Scratch" button

If questions are already loaded, the screen shows quiz readiness details and allows the user to:

- start the quiz
- regenerate the full quiz from scratch

### 2. Sidebar

The sidebar mirrors the same synced configuration controls:

- topic
- difficulty
- question count

It also contains:

- "Generate from Scratch"
- total loaded question count
- "Download Questions PDF"
- "Download Questions JSON"
- upload controls for JSON or CSV

### 3. Quiz Screen

The quiz screen displays:

- current question number
- running score
- four answer options
- instant correctness feedback after answering
- navigation controls

Behavior details:

- Users can answer each question only once.
- The last question shows `End Quiz` instead of `Next`.
- "Generate a New Question" appends one new Gemini question to the existing quiz instead of replacing it.

### 4. Completed Screen

The completed screen shows:

- final score
- number of correct answers
- accuracy percentage
- question-by-question review

Available actions:

- `Give an AI Summary`
  - currently a placeholder button with no attached behavior
- `Restart Current Quiz`
  - replays the same loaded questions from the beginning
- `Start from Scratch`
  - clears all loaded/generated questions and returns to the initial setup state

## Scoring Rules

Scoring is applied when the user submits an answer:

- correct answer: `+4`
- incorrect answer: `-1`
- unattempted question: `0`

Unattempted questions stay neutral because score changes only happen on submission.

## Gemini Integration

Gemini generation is implemented in `services/gemini_service.py`.

The generation prompt is designed to enforce:

- exactly the requested number of questions
- exactly 4 options per question
- exactly 1 correct answer
- concise, natural wording
- difficulty-specific learner targeting
- no duplicate questions
- no "all of the above" or "none of the above"

The app also includes retry handling for temporary Gemini API failures.

## Requirements

Install dependencies from this directory:

```powershell
pip install -r requirements.txt
```

Current dependencies:

- `streamlit`
- `google-genai`
- `reportlab`

`reportlab` is required for PDF export.

## Run The App

From `Python/AI_Quiz`:

```powershell
streamlit run main.py
```

## Gemini API Key Setup

Quiz generation requires a Gemini API key.

You can provide it in either of these ways:

### Option 1: Streamlit secrets

Create:

```text
Python/AI_Quiz/.streamlit/secrets.toml
```

Add:

```toml
GEMINI_API_KEY = "your-real-key-here"
```

### Option 2: Environment variable

```powershell
$env:GEMINI_API_KEY = "your-real-key-here"
```

Notes:

- Do not commit a real API key.
- The app can still be used without Gemini if you upload your own questions.

## Import Formats

The app accepts uploaded quiz files in `JSON` or `CSV`.

### JSON Format

```json
[
  {
    "question": "What is the capital of France?",
    "options": ["Berlin", "Madrid", "Paris", "Rome"],
    "correct_answer": "Paris"
  }
]
```

### CSV Format

```text
question,option1,option2,option3,option4,correct_answer
What is the capital of France?,Berlin,Madrid,Paris,Rome,Paris
```

### Validation Rules

Every uploaded question must:

- contain question text
- have exactly 4 options
- not contain empty options
- not contain duplicate options
- have a correct answer that matches one of the options
- not duplicate another question in the same upload

The validator also accepts `A`, `B`, `C`, or `D` as `correct_answer`, and converts that letter to the matching option.

## Export Formats

The current loaded quiz can be downloaded as:

### PDF

The PDF export includes:

- topic
- difficulty
- total question count
- every question
- all four options
- the correct answer

### JSON

The JSON export is the current in-memory quiz state written as a formatted JSON array.

## Project Structure

```text
Python/AI_Quiz/
|-- main.py
|-- constants.py
|-- models.py
|-- state.py
|-- requirements.txt
|-- README.md
|-- services/
|   |-- __init__.py
|   |-- export_service.py
|   |-- gemini_service.py
|   |-- question_io.py
|   |-- quiz_service.py
|-- ui/
|   |-- __init__.py
|   |-- completed_screen.py
|   |-- quiz_screen.py
|   |-- settings_controls.py
|   |-- setup_screen.py
|   |-- sidebar.py
|   |-- styles.py
|-- tests/
|   |-- __init__.py
|   |-- test_gemini_service.py
|   |-- test_question_io.py
```

## File Overview

### Core

- `main.py`
  - Streamlit entrypoint
  - page config
  - phase routing
- `constants.py`
  - API key name
  - default questions
  - difficulty definitions and prompt guidance
- `models.py`
  - `Question` dataclass
- `state.py`
  - session-state initialization
  - quiz phase transitions
  - reset helpers

### Services

- `services/gemini_service.py`
  - Gemini client setup
  - prompt construction
  - retry logic
  - JSON response parsing
- `services/question_io.py`
  - validation
  - JSON/CSV loading
  - conversion helpers
- `services/quiz_service.py`
  - question generation orchestration
  - score updates
  - next/back navigation
  - completion flow
- `services/export_service.py`
  - JSON export
  - PDF export

### UI

- `ui/setup_screen.py`
  - homepage/setup experience
- `ui/sidebar.py`
  - configuration, exports, uploads
- `ui/settings_controls.py`
  - shared synced settings controls
- `ui/quiz_screen.py`
  - main quiz interaction
- `ui/completed_screen.py`
  - results and replay/reset actions
- `ui/styles.py`
  - styling, overlays, browser-side helpers

### Tests

- `tests/test_question_io.py`
  - validation rules
  - upload parsing
  - Gemini JSON extraction helper coverage
- `tests/test_gemini_service.py`
  - Gemini retry behavior
  - prompt-shaping coverage

## Running Tests

From `Python/AI_Quiz`:

```powershell
python -m unittest tests.test_question_io tests.test_gemini_service
```

## Notes

- The app starts with an empty quiz by default.
- Question generation is limited to `1` to `5` questions per generation request.
- Uploaded questions replace the current quiz.
- "Generate from Scratch" replaces the current quiz.
- "Generate a New Question" appends to the current quiz.
- The app is currently optimized around multiple-choice questions with exactly 4 options.
