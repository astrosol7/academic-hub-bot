import html
import logging
import asyncio
from datetime import datetime

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.bot.session import load_session
from src.core.logging import LogCategory, log_event
from src.core.config import load_config
from .common import HandlerDeps, navigate, track_presence, HubStates, _fire_telemetry

log = logging.getLogger(__name__)

def setup_search(router: Router, deps: HandlerDeps) -> None:
    config = load_config(require_token=False)

    async def _display_search_results(message: types.Message, results: list, query: str) -> None:
        if not results:
            return
            
        response_text = f"🔍 <b>Found {len(results)} results for:</b> <code>{html.escape(query)}</code>\n\n"
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        for i, result in enumerate(results[:5]):
            title = result.get('title', 'Unknown Title')[:40]
            description = result.get('description', '')[:60]
            course_title = result.get('course_title', 'Unknown Course')
            match_type = result.get('match_type', 'unknown')
            score = result.get('score', 0)
            
            if match_type == "exact_title":
                emoji = "🎯"
            elif match_type == "fuzzy" and score > 0.7:
                emoji = "✨"
            elif match_type == "category":
                emoji = "📁"
            else:
                emoji = "📄"
            
            button_text = f"{emoji} {title}"
            if description:
                button_text += f"\n{description}"
            button_text += f"\n📚 {course_title}"
            
            result_data = f"{result.get('id')}|{result.get('course_id')}|{match_type}"
            
            builder.row(
                types.InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"search_result:{result_data}"
                )
            )
        
        if len(results) > 5:
            builder.row(
                types.InlineKeyboardButton(
                    text="📄 Show more results...",
                    callback_data=f"more_search_results:{query}:{5}"
                )
            )
        
        builder.row(
            types.InlineKeyboardButton(text="🔍 New Search", callback_data="new_search"),
            types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
        )
        
        await message.answer(
            response_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    
    async def _handle_no_results(message: types.Message, safe_msg: str, suggestions: list[str], user_id: int) -> None:
        _user_search_attempts = getattr(deps, "_user_search_attempts", {})
        
        _user_search_attempts[user_id] = _user_search_attempts.get(user_id, 0) + 1
        
        response_text = f"📭 <b>Search Results</b>\n\n{safe_msg}"
        
        if suggestions:
            response_text += "\n\n💡 <b>Suggestions:</b>\n"
            response_text += "\n".join(f"• {html.escape(s)}" for s in suggestions[:3])
        
        keyboard = None
        
        if suggestions:
            try:
                from src.bot.keyboards import build_reply_keyboard
                from src.core.services import ButtonLabels
                labels = ButtonLabels()
                suggestion_rows = [tuple(suggestions[:4])]
                suggestion_rows.append((labels.back, labels.main_menu))
                keyboard = build_reply_keyboard(tuple(suggestion_rows), placeholder="Try a suggestion...")
            except Exception as e:
                log.warning(f"Failed to build suggestion keyboard: {e}")
        
        await message.answer(
            response_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        if _user_search_attempts[user_id] >= 3:
            if hasattr(deps, "_offer_ai_help"):
                await deps._offer_ai_help(message, "search_struggle", safe_msg)

    async def handle_search_mode(message: types.Message, state: FSMContext, text: str) -> None:
        session = await load_session(state)
        from src.bot.managers.tasks import task_registry
        task_registry.cancel(session.user_id, "delivery")

        engine_used = "fs_fallback_hit"
        suggestions: list[str] = []
        search_results = []
        
        try:
            search_result = await deps.search.search(text, session.user_id, session.search_target or "resources")
            
            if search_result["status"] == "error":
                log.warning(f"Search service error: {search_result.get('message', 'Unknown error')}")
            else:
                search_results = search_result.get("results", [])
                suggestions = search_result.get("suggestions", [])
                engine_used = search_result.get("engine", "filesystem")
                
                if search_results:
                    log_event(
                        log, logging.INFO, LogCategory.SEARCH_DB_HIT,
                        "Search resolved via enhanced service.",
                        user_id=session.user_id, query=text,
                        engine=engine_used, result_count=len(search_results)
                    )
                    await _display_search_results(message, search_results, text)
                    return
                
        except Exception as e:
            log.error(f"Enhanced search failed, falling back: {e}")
            
        try:
            fallback_results = []
            query_lower = text.lower()
            for course in deps.repository.list_all_courses():
                course_resources = deps.repository.get_course_resources(course.id)
                for resource in course_resources:
                    if query_lower in resource.title.lower():
                        fallback_results.append({
                            'id': str(resource.id),
                            'title': resource.title,
                            'course_id': course.id,
                            'course_title': course.title,
                            'category': getattr(resource, 'category_slug', 'unknown'),
                            'score': 0.7,
                            'match_type': 'title'
                        })
            
            if fallback_results:
                log_event(
                    log, logging.INFO, LogCategory.SEARCH_FS_FALLBACK,
                    "Search resolved via filesystem fallback.",
                    user_id=session.user_id, query=text,
                    result_count=len(fallback_results)
                )
                await _display_search_results(message, fallback_results[:10], text)
            else:
                log_event(
                    log, logging.WARNING, LogCategory.SEARCH_FAILED,
                    "Search returned 0 results from all engines.",
                    user_id=session.user_id, query=text
                )
                safe_msg = f"No results found for <code>{html.escape(text)}</code>"
                await _handle_no_results(message, safe_msg, suggestions, session.user_id)
                
        except Exception as e:
            log.error(f"Fallback search also failed: {e}")
            await message.answer(
                "⚠️ <b>System Database is currently unreachable.</b>\nTransferring you to Voyager AI for assistance...",
                parse_mode="HTML"
            )
            await state.set_state(HubStates.voyager)
            
            from src.bot.handlers.ai import _voyager_sessions, _voyager_last_active
            
            user_id = session.user_id
            _voyager_last_active[user_id] = datetime.now()
            
            system_prompt = (
                "You are Voyager, an elite, highly intelligent AI tutor for the SIT Academic Hub. "
                "Your main role is to help students with their studies, provide deep insights, and assist with system navigation. "
                "IMPORTANT: DO NOT use markdown like asterisks (*), hashes (#), or backticks (`) for formatting. "
                "Use ONLY Telegram HTML tags (<b>, <i>, <code>, <u>, <s>). "
                f"You have deep knowledge of SIT ({config.institution_website}) and this database, but DO NOT discuss administrative backend details. "
                "Keep responses concise, engaging, and professional."
            )
            
            if user_id not in _voyager_sessions or not _voyager_sessions[user_id]:
                _voyager_sessions[user_id] = [{"role": "system", "content": system_prompt}]
                
            _voyager_sessions[user_id].append({
                "role": "system", 
                "content": f"The system database just went down while the user was searching. Apologize briefly, then offer to help them using your general knowledge about SIT ({config.institution_website}) or other academic topics."
            })
            
            from src.bot.keyboards import build_reply_keyboard
            from src.core.services import ButtonLabels
            keyboard = build_reply_keyboard(((ButtonLabels().back,),))
            await message.answer("✨ <b>Voyager</b>\n\nI noticed the database is having trouble. How can I help you while we wait?\n<i>Type /exit or tap 🔙 Back to leave.</i>", reply_markup=keyboard, parse_mode="HTML")
            return

        try:
            from .common import _fire_telemetry
            asyncio.create_task(_fire_telemetry(
                session.user_id, "search",
                {"query": text, "engine": engine_used, "matched": bool(search_results)}
            ))
        except Exception:
            pass
            
    deps.handle_search_mode = handle_search_mode

    @router.callback_query(lambda c: c.data and c.data.startswith("search_result:"))
    async def on_search_result(query: types.CallbackQuery) -> None:
        if not query.data:
            return
        result_data = query.data.split(":", 1)[1]
        parts = result_data.split("|")
        if len(parts) >= 3:
            resource_id, course_id, match_type = parts[0], parts[1], parts[2]
            
            await query.answer("📂 Loading resource...")
            try:
                if query.message and not isinstance(query.message, types.InaccessibleMessage):
                    await query.message.answer(
                        f"📂 <b>Resource Selected</b>\n\n"
                        f"🆔 ID: <code>{resource_id}</code>\n"
                        f"📚 Course: {course_id}\n"
                        f"🏷️ Type: {match_type}\n\n"
                        f"⬇️ Preparing download...",
                        parse_mode="HTML"
                    )
                    
                    await asyncio.sleep(1)
                    await query.message.answer(
                        "✅ <b>Download Ready!</b>\n\n"
                        "📦 Resource package is being prepared for delivery.\n"
                        "You will receive the files shortly.",
                        parse_mode="HTML"
                    )
            except Exception as e:
                log.error(f"Search result selection failed: {e}")
                if query.message and not isinstance(query.message, types.InaccessibleMessage):
                    await query.message.answer(
                        "❌ <b>Failed to load resource</b>\n\nPlease try again later.",
                        parse_mode="HTML"
                    )

    @router.callback_query(lambda c: c.data and c.data.startswith("more_search_results:"))
    async def on_more_search_results(query: types.CallbackQuery) -> None:
        if not query.data:
            return
        query_parts = query.data.split(":", 2)
        if len(query_parts) >= 3:
            search_query = query_parts[1]
            offset = int(query_parts[2])
            
            await query.answer("🔍 Loading more results...")
            
            try:
                search_result = await deps.search.search(search_query, query.from_user.id, "resources")
                
                if search_result["status"] == "success" and query.message and not isinstance(query.message, types.InaccessibleMessage):
                    results = search_result.get("results", [])[offset:offset+5]
                    
                    if results:
                        response_text = f"🔍 <b>More results for:</b> <code>{html.escape(search_query)}</code>\n\n"
                        
                        from aiogram.utils.keyboard import InlineKeyboardBuilder
                        builder = InlineKeyboardBuilder()
                        
                        for result in results:
                            title = result.get('title', 'Unknown Title')[:40]
                            course_title = result.get('course_title', 'Unknown Course')
                            match_type = result.get('match_type', 'unknown')
                            
                            emoji = "🎯" if match_type == "exact_title" else "✨" if match_type == "fuzzy" else "📄"
                            button_text = f"{emoji} {title}\n📚 {course_title}"
                            
                            result_data = f"{result.get('id')}|{result.get('course_id')}|{match_type}"
                            
                            builder.row(
                                types.InlineKeyboardButton(
                                    text=button_text,
                                    callback_data=f"search_result:{result_data}"
                                )
                            )
                        
                        if len(search_result.get("results", [])) > offset + 5:
                            builder.row(
                                types.InlineKeyboardButton(
                                    text="📄 Show more results...",
                                    callback_data=f"more_search_results:{search_query}:{offset+5}"
                                )
                            )
                        
                        builder.row(
                            types.InlineKeyboardButton(text="🔍 New Search", callback_data="new_search"),
                            types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
                        )
                        
                        await query.message.answer(
                            response_text,
                            reply_markup=builder.as_markup(),
                            parse_mode="HTML"
                        )
                    else:
                        await query.message.answer(
                            "📭 <b>No more results</b>\n\nYou've seen all available results.",
                            parse_mode="HTML"
                        )
                elif query.message and not isinstance(query.message, types.InaccessibleMessage):
                    await query.message.answer(
                        "⚠️ <b>Failed to load more results</b>\n\nPlease try again.",
                        parse_mode="HTML"
                    )
                    
            except Exception as e:
                log.error(f"More search results failed: {e}")
                if query.message and not isinstance(query.message, types.InaccessibleMessage):
                    await query.message.answer(
                        "❌ <b>Error loading results</b>\n\nPlease try again later.",
                        parse_mode="HTML"
                    )

    @router.callback_query(lambda c: c.data in ["new_search", "main_menu"])
    async def on_nav_buttons(query: types.CallbackQuery, state: FSMContext) -> None:
        await query.answer()
        if query.message and not isinstance(query.message, types.InaccessibleMessage):
            if query.data == "new_search":
                await navigate(query.message, state, "nav:search", deps)
            else:
                await navigate(query.message, state, "nav:main", deps)
