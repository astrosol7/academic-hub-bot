from __future__ import annotations

from aiogram.fsm.context import FSMContext

from academic_hub.domain.models import TelegramSession


async def load_session(state: FSMContext) -> TelegramSession:
    data = await state.get_data()
    raw = data.get("session") or {}
    return TelegramSession.model_validate(raw or {})


async def save_session(state: FSMContext, session: TelegramSession) -> None:
    await state.update_data(session=session.model_dump(mode="json"))
