from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, timezone

from app.schemas.questions import QuestionCreate, QuestionUpdate, QuestionResolve
from app.core.database import supabase
from app.core.deps import get_current_user, require_role
from app.utils.realtime_broadcast import broadcast_session_event, broadcast_user_notification

router = APIRouter()

def recalculate_queue(session_id: str):
    """Re-sort and renumber all active queue positions for a session.
    Sort: priority (high>medium>low), then created_at ASC.
    Deferred questions always go to the absolute back, sorted by deferred_at ASC.
    """
    priority_map = {"high": 0, "medium": 1, "low": 2}

    active = supabase.table("questions") \
        .select("id, priority, created_at, status, deferred_at") \
        .eq("session_id", session_id) \
        .in_("status", ["queued", "in_progress", "deferred"]) \
        .execute()

    non_deferred = [q for q in active.data if q["status"] != "deferred"]
    deferred = [q for q in active.data if q["status"] == "deferred"]

    non_deferred.sort(key=lambda q: (priority_map.get(q["priority"], 2), q["created_at"]))
    deferred.sort(key=lambda q: q["deferred_at"] or q["created_at"])

    ordered = non_deferred + deferred
    for i, q in enumerate(ordered):
        supabase.table("questions").update({"queue_position": i + 1}).eq("id", q["id"]).execute()

@router.post("")
async def create_question(req: QuestionCreate, user: dict = Depends(require_role("student"))):
    try:
        session_id = req.session_id
        student_id = user["sub"]
        
        # Check if session is active and get course_id for denormalized storage
        session_res = supabase.table("sessions").select("status, course_id").eq("id", session_id).single().execute()
        if not session_res.data or session_res.data["status"] != "active":
            return JSONResponse(status_code=400, content={"success": False, "message": "Session is not active"})
            
        # Check if student already has active question
        existing = supabase.table("questions").select("id").eq("session_id", session_id).eq("student_id", student_id).in_("status", ["queued", "in_progress"]).execute()
        if existing.data:
            return JSONResponse(status_code=400, content={"success": False, "message": "You already have an active question in this session"})
            
        # Calculate queue position (include deferred since they occupy queue slots)
        current_queue = supabase.table("questions").select("id").eq("session_id", session_id).in_("status", ["queued", "in_progress", "deferred"]).execute()
        queue_pos = len(current_queue.data) + 1
        
        q_data = req.model_dump()
        q_data["student_id"] = student_id
        q_data["course_id"] = session_res.data["course_id"]
        q_data["status"] = "queued"
        q_data["queue_position"] = queue_pos
        
        res = supabase.table("questions").insert(q_data).execute()
        created = res.data[0]

        # Broadcast: new question in session queue
        broadcast_session_event(
            session_id=session_id,
            event="question:submitted",
            payload={"question": created},
        )

        return {"success": True, "data": created}
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
        if not q_res.data or q_res.data["status"] not in ["queued", "deferred"]:
            return JSONResponse(status_code=400, content={"success": False, "message": "Question is not queued"})
            
        update_data = {
            "status": "in_progress",
            "claimed_by": user["sub"],
            "claimed_at": datetime.now(timezone.utc).isoformat()
        }
        res = supabase.table("questions").update(update_data).eq("id", q_id).execute()
        updated = res.data[0]

        # Broadcast: question claimed / queue updated
        session_id = updated.get("session_id")
        if session_id:
            broadcast_session_event(
                session_id=session_id,
                event="question:claimed",
                payload={"question": updated},
            )

        # Optionally notify the student who asked the question
        student_id = updated.get("student_id")
        if student_id:
            broadcast_user_notification(
                user_id=student_id,
                payload={
                    "type": "question_claimed",
                    "question_id": updated.get("id"),
                    "session_id": session_id,
                },
            )

        return {"success": True, "data": updated}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.patch("/{q_id}/resolve")
async def resolve_question(q_id: str, req: QuestionResolve, user: dict = Depends(require_role("ta", "professor"))):
    try:
        q_res = supabase.table("questions").select("status, session_id").eq("id", q_id).single().execute()
        if not q_res.data or q_res.data["status"] not in ["queued", "in_progress", "deferred"]:
            return JSONResponse(status_code=400, content={"success": False, "message": "Question cannot be resolved"})
            
        update_data = {
            "status": "resolved",
            "resolution_note": req.resolution_note,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "queue_position": -1  # removed from queue
        }
        res = supabase.table("questions").update(update_data).eq("id", q_id).execute()
        updated = res.data[0]

        session_id = q_res.data["session_id"]
        recalculate_queue(session_id)

        # Broadcast: question resolved / queue updated
        broadcast_session_event(
            session_id=session_id,
            event="question:resolved",
            payload={"question": updated},
        )

        # Notify student
        student_id = updated.get("student_id")
        if student_id:
            broadcast_user_notification(
                user_id=student_id,
                payload={
                    "type": "question_resolved",
                    "question_id": updated.get("id"),
                    "session_id": session_id,
                },
            )

        return {"success": True, "data": updated}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.patch("/{q_id}/defer")
async def defer_question(q_id: str, user: dict = Depends(require_role("ta", "professor"))):
    try:
        q_res = supabase.table("questions").select("status, session_id").eq("id", q_id).single().execute()
        if not q_res.data or q_res.data["status"] not in ["queued", "in_progress"]:
            return JSONResponse(status_code=400, content={"success": False, "message": "Question cannot be deferred"})
            
        session_id = q_res.data["session_id"]

        update_data = {
            "status": "deferred",
            "claimed_by": None,
            "claimed_at": None,
            "deferred_at": datetime.now(timezone.utc).isoformat(),
        }
        res = supabase.table("questions").update(update_data).eq("id", q_id).execute()
        updated = res.data[0]

        recalculate_queue(session_id)

        # Broadcast: question deferred / queue updated
        broadcast_session_event(
            session_id=session_id,
            event="question:deferred",
            payload={"question": updated},
        )

        # Notify student
        student_id = updated.get("student_id")
        if student_id:
            broadcast_user_notification(
                user_id=student_id,
                payload={
                    "type": "question_deferred",
                    "question_id": updated.get("id"),
                    "session_id": session_id,
                },
            )

        return {"success": True, "data": updated}
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
        if q_res.data["status"] not in ["queued", "in_progress", "deferred"]:
            return JSONResponse(status_code=400, content={"success": False, "message": "Cannot withdraw from current status"})
            
        update_data = {
            "status": "withdrawn",
            "queue_position": -1
        }
        res = supabase.table("questions").update(update_data).eq("id", q_id).execute()
        updated = res.data[0]

        session_id = q_res.data["session_id"]
        recalculate_queue(session_id)

        # Broadcast: question withdrawn / queue updated
        broadcast_session_event(
            session_id=session_id,
            event="question:withdrawn",
            payload={"question": updated},
        )

        return {"success": True, "data": updated}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})


@router.post("/{q_id}/helpful")
async def mark_question_helpful(q_id: str, user: dict = Depends(require_role("student"))):
    try:
        student_id = user["sub"]

        # Ensure question exists and is resolved
        q_res = (
            supabase.table("questions")
            .select("id, status, course_id, helpful_votes")
            .eq("id", q_id)
            .single()
            .execute()
        )
        if not q_res.data:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Question not found"},
            )
        if q_res.data["status"] != "resolved":
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Only resolved questions can be marked helpful",
                },
            )

        # Insert helpful vote (one per student per question enforced by DB unique constraint)
        try:
            supabase.table("helpful_votes").insert(
                {"question_id": q_res.data["id"], "student_id": student_id}
            ).execute()
        except Exception as e:
            # Assume any insert error here is due to unique constraint (already voted)
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Already voted helpful"},
            )

        # Increment helpful_votes counter on questions table
        new_count = (q_res.data.get("helpful_votes") or 0) + 1
        update_res = (
            supabase.table("questions")
            .update({"helpful_votes": new_count})
            .eq("id", q_id)
            .execute()
        )
        updated = update_res.data[0] if update_res.data else None

        return {"success": True, "data": updated or {"id": q_id, "helpful_votes": new_count}}
    except Exception as e:
        return JSONResponse(
            status_code=400, content={"success": False, "message": str(e)}
        )
