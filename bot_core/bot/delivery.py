from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramRetryAfter
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message

from src.bot.session import load_session, save_session
from src.core.models import DeliverySession, ResourceFile, SendOutcome
from src.core.logging import LogCategory, log_event


log = logging.getLogger(__name__)


def _path_key(path: Path) -> str:
    return path.resolve().as_posix()


def _human_size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024.0 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"


def _progress_bar(done: int, total: int, width: int = 12) -> str:
    if total <= 0:
        return "░" * width
    filled = int((done / total) * width)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


class DeliveryCoordinator:
    def __init__(self, *, max_attempts: int = 2, send_delay_seconds: float = 0.5) -> None:
        self.max_attempts = max_attempts
        self.send_delay_seconds = send_delay_seconds

    async def send_bundle(
        self,
        trigger_message: Message,
        state: FSMContext,
        items: list[ResourceFile],
        *,
        phase_label: str = "📦 <b>Preparing your materials...</b>",
    ) -> SendOutcome:
        delivery_id = str(uuid.uuid4())
        session = await load_session(state)
        session.delivery = DeliverySession(session_id=delivery_id, total_files=len(items))
        session.retry_request = None
        session.delivery_active = True
        await save_session(state, session)

        total_bytes = 0
        for it in items:
            try:
                p = Path(it.path)
                if p.exists():
                    total_bytes += p.stat().st_size
            except (OSError, AttributeError):
                continue
        status_message = await trigger_message.answer(
            f"{phase_label}\n\n📦 Batch size: <b>{_human_size(total_bytes)}</b>",
            parse_mode="HTML",
        )
        await self._track_transient(state, status_message.message_id)

        sent_count = 0
        failed_items: list[ResourceFile] = []
        sent_paths: set[str] = set()

        try:
            for index, item in enumerate(items, start=1):
                # Yield control for cancellation check
                await asyncio.sleep(0)
                
                session = await load_session(state)
                # HARD INTERRUPT: Check cancel flag
                if (session.delivery is None or 
                    session.delivery.session_id != delivery_id or 
                    session.delivery.cancel_requested):
                    
                    log_event(
                        log, logging.WARNING, LogCategory.DELIVERY_CANCEL,
                        "Delivery aborted due to intent shift or explicit cancellation.",
                        user_id=session.user_id,
                        session_mode=session.mode.value,
                        action="DELIVERY_ABORTED"
                    )
                    
                    await self._safe_delete(status_message)
                    if session.delivery and session.delivery.cancel_requested:
                        await self._notify_cancel_once(trigger_message, state)
                    return SendOutcome(sent_count=sent_count, failed_items=tuple(failed_items), cancelled=True)
                 
                # Double-tap verification check
                if session.delivery and session.delivery.cancel_requested:
                    await self._notify_cancel_once(trigger_message, state)
                    return SendOutcome(sent_count=sent_count, failed_items=tuple(failed_items), cancelled=True)

                item_path = Path(item.path)
                path_key = _path_key(item_path)
                if path_key in sent_paths or path_key in session.delivery.sent_paths:
                    continue

                file_size = 0
                try:
                    file_size = item_path.stat().st_size
                except OSError:
                    file_size = 0
                bar = _progress_bar(index - 1, len(items))
                progress_text = (
                    f"{phase_label}\n\n"
                    f"📤 <b>Sending {index}/{len(items)}</b>\n"
                    f"{bar}\n"
                    f"📄 {item.label} — <b>{_human_size(file_size)}</b>\n"
                    f"<i>Interrupting will stop current batch.</i>"
                )
                await self._safe_edit(
                    status_message, 
                    progress_text
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
                        failed_paths={_path_key(Path(failed.path)) for failed in failed_items},
                    )

                # Throttle to respect Telegram limits
                await asyncio.sleep(self.send_delay_seconds)

            await self._safe_delete(status_message)
            done_text = (
                f"✅ <b>Done.</b>\n"
                f"Sent: <b>{sent_count}/{len(items)}</b>\n"
                f"Batch size: <b>{_human_size(total_bytes)}</b>"
            )
            if failed_items:
                done_text += f"\n⚠️ Failed: <b>{len(failed_items)}</b> file(s)."
            notice = await trigger_message.answer(done_text, parse_mode="HTML")
            await self._track_transient(state, notice.message_id)
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
                # Sprint 1: Renderers will own captions completely in Sprint 3
                await message.answer_document(
                    FSInputFile(Path(item.path))
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
