from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import (
    auth,
    courses,
    health,
    knowledge_base,
    questions,
    sessions,
    analytics,
)

app = FastAPI(
    title="OfficeHoursQ API",
    description=(
        "Real-time office hours queue management API for university courses. "
        "Supports three user roles: Student, TA, and Professor. "
        "Features include question queue management, real-time updates via Supabase Realtime, "
        "knowledge base search, and analytics dashboards."
    ),
    version="1.0.0",
    contact={"name": "OfficeHoursQ Team"},
    license_info={"name": "MIT"},
    servers=[
        {
            "url": "https://officehoursq.onrender.com",
            "description": "Production",
        },
        {"url": "http://localhost:8000", "description": "Local Development"},
    ],
    openapi_tags=[
        {
            "name": "Auth",
            "description": "User registration, login, and authentication",
        },
        {
            "name": "Courses",
            "description": "Course creation, enrollment, and management",
        },
        {
            "name": "Sessions",
            "description": "Office hours session scheduling and lifecycle",
        },
        {
            "name": "Questions",
            "description": "Question submission, claiming, resolving, and queue management",
        },
        {
            "name": "Knowledge Base",
            "description": "Search resolved questions and find similar past questions",
        },
        {
            "name": "Analytics",
            "description": "Professor-only dashboards: overview, categories, trends, TA performance",
        },
        {
            "name": "Notifications",
            "description": "User notification retrieval and read status management",
        },
    ],
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
app.include_router(
    courses.router, prefix=f"{settings.API_V1_PREFIX}/courses", tags=["courses"]
)
app.include_router(
    sessions.router, prefix=f"{settings.API_V1_PREFIX}/sessions", tags=["sessions"]
)
app.include_router(
    questions.router, prefix=f"{settings.API_V1_PREFIX}/questions", tags=["questions"]
)
app.include_router(
    knowledge_base.router,
    prefix=f"{settings.API_V1_PREFIX}/knowledge-base",
    tags=["knowledge-base"],
)
app.include_router(
    analytics.router,
    prefix=f"{settings.API_V1_PREFIX}/analytics",
    tags=["analytics"],
)


@app.get("/")
async def root():
    return {
        "success": True,
        "data": {"name": settings.PROJECT_NAME, "version": "0.1.0"},
    }
