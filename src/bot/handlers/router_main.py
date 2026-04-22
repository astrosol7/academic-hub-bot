import html
import logging
import asyncio

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from src.bot.state import HubStates
from src.bot.session import load_session, save_session
from src.core.models import SessionMode
from src.core.services import ButtonLabels
from src.core.intent import IntentDecision, classify_intent
from src.core.logging import LogCategory, log_event
from src.core.config import load_config
from .common import HandlerDeps, navigate, track_presence, _fire_telemetry

log = logging.getLogger(__name__)

def setup_fast_router(router: Router, deps: HandlerDeps) -> None:
    labels = ButtonLabels()
    config = load_config(require_token=False)

    async def _save_incident_API(user_id: int, category: str, description: str, course_id: str | None) -> None:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{config.backend_base_url}/api/v1/incidents",
                    json={
                        "telegram_id": str(user_id),
                        "category": category,
                        "description": description,
                        "course_id": course_id
                    }
                )
        except Exception as e:
            log.warning(f"Failed to save incident to API: {e}")

    async def handle_report_description(message: types.Message, state: FSMContext, text: str) -> None:
        if len(text.strip()) < 5:
            await message.answer("⚠️ <b>Report too short.</b> Please describe the issue with more details.", parse_mode="HTML")
            return

        session = await load_session(state)
        from src.bot.managers.tasks import task_registry
        task_registry.cancel(session.user_id, "delivery")
        
        log_event(
            log, 
            logging.INFO, 
            LogCategory.COMMAND,
            "Issue report submitted.",
            user_id=session.user_id,
            report_category=session.report_category,
            description=text,
            course_context=session.course_id,
            section_context=session.section
        )

        admin_id = config.admin_telegram_id
        if not admin_id:
            await message.answer("✅ <b>Report received.</b> Thank you for helping us improve!", parse_mode="HTML")
            await navigate(message, state, "nav:main", deps)
            return
        
        course_slug = html.escape(session.course_id or "General")
        safe_cat = html.escape(session.report_category or "Unknown")
        safe_text = html.escape(text)
        
        report_text = (
            f"⚠️ <b>New Issue Reported [OPEN]</b>\n"
            f"<b>Category:</b> {safe_cat}\n"
            f"<b>Course:</b> {course_slug}\n"
            f"<b>User ID:</b> {session.user_id}\n\n"
            f"<b>Description:</b>\n<i>{safe_text}</i>"
        )
        
        try:
            if message.bot:
                await message.bot.send_message(
                    chat_id=admin_id,
                    text=report_text,
                    parse_mode="HTML"
                )
        except Exception as e:
            log.warning(f"Failed to forward report to admin {admin_id}: {e}")
        
        asyncio.create_task(_save_incident_API(
            session.user_id, 
            session.report_category or "Other", 
            text, 
            session.course_id
        ))
        
        await message.answer("✅ <b>Report received.</b> Thank you for helping us improve!", parse_mode="HTML")
        await navigate(message, state, "nav:main", deps)

    async def handle_suggestion(message: types.Message, state: FSMContext, text: str) -> None:
        if len(text.strip()) < 5:
            await message.answer("⚠️ <b>Suggestion too short.</b> Please describe the resource you'd like us to add.", parse_mode="HTML")
            return

        session = await load_session(state)
        from src.bot.managers.tasks import task_registry
        task_registry.cancel(session.user_id, "delivery")

        log_event(
            log,
            logging.INFO,
            LogCategory.USER_SUGGESTION,
            "Content suggestion submitted.",
            user_id=session.user_id,
            description=text,
            course_context=session.course_id,
        )

        admin_id = config.admin_telegram_id
        if not admin_id:
            await message.answer("✅ <b>Suggestion received.</b> We'll review it and add it if valid. Thank you!", parse_mode="HTML")
            await navigate(message, state, "nav:main", deps)
            return

        safe_text = html.escape(text)
        suggestion_text = (
            f"💡 <b>New Content Suggestion</b>\n"
            f"<b>User ID:</b> {session.user_id}\n\n"
            f"<b>Suggestion:</b>\n<i>{safe_text}</i>"
        )

        try:
            if message.bot:
                await message.bot.send_message(
                    chat_id=admin_id,
                    text=suggestion_text,
                    parse_mode="HTML"
                )
        except Exception as e:
            log.warning(f"Failed to forward suggestion to admin {admin_id}: {e}")

        await message.answer("✅ <b>Suggestion received.</b> We'll review it and add it if valid. Thank you!", parse_mode="HTML")
        await navigate(message, state, "nav:main", deps)


    @router.message()
    async def fast_router(message: types.Message, state: FSMContext) -> None:
        try:
            # Handle attachments for reports
            current_state = await state.get_state()
            session = await load_session(state)
            
            if current_state == HubStates.report_description.state:
                text = ""
                if message.text:
                    text = message.text.strip()
                elif message.caption:
                    text = message.caption.strip()
                
                if message.photo:
                    text += f"\n[Attached Photo ID: {message.photo[-1].file_id}]"
                elif message.document:
                    text += f"\n[Attached Document: {message.document.file_name} ({message.document.file_id})]"
                    
                if not text.strip():
                    await message.answer("⚠️ Please describe the issue or add a caption to your attachment.")
                    return
                await handle_report_description(message, state, text)
                return

            if not message.text:
                return

            text = message.text.strip()
            
            if message.message_thread_id != session.message_thread_id:
                session = session.model_copy(update={"message_thread_id": message.message_thread_id})
                await save_session(state, session)

            current_state = await state.get_state()

            # Verification Mode
            if current_state == HubStates.verify.state:
                school_id = text.strip()
                telegram_id = str(session.user_id)
                try:
                    import httpx
                    async with httpx.AsyncClient(timeout=8.0) as client:
                        resp = await client.post(
                            f"{config.backend_base_url}/api/v1/bot/bind",
                            headers={"X-Orbit-Bot-Key": config.orbit_bot_api_key},
                            json={
                                "institution_slug": config.institution_slug,
                                "telegram_id": telegram_id,
                                "school_id": school_id,
                            },
                        )
                    if resp.status_code == 200:
                        data = resp.json()
                        name = data.get("student_name") or "Student"
                        await message.answer(f"✅ Verified. Welcome, <b>{html.escape(name)}</b>.", parse_mode="HTML")
                        await navigate(message, state, "nav:main", deps)
                    elif resp.status_code == 404:
                        await message.answer("❌ Student ID not found. Please re-check and try again.")
                    elif resp.status_code == 409:
                        await message.answer(
                            "⚠️ Conflict detected.\n"
                            "This School ID (or this Telegram account) is already linked elsewhere.\n"
                            "An admin must resolve this in the dashboard."
                        )
                    else:
                        await message.answer("⚠️ Verification failed. Please try again in a moment.")
                except Exception:
                    await message.answer("⚠️ Verification service unreachable. Please try again later.")
                return

            # Q&A Mode
            if current_state == HubStates.ask_title.state:
                title = text.strip()
                if len(title) < 4:
                    await message.answer("Title too short. Please send a clearer title (4+ chars).")
                    return
                await state.update_data(ask_title=title)
                await state.set_state(HubStates.ask_body)
                await message.answer("Now send the <b>details</b> (what you tried, what you need).", parse_mode="HTML")
                return

            if current_state == HubStates.ask_body.state:
                data = await state.get_data()
                title = (data.get("ask_title") or "").strip()
                body = text.strip()
                if len(body) < 4:
                    await message.answer("Body too short. Please add more detail.")
                    return
                # Inline function for create question since QA deps are in qa.py
                async def _qa_create_question(user_id, title, body):
                    if not config.orbit_bot_api_key: return None
                    try:
                        import httpx
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            resp = await client.post(
                                f"{config.backend_base_url}/api/v1/qa/questions",
                                headers={"X-Orbit-Bot-Key": config.orbit_bot_api_key},
                                json={"institution_slug": config.institution_slug, "telegram_id": str(user_id), "title": title, "body": body}
                            )
                        if resp.status_code == 200: return resp.json()
                    except Exception:
                        pass
                    return None
                
                created = await _qa_create_question(session.user_id, title=title, body=body)
                await state.clear()
                if not created:
                    await message.answer(
                        "⚠️ Failed to post question.\n"
                        "Make sure you are verified first (/start), then try again."
                    )
                    return
                qid = created.get("id")
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                await message.answer(
                    f"✅ Question posted.\n<b>ID:</b> <code>{qid}</code>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="👍 Upvote", callback_data=f"qa:vote:q:{qid}:+1"), InlineKeyboardButton(text="👎 Downvote", callback_data=f"qa:vote:q:{qid}:-1")],
                        [InlineKeyboardButton(text="✍️ Answer", callback_data=f"qa:answer:{qid}")]
                    ])
                )
                return

            if current_state == HubStates.answer_body.state:
                data = await state.get_data()
                qid = (data.get("answer_qid") or "").strip()
                if not qid:
                    await message.answer("Missing question id. Use /answer <question_id>.")
                    await state.clear()
                    return
                
                async def _qa_create_answer(user_id, qid, body):
                    if not config.orbit_bot_api_key: return False
                    try:
                        import httpx
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            resp = await client.post(
                                f"{config.backend_base_url}/api/v1/qa/answers",
                                headers={"X-Orbit-Bot-Key": config.orbit_bot_api_key},
                                json={"institution_slug": config.institution_slug, "telegram_id": str(user_id), "question_id": qid, "body": body}
                            )
                        if resp.status_code == 200: return True
                    except Exception:
                        pass
                    return False

                ok = await _qa_create_answer(session.user_id, qid, text.strip())
                await state.clear()
                await message.answer("✅ Answer posted." if ok else "⚠️ Failed to post answer (are you verified?).")
                return
            
            if text in (labels.back, labels.main_menu, labels.exit_search):
                await navigate(message, state, "nav:back" if text == labels.back else "nav:main", deps)
                return

            if text.startswith("📍 Continue:"):
                resume_target = getattr(session, "resume_target", None)
                if resume_target:
                    _, action = resume_target
                    await navigate(message, state, action, deps)
                return

            if text == labels.browse:
                await navigate(message, state, "nav:resources", deps)
                return
            if text == labels.search:
                await navigate(message, state, "nav:search", deps)
                return
            if text == labels.voyager:
                await state.set_state(HubStates.voyager)
                from src.bot.keyboards import build_reply_keyboard
                keyboard = build_reply_keyboard(((labels.back,),))
                await message.answer("✨ <b>Voyager</b>\n\nI am Voyager, your continuous AI tutor. Ask me anything!\n<i>Type /exit or tap 🔙 Back to leave.</i>", reply_markup=keyboard, parse_mode="HTML")
                return
            if text == labels.search_resources:
                await navigate(message, state, "nav:search_scope:resources", deps)
                await message.answer("📚 Resource search selected. Type your query.")
                return
            if text == labels.search_community:
                await navigate(message, state, "nav:search_scope:community", deps)
                await message.answer("👥 Community search selected. Type your query.")
                return
            if text == labels.about:
                await navigate(message, state, "nav:about", deps)
                return
            if text == labels.report:
                await navigate(message, state, "nav:report", deps)
                return
            if text == labels.suggest:
                await navigate(message, state, "nav:suggest", deps)
                return
            if text == labels.retry and session.retry_request:
                await deps.handle_retry(message, state, session)
                return

            if session.mode == SessionMode.SEARCH:
                if text == labels.search_resources:
                    await navigate(message, state, "nav:search_scope:resources", deps)
                    await message.answer("📖 Resource search selected. Type your query.")
                    return
                if text == labels.search_community:
                    await navigate(message, state, "nav:search_scope:community", deps)
                    await message.answer("💬 Community search selected. Type your query.")
                    return
                
                if not session.search_target:
                    await message.answer("⚠️ <b>Choose search type first:</b>\n[📖 Resources] [💬 Community]", parse_mode="HTML")
                    return
                    
                if session.search_target == "community":
                    async def _qa_search_questions(q):
                        if not config.orbit_bot_api_key: return []
                        try:
                            import httpx
                            async with httpx.AsyncClient(timeout=10.0) as client:
                                resp = await client.get(
                                    f"{config.backend_base_url}/api/v1/qa/search",
                                    params={"institution_slug": config.institution_slug, "query": q, "limit": 8},
                                    headers={"X-Orbit-Bot-Key": config.orbit_bot_api_key}
                                )
                            if resp.status_code == 200: return resp.json()
                        except Exception:
                            pass
                        return []
                    hits = await _qa_search_questions(text)
                    if not hits:
                        await message.answer("No community matches yet. Try /ask to post your question.")
                        return
                    await message.answer("💬 <b>Community results</b>", parse_mode="HTML")
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    for hit in hits:
                        qid = hit.get("question_id")
                        title = html.escape(hit.get("title") or "")
                        score = float(hit.get("score") or 0.0)
                        await message.answer(
                            f"• <b>{title}</b>\n<code>{qid}</code>\nScore: {score:.2f}",
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(text="👍 Upvote", callback_data=f"qa:vote:q:{qid}:+1"), InlineKeyboardButton(text="👎 Downvote", callback_data=f"qa:vote:q:{qid}:-1")],
                                [InlineKeyboardButton(text="✍️ Answer", callback_data=f"qa:answer:{qid}")]
                            ])
                        )
                    return
                await deps.handle_search_mode(message, state, text)
                return

            # Voyager Chat Mode
            if current_state == HubStates.voyager.state:
                if text.lower() == "/exit" or text == labels.back:
                    await navigate(message, state, "nav:main", deps)
                    return
                from src.bot.handlers.ai import handle_voyager_message
                await handle_voyager_message(message, text, session.user_id, deps)
                return

            if session.mode == SessionMode.REPORT:
                if session.section == "report_1":
                    clean_text = text.lower()
                    cat_map = {
                        "missing file": "Missing file",
                        "wrong content": "Wrong content",
                        "unavailable": "Unavailable",
                        "other": "Other",
                    }
                    matched_cat = None
                    for k, v in cat_map.items():
                        if k in clean_text:
                            matched_cat = v
                            break
                    
                    if matched_cat:
                        await navigate(message, state, f"nav:report_category:{matched_cat}", deps)
                    else:
                        await message.answer("⚠️ Please choose a category from the menu.")
                    return
                elif session.section == "report_2" and session.report_category:
                    await handle_report_description(message, state, text)
                    return
                elif session.section == "suggest":
                    await handle_suggestion(message, state, text)
                    return

            if session.mode == SessionMode.BROWSE or session.mode == SessionMode.HOME:
                matched_button = False
                
                if session.level == "resources" and deps.repository.institution:
                    for q, label in deps.repository.institution.quarter_labels.items():
                        if text == label:
                            await navigate(message, state, f"nav:select_quarter:{q}", deps)
                            matched_button = True
                            break

                elif session.level == "quarter" and session.quarter is not None:
                    for course in deps.repository.list_courses(int(session.quarter)):
                        if text == course.title:
                            await navigate(message, state, f"nav:select_course:{course.id}", deps)
                            matched_button = True
                            break

                elif session.level == "course" and session.course_id:
                    course = deps.repository.get_course(session.course_id)
                    if course:
                        if text == labels.overview:
                            await navigate(message, state, "nav:overview", deps)
                            matched_button = True
                        elif text == labels.by_week:
                            await navigate(message, state, "nav:week_list", deps)
                            matched_button = True
                        elif text == labels.more_files:
                            await navigate(message, state, "nav:more_files", deps)
                            matched_button = True
                        else:
                            allowed = (*course.top_level_actions, *course.more_files_actions)
                            cat_slug = deps.find_category_slug(text, allowed)
                            if cat_slug:
                                await deps.handle_delivery(message, state, session.course_id, cat_slug)
                                matched_button = True

                        if not matched_button:
                            if session.section == "week_list":
                                if text.startswith("🗂 Week ") or text.lower().startswith("week "):
                                    num = text.split(" ")[-1]
                                    await navigate(message, state, f"nav:week_category:{num}", deps)
                                    matched_button = True
                                    
                            if session.section == "week_category" and session.week_number is not None:
                                cat_slug = deps.find_category_slug(text, course.week_actions)
                                if cat_slug:
                                    await deps.handle_delivery_week(message, state, session.course_id, session.week_number, cat_slug)
                                    matched_button = True

                if not matched_button:
                    decision, n_score, s_score = classify_intent(text)

                    if decision == IntentDecision.SEARCH:
                        updated = session.model_copy(update={"noise_count": 0})
                        await save_session(state, updated)
                        await deps.handle_search_mode(message, state, text)
                    else:
                        new_count = session.noise_count + 1
                        updated = session.model_copy(update={"noise_count": new_count})
                        await save_session(state, updated)
                        
                        if new_count >= 3:
                            updated = updated.model_copy(update={"noise_count": 0})
                            await save_session(state, updated)
                            await message.answer("💡 It seems you're having trouble. Please use the visible buttons or tap 🔍 Search first.")
                        else:
                            await message.answer(
                                "💡 Please use the buttons on screen.\n"
                                "If you want search, tap 🔍 Search first."
                            )
        except Exception as e:
            log.exception("event=fast_router_error detail=%s", e)
            await message.answer("⚠️ Internal error. Please try again.")
