import html
import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.bot.state import HubStates
from src.bot.session import load_session
from src.core.config import load_config
from .common import HandlerDeps, track_presence

log = logging.getLogger(__name__)

def setup_qa(router: Router, deps: HandlerDeps) -> None:
    config = load_config(require_token=False)

    def _qa_inline(question_id: str) -> InlineKeyboardMarkup:
        qid = str(question_id)
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👍 Upvote", callback_data=f"qa:vote:q:{qid}:+1"),
                    InlineKeyboardButton(text="👎 Downvote", callback_data=f"qa:vote:q:{qid}:-1"),
                ],
                [InlineKeyboardButton(text="✍️ Answer", callback_data=f"qa:answer:{qid}")],
            ]
        )

    async def _qa_list_questions() -> list[dict]:
        if not config.orbit_bot_api_key:
            return []
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{config.backend_base_url}/api/v1/qa/questions",
                    params={"institution_slug": config.institution_slug, "limit": 10},
                    headers={"X-Orbit-Bot-Key": config.orbit_bot_api_key},
                )
            if resp.status_code == 200:
                return resp.json()
            log.warning("event=qa_list_questions_failed status=%s body=%s", resp.status_code, resp.text[:200])
            return []
        except Exception as e:
            log.warning("event=qa_list_questions_error detail=%s", e)
            return []

    async def _qa_vote(user_id: int, question_id: str | None, answer_id: str | None, value: int) -> bool:
        if not config.orbit_bot_api_key:
            return False
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{config.backend_base_url}/api/v1/qa/vote",
                    headers={"X-Orbit-Bot-Key": config.orbit_bot_api_key},
                    json={
                        "institution_slug": config.institution_slug,
                        "telegram_id": str(user_id),
                        "question_id": question_id,
                        "answer_id": answer_id,
                        "value": int(value),
                    },
                )
            if resp.status_code == 200:
                return True
            log.warning("event=qa_vote_failed status=%s body=%s", resp.status_code, resp.text[:200])
            return False
        except Exception as e:
            log.warning("event=qa_vote_error detail=%s", e)
            return False

    @router.message(Command("ask"))
    async def cmd_ask(message: types.Message, state: FSMContext) -> None:
        session = await load_session(state)
        await track_presence(session.user_id)
        await state.set_state(HubStates.ask_title)
        await message.answer("✍️ Send a short <b>title</b> for your question.", parse_mode="HTML")

    @router.message(Command("top"))
    async def cmd_top(message: types.Message, state: FSMContext) -> None:
        session = await load_session(state)
        await track_presence(session.user_id)
        items = await _qa_list_questions()
        if not items:
            await message.answer("No questions yet. Be the first: /ask")
            return
        for q in items:
            qid = q.get("id")
            title = html.escape(q.get("title") or "")
            score = q.get("score", 0)
            answers = q.get("answers_count", 0)
            await message.answer(
                f"🔥 <b>{title}</b>\n"
                f"<b>ID:</b> <code>{qid}</code>\n"
                f"<b>Score:</b> {score} • <b>Answers:</b> {answers}",
                parse_mode="HTML",
                reply_markup=_qa_inline(str(qid)),
            )

    @router.message(Command("my"))
    async def cmd_my(message: types.Message, state: FSMContext) -> None:
        session = await load_session(state)
        await track_presence(session.user_id)
        await cmd_top(message, state)

    @router.message(Command("answer"))
    async def cmd_answer(message: types.Message, state: FSMContext) -> None:
        session = await load_session(state)
        await track_presence(session.user_id)
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("Usage: /answer <question_id>")
            return
        await state.update_data(answer_qid=parts[1].strip())
        await state.set_state(HubStates.answer_body)
        await message.answer("✍️ Send your answer text.")

    @router.callback_query(lambda c: c.data and c.data.startswith("qa:vote:"))
    async def on_qa_vote(query: types.CallbackQuery, state: FSMContext) -> None:
        if not query.data:
            return
        parts = query.data.split(":")
        if len(parts) == 5:
            obj_type = parts[2]
            obj_id = parts[3]
            value = int(parts[4])
            ok = await _qa_vote(query.from_user.id, obj_id if obj_type == "q" else None, obj_id if obj_type == "a" else None, value)
            await query.answer("Voted" if ok else "Vote failed", show_alert=not ok)

    @router.callback_query(lambda c: c.data and c.data.startswith("qa:answer:"))
    async def on_qa_answer(query: types.CallbackQuery, state: FSMContext) -> None:
        if not query.data:
            return
        qid = query.data.split(":", 2)[2]
        await state.update_data(answer_qid=qid)
        await state.set_state(HubStates.answer_body)
        await query.answer()
        if query.message and not isinstance(query.message, types.InaccessibleMessage):
            await query.message.answer(f"Reply with your answer for:\n<code>{qid}</code>", parse_mode="HTML")
