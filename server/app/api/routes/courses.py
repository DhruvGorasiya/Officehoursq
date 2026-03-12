import string
import random
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.courses import CourseCreate, CourseJoin
from app.core.database import supabase
from app.core.deps import get_current_user, require_role

router = APIRouter()

def generate_invite_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@router.post(
    "",
    tags=["Courses"],
    summary="Create a new course",
    description=(
        "Professor creates a new course. An invite code is auto-generated. "
        "Only users with the professor role can call this."
    ),
    response_model=SuccessResponse,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "User is not a professor",
        },
    },
)
async def create_course(
    req: CourseCreate, 
    user: dict = Depends(require_role("professor"))
):
    try:
        # Generate a unique invite code
        invite_code = generate_invite_code()
        
        course_data = {
            "name": req.name,
            "invite_code": invite_code,
            "professor_id": user["sub"]
        }
        res = supabase.table("courses").insert(course_data).execute()
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.get(
    "",
    tags=["Courses"],
    summary="List enrolled or owned courses",
    description=(
        "Returns all courses the authenticated user is enrolled in (as student or TA) "
        "or owns (as professor)."
    ),
    response_model=SuccessResponse,
)
async def list_courses(user: dict = Depends(get_current_user)):
    try:
        user_id = user["sub"]
        role = user.get("role", "student")
        
        if role == "professor":
            res = supabase.table("courses").select("*").eq("professor_id", user_id).execute()
            data = res.data
        else:
            # For students and TAs, we need courses they are enrolled in.
            res = supabase.table("course_enrollments").select("courses(*)").eq("user_id", user_id).execute()
            # The data will be like [{"courses": {"id": ...}}]
            data = [item["courses"] for item in res.data if item.get("courses")]
            
        return {"success": True, "data": data}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.get(
    "/{course_id}",
    tags=["Courses"],
    summary="Get course by ID",
    description=(
        "Returns course details. User must be enrolled in the course or be the owning professor."
    ),
    response_model=SuccessResponse,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "User is not enrolled in this course",
        },
        404: {
            "model": ErrorResponse,
            "description": "Course not found",
        },
    },
)
async def get_course(course_id: str, user: dict = Depends(get_current_user)):
    try:
        user_id = user["sub"]
        res = supabase.table("courses").select("*").eq("id", course_id).single().execute()
        
        # Check ownership or enrollment
        if res.data["professor_id"] != user_id:
            enroll_res = supabase.table("course_enrollments").select("*").eq("course_id", course_id).eq("user_id", user_id).execute()
            if not enroll_res.data:
                return JSONResponse(status_code=403, content={"success": False, "message": "Not enrolled in this course"})
                
        return {"success": True, "data": res.data}
    except Exception as e:
        # Supabase raises an error if single() finds nothing, so we handle it here
        if "contains 0 rows" in str(e):
             return JSONResponse(status_code=404, content={"success": False, "message": "Course not found"})
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.post(
    "/join",
    tags=["Courses"],
    summary="Join a course by invite code",
    description=(
        "Student or TA joins a course using a 6-character invite code. "
        "Fails if already enrolled or code is invalid."
    ),
    response_model=SuccessResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid invite code or already enrolled",
        },
    },
)
async def join_course(req: CourseJoin, user: dict = Depends(get_current_user)):
    try:
        user_id = user["sub"]
        role = user.get("role", "student")
        
        if role == "professor":
            return JSONResponse(status_code=403, content={"success": False, "message": "Professors cannot join via invite code"})
            
        # Find course by invite code
        try:
             course_res = supabase.table("courses").select("*").eq("invite_code", req.invite_code).single().execute()
        except Exception:
             return JSONResponse(status_code=404, content={"success": False, "message": "Invalid invite code"})
             
        course_id = course_res.data["id"]
        
        # Check if already enrolled
        enroll_res = supabase.table("course_enrollments").select("*").eq("course_id", course_id).eq("user_id", user_id).execute()
        if enroll_res.data:
            return JSONResponse(status_code=400, content={"success": False, "message": "Already enrolled"})
            
        enroll_data = {
            "course_id": course_id,
            "user_id": user_id,
            "role": role
        }
        res = supabase.table("course_enrollments").insert(enroll_data).execute()
        return {"success": True, "data": res.data[0]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})
