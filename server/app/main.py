"""FastAPI application entrypoint with Supabase and JWT auth."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health

app = FastAPI(
    title="OfficeHoursQ API",
    description="Real-time office hours queue management for universities",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "OfficeHoursQ API", "docs": "/docs"}
