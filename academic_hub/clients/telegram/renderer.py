from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from academic_hub.clients.telegram.keyboards import build_reply_keyboard
from academic_hub.domain.models import ScreenView


log = logging.getLogger(__name__)


class TelegramRenderer:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def render(self, message: Message, state: FSMContext, screen: ScreenView) -> Message:
        data = await state.get_data()
        previous_id = data.get("screen_message_id")
        if previous_id:
            await self._safe_delete(message.chat.id, previous_id)

        sent = await message.answer(
            screen.text,
            reply_markup=build_reply_keyboard(screen.button_rows, placeholder=screen.placeholder),
        )
        await state.update_data(screen_message_id=sent.message_id, screen_key=screen.key)
        log.info("event=screen_rendered chat=%s screen=%s", message.chat.id, screen.key)
        return sent

    async def _safe_delete(self, chat_id: int, message_id: int) -> None:
        try:
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except TelegramBadRequest as exc:
            log.debug("event=screen_delete_skipped chat=%s message=%s detail=%s", chat_id, message_id, exc)
        except TelegramAPIError as exc:
            log.warning("event=screen_delete_failed chat=%s message=%s detail=%s", chat_id, message_id, exc)

