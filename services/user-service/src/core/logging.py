"""
PANDORA User Service Logging Configuration
Structured logging with OpenTelemetry integration
"""
import logging
import sys
from typing import Any

import structlog
from opentelemetry import trace

from src.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Set up standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )

    # Configure structlog processors
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if not settings.debug else _console_renderer,
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _console_renderer(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> str:
    """Console renderer for development."""
    # Add trace ID if available
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        event_dict["trace_id"] = format(span.get_span_context().trace_id, "032x")

    # Format as console output
    level = event_dict.pop("level", "").upper()
    timestamp = event_dict.pop("timestamp", "")
    message = event_dict.pop("event", "")
    
    parts = [f"[{timestamp}]"]
    if level:
        parts.append(f"[{level}]")
    parts.append(message)
    
    if event_dict:
        parts.append("|")
        for key, value in event_dict.items():
            if key not in ["logger", "handler"]:
                parts.append(f"{key}={value}")
    
    return " ".join(str(p) for p in parts)


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a logger instance."""
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(service=name)
    return logger
