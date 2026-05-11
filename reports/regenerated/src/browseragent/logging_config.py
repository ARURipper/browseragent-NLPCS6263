"""Structured JSON logging with request_id propagation via ContextVar."""

import logging
import json
import contextvars
from typing import Optional

# ContextVar for request_id propagation
_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


def get_request_id() -> Optional[str]:
    """Get the current request_id from context."""
    return _request_id_var.get()


def set_request_id(request_id: str) -> contextvars.Token:
    """Set the request_id in context. Returns token for reset."""
    return _request_id_var.set(request_id)


class JSONFormatter(logging.Formatter):
    """JSON formatter that includes request_id."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logging(level: str = "INFO") -> None:
    """Configure structured JSON logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add JSON handler
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
