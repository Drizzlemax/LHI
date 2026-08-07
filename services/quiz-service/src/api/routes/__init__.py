"""PANDORA Quiz Service API Routes."""
from src.api.routes.quiz import router as quiz_router
from src.api.routes.session import router as session_router
from src.api.routes.response import router as response_router
from src.api.routes.analytics import router as analytics_router

__all__ = [
    "quiz_router",
    "session_router",
    "response_router",
    "analytics_router",
]