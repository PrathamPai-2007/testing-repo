# AI Quiz

A Streamlit quiz app that generates and runs multiple-choice quizzes with Gemini.

It supports:

- quiz generation by topic and difficulty
- question uploads from `JSON` or `CSV`
- live scoring with one-question-at-a-time gameplay
- per-question AI hints
- export of the current quiz as `JSON` or `PDF`

## Highlights

- Gemini-powered quiz generation
- Four difficulty levels: `easy`, `medium`, `hard`, `insane`
- One-click hint generation for each question
- Upload your own quiz sets
- Review screen with score, accuracy, and answer breakdown
- Restart the current quiz or start over from scratch
- Sidebar controls for generation, exports, and uploads

## How It Works

1. Choose a topic, difficulty, question count, and Gemini model.
2. Generate a new quiz or upload your own questions.
3. Answer each question one at a time.
4. Use the `Hint` button if you want a small nudge from Gemini.
5. Finish the quiz and review your results.

## Features

### Quiz Generation

The app can generate fresh multiple-choice questions using Gemini based on:

- topic
- difficulty
- requested number of questions
- selected Gemini model

Generated quizzes are validated before they are added to the session.

### AI Hints

Each question includes a `Hint` button.

When clicked:

- the app calls a lightweight Gemini model for a short hint
- the button temporarily changes to `Generating..`
- the generated hint is shown in a small text box

Hints are designed to guide the user without directly revealing the answer.

### Quiz Rules

- Each question has exactly 4 options.
- Only one option is correct.
- Each question can only be answered once.
- Correct answer: `+4`
- Incorrect answer: `-1`
- Unanswered question: `0`

### Upload Support

You can load custom quizzes from:

- `JSON`
- `CSV`

Uploaded questions are validated for:

- required question text
- exactly 4 options
- non-empty options
- no duplicate options
- valid correct answer
- no duplicate questions in the same upload

### Export Support

The current quiz can be downloaded as:

- `JSON`
- `PDF`

The PDF export includes the topic, difficulty, question list, options, and correct answers.

## Screens

### Setup Screen

The setup screen lets you:

- choose topic, difficulty, question count, and model
- generate a new quiz
- start an already prepared quiz

### Sidebar

The sidebar provides:

- synced quiz settings
- quiz generation
- export buttons
- upload controls
- loaded question count

### Quiz Screen

The quiz screen shows:

- current question number
- current score
- answer options
- correctness feedback after submission
- navigation controls
- hint generation
- append-a-question generation

### Completed Screen

The completed screen shows:

- final score
- accuracy
- correct answer count
- per-question review

It also lets the user:

- restart the current quiz
- start from scratch

## Tech Stack

- Python
- Streamlit
- Google Gemini API
- ReportLab

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
|   |-- export_service.py
|   |-- gemini_service.py
|   |-- question_io.py
|   |-- quiz_engine.py
|   |-- quiz_service.py
|-- ui/
|   |-- completed_screen.py
|   |-- quiz_screen.py
|   |-- settings_controls.py
|   |-- setup_screen.py
|   |-- sidebar.py
|   |-- styles.py
|-- tests/
|   |-- test_gemini_service.py
|   |-- test_question_io.py
|   |-- test_quiz_engine.py
```

## Installation

From the `Python/AI_Quiz` directory:

```powershell
pip install -r requirements.txt
```

## Running The App

```powershell
streamlit run main.py
```

## Gemini API Key Setup

Quiz generation and hints require a Gemini API key.

You can provide it in one of these ways.

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

## Input Formats

### JSON

```json
[
  {
    "question": "What is the capital of France?",
    "options": ["Berlin", "Madrid", "Paris", "Rome"],
    "correct_answer": "Paris"
  }
]
```

### CSV

```text
question,option1,option2,option3,option4,correct_answer
What is the capital of France?,Berlin,Madrid,Paris,Rome,Paris
```

The validator also accepts `A`, `B`, `C`, or `D` as `correct_answer`.

## Running Tests

```powershell
python -m unittest discover -s tests
```

## Notes

- The app starts with no questions loaded.
- A generation request currently allows `1` to `5` questions.
- `Generate from Scratch` replaces the current quiz.
- `Generate a New Question` appends a new question to the current quiz.
- If no Gemini API key is configured, uploaded quizzes still work.
