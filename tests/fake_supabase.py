from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class FakeUser:
    id: str
    email: str


@dataclass(slots=True)
class FakeSession:
    access_token: str
    refresh_token: str
    user: FakeUser


@dataclass(slots=True)
class FakeAuthResponse:
    user: FakeUser | None = None
    session: FakeSession | None = None


@dataclass(slots=True)
class FakeTableResponse:
    data: list[dict[str, Any]]


@dataclass(slots=True)
class FakeRpcResponse:
    data: Any


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


PROTECTED_PROFILE_COLUMNS = {"is_admin", "generated_quiz_count", "last_online_at", "created_at"}
PROFILE_INSERTABLE_COLUMNS = {"id", "email"}


class FakeAuth:
    def __init__(self, client: "FakeSupabaseClient") -> None:
        self.client = client
        self._users_by_email: dict[str, dict[str, Any]] = {}
        self._sessions_by_access_token: dict[str, FakeSession] = {}
        self._sessions_by_refresh_token: dict[str, FakeSession] = {}
        self._current_session: FakeSession | None = None

    def _issue_session(self, user: FakeUser) -> FakeSession:
        access_token = f"access-{uuid4()}"
        refresh_token = f"refresh-{uuid4()}"
        session = FakeSession(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user,
        )
        self._sessions_by_access_token[access_token] = session
        self._sessions_by_refresh_token[refresh_token] = session
        self._current_session = session
        return session

    def sign_up(self, credentials: dict[str, Any]) -> FakeAuthResponse:
        email = str(credentials["email"]).strip().casefold()
        password = str(credentials["password"])
        if email in self._users_by_email:
            raise RuntimeError("User already registered")

        user = FakeUser(
            id=str(uuid4()),
            email=str(credentials["email"]).strip(),
        )
        self._users_by_email[email] = {
            "user": user,
            "password": password,
        }
        session = self._issue_session(user)
        return FakeAuthResponse(user=user, session=session)

    def sign_in_with_password(self, credentials: dict[str, Any]) -> FakeAuthResponse:
        email = str(credentials["email"]).strip().casefold()
        password = str(credentials["password"])
        existing_user = self._users_by_email.get(email)
        if existing_user is None or str(existing_user["password"]) != password:
            raise RuntimeError("Invalid login credentials")

        user = existing_user["user"]
        session = self._issue_session(user)
        return FakeAuthResponse(user=user, session=session)

    def set_session(self, access_token: str, refresh_token: str) -> FakeAuthResponse:
        session_by_access = self._sessions_by_access_token.get(str(access_token))
        session_by_refresh = self._sessions_by_refresh_token.get(str(refresh_token))
        if session_by_access is None or session_by_access is not session_by_refresh:
            raise RuntimeError("Invalid session")
        self._current_session = session_by_access
        return FakeAuthResponse(user=session_by_access.user, session=session_by_access)

    def get_user(self, jwt: str | None = None) -> FakeAuthResponse:
        session = self._current_session
        if jwt is not None:
            session = self._sessions_by_access_token.get(str(jwt))
        if session is None:
            raise RuntimeError("No active session")
        return FakeAuthResponse(user=session.user, session=session)

    def sign_out(self) -> None:
        if self._current_session is None:
            return
        access_token = self._current_session.access_token
        refresh_token = self._current_session.refresh_token
        self._sessions_by_access_token.pop(access_token, None)
        self._sessions_by_refresh_token.pop(refresh_token, None)
        self._current_session = None


class FakeTableQuery:
    def __init__(self, client: "FakeSupabaseClient", table_name: str) -> None:
        self.client = client
        self.table_name = table_name
        self.action = "select"
        self.payload: Any = None
        self.filters: list[tuple[str, Any]] = []
        self.limit_value: int | None = None

    def select(self, *_args, **_kwargs) -> "FakeTableQuery":
        self.action = "select"
        return self

    def eq(self, column: str, value: Any) -> "FakeTableQuery":
        self.filters.append((column, value))
        return self

    def limit(self, value: int) -> "FakeTableQuery":
        self.limit_value = int(value)
        return self

    def insert(self, payload: dict[str, Any]) -> "FakeTableQuery":
        self.action = "insert"
        self.payload = deepcopy(payload)
        return self

    def update(self, payload: dict[str, Any]) -> "FakeTableQuery":
        self.action = "update"
        self.payload = deepcopy(payload)
        return self

    def upsert(self, payload: dict[str, Any]) -> "FakeTableQuery":
        self.action = "upsert"
        self.payload = deepcopy(payload)
        return self

    def _matches_filters(self, row: dict[str, Any]) -> bool:
        for column, value in self.filters:
            if row.get(column) != value:
                return False
        return True

    def execute(self) -> FakeTableResponse:
        table = self.client.tables[self.table_name]

        if self.action == "select":
            rows = [deepcopy(row) for row in table if self._matches_filters(row)]
            if self.limit_value is not None:
                rows = rows[: self.limit_value]
            return FakeTableResponse(data=rows)

        if self.action == "upsert":
            payload = dict(self.payload or {})
            if self.table_name == "profiles" and PROTECTED_PROFILE_COLUMNS.intersection(payload):
                raise RuntimeError("Direct writes to protected profile columns are not allowed.")
            row_id = str(payload["id"])
            existing_row = next((row for row in table if str(row.get("id")) == row_id), None)
            if existing_row is None:
                new_row = {
                    "id": row_id,
                    "email": str(payload["email"]),
                    "is_admin": bool(payload.get("is_admin", False)),
                    "generated_quiz_count": int(payload.get("generated_quiz_count", 0)),
                    "last_online_at": payload.get("last_online_at"),
                    "created_at": payload.get("created_at") or _now_iso(),
                }
                table.append(new_row)
                return FakeTableResponse(data=[deepcopy(new_row)])

            existing_row.update(payload)
            return FakeTableResponse(data=[deepcopy(existing_row)])

        if self.action == "insert":
            payload = dict(self.payload or {})
            if self.table_name == "profiles":
                unexpected_columns = set(payload) - PROFILE_INSERTABLE_COLUMNS
                if unexpected_columns:
                    raise RuntimeError("Direct writes to protected profile columns are not allowed.")
                payload.setdefault("is_admin", False)
                payload.setdefault("generated_quiz_count", 0)
                payload.setdefault("last_online_at", None)
                payload.setdefault("created_at", _now_iso())
            if self.table_name == "quiz_attempts":
                payload["id"] = self.client.next_quiz_attempt_id
                self.client.next_quiz_attempt_id += 1
                payload["created_at"] = payload.get("created_at") or _now_iso()
            table.append(payload)
            return FakeTableResponse(data=[deepcopy(payload)])

        if self.action == "update":
            if self.table_name == "profiles" and PROTECTED_PROFILE_COLUMNS.intersection(self.payload or {}):
                raise RuntimeError("Direct writes to protected profile columns are not allowed.")
            updated_rows: list[dict[str, Any]] = []
            for row in table:
                if self._matches_filters(row):
                    row.update(self.payload or {})
                    updated_rows.append(deepcopy(row))
            return FakeTableResponse(data=updated_rows)

        raise RuntimeError(f"Unsupported fake table action: {self.action}")


class FakeRpcQuery:
    def __init__(self, client: "FakeSupabaseClient", function_name: str, params: dict[str, Any] | None = None) -> None:
        self.client = client
        self.function_name = function_name
        self.params = dict(params or {})

    def execute(self) -> FakeRpcResponse:
        current_session = self.client.auth._current_session
        if current_session is None:
            raise RuntimeError("No active session")

        profile_row = self.client._get_profile_row(current_session.user.id)
        if profile_row is None:
            raise RuntimeError("Could not find your profile in Supabase.")

        if self.function_name == "touch_my_last_online":
            updated_timestamp = _now_iso()
            profile_row["last_online_at"] = updated_timestamp
            return FakeRpcResponse(data=updated_timestamp)

        if self.function_name == "increment_my_generated_quiz_count":
            updated_count = int(profile_row.get("generated_quiz_count") or 0) + 1
            profile_row["generated_quiz_count"] = updated_count
            return FakeRpcResponse(data=updated_count)

        if self.function_name == "delete_my_quiz_attempt":
            target_attempt_id = int(self.params.get("target_attempt_id") or 0)
            deleted_count = 0
            remaining_attempts: list[dict[str, Any]] = []
            for row in self.client.tables["quiz_attempts"]:
                if int(row.get("id") or 0) == target_attempt_id and str(row.get("user_id")) == current_session.user.id:
                    deleted_count += 1
                else:
                    remaining_attempts.append(row)
            self.client.tables["quiz_attempts"] = remaining_attempts
            return FakeRpcResponse(data=deleted_count)

        raise RuntimeError(f"Unsupported fake RPC: {self.function_name}")


class FakeSupabaseClient:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {
            "profiles": [],
            "quiz_attempts": [],
        }
        self.next_quiz_attempt_id = 1
        self.auth = FakeAuth(self)

    def _get_profile_row(self, user_id: str) -> dict[str, Any] | None:
        return next((row for row in self.tables["profiles"] if str(row.get("id")) == str(user_id)), None)

    def set_profile_admin(self, user_id: str, *, is_admin: bool) -> None:
        profile_row = self._get_profile_row(user_id)
        if profile_row is None:
            raise RuntimeError("Unknown profile")
        profile_row["is_admin"] = bool(is_admin)

    def table(self, table_name: str) -> FakeTableQuery:
        if table_name not in self.tables:
            raise RuntimeError(f"Unknown fake table: {table_name}")
        return FakeTableQuery(self, table_name)

    def rpc(self, function_name: str, params: dict[str, Any] | None = None) -> FakeRpcQuery:
        return FakeRpcQuery(self, function_name=function_name, params=params)
