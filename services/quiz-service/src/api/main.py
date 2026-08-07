"""
PANDORA Quiz Service API Application
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger
from src.core.cache import get_redis_client, close_redis_client
from src.api.routes import (
    quiz_router,
    session_router,
    response_router,
    analytics_router,
)

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Quiz Service", app=settings.app_name)
    await get_redis_client()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Quiz Service")
    await close_redis_client()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()
    
    app = FastAPI(
        title=settings.app_name,
        description="PANDORA Quiz Service - Adaptive testing and assessment",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(quiz_router, prefix="/api/v1")
    app.include_router(session_router, prefix="/api/v1")
    app.include_router(response_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": settings.app_name}
    
    @app.get("/ready")
    async def readiness_check():
        # Check database connection
        from src.core.database import engine
        try:
            async with engine.connect() as conn:
                from sqlalchemy import text
                await conn.execute(text("SELECT 1"))
            return {"status": "ready", "database": "connected"}
        except Exception as e:
            return {"status": "not ready", "database": str(e)}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
    )
