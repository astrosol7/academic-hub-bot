from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from academic_hub.clients.telegram.keyboards import build_reply_keyboard
from academic_hub.clients.telegram.session import load_session, save_session
from academic_hub.domain.models import ScreenView
from academic_hub.utils.logging import LogCategory, log_event


log = logging.getLogger(__name__)


class TelegramRenderer:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def render(self, message: Message, state: FSMContext, screen: ScreenView) -> Message:
        """Render a screen. Rules:
        1. Delete ALL transient messages (status updates like "Sending...")
        2. NEVER delete the screen_message_id (the keyboard carrier)
        3. Send ONE new message with the keyboard
        """
        session = await load_session(state)

        # Step 1: Clean transient messages ONLY
        for transient_id in session.transient_messages:
            await self._safe_delete(message.chat.id, transient_id)

        # Step 2: Send the new screen message with keyboard
        sent = await message.answer(
            screen.text,
            reply_markup=build_reply_keyboard(screen.button_rows, placeholder=screen.placeholder),
            parse_mode="HTML",
        )

        # Step 3: Save state — new screen_message_id, clear transients
        updated = session.model_copy(
            update={
                "screen_message_id": sent.message_id,
                "screen_key": screen.key,
                "transient_messages": (),
            }
        )
        await save_session(state, updated)
        log_event(log, logging.INFO, LogCategory.SCREEN, "Rendered screen.", chat_id=message.chat.id, screen=screen.key)
        return sent

    async def track_transient_message(self, state: FSMContext, message_id: int) -> None:
        session = await load_session(state)
        transient_messages = tuple(dict.fromkeys((*session.transient_messages, message_id)))
        await save_session(state, session.model_copy(update={"transient_messages": transient_messages}))

    async def _safe_delete(self, chat_id: int, message_id: int) -> None:
        try:
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except TelegramBadRequest as exc:
            log.debug("event=screen_delete_skipped chat=%s message=%s detail=%s", chat_id, message_id, exc)
        except TelegramAPIError as exc:
            log.warning("event=screen_delete_failed chat=%s message=%s detail=%s", chat_id, message_id, exc)
