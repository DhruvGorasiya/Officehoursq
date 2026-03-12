from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorResponse, SuccessResponse, PaginatedSuccessResponse
from app.core.database import supabase
from app.core.deps import get_current_user

router = APIRouter()

PAGE_SIZE = 20


def check_enrollment(user_id: str, role: str, course_id: str) -> bool:
    """Return True if the user owns or is enrolled in the course."""
    if role == "professor":
        res = (
            supabase.table("courses")
            .select("id")
            .eq("id", course_id)
            .eq("professor_id", user_id)
            .execute()
        )
        return bool(res.data)
    res = (
        supabase.table("course_enrollments")
        .select("id")
        .eq("course_id", course_id)
        .eq("user_id", user_id)
        .execute()
    )
    return bool(res.data)


@router.get(
    "",
    tags=["Knowledge Base"],
    summary="Search resolved questions",
    description=(
        "Search the knowledge base of resolved questions for a course. Supports keyword search "
        "and category filtering. Paginated at 20 results per page."
    ),
    response_model=PaginatedSuccessResponse,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "User is not enrolled in this course",
        },
    },
)
async def search_knowledge_base(
    course_id: str = Query(..., description="Course to search within"),
    search: Optional[str] = Query(None, description="Full-text search query"),
    category: Optional[str] = Query(None, description="Filter by question category"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    user: dict = Depends(get_current_user),
):
    try:
        if not check_enrollment(user["sub"], user.get("role", "student"), course_id):
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Not enrolled in this course"},
            )

        offset = (page - 1) * PAGE_SIZE

        select_fields = (
            "id, title, description, category, resolution_note, "
            "helpful_votes, resolved_at, created_at, "
            "student:users!questions_student_id_fkey(name)"
        )

        query = (
            supabase.table("questions")
            .select(select_fields, count="exact")
            .eq("status", "resolved")
            .eq("course_id", course_id)
        )

        is_search = bool(search and search.strip())

        if search and search.strip():
            # Use ILIKE across title, description, resolution_note so short or partial terms
            # (e.g. "uni") match substrings (e.g. "unit", "university"). Full-text search
            # often drops or fails to match short tokens, so ILIKE gives predictable results.
            term = search.strip()
            # Escape ILIKE special chars so % and _ are literal
            escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            query = query.or_(
                f"title.ilike.{pattern},description.ilike.{pattern},resolution_note.ilike.{pattern}"
            )

        if category:
            query = query.eq("category", category)

        if is_search:
            # .or_() builder may not support .order()/.range(), so sort and paginate in Python.
            res = query.execute()
            rows = res.data or []

            # Sort by helpful_votes DESC, then resolved_at DESC (fallback to created_at).
            def sort_key(r):
                hv = r.get("helpful_votes") or 0
                resolved_at = r.get("resolved_at") or r.get("created_at")
                return (-hv, resolved_at or "")

            rows.sort(key=sort_key)
            total_count = len(rows)
            paged_rows = rows[offset : offset + PAGE_SIZE]
        else:
            # Non-search path can use PostgREST ordering and server-side pagination.
            query = (
                query
                .order("helpful_votes", desc=True)
                .order("resolved_at", desc=True)
                .range(offset, offset + PAGE_SIZE - 1)
            )
            res = query.execute()
            paged_rows = res.data or []
            total_count = res.count if res.count is not None else len(paged_rows)

        items = []
        for row in paged_rows:
            student_info = row.pop("student", None)
            row["student_name"] = student_info.get("name") if student_info else None
            items.append(row)

        return {
            "success": True,
            "data": items,
            "page": page,
            "page_size": PAGE_SIZE,
            "total_count": total_count,
        }
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(e)},
        )


@router.get(
    "/similar",
    tags=["Knowledge Base"],
    summary="Find similar resolved questions",
    description=(
        "Returns the top 5 resolved questions similar to the given title, matched by keyword. "
        "Used to show the 'Similar Questions' panel when a student is typing their question title."
    ),
    response_model=SuccessResponse,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "User is not a student in this course",
        },
    },
)
async def find_similar_questions(
    course_id: str = Query(..., description="Course to search within"),
    title: str = Query(..., min_length=1, description="Title text to find similar matches for"),
    user: dict = Depends(get_current_user),
):
    try:
        if not check_enrollment(user["sub"], user.get("role", "student"), course_id):
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Not enrolled in this course"},
            )

        res = supabase.rpc(
            "find_similar_questions",
            {"p_course_id": course_id, "p_title": title, "p_limit": 5},
        ).execute()

        return {"success": True, "data": res.data or []}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(e)},
        )
