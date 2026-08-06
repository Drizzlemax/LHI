"""
PANDORA Content Service Health Routes
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "content-service",
    }


@router.get("/ready")
async def readiness_check() -> dict:
    """Readiness check endpoint."""
    return {
        "status": "ready",
        "checks": {
            "database": "ok",
        },
    }
