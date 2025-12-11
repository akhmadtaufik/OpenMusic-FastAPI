"""Structured logging utilities for the OpenMusic API.

Provides a JSON formatter and a helper to obtain a configured logger with
environment-driven log level (LOG_LEVEL).
"""

import json
import logging
import os
from datetime import datetime, timezone
from app.core.config import settings


class JsonFormatter(logging.Formatter):
    """Serialize log records as JSON for better observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add common HTTP fields if provided via extra
        for key in (
            "method",
            "path",
            "status_code",
            "duration_ms",
            "client_ip",
            "request_id",
        ):
            if hasattr(record, key):
                log_record[key] = getattr(record, key)

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


def _resolve_log_level() -> str:
    level = os.getenv("LOG_LEVEL", settings.LOG_LEVEL)
    return str(level).upper()


def get_logger(name: str = "openmusic") -> logging.Logger:
    """Return a JSON-formatted logger with env-configured level."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    logger.setLevel(_resolve_log_level())
    logger.propagate = False
    return logger
