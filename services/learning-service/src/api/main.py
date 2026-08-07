"""
PANDORA Learning Service Main Application
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger
from src.graph.neo4j_client import get_neo4j_client, close_neo4j_client

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    # Startup
    setup_logging()
    logger.info("starting_service", service="learning-service")
    
    # Connect to Neo4j
    try:
        await get_neo4j_client()
    except Exception as e:
        logger.warning("neo4j_connection_skipped", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("shutting_down_service", service="learning-service")
    await close_neo4j_client()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="PANDORA Learning Service - Adaptive Learning Paths & Progress Tracking",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            path=request.url.path,
            error=str(exc),
            exc_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
    
    # Health check endpoints
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """Basic health check."""
        return {"status": "healthy", "service": settings.app_name}
    
    @app.get("/ready", tags=["Health"])
    async def readiness_check() -> dict:
        """Readiness check with dependency status."""
        neo4j_status = "disconnected"
        try:
            client = await get_neo4j_client()
            if client._driver is not None:
                neo4j_status = "connected"
        except Exception:
            pass
        
        return {
            "status": "ready",
            "service": settings.app_name,
            "dependencies": {
                "neo4j": neo4j_status,
            },
        }
    
    @app.get("/api/v1/health", tags=["Health"])
    async def api_health_check() -> dict:
        """API health check."""
        return {
            "status": "healthy",
            "version": settings.app_version,
            "service": "learning-service",
        }
    
    # Register routers
    from src.api.routes import learning_paths, progress, recommendations, quiz
    
    app.include_router(
        learning_paths.router,
        prefix="/api/v1/learning-paths",
        tags=["Learning Paths"],
    )
    
    app.include_router(
        progress.router,
        prefix="/api/v1/progress",
        tags=["Progress"],
    )
    
    app.include_router(
        recommendations.router,
        prefix="/api/v1/recommendations",
        tags=["Recommendations"],
    )
    
    app.include_router(
        quiz.router,
        prefix="/api/v1/quiz",
        tags=["Quiz"],
    )
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
