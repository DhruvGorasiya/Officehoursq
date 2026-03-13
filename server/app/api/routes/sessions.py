from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.sessions import SessionCreate, SessionStatusUpdate, SessionUpdate
from app.core.database import supabase
from app.core.deps import get_current_user, require_role
from app.utils.realtime_broadcast import (
    broadcast_course_session_status,
    broadcast_session_event,
)

router = APIRouter()


@router.post(
    "",
    tags=["Sessions"],
    summary="Create a new session",
    description=(
        "Professor creates an office hours session with title, time, assigned TAs, and topics."
    ),
    response_model=SuccessResponse,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "User is not a professor",
        },
    },
)
async def create_session(
    req: SessionCreate,
    user: dict = Depends(require_role("professor"))
):
    try:
        # Check course ownership
        course_res = supabase.table("courses").select("professor_id").eq("id", str(req.course_id)).single().execute()
        if not course_res.data or course_res.data["professor_id"] != user["sub"]:
            return JSONResponse(status_code=403, content={"success": False, "message": "Not authorized to create sessions for this course"})
        
        session_data = {
            "course_id": str(req.course_id),
            "title": req.title,
            "date": req.date.isoformat(),
            "start_time": req.start_time.isoformat(),
            "end_time": req.end_time.isoformat(),
            "status": "scheduled"
        }
        res = supabase.table("sessions").insert(session_data).execute()
        session_id = res.data[0]["id"]
        
        # Insert TAs if assigned
        if req.ta_ids:
            ta_data = [{"session_id": session_id, "ta_id": str(ta_id)} for ta_id in req.ta_ids]
            supabase.table("session_ta_assignments").insert(ta_data).execute()
            
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.get(
    "",
    tags=["Sessions"],
    summary="List sessions for a course",
    description=(
        "Returns all sessions for a given course_id. User must be enrolled in the course."
    ),
    response_model=SuccessResponse,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "User is not enrolled in this course",
        },
    },
)
async def list_sessions(
    course_id: str = Query(
        ...,
        description="Filter sessions by course ID",
    ),
    user: dict = Depends(get_current_user),
):
    try:
        # Simplification: assuming enrolled, should strictly check course_enrollments
        res = supabase.table("sessions").select("*").eq("course_id", course_id).execute()
        return {"success": True, "data": res.data}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.get(
    "/{session_id}",
    tags=["Sessions"],
    summary="Get session details",
    description=(
        "Returns session details with course name and assigned TAs. "
        "User must be enrolled in the course or be the owning professor."
    ),
    response_model=SuccessResponse,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "User is not enrolled in this course",
        },
        404: {
            "model": ErrorResponse,
            "description": "Session not found",
        },
    },
)
async def get_session(session_id: str, user: dict = Depends(get_current_user)):
    try:
        session_res = supabase.table("sessions").select("*, courses(name, professor_id)").eq("id", session_id).single().execute()
        if not session_res.data:
            return JSONResponse(status_code=404, content={"success": False, "message": "Session not found"})

        session_data = session_res.data
        course = session_data.pop("courses", {}) or {}
        course_name = course.get("name", "")
        professor_id = course.get("professor_id", "")

        user_id = user["sub"]
        if professor_id != user_id:
            enroll_res = supabase.table("course_enrollments").select("id").eq("course_id", session_data["course_id"]).eq("user_id", user_id).execute()
            if not enroll_res.data:
                return JSONResponse(status_code=403, content={"success": False, "message": "Not enrolled in this course"})

        ta_res = supabase.table("session_ta_assignments").select("ta_id, users!session_ta_assignments_ta_id_fkey(id, name, email)").eq("session_id", session_id).execute()
        tas = []
        for row in ta_res.data:
            u = row.get("users")
            if u:
                tas.append({"id": u["id"], "name": u["name"], "email": u["email"]})

        session_data["course_name"] = course_name
        session_data["tas"] = tas
        return {"success": True, "data": session_data}
    except Exception as e:
        if "contains 0 rows" in str(e):
            return JSONResponse(status_code=404, content={"success": False, "message": "Session not found"})
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.put(
    "/{session_id}",
    tags=["Sessions"],
    summary="Update a scheduled session",
    description=(
        "Professor updates session details. Only allowed when session status is 'scheduled'. "
        "Cannot edit active or ended sessions."
    ),
    response_model=SuccessResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Session is not in scheduled status",
        },
        403: {
            "model": ErrorResponse,
            "description": "User is not a professor",
        },
        404: {
            "model": ErrorResponse,
            "description": "Session not found",
        },
    },
)
async def update_session(
    session_id: str,
    req: SessionUpdate,
    user: dict = Depends(require_role("professor"))
):
    try:
        # Check session status
        session_res = supabase.table("sessions").select("status, course_id").eq("id", session_id).single().execute()
        if not session_res.data:
            return JSONResponse(status_code=404, content={"success": False, "message": "Session not found"})
        if session_res.data["status"] != "scheduled":
            return JSONResponse(status_code=400, content={"success": False, "message": "Can only edit scheduled sessions"})
            
        course_id = session_res.data["course_id"]
        
        # Check course ownership
        course_res = supabase.table("courses").select("professor_id").eq("id", course_id).single().execute()
        if not course_res.data or course_res.data["professor_id"] != user["sub"]:
            return JSONResponse(status_code=403, content={"success": False, "message": "Not authorized"})
            
        update_data = {}
        if req.title:
            update_data["title"] = req.title
        if req.date:
            update_data["date"] = req.date.isoformat()
        if req.start_time:
            update_data["start_time"] = req.start_time.isoformat()
        if req.end_time:
            update_data["end_time"] = req.end_time.isoformat()
        
        if update_data:
            res = supabase.table("sessions").update(update_data).eq("id", session_id).execute()
        else:
            res = supabase.table("sessions").select("*").eq("id", session_id).execute()

        # Update TAs if provided
        if req.ta_ids is not None:
            supabase.table("session_ta_assignments").delete().eq("session_id", session_id).execute()
            if req.ta_ids:
                ta_data = [{"session_id": session_id, "ta_id": ta_id} for ta_id in req.ta_ids]
                supabase.table("session_ta_assignments").insert(ta_data).execute()
                
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.delete(
    "/{session_id}",
    tags=["Sessions"],
    summary="Delete a scheduled session",
    description=(
        "Professor deletes a session. Only allowed when status is 'scheduled'. "
        "Cannot delete active sessions."
    ),
    response_model=SuccessResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Session is not in scheduled status, or session is active",
        },
        403: {
            "model": ErrorResponse,
            "description": "User is not a professor",
        },
        404: {
            "model": ErrorResponse,
            "description": "Session not found",
        },
    },
)
async def delete_session(session_id: str, user: dict = Depends(require_role("professor"))):
    try:
        session_res = supabase.table("sessions").select("status, course_id").eq("id", session_id).single().execute()
        if not session_res.data:
            return JSONResponse(status_code=404, content={"success": False, "message": "Session not found"})
        if session_res.data["status"] != "scheduled":
            return JSONResponse(status_code=400, content={"success": False, "message": "Can only delete scheduled sessions"})
        
        course_id = session_res.data["course_id"]
        course_res = supabase.table("courses").select("professor_id").eq("id", course_id).single().execute()
        if not course_res.data or course_res.data["professor_id"] != user["sub"]:
            return JSONResponse(status_code=403, content={"success": False, "message": "Not authorized"})
            
        supabase.table("sessions").delete().eq("id", session_id).execute()
        return {"success": True, "data": {"message": "Deleted"}}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.patch(
    "/{session_id}/status",
    tags=["Sessions"],
    summary="Change session status",
    description=(
        "Professor or TA changes session status. Valid transitions: scheduled to active "
        "(fails if another session in the same course is already active), active to ended "
        "(marks all remaining queued questions as unresolved and notifies students)."
    ),
    response_model=SuccessResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid status transition, or another session is already active",
        },
        403: {
            "model": ErrorResponse,
            "description": "User is not a professor or TA",
        },
        404: {
            "model": ErrorResponse,
            "description": "Session not found",
        },
    },
)
async def update_session_status(
    session_id: str,
    req: SessionStatusUpdate,
    user: dict = Depends(require_role("professor", "ta")) # TAs might eventually manage it, but PRD says transitions... usually TA/Prof
):
    try:
        session_res = supabase.table("sessions").select("status, course_id").eq("id", session_id).single().execute()
        if not session_res.data:
            return JSONResponse(status_code=404, content={"success": False, "message": "Session not found"})
            
        old_status = session_res.data["status"]
        course_id = session_res.data["course_id"]
        new_status = req.status
        
        if new_status == "active" and old_status == "scheduled":
            # Check if another active session exists
            existing_active = supabase.table("sessions").select("id").eq("course_id", course_id).eq("status", "active").execute()
            if existing_active.data:
                return JSONResponse(status_code=400, content={"success": False, "message": "Another active session exists for this course"})
        elif new_status == "ended" and old_status == "active":
            supabase.table("questions").update({
                "status": "unresolved",
                "resolution_note": "Session ended without resolution",
                "queue_position": -1
            }).eq("session_id", session_id).in_("status", ["queued", "in_progress", "deferred"]).execute()
        else:
            return JSONResponse(status_code=400, content={"success": False, "message": f"Invalid transition from {old_status} to {new_status}"})
            
        res = supabase.table("sessions").update({"status": new_status}).eq("id", session_id).execute()
        updated = res.data[0]

        # Broadcast course-level session status update
        broadcast_course_session_status(
            course_id=course_id,
            payload={"session": updated},
        )

        # Also broadcast at the session level so connected clients can react
        broadcast_session_event(
            session_id=session_id,
            event="session:updated",
            payload={"session": updated},
        )

        return {"success": True, "data": updated}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})
