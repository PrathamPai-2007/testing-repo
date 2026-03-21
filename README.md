# AI Quiz

AI Quiz is a Streamlit quiz app that uses Gemini for question generation and Supabase for authentication and persisted quiz history.

## Current Architecture

- Streamlit UI
- Gemini API for quiz generation and hints
- Supabase Auth for email/password sign up and login
- Supabase PostgREST via the Supabase Python client for `profiles` and `quiz_attempts`

## Features

- Email/password sign up and login
- Gemini-powered quiz generation
- AI hints for quiz questions
- JSON and CSV upload support
- JSON and PDF export support
- Per-user quiz history
- Admin dashboard powered by `profiles.is_admin`

## Important v1 Auth Notes

- Login is email-only
- Username support has been removed
- Password reset is intentionally out of scope for this version
- Admin access is assigned manually in Supabase by setting `profiles.is_admin = true`

## Required Secrets

Add these to Streamlit secrets:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_xxxxx"
```

Example local file:

```text
Python/AI_Quiz/.streamlit/secrets.toml
```

There is also a template at:

```text
Python/AI_Quiz/.streamlit/secrets.toml.example
```

## Supabase Setup

Run the SQL in [`supabase_schema.sql`](./supabase_schema.sql) inside the Supabase SQL editor. It creates:

- `public.profiles`
- `public.quiz_attempts`
- row-level security policies for user-scoped reads/writes
- admin read access on `profiles`

Supabase project expectations:

- Email/password auth enabled
- Email confirmation turned off for this first version
- At least one admin row manually marked with `is_admin = true`

## Install

From the `Python/AI_Quiz` directory:

```powershell
pip install -r requirements.txt
```

## Run

```powershell
streamlit run main.py
```

## Test

```powershell
python -m unittest discover -s tests
```

## Project Layout

```text
Python/AI_Quiz/
|-- main.py
|-- constants.py
|-- models.py
|-- state.py
|-- requirements.txt
|-- README.md
|-- supabase_schema.sql
|-- services/
|   |-- __init__.py
|   |-- admin_service.py
|   |-- auth_service.py
|   |-- export_service.py
|   |-- gemini_service.py
|   |-- history_service.py
|   |-- question_io.py
|   |-- quiz_engine.py
|   |-- quiz_service.py
|   |-- supabase_client.py
|-- ui/
|   |-- __init__.py
|   |-- admin_screen.py
|   |-- auth_screen.py
|   |-- completed_screen.py
|   |-- history_screen.py
|   |-- quiz_screen.py
|   |-- settings_controls.py
|   |-- setup_screen.py
|   |-- sidebar.py
|   |-- styles.py
|-- tests/
|   |-- __init__.py
|   |-- fake_supabase.py
|   |-- test_admin_service.py
|   |-- test_auth_service.py
|   |-- test_gemini_service.py
|   |-- test_history_service.py
|   |-- test_question_io.py
|   |-- test_quiz_engine.py
```
