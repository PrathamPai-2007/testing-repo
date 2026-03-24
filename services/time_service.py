from __future__ import annotations

from datetime import UTC, datetime, tzinfo


def format_timestamp_local(timestamp_iso: str | None, *, target_tz: tzinfo | None = None) -> str:
    if not timestamp_iso:
        return "Never"

    normalized_timestamp = str(timestamp_iso).strip()
    if not normalized_timestamp:
        return "Never"

    try:
        parsed_timestamp = datetime.fromisoformat(normalized_timestamp.replace("Z", "+00:00"))
    except ValueError:
        return normalized_timestamp

    if parsed_timestamp.tzinfo is None:
        parsed_timestamp = parsed_timestamp.replace(tzinfo=UTC)

    resolved_target_tz = target_tz or datetime.now().astimezone().tzinfo or UTC
    local_timestamp = parsed_timestamp.astimezone(resolved_target_tz)
    return local_timestamp.strftime("%d %b %Y, %I:%M %p")
