"""
PANDORA Learning Service Logging Configuration
"""
import sys
from typing import Any

import structlog
from structlog.types import Processor

from src.core.config import get_settings


def add_service_context(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Add service context to all log entries."""
    settings = get_settings()
    event_dict["service"] = settings.otel_service_name
    event_dict["version"] = settings.app_version
    return event_dict


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging."""
    settings = get_settings()
    
    # Determine log level
    level = getattr(settings, "log_level", log_level)
    
    # Configure processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        add_service_context,
    ]
    
    # Configure based on environment
    if settings.debug:
        # Pretty console output for development
        shared_processors.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON output for production
        shared_processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(structlog.stdlib, level.upper(), structlog.stdlib.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a logger instance."""
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()
