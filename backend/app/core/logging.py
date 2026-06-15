from __future__ import annotations

import contextvars
import uuid
from typing import Any

import structlog

from app.core.config import Settings

# Context variable to store the current request's trace ID
_trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_id", default=""
)


def set_trace_id(trace_id: str) -> None:
    _trace_id_var.set(trace_id)


def get_trace_id() -> str:
    return _trace_id_var.get() or str(uuid.uuid4())


def _add_trace_id(
    logger: structlog.BoundLogger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add trace_id to every log event."""
    trace_id = _trace_id_var.get()
    if trace_id:
        event_dict["trace_id"] = trace_id
    return event_dict


def configure_logging(settings: Settings) -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _add_trace_id,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer()
            if settings.environment.value == "development"
            else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
