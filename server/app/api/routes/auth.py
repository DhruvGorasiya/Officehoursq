from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse
from app.schemas.common import SuccessResponse
from app.core.database import supabase
from app.core.deps import get_current_user

router = APIRouter()

@router.post("/register")
async def register(req: RegisterRequest):
    try:
        res = supabase.auth.sign_up({
            "email": req.email,
            "password": req.password,
            "options": {
                "data": {
                    "name": req.name,
                    "role": req.role.value,
                }
            }
        })
        if not res.user or not res.session:
            return JSONResponse(status_code=400, content={"success": False, "message": "Registration failed or requires email confirmation."})

        # Manually insert into public.users
        try:
            supabase.table("users").insert({
                "id": res.user.id,
                "email": req.email,
                "name": req.name,
                "role": req.role.value.lower(),
            }).execute()
        except Exception as db_err:
            import traceback
            traceback.print_exc()
            return JSONResponse(status_code=400, content={"success": False, "message": f"Auth succeeded but profile creation failed: {str(db_err)}"})

        auth_res = AuthResponse(
            id=res.user.id,
            email=res.user.email,
            name=req.name,
            role=req.role.value,
            token=res.session.access_token
        )
        return {"success": True, "data": auth_res.model_dump()}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})

@router.post("/login")
async def login(req: LoginRequest):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password
        })
        if not res.user or not res.session:
            return JSONResponse(status_code=401, content={"success": False, "message": "Invalid credentials"})
        
        # In a fully synced system we might trust user metadata, but let's fetch from our public.users table just in case it's updated.
        try:
            user_response = supabase.table("users").select("*").eq("id", res.user.id).single().execute()
            user_data = user_response.data
            name = user_data["name"]
            role = user_data["role"]
        except Exception:
            # Fallback to metadata
            user_meta = res.user.user_metadata or {}
            name = user_meta.get("name", "")
            role = user_meta.get("role", "student")

        auth_res = AuthResponse(
            id=res.user.id,
            email=res.user.email,
            name=name,
            role=role,
            token=res.session.access_token
        )
        return {"success": True, "data": auth_res.model_dump()}
    except Exception as e:
        return JSONResponse(status_code=401, content={"success": False, "message": str(e)})

@router.get("/me")
async def get_me(user_payload: dict = Depends(get_current_user)):
    user_id = user_payload.get("sub")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Invalid token payload"})
        
    try:
        user_response = supabase.table("users").select("*").eq("id", user_id).single().execute()
        if not user_response.data:
            return JSONResponse(status_code=404, content={"success": False, "message": "User not found"})
            
        user_data = user_response.data
        auth_res = AuthResponse(
            id=user_data["id"],
            email=user_data["email"],
            name=user_data["name"],
            role=user_data["role"],
            token="" # Not required for /me, but returned for schema compliance
        )
        return {"success": True, "data": auth_res.model_dump()}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})