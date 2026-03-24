from __future__ import annotations

import re
from dataclasses import dataclass
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


class SessionExpiredError(RuntimeError):
    """Raised when stored auth tokens no longer represent a valid session."""


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


def _is_expired_session_error(exc: Exception) -> bool:
    lowered = _error_message(exc).casefold()
    return any(
        fragment in lowered
        for fragment in (
            "session expired",
            "session has expired",
            "invalid session",
            "invalid refresh token",
            "refresh token",
            "jwt expired",
            "token has expired",
        )
    )


def _create_authenticated_supabase_client(access_token: str, refresh_token: str):
    normalized_access_token = str(access_token).strip()
    normalized_refresh_token = str(refresh_token).strip()
    if not normalized_access_token or not normalized_refresh_token:
        raise SessionExpiredError("Your session has expired. Please sign in again.")

    auth_client = create_supabase_client()
    try:
        session_response = auth_client.auth.set_session(normalized_access_token, normalized_refresh_token)
    except Exception as exc:
        if _is_expired_session_error(exc):
            raise SessionExpiredError("Your session has expired. Please sign in again.") from exc
        raise RuntimeError(f"Could not restore your Supabase session: {_error_message(exc)}") from exc
    session = _extract_session(session_response)
    current_user = _extract_user(session_response)
    refreshed_access_token, refreshed_refresh_token = _extract_tokens(session)
    if current_user is None or not refreshed_access_token or not refreshed_refresh_token:
        raise SessionExpiredError("Your session has expired. Please sign in again.")
    client = create_supabase_client(access_token=refreshed_access_token)
    return client, current_user, refreshed_access_token, refreshed_refresh_token


def _fetch_profile(client, user_id: str) -> dict[str, Any] | None:
    response = client.table("profiles").select("*").eq("id", user_id).limit(1).execute()
    rows = list(_read_attr(response, "data", []) or [])
    if not rows:
        return None
    return dict(rows[0])


def _execute_profile_rpc(client, function_name: str) -> Any:
    try:
        response = client.rpc(function_name, {}).execute()
    except Exception as exc:
        raise RuntimeError(
            "Supabase rejected the protected profile update. Run supabase_schema.sql in your Supabase project so the "
            "expected RPC functions and grants are in place."
        ) from exc
    return _read_attr(response, "data")


def _upsert_profile(client, *, user_id: str, email: str) -> dict[str, Any]:
    existing_profile = _fetch_profile(client, user_id=user_id)
    try:
        if existing_profile is None:
            client.table("profiles").insert({"id": user_id, "email": email}).execute()
        elif str(existing_profile.get("email") or "") != email:
            client.table("profiles").update({"email": email}).eq("id", user_id).execute()
        else:
            return existing_profile
    except Exception as exc:
        raise RuntimeError(
            "Supabase rejected the profile write. Run supabase_schema.sql in your Supabase project and confirm the "
            "profiles table plus RLS policies were created correctly."
        ) from exc

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
            raise RuntimeError("Supabase did not return the stored account details.")
        profile = _upsert_profile(client, user_id=user_id, email=email)
    except SessionExpiredError:
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


def touch_user_last_online(*, access_token: str, refresh_token: str) -> None:
    client, _, _, _ = _create_authenticated_supabase_client(
        access_token=access_token,
        refresh_token=refresh_token,
    )
    updated_timestamp = _execute_profile_rpc(client, "touch_my_last_online")
    if updated_timestamp is None:
        raise RuntimeError("Could not update your last online timestamp in Supabase.")


def increment_generated_quiz_count(*, access_token: str, refresh_token: str) -> None:
    client, _, _, _ = _create_authenticated_supabase_client(
        access_token=access_token,
        refresh_token=refresh_token,
    )
    updated_count = _execute_profile_rpc(client, "increment_my_generated_quiz_count")
    if updated_count is None:
        raise RuntimeError("Could not update your generated quiz count in Supabase.")
