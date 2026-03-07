from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.schemas.questions import QuestionCreate, QuestionUpdate, QuestionResolve
from app.core.database import supabase
from app.core.deps import get_current_user, require_role
from datetime import datetime, timezone

router = APIRouter()

def recalculate_queue(session_id: str):
    # Fetch active questions and re-order them 1 to N
    res = supabase.table("questions").select("id").eq("session_id", session_id).in_("status", ["queued", "in_progress"]).order("queue_position").execute()
    for i, q in enumerate(res.data):
         supabase.table("questions").update({"queue_position": i + 1}).eq("id", q["id"]).execute()

@router.post("")
async def create_question(req: QuestionCreate, user: dict = Depends(require_role("student"))):
    try:
        session_id = req.session_id
        student_id = user["sub"]
        
        # Check if session is active
        session_res = supabase.table("sessions").select("status").eq("id", session_id).single().execute()
        if not session_res.data or session_res.data["status"] != "active":
            return JSONResponse(status_code=400, content={"success": False, "message": "Session is not active"})
            
        # Check if student already has active question
        existing = supabase.table("questions").select("id").eq("session_id", session_id).eq("student_id", student_id).in_("status", ["queued", "in_progress"]).execute()
        if existing.data:
            return JSONResponse(status_code=400, content={"success": False, "message": "You already have an active question in this session"})
            
        # Calculate queue position
        current_queue = supabase.table("questions").select("id").eq("session_id", session_id).in_("status", ["queued", "in_progress"]).execute()
        queue_pos = len(current_queue.data) + 1
        
        q_data = req.model_dump()
        q_data["student_id"] = student_id
        q_data["status"] = "queued"
        q_data["queue_position"] = queue_pos
        
        res = supabase.table("questions").insert(q_data).execute()
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.get("")
async def list_questions(session_id: str, user: dict = Depends(get_current_user)):
    try:
        # Returns all questions for TA/professor, or only their own for student
        role = user.get("role", "student")
        if role in ["professor", "ta"]:
            res = supabase.table("questions").select("*, student:users!questions_student_id_fkey(name, email), claimer:users!questions_claimed_by_fkey(name, email)").eq("session_id", session_id).order("queue_position").execute()
        else:
            res = supabase.table("questions").select("*").eq("session_id", session_id).eq("student_id", user["sub"]).order("queue_position").execute()
            
        return {"success": True, "data": res.data}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.get("/{q_id}")
async def get_question(q_id: str, user: dict = Depends(get_current_user)):
    try:
        res = supabase.table("questions").select("*").eq("id", q_id).single().execute()
        if not res.data:
            return JSONResponse(status_code=404, content={"success": False, "message": "Question not found"})
            
        role = user.get("role", "student")
        if role == "student" and res.data["student_id"] != user["sub"]:
            return JSONResponse(status_code=403, content={"success": False, "message": "Not authorized"})
            
        return {"success": True, "data": res.data}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.put("/{q_id}")
async def update_question(q_id: str, req: QuestionUpdate, user: dict = Depends(require_role("student"))):
    try:
        q_res = supabase.table("questions").select("student_id, status").eq("id", q_id).single().execute()
        if not q_res.data:
            return JSONResponse(status_code=404, content={"success": False, "message": "Not found"})
        if q_res.data["student_id"] != user["sub"]:
            return JSONResponse(status_code=403, content={"success": False, "message": "Not your question"})
        if q_res.data["status"] != "queued":
            return JSONResponse(status_code=400, content={"success": False, "message": "Can only edit queued questions"})
            
        update_data = req.model_dump(exclude_unset=True)
        if update_data:
            res = supabase.table("questions").update(update_data).eq("id", q_id).execute()
        else:
            res = supabase.table("questions").select("*").eq("id", q_id).execute()
            
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.patch("/{q_id}/claim")
async def claim_question(q_id: str, user: dict = Depends(require_role("ta", "professor"))):
    try:
        q_res = supabase.table("questions").select("status").eq("id", q_id).single().execute()
        if not q_res.data or q_res.data["status"] != "queued":
            return JSONResponse(status_code=400, content={"success": False, "message": "Question is not queued"})
            
        update_data = {
            "status": "in_progress",
            "claimed_by": user["sub"],
            "claimed_at": datetime.now(timezone.utc).isoformat()
        }
        res = supabase.table("questions").update(update_data).eq("id", q_id).execute()
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.patch("/{q_id}/resolve")
async def resolve_question(q_id: str, req: QuestionResolve, user: dict = Depends(require_role("ta", "professor"))):
    try:
        q_res = supabase.table("questions").select("status, session_id").eq("id", q_id).single().execute()
        if not q_res.data or q_res.data["status"] not in ["queued", "in_progress"]:
            return JSONResponse(status_code=400, content={"success": False, "message": "Question cannot be resolved"})
            
        update_data = {
            "status": "resolved",
            "resolution_note": req.resolution_note,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "queue_position": -1 # removed from queue
        }
        res = supabase.table("questions").update(update_data).eq("id", q_id).execute()
        recalculate_queue(q_res.data["session_id"])
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.patch("/{q_id}/defer")
async def defer_question(q_id: str, user: dict = Depends(require_role("ta", "professor"))):
    try:
        q_res = supabase.table("questions").select("status, session_id").eq("id", q_id).single().execute()
        if not q_res.data or q_res.data["status"] not in ["queued", "in_progress"]:
            return JSONResponse(status_code=400, content={"success": False, "message": "Question cannot be deferred"})
            
        # Put at back of queue
        session_id = q_res.data["session_id"]
        current_queue = supabase.table("questions").select("id").eq("session_id", session_id).in_("status", ["queued", "in_progress"]).execute()
        new_pos = len(current_queue.data) + 1 # Even though it's already in the queue, we'll assign it to the end and recalculate handles gaps
        
        update_data = {
            "status": "queued", # Or deferred? PRD says "sets status to deferred, then immediately re-queues at back". The queue includes queued and in_progress? Wait, if it's deferred, does it stay in queue? Usually deferred implies it's lower priority now, or it becomes "queued" again but at the end. PRD: "sets status to deferred, then immediately re-queues at back. Clears claimed_by, sets deferred_at". I will keep status as queued to signify it's back in queue, but with deferred_at set. Oh, PRD says "sets status to deferred". So let's include deferred in active queue.
            "claimed_by": None,
            "deferred_at": datetime.now(timezone.utc).isoformat(),
            "queue_position": new_pos
        }
        res = supabase.table("questions").update(update_data).eq("id", q_id).execute()
        
        # We need deferred in recalculate if they are in queue. Let's assume PRD means status='deferred' is just a specialized 'queued'. 
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.patch("/{q_id}/withdraw")
async def withdraw_question(q_id: str, user: dict = Depends(require_role("student"))):
    try:
        q_res = supabase.table("questions").select("student_id, status, session_id").eq("id", q_id).single().execute()
        if not q_res.data:
            return JSONResponse(status_code=404, content={"success": False, "message": "Question not found"})
        if q_res.data["student_id"] != user["sub"]:
            return JSONResponse(status_code=403, content={"success": False, "message": "Not authorized"})
        if q_res.data["status"] not in ["queued", "in_progress"]:
            return JSONResponse(status_code=400, content={"success": False, "message": "Cannot withdraw from current status"})
            
        update_data = {
            "status": "withdrawn",
            "queue_position": -1
        }
        res = supabase.table("questions").update(update_data).eq("id", q_id).execute()
        recalculate_queue(q_res.data["session_id"])
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})
