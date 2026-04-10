from __future__ import annotations

import json
import logging
from enum import Enum
from typing import Any


class LogCategory(str, Enum):
    SEARCH_HIT = "SEARCH_HIT"
    SEARCH_MISS = "SEARCH_MISS"
    SEND_FAIL = "SEND_FAIL"
    EMPTY_SECTION = "EMPTY_SECTION"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    USER_REPORT = "USER_REPORT"
    SYSTEM_ORPHAN = "SYSTEM_ORPHAN"
    SYSTEM_WARNING = "SYSTEM_WARNING"
    DELIVERY_CANCEL = "DELIVERY_CANCEL"
    SCREEN = "SCREEN"


def log_event(
    logger: logging.Logger,
    level: int,
    category: LogCategory,
    message: str,
    **context: Any,
) -> None:
    logger.log(
        level,
        "category=%s message=%s context=%s",
        category.value,
        message,
        json.dumps(context, sort_keys=True, default=str),
    )
