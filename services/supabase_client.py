from __future__ import annotations

import os
from typing import Any

import streamlit as st  # type: ignore

SUPABASE_URL_KEY = "SUPABASE_URL"
SUPABASE_PUBLISHABLE_KEY = "SUPABASE_PUBLISHABLE_KEY"

try:
    from supabase import create_client
except ImportError:
    create_client = None


def _read_config_value(name: str) -> str | None:
    secret_value: Any = None
    try:
        secret_value = st.secrets.get(name)
    except Exception:
        secret_value = None

    env_value = os.getenv(name)
    resolved_value = secret_value or env_value
    if resolved_value is None:
        return None
    normalized_value = str(resolved_value).strip()
    return normalized_value or None


def get_supabase_url() -> str | None:
    return _read_config_value(SUPABASE_URL_KEY)


def get_supabase_publishable_key() -> str | None:
    return _read_config_value(SUPABASE_PUBLISHABLE_KEY)


def has_supabase_config() -> bool:
    return bool(get_supabase_url() and get_supabase_publishable_key())


def create_supabase_client():
    supabase_url = get_supabase_url()
    publishable_key = get_supabase_publishable_key()
    if create_client is None:
        raise RuntimeError("Missing dependency: install the Supabase Python client first.")
    if not supabase_url or not publishable_key:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY in Streamlit secrets."
        )
    return create_client(supabase_url, publishable_key)
