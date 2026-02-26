"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok"}
