import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse

from app.schemas.analytics import (
    CategoryBreakdown,
    OverviewResponse,
    TAPerformance,
    WeeklyTrend,
)
from app.schemas.common import ErrorResponse, SuccessResponse
from app.core.database import supabase
from app.core.deps import require_role

router = APIRouter()


def _is_course_owner(course_id: str, professor_id: str) -> bool:
    """Return True if the given professor owns the course."""
    res = (
        supabase.table("courses")
        .select("id")
        .eq("id", course_id)
        .eq("professor_id", professor_id)
        .execute()
    )
    return bool(res.data)


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO timestamp from Supabase into a datetime, or None on failure."""
    if not value:
        return None
    try:
        # Handle possible trailing Z from Postgres / Supabase
        if isinstance(value, str) and value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)  # type: ignore[arg-type]
    except Exception:
        return None


@router.get(
    "/overview",
    tags=["Analytics"],
    summary="Get analytics overview",
    description=(
        "Professor-only. Returns total questions, average wait time, average resolve time, "
        "and recent session summaries for a course."
    ),
    response_model=SuccessResponse,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "User is not a professor or does not own the course",
        },
    },
)
async def analytics_overview(
    course_id: str = Query(..., description="Course to analyze"),
    user: Dict = Depends(require_role("professor")),
):
    """High-level analytics overview for a course."""
    try:
        professor_id = user["sub"]
        if not _is_course_owner(course_id, professor_id):
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Not authorized for this course"},
            )

        # Fetch all questions for this course once and aggregate in Python.
        q_res = (
            supabase.table("questions")
            .select(
                "id, session_id, created_at, claimed_at, resolved_at",
            )
            .eq("course_id", course_id)
            .execute()
        )
        questions = q_res.data or []

        total_questions = len(questions)

        # Average wait: created_at -> claimed_at (only rows with both).
        wait_minutes_sum = 0.0
        wait_count = 0

        # Average resolve: created_at -> resolved_at (only rows with both).
        resolve_minutes_sum = 0.0
        resolve_count = 0

        per_session_counts: Dict[str, int] = {}

        for q in questions:
            session_id = q.get("session_id")
            if session_id:
                per_session_counts[session_id] = per_session_counts.get(session_id, 0) + 1

            created = _parse_timestamp(q.get("created_at"))
            claimed = _parse_timestamp(q.get("claimed_at"))
            resolved = _parse_timestamp(q.get("resolved_at"))

            if created and claimed:
                delta = (claimed - created).total_seconds() / 60.0
                if delta >= 0:
                    wait_minutes_sum += delta
                    wait_count += 1

            if created and resolved:
                delta = (resolved - created).total_seconds() / 60.0
                if delta >= 0:
                    resolve_minutes_sum += delta
                    resolve_count += 1

        avg_wait_minutes: Optional[float] = (
            round(wait_minutes_sum / wait_count, 1) if wait_count > 0 else None
        )
        avg_resolve_minutes: Optional[float] = (
            round(resolve_minutes_sum / resolve_count, 1) if resolve_count > 0 else None
        )

        # Recent sessions: sort by date descending and include per-session question counts.
        s_res = (
            supabase.table("sessions")
            .select("id, title, date")
            .eq("course_id", course_id)
            .execute()
        )
        sessions = s_res.data or []

        def session_sort_key(s: Dict) -> str:
            # Newest first; fall back to empty string if date missing.
            return s.get("date") or ""

        sessions_sorted = sorted(sessions, key=session_sort_key, reverse=True)
        recent_sessions = []
        for s in sessions_sorted[:5]:
            sid = s.get("id")
            recent_sessions.append(
                {
                    "id": sid,
                    "title": s.get("title"),
                    "date": s.get("date"),
                    "total_questions": per_session_counts.get(sid, 0),
                }
            )

        data = {
            "total_questions": total_questions,
            "avg_wait_minutes": avg_wait_minutes,
            "avg_resolve_minutes": avg_resolve_minutes,
            "recent_sessions": recent_sessions,
        }

        return {"success": True, "data": data}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(e)},
        )


@router.get(
    "/categories",
    tags=["Analytics"],
    summary="Get category breakdown",
    description=(
        "Professor-only. Returns the distribution of resolved questions across categories "
        "(debugging, conceptual, setup, assignment, other) with counts and percentages."
    ),
    response_model=SuccessResponse,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "User is not a professor or does not own the course",
        },
    },
)
async def analytics_categories(
    course_id: str = Query(..., description="Course to analyze"),
    user: Dict = Depends(require_role("professor")),
):
    """Category breakdown for resolved questions in a course."""
    try:
        professor_id = user["sub"]
        if not _is_course_owner(course_id, professor_id):
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Not authorized for this course"},
            )

        q_res = (
            supabase.table("questions")
            .select("id, category")
            .eq("course_id", course_id)
            .eq("status", "resolved")
            .execute()
        )
        questions = q_res.data or []

        counts: Dict[str, int] = {}
        for q in questions:
            cat = (q.get("category") or "other").lower()
            counts[cat] = counts.get(cat, 0) + 1

        total_resolved = sum(counts.values())
        categories: List[Dict] = []
        for cat, count in counts.items():
            pct = round((count / total_resolved) * 100.0, 1) if total_resolved > 0 else 0.0
            categories.append(
                {
                    "category": cat,
                    "count": count,
                    "percentage": pct,
                }
            )

        # Simple insight generation – the frontend can refine copy if needed.
        insight = None
        if categories:
            top = max(categories, key=lambda c: c["count"])
            insight = f"Most questions are {top['category']} ({top['percentage']}%)."

        data = {
            "categories": categories,
            "total_resolved": total_resolved,
            "insight": insight,
        }
        return {"success": True, "data": data}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(e)},
        )


@router.get(
    "/trends",
    tags=["Analytics"],
    summary="Get weekly question trends",
    description=(
        "Professor-only. Returns question volume per week and highlights the peak week and session."
    ),
    response_model=SuccessResponse,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "User is not a professor or does not own the course",
        },
    },
)
async def analytics_trends(
    course_id: str = Query(..., description="Course to analyze"),
    user: Dict = Depends(require_role("professor")),
):
    """Weekly question volume trends for a course."""
    try:
        professor_id = user["sub"]
        if not _is_course_owner(course_id, professor_id):
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Not authorized for this course"},
            )

        q_res = (
            supabase.table("questions")
            .select("id, session_id, created_at")
            .eq("course_id", course_id)
            .execute()
        )
        questions = q_res.data or []

        # Group by ISO week start (Monday) in Python.
        weekly_counts: Dict[str, int] = {}
        for q in questions:
            created = _parse_timestamp(q.get("created_at"))
            if not created:
                continue
            # Normalize to Monday of that week.
            week_start = created - timedelta(days=created.weekday())
            week_key = week_start.date().isoformat()
            weekly_counts[week_key] = weekly_counts.get(week_key, 0) + 1

        weeks = [
            {"week_start": wk, "count": cnt}
            for wk, cnt in sorted(weekly_counts.items(), key=lambda i: i[0])
        ]

        peak_week = None
        if weeks:
            top_week = max(weeks, key=lambda w: w["count"])
            peak_week = top_week

        # Compute peak session based on total questions per session.
        per_session_counts: Dict[str, int] = {}
        for q in questions:
            sid = q.get("session_id")
            if sid:
                per_session_counts[sid] = per_session_counts.get(sid, 0) + 1

        peak_session = None
        if per_session_counts:
            top_sid = max(per_session_counts.items(), key=lambda p: p[1])[0]
            s_res = (
                supabase.table("sessions")
                .select("id, title")
                .eq("id", top_sid)
                .single()
                .execute()
            )
            if s_res.data:
                peak_session = {
                    "session_id": s_res.data["id"],
                    "title": s_res.data.get("title"),
                    "question_count": per_session_counts.get(top_sid, 0),
                }

        data = {
            "weeks": weeks,
            "peak_week": peak_week,
            "peak_session": peak_session,
        }
        return {"success": True, "data": data}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(e)},
        )


@router.get(
    "/ta-performance",
    tags=["Analytics"],
    summary="Get TA performance metrics",
    description=(
        "Professor-only. Returns per-TA stats: resolved count, average resolve time, and rating."
    ),
    response_model=SuccessResponse,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "User is not a professor or does not own the course",
        },
    },
)
async def analytics_ta_performance(
    course_id: str = Query(..., description="Course to analyze"),
    user: Dict = Depends(require_role("professor")),
):
    """Per-TA performance metrics for a course."""
    try:
        professor_id = user["sub"]
        if not _is_course_owner(course_id, professor_id):
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Not authorized for this course"},
            )

        q_res = (
            supabase.table("questions")
            .select("id, claimed_by, created_at, claimed_at, resolved_at")
            .eq("course_id", course_id)
            .eq("status", "resolved")
            .execute()
        )
        questions = q_res.data or []

        # Aggregate metrics per TA by claimed_by.
        stats: Dict[str, Dict[str, float]] = {}
        for q in questions:
            ta_id = q.get("claimed_by")
            if not ta_id:
                continue

            created = _parse_timestamp(q.get("created_at"))
            claimed = _parse_timestamp(q.get("claimed_at"))
            resolved = _parse_timestamp(q.get("resolved_at"))

            # Use created->resolved as total resolution time.
            resolve_minutes = None
            if created and resolved:
                delta = (resolved - created).total_seconds() / 60.0
                if delta >= 0:
                    resolve_minutes = delta

            if ta_id not in stats:
                stats[ta_id] = {
                    "resolved_count": 0,
                    "resolve_minutes_sum": 0.0,
                }

            stats[ta_id]["resolved_count"] += 1
            if resolve_minutes is not None:
                stats[ta_id]["resolve_minutes_sum"] += resolve_minutes

        ta_ids = list(stats.keys())
        tas: List[Dict] = []
        if ta_ids:
            # Fetch TA user profiles for names.
            user_res = (
                supabase.table("users")
                .select("id, name")
                .in_("id", ta_ids)
                .execute()
            )
            users_by_id = {u["id"]: u for u in (user_res.data or [])}

            for ta_id, s in stats.items():
                resolved_count = int(s["resolved_count"])
                avg_resolve_minutes = (
                    round(s["resolve_minutes_sum"] / resolved_count, 1)
                    if resolved_count > 0
                    else None
                )

                user_row = users_by_id.get(ta_id, {})
                name = user_row.get("name") or "Unknown TA"
                initials = "".join([part[0] for part in name.split() if part]).upper()[:2]

                # Simple rating heuristic based on avg resolve time.
                rating = 5
                if avg_resolve_minutes is not None:
                    if avg_resolve_minutes > 40:
                        rating = 2
                    elif avg_resolve_minutes > 25:
                        rating = 3
                    elif avg_resolve_minutes > 15:
                        rating = 4

                tas.append(
                    {
                        "id": ta_id,
                        "name": name,
                        "initials": initials,
                        "resolved_count": resolved_count,
                        "avg_resolve_minutes": avg_resolve_minutes,
                        "rating": rating,
                    }
                )

        # Sort TAs by resolved count descending.
        tas.sort(key=lambda t: t["resolved_count"], reverse=True)

        return {"success": True, "data": {"tas": tas}}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(e)},
        )


@router.get(
    "/export",
    tags=["Analytics"],
    summary="Export analytics as CSV",
    description=(
        "Professor-only. Downloads a CSV file with analytics data for the course. "
        "Returns a file response, not JSON."
    ),
    responses={
        403: {
            "model": ErrorResponse,
            "description": "User is not a professor or does not own the course",
        },
    },
)
async def analytics_export_csv(
    course_id: str = Query(..., description="Course to export analytics for"),
    user: Dict = Depends(require_role("professor")),
):
    """Export per-question analytics as CSV for a course."""
    try:
        professor_id = user["sub"]
        if not _is_course_owner(course_id, professor_id):
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Not authorized for this course"},
            )

        # Fetch questions and join minimal session + TA data.
        q_res = (
            supabase.table("questions")
            .select(
                "id, session_id, created_at, claimed_at, resolved_at, category, priority, status, "
                "claimer:users!questions_claimed_by_fkey(name)"
            )
            .eq("course_id", course_id)
            .execute()
        )
        questions = q_res.data or []

        # Preload sessions for titles.
        s_res = (
            supabase.table("sessions")
            .select("id, title")
            .eq("course_id", course_id)
            .execute()
        )
        sessions = s_res.data or []
        session_titles = {s["id"]: s.get("title") for s in sessions}

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "question_id",
                "session_title",
                "created_at",
                "claimed_at",
                "resolved_at",
                "wait_minutes",
                "resolve_minutes",
                "category",
                "priority",
                "status",
                "ta_name",
            ]
        )

        for q in questions:
            created = _parse_timestamp(q.get("created_at"))
            claimed = _parse_timestamp(q.get("claimed_at"))
            resolved = _parse_timestamp(q.get("resolved_at"))

            wait_minutes = (
                round((claimed - created).total_seconds() / 60.0, 1)
                if created and claimed and (claimed - created).total_seconds() >= 0
                else None
            )
            resolve_minutes = (
                round((resolved - created).total_seconds() / 60.0, 1)
                if created and resolved and (resolved - created).total_seconds() >= 0
                else None
            )

            session_title = session_titles.get(q.get("session_id"), "")
            claimer = q.get("claimer") or {}
            ta_name = claimer.get("name")

            writer.writerow(
                [
                    q.get("id"),
                    session_title,
                    q.get("created_at"),
                    q.get("claimed_at"),
                    q.get("resolved_at"),
                    wait_minutes,
                    resolve_minutes,
                    q.get("category"),
                    q.get("priority"),
                    q.get("status"),
                    ta_name,
                ]
            )

        output.seek(0)

        headers = {
            "Content-Disposition": f'attachment; filename="analytics_{course_id}.csv"'
        }

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers=headers,
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(e)},
        )

