import html
from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.bot.state import HubStates
from src.bot.session import TelegramSession, load_session, save_session
from src.bot.managers.tasks import task_registry
from src.core.config import load_config
from .common import HandlerDeps, navigate, track_presence

def setup_identity(router: Router, deps: HandlerDeps) -> None:
    
    @router.message(CommandStart())
    async def cmd_start(message: types.Message, state: FSMContext) -> None:
        await state.clear()
        session = TelegramSession(
            user_id=message.from_user.id if message.from_user else 0,
            chat_id=message.chat.id,
            message_thread_id=message.message_thread_id
        )
        task_registry.cancel(session.user_id)
        await save_session(state, session)
        await track_presence(session.user_id)

        config = load_config(require_token=False)
        if not config.orbit_bot_api_key:
            await message.answer(
                "⚠️ System misconfigured: missing ORBIT_BOT_API_KEY.\n"
                "Admin must set it in `.env` to enable identity verification."
            )
            await navigate(message, state, "nav:main", deps)
            return

        if config.required_group_id:
            try:
                member = await message.bot.get_chat_member(chat_id=config.required_group_id, user_id=session.user_id)
                if getattr(member, "status", None) in ("left", "kicked"):
                    link = config.required_group_invite_link or "Ask admin for the official invite link."
                    await message.answer(
                        "⛔ Access denied.\n\n"
                        "To use Academic Hub, you must join the official SIT community first.\n"
                        f"Join: {link}"
                    )
                    return
            except Exception:
                await message.answer(
                    "⚠️ Unable to verify community membership right now.\n"
                    "Please try again later."
                )
                return

        telegram_id = str(session.user_id)
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{config.backend_base_url}/api/v1/bot/link-status",
                    params={"institution_slug": config.institution_slug, "telegram_id": telegram_id},
                    headers={"X-Orbit-Bot-Key": config.orbit_bot_api_key},
                )
            if resp.status_code == 200 and resp.json().get("is_linked") and not resp.json().get("is_conflicted"):
                await navigate(message, state, "nav:main", deps)
                return
        except Exception:
            await navigate(message, state, "nav:main", deps)
            await message.answer(
                "⚠️ Verification service is currently offline.\n"
                "You can browse resources, but identity-required features may be limited."
            )
            return

        await state.set_state(HubStates.verify)
        await message.answer(
            "👋 <b>Welcome to Academic Hub</b>\n\n"
            "To activate your account, please enter your <b>SIT Student ID</b>.\n"
            "Example: <code>SIT-ST-2029-00004</code>\n\n"
            "Your Telegram numeric ID will be permanently bound to that School ID.\n"
            "If a conflict occurs, an admin must resolve it.",
            parse_mode="HTML",
        )

    @router.message(Command("menu"))
    async def cmd_menu(message: types.Message, state: FSMContext) -> None:
        session = await load_session(state)
        await track_presence(session.user_id)
        await navigate(message, state, "nav:main", deps)

    @router.message(Command("help"))
    async def cmd_help(message: types.Message, state: FSMContext) -> None:
        session = await load_session(state)
        await track_presence(session.user_id)
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="AI Assistant", callback_data="ai_help_more"),
            types.InlineKeyboardButton(text="Browse Menu", callback_data="nav:main")
        )
        
        await message.answer(
            "🚀 <b>Academic Hub Commands</b>\n\n"
            "Core:\n"
            "• <code>/menu</code> Browse resources\n"
            "• <code>/search &lt;keywords&gt;</code> Smart search\n\n"
            "Community:\n"
            "• <code>/ask</code> Ask a question\n"
            "• <code>/answer &lt;question_id&gt;</code> Answer a question\n"
            "• <code>/top</code> Top questions\n"
            "• <code>/my</code> Your questions\n\n"
            "Access:\n"
            "• You must be inside the official SIT community group to verify.\n\n"
            "💡 <b>Stuck?</b> Try the AI Assistant for help!\n\n"
            "Tip: Use short keywords like <code>calc week 2 notes</code>",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

    @router.message(Command("stop"))
    async def cmd_stop(message: types.Message, state: FSMContext) -> None:
        session = await load_session(state)
        await track_presence(session.user_id)
        
        confirm_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Yes, Sign Out", callback_data="stop:confirm"),
                    InlineKeyboardButton(text="❌ Cancel", callback_data="stop:cancel")
                ]
            ]
        )
        
        await message.answer(
            "🚪 <b>Sign Out Confirmation</b>\n\n"
            "Are you sure you want to sign out?\n"
            "• Your session will be cleared\n"
            "• Any ongoing tasks will be cancelled\n"
            "• You'll need to use /start to use the bot again",
            parse_mode="HTML",
            reply_markup=confirm_keyboard
        )

    @router.callback_query(lambda c: c.data and c.data.startswith("stop:"))
    async def handle_stop_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
        if not callback.data:
            return
        action = callback.data.split(":")[1]
        
        if action == "confirm":
            await state.clear()
            task_registry.cancel(callback.from_user.id)
            if callback.message and not isinstance(callback.message, types.InaccessibleMessage):
                await callback.message.edit_text(
                    "✅ <b>Signed Out Successfully</b>\n\n"
                    "Your session has been cleared.\n"
                    "Use /start to use the bot again.",
                    parse_mode="HTML"
                )
        elif action == "cancel":
            if callback.message and not isinstance(callback.message, types.InaccessibleMessage):
                await callback.message.edit_text(
                    "❌ <b>Sign Out Cancelled</b>\n\n"
                    "Your session remains active.",
                    parse_mode="HTML"
                )
        await callback.answer()
