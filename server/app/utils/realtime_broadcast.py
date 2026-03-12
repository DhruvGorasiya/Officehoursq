from __future__ import annotations

from typing import Any, Dict

from supabase import Client

from app.core.database import supabase


def _safe_broadcast(channel: str, event: str, payload: Dict[str, Any]) -> None:
    """
    Best-effort wrapper around Supabase Realtime / Broadcast.

    If broadcasting fails for any reason, the exception is swallowed so that
    it never breaks the main request flow.
    """
    try:
        # Using Supabase 2.x broadcast API via the underlying client.
        # The Python SDK exposes a 'realtime' interface that supports broadcast.
        realtime = getattr(supabase, "realtime", None)
        if realtime is None:
            return

        # Some versions expose broadcast as a method; use getattr defensively.
        broadcast_fn = getattr(realtime, "broadcast", None)
        if broadcast_fn is None:
            return

        broadcast_fn(
            channel=channel,
            event=event,
            payload=payload,
        )
    except Exception:
        # Intentionally ignore; logging can be added here later if needed.
        return


def broadcast_session_event(session_id: str, event: str, payload: Dict[str, Any]) -> None:
    """
    Broadcast an event to all participants in a specific session.

    Channel naming follows the conventions in .cursorrules / rules:
    - session:{id}
    """
    channel = f"session:{session_id}"
    _safe_broadcast(channel, event, payload)


def broadcast_user_notification(user_id: str, payload: Dict[str, Any]) -> None:
    """
    Broadcast a notification to a single user.

    Channel naming:
    - user:{id}
    """
    channel = f"user:{user_id}"
    _safe_broadcast(channel, "notification:new", payload)


def broadcast_course_session_status(course_id: str, payload: Dict[str, Any]) -> None:
    """
    Broadcast a session status update for all users enrolled in a course.

    Channel naming:
    - course:{id}
    """
    channel = f"course:{course_id}"
    _safe_broadcast(channel, "session:updated", payload)

