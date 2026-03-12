from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.core.database import supabase


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO8601 timestamp from Supabase into a datetime, or None."""
    if not value:
        return None
    # Supabase/Postgres often return ISO strings; handle a trailing Z if present.
    if isinstance(value, str) and value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value)  # type: ignore[arg-type]
    except Exception:
        return None


def get_session_avg_resolve_time_minutes(session_id: str) -> float:
    """
    Compute the average resolve time (in minutes) for resolved questions in a session.

    Uses questions.created_at (PRD 'submitted_at') -> questions.resolved_at.
    Returns 5.0 minutes if there is not enough data.
    """
    try:
        res = (
            supabase.table("questions")
            .select("created_at, resolved_at, status")
            .eq("session_id", session_id)
            .eq("status", "resolved")
            .execute()
        )
    except Exception:
        # On any unexpected error, fall back to default.
        return 5.0

    rows = res.data or []
    if not rows:
        return 5.0

    total_minutes = 0.0
    count = 0

    for row in rows:
        created = _parse_ts(row.get("created_at"))
        resolved = _parse_ts(row.get("resolved_at"))
        if not created or not resolved:
            continue
        delta_seconds = (resolved - created).total_seconds()
        if delta_seconds < 0:
            continue
        minutes = max(1.0, delta_seconds / 60.0)
        total_minutes += minutes
        count += 1

    if count == 0:
        return 5.0

    return round(total_minutes / count, 2)


def compute_estimated_wait_minutes(position: int, avg_resolve_time: float) -> int:
    """
    Compute the capped estimated wait time in minutes for a queue position.

    - raw = position * avg_resolve_time
    - rounded to nearest minute
    - capped at 60 minutes (PRD: display as '60+ min')
    """
    if position <= 0 or avg_resolve_time <= 0:
        return 5
    raw = position * avg_resolve_time
    minutes = int(round(raw))
    if minutes <= 0:
        minutes = 1
    return min(minutes, 60)

