import logging
from datetime import datetime
from aiogram import Router, types

from src.core.ai_helper import get_ai_helper
from src.bot.state import HubStates
from .common import HandlerDeps, HubStates
from src.core.config import load_config

log = logging.getLogger(__name__)
ai_helper = get_ai_helper()

_user_search_attempts = {}
_user_last_search = {}

# Voyager Chat Memory
_voyager_sessions: dict[int, list[dict]] = {}
_voyager_last_active: dict[int, datetime] = {}

async def handle_voyager_message(message: types.Message, text: str, user_id: int, deps: HandlerDeps) -> None:
    """Handle continuous Voyager chat mode with RAG."""
    config = load_config(require_token=False)
    now = datetime.now()
    
    # Session timeout (30 mins)
    last_active = _voyager_last_active.get(user_id)
    if last_active and (now - last_active).total_seconds() > 1800:
        _voyager_sessions[user_id] = []
        
    _voyager_last_active[user_id] = now
    
    if user_id not in _voyager_sessions or not _voyager_sessions[user_id]:
        system_prompt = (
            "You are Voyager, an elite, highly intelligent AI tutor for the SIT Academic Hub. "
            "Your main role is to help students with their studies, provide deep insights, and assist with system navigation. "
            "IMPORTANT: DO NOT use markdown like asterisks (*), hashes (#), or backticks (`) for formatting. "
            "Use ONLY Telegram HTML tags (<b>, <i>, <code>, <u>, <s>). "
            f"You have deep knowledge of SIT ({config.institution_website}) and this database, but DO NOT discuss administrative backend details. "
            "Keep responses concise, engaging, and professional."
        )
        _voyager_sessions[user_id] = [
            {"role": "system", "content": system_prompt}
        ]
        
    # Semantic Search RAG Injection
    try:
        search_result = await deps.search.search(text, user_id, "resources")
        if search_result.get("status") == "success" and search_result.get("results"):
            top_results = search_result["results"][:3]
            file_context = "System Database retrieved the following relevant files for the user's query:\n"
            for r in top_results:
                file_context += f"- Title: {r.get('title')}, Course: {r.get('course_title')}, ID: {r.get('id')}\n"
            file_context += "If the user is asking for these materials, summarize them and present the file IDs."
            
            # Inject transient system message
            _voyager_sessions[user_id].append({"role": "system", "content": file_context})
    except Exception as e:
        log.warning(f"Voyager RAG search failed: {e}")

    _voyager_sessions[user_id].append({"role": "user", "content": text})
    
    # Keep history manageable (last 10 turns = 21 messages max)
    if len(_voyager_sessions[user_id]) > 21:
        _voyager_sessions[user_id] = [_voyager_sessions[user_id][0]] + _voyager_sessions[user_id][-20:]
        
    sent_msg = await message.answer("✨ <i>Voyager is thinking...</i>", parse_mode="HTML")
    
    full_response = ""
    last_update = now
    
    try:
        async for chunk in ai_helper.stream_chat(_voyager_sessions[user_id]):
            # Clean common markdown astrix before streaming
            clean_chunk = chunk.replace("**", "<b>").replace("*", "")
            full_response += clean_chunk
            if (datetime.now() - last_update).total_seconds() > 1.5:
                try:
                    # Fix unclosed bold tags for telegram streaming safety
                    safe_response = full_response
                    if safe_response.count("<b>") > safe_response.count("</b>"):
                        safe_response += "</b>"
                    await sent_msg.edit_text(f"✨ <b>Voyager</b>\n\n{safe_response} ▌", parse_mode="HTML")
                    last_update = datetime.now()
                except Exception:
                    pass
                    
        # Final cleanup for unclosed tags
        if full_response.count("<b>") > full_response.count("</b>"):
            full_response += "</b>"
            
        await sent_msg.edit_text(f"✨ <b>Voyager</b>\n\n{full_response}", parse_mode="HTML")
        
        # Remove the transient system RAG message from history to save tokens
        if _voyager_sessions[user_id][-2]["role"] == "system":
            _voyager_sessions[user_id].pop(-2)
            
        _voyager_sessions[user_id].append({"role": "assistant", "content": full_response})
        
    except Exception as e:
        log.error(f"Voyager streaming failed: {e}")
        await sent_msg.edit_text("⚠️ <i>Voyager encountered an anomaly. Please try again.</i>", parse_mode="HTML")


def setup_ai(router: Router, deps: HandlerDeps) -> None:
    
    async def _offer_ai_help(message: types.Message, reason: str, context: str) -> None:
        """Offer AI help with Premium Formatting"""
        try:
            user_id = message.from_user.id if message.from_user else 0
            thread_id = message.message_thread_id
            
            prompt_context = ""
            if reason == "search_struggle":
                prompt_context = f"User searched: \"{context}\" but got no results. Suggest ONE short improvement."
            elif reason == "navigation_confusion":
                prompt_context = f"User seems lost. Context: {context}. Give ONE simple direction."
            elif reason == "general_help":
                prompt_context = f"User asked: \"{context}\". Give a quick, helpful answer."
            else:
                prompt_context = f"User seems frustrated. Situation: {reason}. Send one encouraging sentence."

            messages = [
                {"role": "system", "content": ai_helper.system_prompt},
                {"role": "user", "content": prompt_context}
            ]

            sent_msg = await message.answer(
                "<i>Thinking...</i>",
                parse_mode="HTML",
                message_thread_id=thread_id
            )

            full_response = ""
            last_update_time = datetime.now()
            
            async for chunk in ai_helper.stream_chat(messages):
                full_response += chunk
                
                if (datetime.now() - last_update_time).total_seconds() > 1.5:
                    try:
                        await sent_msg.edit_text(
                            f"{full_response} ▌",
                            parse_mode="HTML"
                        )
                        last_update_time = datetime.now()
                    except Exception:
                        pass 

            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.row(
                types.InlineKeyboardButton(text="More Help", callback_data="ai_help_more"),
                types.InlineKeyboardButton(text="Thanks!", callback_data="ai_help_dismiss")
            )
            builder.row(
                types.InlineKeyboardButton(text="Search Again", callback_data="new_search"),
                types.InlineKeyboardButton(text="Main Menu", callback_data="main_menu")
            )

            await sent_msg.edit_text(
                full_response,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            
            _user_search_attempts[user_id] = 0
            log.info(f"AI helper streamed response to user {user_id}")

        except Exception as e:
            log.error(f"AI streaming failed: {e}")
            await message.answer(
                "🤖 <b>Orbit Assistant</b>\n\nTry different keywords or use the menu. You got this!",
                parse_mode="HTML",
                message_thread_id=message.message_thread_id
            )

    @router.callback_query(lambda c: c.data and c.data.startswith("ai_help_"))
    async def on_ai_help(query: types.CallbackQuery) -> None:
        if not query.data:
            return
        action = query.data.split("_", 2)[2]
        
        if action == "more":
            await query.answer("Getting more help...")
            if query.message and not isinstance(query.message, types.InaccessibleMessage):
                await _offer_ai_help(query.message, "general_help", "User requested more assistance")
        elif action == "dismiss":
            await query.answer("You're welcome!")
            if query.message and not isinstance(query.message, types.InaccessibleMessage):
                await query.message.edit_text(
                    "🤖 <b>Orbit Assistant</b>\n\n"
                    "Glad I could help! I'm here if you need more assistance.",
                    parse_mode="HTML"
                )

    deps._offer_ai_help = _offer_ai_help
    deps._user_search_attempts = _user_search_attempts
