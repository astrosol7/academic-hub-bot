from typing import Any, Awaitable, Callable, Dict

import asyncio
import logging
from time import monotonic
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, Message

from src.core.models import SessionMode
from src.core.services import ButtonLabels
from src.core.logging import LogCategory, log_event

log = logging.getLogger(__name__)

class ConcurrencyGuardMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super().__init__()
        self._user_locks: dict[int, asyncio.Lock] = {}
        self._latest_intent_low: dict[int, float] = {}
        self._last_active_at: dict[int, float] = {}
        
        labels = ButtonLabels()
        self._all_buttons = {
            labels.browse, labels.search, labels.about, 
            labels.report, labels.BACK, labels.MAIN_MENU, 
            labels.MORE_FILES, labels.OVERVIEW, labels.BY_WEEK, 
            labels.RETRY, labels.EXIT_SEARCH
        }

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)
            
        # We rely on aiogram's built-in handling and task_registry for cancellation.
        # Minimalist middleware that doesn't maintain in-memory state.
        return await handler(event, data)

concurrency_guard = ConcurrencyGuardMiddleware()
