"""Structured JSON logging configuration with request_id propagation."""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Optional

# Context variable for request_id propagation across async/sync calls
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON with required fields for traceability."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)
            ),
            "level": record.levelname,
            "module": record.module,
            "request_id": request_id_var.get() or "NO_REQUEST_ID",
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with JSON formatter to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


def get_logger(name: str) -> logging.Logger:
    """Return a named logger that inherits root JSON config."""
    return logging.getLogger(name)


def new_request_id() -> str:
    """Generate a short UUID for a new request and set it in context."""
    rid = str(uuid.uuid4())[:8]
    request_id_var.set(rid)
    return rid


def set_request_id(rid: str) -> None:
    """Set an existing request_id into context."""
    request_id_var.set(rid)
