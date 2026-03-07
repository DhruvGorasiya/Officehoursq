from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.schemas.sessions import SessionCreate, SessionUpdate, SessionStatusUpdate
from app.core.database import supabase
from app.core.deps import get_current_user, require_role

router = APIRouter()

@router.post("")
async def create_session(
    req: SessionCreate,
    user: dict = Depends(require_role("professor"))
):
    try:
        # Check course ownership
        course_res = supabase.table("courses").select("professor_id").eq("id", req.course_id).single().execute()
        if not course_res.data or course_res.data["professor_id"] != user["sub"]:
            return JSONResponse(status_code=403, content={"success": False, "message": "Not authorized to create sessions for this course"})
        
        session_data = {
            "course_id": req.course_id,
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
            ta_data = [{"session_id": session_id, "ta_id": ta_id} for ta_id in req.ta_ids]
            supabase.table("session_ta_assignments").insert(ta_data).execute()
            
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.get("")
async def list_sessions(course_id: str, user: dict = Depends(get_current_user)):
    try:
        # Simplification: assuming enrolled, should strictly check course_enrollments
        res = supabase.table("sessions").select("*").eq("course_id", course_id).execute()
        return {"success": True, "data": res.data}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.put("/{session_id}")
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
        if req.title: update_data["title"] = req.title
        if req.date: update_data["date"] = req.date.isoformat()
        if req.start_time: update_data["start_time"] = req.start_time.isoformat()
        if req.end_time: update_data["end_time"] = req.end_time.isoformat()
        
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

@router.delete("/{session_id}")
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
        return {"success": True, "message": "Deleted"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.patch("/{session_id}/status")
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
            # Mark remaining questions as resolved
            supabase.table("questions").update({
                "status": "resolved",
                "resolution_note": "Session ended without resolution"
            }).eq("session_id", session_id).neq("status", "resolved").neq("status", "withdrawn").execute()
        else:
            return JSONResponse(status_code=400, content={"success": False, "message": f"Invalid transition from {old_status} to {new_status}"})
            
        res = supabase.table("sessions").update({"status": new_status}).eq("id", session_id).execute()
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})
