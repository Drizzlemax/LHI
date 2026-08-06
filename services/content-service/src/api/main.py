"""
PANDORA Content Service
Main FastAPI Application
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from src.api.routes import content, collections, health
from src.core.config import settings
from src.core.database import init_db, close_db, check_db_connection
from src.core.logging import setup_logging

# Initialize logging
setup_logging()

# Initialize tracer
tracer = trace.get_tracer(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="PANDORA Content Service - Document Storage and Management",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
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
    """Handle unhandled exceptions."""
    trace.get_current_span().record_exception(exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
            }
        },
    )


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(content.router, prefix="/api/v1", tags=["Content"])
app.include_router(collections.router, prefix="/api/v1", tags=["Collections"])


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


# Readiness check endpoint
@app.get("/ready", tags=["Health"])
async def readiness_check() -> dict:
    """Readiness check endpoint."""
    db_healthy = await check_db_connection()
    return {
        "status": "ready" if db_healthy else "not_ready",
        "checks": {
            "database": "ok" if db_healthy else "failed",
        },
    }


# Instrument with OpenTelemetry
if settings.otel_enabled:
    FastAPIInstrumentor.instrument_app(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
