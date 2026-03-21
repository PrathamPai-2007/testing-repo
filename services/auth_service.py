from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from services.supabase_client import create_supabase_client


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MIN_LENGTH = 8


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: str
    email: str
    is_admin: bool
    access_token: str
    refresh_token: str


def validate_email(email: str) -> str:
    cleaned_email = str(email).strip()
    if not EMAIL_PATTERN.fullmatch(cleaned_email):
        raise ValueError("Please enter a valid email address.")
    return cleaned_email


def validate_password(password: str) -> str:
    cleaned_password = str(password)
    if len(cleaned_password) < PASSWORD_MIN_LENGTH:
        raise ValueError("Password must be at least 8 characters long.")
    return cleaned_password


def _read_attr(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _extract_session(response: Any) -> Any:
    return _read_attr(response, "session")


def _extract_user(response: Any) -> Any:
    user = _read_attr(response, "user")
    if user is not None:
        return user
    session = _extract_session(response)
    return _read_attr(session, "user")


def _extract_tokens(session: Any) -> tuple[str | None, str | None]:
    access_token = _read_attr(session, "access_token")
    refresh_token = _read_attr(session, "refresh_token")
    if access_token:
        access_token = str(access_token).strip()
    if refresh_token:
        refresh_token = str(refresh_token).strip()
    return access_token or None, refresh_token or None


def _extract_user_identity(user: Any) -> tuple[str | None, str | None]:
    user_id = _read_attr(user, "id")
    email = _read_attr(user, "email")
    if user_id:
        user_id = str(user_id).strip()
    if email:
        email = str(email).strip()
    return user_id or None, email or None


def _error_message(exc: Exception) -> str:
    return str(exc).strip() or exc.__class__.__name__


def _is_invalid_login_error(exc: Exception) -> bool:
    lowered = _error_message(exc).casefold()
    return "invalid login credentials" in lowered or "invalid email or password" in lowered


def _is_duplicate_email_error(exc: Exception) -> bool:
    lowered = _error_message(exc).casefold()
    return "already registered" in lowered or "already been registered" in lowered


def _create_authenticated_supabase_client(access_token: str, refresh_token: str):
    normalized_access_token = str(access_token).strip()
    normalized_refresh_token = str(refresh_token).strip()
    if not normalized_access_token or not normalized_refresh_token:
        raise RuntimeError("Your session has expired. Please sign in again.")

    client = create_supabase_client()
    session_response = client.auth.set_session(normalized_access_token, normalized_refresh_token)
    session = _extract_session(session_response)
    current_user = _extract_user(session_response)
    refreshed_access_token, refreshed_refresh_token = _extract_tokens(session)
    if current_user is None or not refreshed_access_token or not refreshed_refresh_token:
        raise RuntimeError("Could not restore your Supabase session. Please sign in again.")
    return client, current_user, refreshed_access_token, refreshed_refresh_token


def _fetch_profile(client, user_id: str) -> dict[str, Any] | None:
    response = client.table("profiles").select("*").eq("id", user_id).limit(1).execute()
    rows = list(_read_attr(response, "data", []) or [])
    if not rows:
        return None
    return dict(rows[0])


def _upsert_profile(client, *, user_id: str, email: str) -> dict[str, Any]:
    existing_profile = _fetch_profile(client, user_id=user_id)
    payload: dict[str, Any] = {
        "id": user_id,
        "email": email,
    }
    if existing_profile is not None:
        payload["is_admin"] = bool(existing_profile.get("is_admin", False))
        payload["generated_quiz_count"] = int(existing_profile.get("generated_quiz_count") or 0)
        payload["last_online_at"] = existing_profile.get("last_online_at")
        payload["created_at"] = existing_profile.get("created_at")

    client.table("profiles").upsert(payload).execute()
    profile = _fetch_profile(client, user_id=user_id)
    if profile is None:
        raise RuntimeError("Could not load your profile from Supabase.")
    return profile


def _build_authenticated_user(*, user: Any, profile: dict[str, Any], access_token: str, refresh_token: str) -> AuthenticatedUser:
    user_id, email = _extract_user_identity(user)
    if not user_id or not email:
        raise RuntimeError("Supabase did not return a complete user profile.")
    return AuthenticatedUser(
        id=user_id,
        email=str(profile.get("email") or email),
        is_admin=bool(profile.get("is_admin", False)),
        access_token=access_token,
        refresh_token=refresh_token,
    )


def create_user(email: str, password: str) -> AuthenticatedUser:
    cleaned_email = validate_email(email)
    cleaned_password = validate_password(password)
    client = create_supabase_client()

    try:
        response = client.auth.sign_up(
            {
                "email": cleaned_email,
                "password": cleaned_password,
            }
        )
    except Exception as exc:
        if _is_duplicate_email_error(exc):
            raise ValueError("That email address is already registered.") from exc
        raise RuntimeError(f"Could not create your account: {_error_message(exc)}") from exc

    session = _extract_session(response)
    user = _extract_user(response)
    access_token, refresh_token = _extract_tokens(session)
    if user is None or not access_token or not refresh_token:
        raise RuntimeError(
            "Supabase sign up did not return a session. Turn off email confirmation in Supabase for this first version."
        )

    restored_client, restored_user, refreshed_access_token, refreshed_refresh_token = _create_authenticated_supabase_client(
        access_token=access_token,
        refresh_token=refresh_token,
    )
    user_id, resolved_email = _extract_user_identity(restored_user or user)
    if not user_id or not resolved_email:
        raise RuntimeError("Supabase did not return the new account details.")
    profile = _upsert_profile(restored_client, user_id=user_id, email=resolved_email)
    return _build_authenticated_user(
        user=restored_user or user,
        profile=profile,
        access_token=refreshed_access_token,
        refresh_token=refreshed_refresh_token,
    )


def authenticate_user(email: str, password: str) -> AuthenticatedUser | None:
    cleaned_email = validate_email(email)
    client = create_supabase_client()

    try:
        response = client.auth.sign_in_with_password(
            {
                "email": cleaned_email,
                "password": str(password),
            }
        )
    except Exception as exc:
        if _is_invalid_login_error(exc):
            return None
        raise RuntimeError(f"Could not sign in: {_error_message(exc)}") from exc

    session = _extract_session(response)
    user = _extract_user(response)
    access_token, refresh_token = _extract_tokens(session)
    if user is None or not access_token or not refresh_token:
        return None

    restored_client, restored_user, refreshed_access_token, refreshed_refresh_token = _create_authenticated_supabase_client(
        access_token=access_token,
        refresh_token=refresh_token,
    )
    user_id, resolved_email = _extract_user_identity(restored_user or user)
    if not user_id or not resolved_email:
        raise RuntimeError("Supabase did not return the signed-in user details.")
    profile = _upsert_profile(restored_client, user_id=user_id, email=resolved_email)
    return _build_authenticated_user(
        user=restored_user or user,
        profile=profile,
        access_token=refreshed_access_token,
        refresh_token=refreshed_refresh_token,
    )


def restore_authenticated_user(*, access_token: str, refresh_token: str) -> AuthenticatedUser | None:
    normalized_access_token = str(access_token).strip()
    normalized_refresh_token = str(refresh_token).strip()
    if not normalized_access_token or not normalized_refresh_token:
        return None

    try:
        client, user, refreshed_access_token, refreshed_refresh_token = _create_authenticated_supabase_client(
            access_token=normalized_access_token,
            refresh_token=normalized_refresh_token,
        )
        user_id, email = _extract_user_identity(user)
        if not user_id or not email:
            return None
        profile = _upsert_profile(client, user_id=user_id, email=email)
    except Exception:
        return None

    return _build_authenticated_user(
        user=user,
        profile=profile,
        access_token=refreshed_access_token,
        refresh_token=refreshed_refresh_token,
    )


def sign_out_user(*, access_token: str, refresh_token: str) -> None:
    client, _, _, _ = _create_authenticated_supabase_client(
        access_token=access_token,
        refresh_token=refresh_token,
    )
    client.auth.sign_out()


def touch_user_last_online(*, user_id: str, access_token: str, refresh_token: str) -> None:
    client, _, _, _ = _create_authenticated_supabase_client(
        access_token=access_token,
        refresh_token=refresh_token,
    )
    client.table("profiles").update({"last_online_at": datetime.now(UTC).isoformat()}).eq("id", str(user_id).strip()).execute()


def increment_generated_quiz_count(*, user_id: str, access_token: str, refresh_token: str) -> None:
    client, _, _, _ = _create_authenticated_supabase_client(
        access_token=access_token,
        refresh_token=refresh_token,
    )
    profile = _fetch_profile(client, user_id=str(user_id).strip())
    if profile is None:
        raise RuntimeError("Could not find your profile in Supabase.")
    updated_count = int(profile.get("generated_quiz_count") or 0) + 1
    client.table("profiles").update({"generated_quiz_count": updated_count}).eq("id", str(user_id).strip()).execute()
