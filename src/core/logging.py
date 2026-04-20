"""
Core logging utilities for Academic Hub — Orbit V1.0
"""

import logging
from enum import Enum
from typing import Any


class LogCategory(Enum):
    """Log categories for structured telemetry."""
    BOT = "bot"
    API = "api"
    DATABASE = "database"
    SECURITY = "security"
    DELIVERY = "delivery"
    DELIVERY_CANCEL = "delivery.cancel"
    SEARCH = "search"
    SEARCH_DB_HIT = "search.db_hit"
    SEARCH_FS_FALLBACK = "search.fs_fallback"
    SEARCH_FAILED = "search.failed"
    NAVIGATION = "navigation"
    SCREEN = "screen"
    COMMAND = "command"
    USER_SUGGESTION = "user_suggestion"
    SEND_FAIL = "send_fail"
    SYSTEM_TOKEN_MISMATCH = "system.token_mismatch"
    SYSTEM_TASK_KILLED = "system.task_killed"


def log_event(logger: logging.Logger, level: int, category: LogCategory, message: str, **kwargs: Any) -> None:
    """
    Structured log event.
    Usage: log_event(log, logging.INFO, LogCategory.SEARCH, "query resolved", query=q)
    """
    extras = " ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    full_msg = f"event={category.value} {message}" + (f" {extras}" if extras else "")
    logger.log(level, full_msg)
