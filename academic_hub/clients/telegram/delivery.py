from __future__ import annotations

import asyncio
import logging
import uuid

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message

from academic_hub.domain.models import ResourceFile, SendOutcome


log = logging.getLogger(__name__)


class DeliveryCoordinator:
    def __init__(self, *, max_attempts: int = 2) -> None:
        self.max_attempts = max_attempts

    async def send_bundle(
        self,
        trigger_message: Message,
        state: FSMContext,
        items: list[ResourceFile],
        *,
        phase_label: str = "Preparing materials...",
    ) -> SendOutcome:
        delivery_id = str(uuid.uuid4())
        await state.update_data(
            active_delivery_id=delivery_id,
            cancel_delivery_id=None,
            stop_notified_for=None,
        )
        status_message = await trigger_message.answer(phase_label)
        await asyncio.sleep(0.25)

        sent_count = 0
        failed_items: list[ResourceFile] = []

        for index, item in enumerate(items, start=1):
            if await self._cancelled(state, delivery_id):
                await self._safe_delete(status_message)
                await self._notify_cancel_once(trigger_message, state, delivery_id)
                await self._clear_delivery_state(state, delivery_id)
                return SendOutcome(sent_count=sent_count, cancelled=True)

            await self._safe_edit(status_message, f"Sending files ({index}/{len(items)})...")
            if await self._send_file(trigger_message, item):
                sent_count += 1
            else:
                failed_items.append(item)

        await self._safe_delete(status_message)
        await self._clear_delivery_state(state, delivery_id)
        return SendOutcome(sent_count=sent_count, failed_items=failed_items, cancelled=False)

    async def cancel_active_delivery(self, state: FSMContext) -> bool:
        data = await state.get_data()
        active_delivery_id = data.get("active_delivery_id")
        if not active_delivery_id:
            return False
        await state.update_data(cancel_delivery_id=active_delivery_id)
        return True

    async def _send_file(self, message: Message, item: ResourceFile) -> bool:
        for attempt in range(1, self.max_attempts + 1):
            try:
                await message.answer_document(
                    FSInputFile(item.path),
                    caption=item.label[:1024],
                )
                return True
            except TelegramAPIError as exc:
                log.warning(
                    "event=file_send_failed path=%s attempt=%s detail=%s",
                    item.path,
                    attempt,
                    exc,
                )
                await asyncio.sleep(0.4)
        return False

    async def _cancelled(self, state: FSMContext, delivery_id: str) -> bool:
        data = await state.get_data()
        return data.get("cancel_delivery_id") == delivery_id

    async def _notify_cancel_once(self, message: Message, state: FSMContext, delivery_id: str) -> None:
        data = await state.get_data()
        if data.get("stop_notified_for") == delivery_id:
            return
        await message.answer("Stopped here. If you still need those files, open that section again.")
        await state.update_data(stop_notified_for=delivery_id)

    async def _clear_delivery_state(self, state: FSMContext, delivery_id: str) -> None:
        data = await state.get_data()
        if data.get("active_delivery_id") != delivery_id:
            return
        await state.update_data(active_delivery_id=None, cancel_delivery_id=None, stop_notified_for=None)

    async def _safe_edit(self, message: Message, text: str) -> None:
        try:
            await message.edit_text(text)
        except TelegramBadRequest as exc:
            log.debug("event=status_edit_skipped message=%s detail=%s", message.message_id, exc)
        except TelegramAPIError as exc:
            log.warning("event=status_edit_failed message=%s detail=%s", message.message_id, exc)

    async def _safe_delete(self, message: Message) -> None:
        try:
            await message.delete()
        except TelegramBadRequest as exc:
            log.debug("event=status_delete_skipped message=%s detail=%s", message.message_id, exc)
        except TelegramAPIError as exc:
            log.warning("event=status_delete_failed message=%s detail=%s", message.message_id, exc)
