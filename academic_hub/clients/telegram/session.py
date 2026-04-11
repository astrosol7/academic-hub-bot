from __future__ import annotations

import logging

from aiogram.fsm.context import FSMContext
from pydantic import ValidationError

from academic_hub.domain.models import TelegramSession


log = logging.getLogger(__name__)


async def load_session(state: FSMContext) -> TelegramSession:
    data = await state.get_data()
    raw = data.get("session") or {}
    if not isinstance(raw, dict):
        session = TelegramSession()
        await save_session(state, session)
        return session
    try:
        return TelegramSession.model_validate(raw)
    except ValidationError as exc:
        log.warning("event=session_reset detail=%s", exc)
        session = TelegramSession()
        await save_session(state, session)
        return session


async def save_session(state: FSMContext, session: TelegramSession) -> None:
    await state.update_data(session=session.model_dump(mode="json"))
