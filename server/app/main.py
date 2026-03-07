from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import health, auth, courses, sessions, questions

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_V1_PREFIX, tags=["health"])
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["auth"])
app.include_router(courses.router, prefix=f"{settings.API_V1_PREFIX}/courses", tags=["courses"])
app.include_router(sessions.router, prefix=f"{settings.API_V1_PREFIX}/sessions", tags=["sessions"])
app.include_router(questions.router, prefix=f"{settings.API_V1_PREFIX}/questions", tags=["questions"])

@app.get("/")
async def root():
    return {
        "success": True,
        "data": {"name": settings.PROJECT_NAME, "version": "0.1.0"},
    }
