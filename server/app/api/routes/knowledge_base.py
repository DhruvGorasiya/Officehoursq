from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional

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


@router.get("")
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

        if search:
            query = query.text_search("search_vector", search, options={"type": "websearch"})

        if category:
            query = query.eq("category", category)

        query = (
            query
            .order("helpful_votes", desc=True)
            .order("resolved_at", desc=True)
            .range(offset, offset + PAGE_SIZE - 1)
        )

        res = query.execute()

        items = []
        for row in res.data:
            student_info = row.pop("student", None)
            row["student_name"] = student_info.get("name") if student_info else None
            items.append(row)

        return {
            "success": True,
            "data": items,
            "page": page,
            "page_size": PAGE_SIZE,
            "total_count": res.count if res.count is not None else len(items),
        }
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(e)},
        )


@router.get("/similar")
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
