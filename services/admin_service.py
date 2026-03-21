from __future__ import annotations

from dataclasses import dataclass

from services.auth_service import _create_authenticated_supabase_client, _read_attr


@dataclass(frozen=True, slots=True)
class AdminUserOverview:
    id: str
    email: str
    is_admin: bool
    generated_quiz_count: int
    last_online_at_iso: str | None
    created_at_iso: str


def fetch_all_user_overviews(*, access_token: str, refresh_token: str) -> list[AdminUserOverview]:
    client, _, _, _ = _create_authenticated_supabase_client(
        access_token=access_token,
        refresh_token=refresh_token,
    )
    response = client.table("profiles").select("*").execute()
    rows = [dict(row) for row in list(_read_attr(response, "data", []) or [])]
    rows.sort(
        key=lambda row: (
            row.get("last_online_at") is None,
            str(row.get("last_online_at") or ""),
            str(row.get("created_at") or ""),
        ),
        reverse=False,
    )
    rows.reverse()
    return [
        AdminUserOverview(
            id=str(row["id"]),
            email=str(row["email"]),
            is_admin=bool(row.get("is_admin", False)),
            generated_quiz_count=int(row.get("generated_quiz_count") or 0),
            last_online_at_iso=str(row["last_online_at"]) if row.get("last_online_at") else None,
            created_at_iso=str(row["created_at"]),
        )
        for row in rows
    ]
