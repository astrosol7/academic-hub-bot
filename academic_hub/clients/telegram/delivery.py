from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramRetryAfter
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message

from academic_hub.clients.telegram.session import load_session, save_session
from academic_hub.domain.models import DeliverySession, ResourceFile, SendOutcome
from academic_hub.utils.logging import LogCategory, log_event


log = logging.getLogger(__name__)


def _path_key(path: Path) -> str:
    return path.resolve().as_posix()


class DeliveryCoordinator:
    def __init__(self, *, max_attempts: int = 2, send_delay_seconds: float = 0.5) -> None:
        self.max_attempts = max_attempts
        self.send_delay_seconds = send_delay_seconds

    async def send_bundle(
        self,
        trigger_message: Message,
        state: FSMContext,
        items: list[ResourceFile],
        original_execution_id: int,
        *,
        phase_label: str = "📦 <b>Preparing your materials...</b>",
    ) -> SendOutcome:
        delivery_id = str(uuid.uuid4())
        session = await load_session(state)
        session.delivery = DeliverySession(session_id=delivery_id, total_files=len(items))
        session.retry_request = None
        session.delivery_active = True
        await save_session(state, session)

        status_message = await trigger_message.answer(phase_label, parse_mode="HTML")
        await self._track_transient(state, status_message.message_id)

        sent_count = 0
        failed_items: list[ResourceFile] = []
        sent_paths: set[str] = set()

        try:
            for index, item in enumerate(items, start=1):
                # Yield control for cancellation check
                await asyncio.sleep(0)
                
                session = await load_session(state)
                # HARD INTERRUPT: Check token mismatch or cancel flag
                if (session.execution_id != original_execution_id or 
                    session.delivery is None or 
                    session.delivery.session_id != delivery_id or 
                    session.delivery.cancel_requested):
                    
                    log_event(
                        log, logging.WARNING, LogCategory.SYSTEM_TOKEN_MISMATCH,
                        "Delivery aborted due to intent shift or explicit cancellation.",
                        user_id=session.user_id,
                        session_mode=session.mode.value,
                        execution_id=session.execution_id,
                        expected_execution_id=original_execution_id,
                        action="EXECUTION_TOKEN_MISMATCH"
                    )
                    
                    await self._safe_delete(status_message)
                    if session.delivery and session.delivery.cancel_requested:
                        await self._notify_cancel_once(trigger_message, state)
                    return SendOutcome(sent_count=sent_count, failed_items=tuple(failed_items), cancelled=True)

                path_key = _path_key(item.path)
                if path_key in sent_paths or path_key in session.delivery.sent_paths:
                    continue

                dots = "." * ((index - 1) % 3 + 1)
                await self._safe_edit(
                    status_message, 
                    f"📤 <b>Sending files ({index}/{len(items)}){dots}</b>\n<i>Interrupting will stop current batch.</i>"
                )

                if await self._send_file(trigger_message, item):
                    sent_paths.add(path_key)
                    sent_count += 1
                    await self._update_progress(state, delivery_id, sent_paths=sent_paths)
                else:
                    failed_items.append(item)
                    await self._update_progress(
                        state,
                        delivery_id,
                        sent_paths=sent_paths,
                        failed_paths={_path_key(failed.path) for failed in failed_items},
                    )

                # Throttle to respect Telegram limits
                await asyncio.sleep(self.send_delay_seconds)

            await self._safe_delete(status_message)
            return SendOutcome(sent_count=sent_count, failed_items=tuple(failed_items), cancelled=False)
            
        except asyncio.CancelledError:
            session = await load_session(state)
            log_event(
                log, logging.INFO, LogCategory.SYSTEM_TASK_KILLED,
                f"Delivery {delivery_id} forcefully cancelled by task registry.",
                user_id=session.user_id, action="TASK_CANCELLED"
            )
            await self._safe_delete(status_message)
            await self._notify_cancel_once(trigger_message, state)
            raise
        finally:
            await self._clear_delivery_state(state, delivery_id)

    async def cancel_active_delivery(self, state: FSMContext) -> bool:
        session = await load_session(state)
        if session.delivery is None:
            return False
        session.delivery = session.delivery.model_copy(update={"cancel_requested": True})
        session.delivery_active = False
        await save_session(state, session)
        return True

    async def _send_file(self, message: Message, item: ResourceFile) -> bool:
        for attempt in range(1, self.max_attempts + 1):
            try:
                # Use item.caption (which we populated during indexing) or fallback to label
                caption = item.caption if hasattr(item, "caption") and item.caption else item.label
                await message.answer_document(
                    FSInputFile(item.path),
                    caption=caption[:1024],
                )
                return True
            except TelegramRetryAfter as exc:
                retry_after = max(float(exc.retry_after), 1.0)
                log_event(
                    log,
                    logging.WARNING,
                    LogCategory.SEND_FAIL,
                    "Telegram asked for retry-after.",
                    path=str(item.path),
                    attempt=attempt,
                    retry_after=retry_after,
                )
                await asyncio.sleep(retry_after)
            except TelegramAPIError as exc:
                log_event(
                    log,
                    logging.WARNING,
                    LogCategory.SEND_FAIL,
                    "File delivery failed.",
                    path=str(item.path),
                    attempt=attempt,
                    detail=str(exc),
                )
                await asyncio.sleep(self.send_delay_seconds)
            except Exception as exc:
                log.exception("Unexpected error during file delivery: %s", exc)
                return False
        return False

    async def _notify_cancel_once(self, message: Message, state: FSMContext) -> None:
        session = await load_session(state)
        if session.delivery is None or session.delivery.stop_notice_sent:
            return
        
        notice = await message.answer("🛑 <b>Delivery stopped.</b>", parse_mode="HTML")
        await self._track_transient(state, notice.message_id)
        
        session = await load_session(state)
        if session.delivery is not None:
            session.delivery = session.delivery.model_copy(update={"stop_notice_sent": True})
            await save_session(state, session)
        
        log_event(log, logging.INFO, LogCategory.DELIVERY_CANCEL, "Delivery stopped by user.", chat_id=message.chat.id)

    async def _update_progress(
        self,
        state: FSMContext,
        delivery_id: str,
        *,
        sent_paths: set[str],
        failed_paths: set[str] | None = None,
    ) -> None:
        session = await load_session(state)
        if session.delivery is None or session.delivery.session_id != delivery_id:
            return
        session.delivery = session.delivery.model_copy(
            update={
                "files_sent_count": len(sent_paths),
                "sent_paths": tuple(sorted(sent_paths)),
                "failed_paths": tuple(sorted(failed_paths or session.delivery.failed_paths)),
            }
        )
        await save_session(state, session)

    async def _clear_delivery_state(self, state: FSMContext, delivery_id: str) -> None:
        session = await load_session(state)
        session.delivery_active = False
        if session.delivery is None or session.delivery.session_id != delivery_id:
            await save_session(state, session)
            return
        session.delivery = None
        await save_session(state, session)

    async def _track_transient(self, state: FSMContext, message_id: int) -> None:
        session = await load_session(state)
        session.transient_messages = tuple(dict.fromkeys((*session.transient_messages, message_id)))
        await save_session(state, session)

    async def _safe_edit(self, message: Message, text: str) -> None:
        try:
            await message.edit_text(text, parse_mode="HTML")
        except Exception:
            pass

    async def _safe_delete(self, message: Message) -> None:
        try:
            await message.delete()
        except Exception:
            pass
