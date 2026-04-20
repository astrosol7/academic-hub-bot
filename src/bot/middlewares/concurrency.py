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
            
        user_id = user.id
        state: FSMContext | None = data.get("state")
        current_time = monotonic()
        self._last_active_at[user_id] = current_time
        
        is_low_priority = True
        mode_context = "UNKNOWN"
        execution_id = "UNKNOWN"
        
        # Priority check
        if state and isinstance(event, Message) and event.text:
            text = event.text.strip()
            from academic_hub.clients.telegram.session import load_session
            session = await load_session(state)
            mode_context = session.mode.value
            execution_id = session.execution_id
            
            if session.mode in (SessionMode.SEARCH, SessionMode.REPORT):
                if text not in self._all_buttons:
                    is_low_priority = False
                    
        if is_low_priority:
            self._latest_intent_low[user_id] = current_time
            
        if user_id not in self._user_locks:
            self._user_locks[user_id] = asyncio.Lock()
            
        async with self._user_locks[user_id]:
            if is_low_priority and self._latest_intent_low[user_id] != current_time:
                log_event(
                    log,
                    logging.DEBUG,
                    LogCategory.SYSTEM_DROPPED_EVENT,
                    "Dropped stale low-priority navigation intent.",
                    user_id=user_id,
                    session_mode=mode_context,
                    execution_id=execution_id,
                    action="DROP_STALE"
                )
                return None
                
            return await handler(event, data)

concurrency_guard = ConcurrencyGuardMiddleware()
