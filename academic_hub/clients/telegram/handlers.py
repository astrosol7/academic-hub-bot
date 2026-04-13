from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any
import html

from aiogram import Dispatcher, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from academic_hub.clients.telegram.delivery import DeliveryCoordinator
from academic_hub.clients.telegram.managers.tasks import task_registry
from academic_hub.clients.telegram.renderer import TelegramRenderer
from academic_hub.clients.telegram.session import load_session, save_session
from academic_hub.clients.telegram.state import HubStates
from academic_hub.domain.models import DeliveryScope, RetryRequest, SessionMode, TelegramSession
from academic_hub.domain.services import ButtonLabels, DeliveryService, NavigationService, SearchService
from academic_hub.infrastructure.repository import FilesystemContentRepository
from academic_hub.utils.intent import IntentDecision, classify_intent
from academic_hub.utils.logging import LogCategory, log_event

log = logging.getLogger(__name__)

EMPTY_MESSAGE = "📭 Nothing here yet. Check back later or choose another section."

# Map FSM level/section → aiogram State
_STATE_MAP = {
    "home": HubStates.home,
    "resources": HubStates.resources,
    "quarter": HubStates.quarter,
    "course": HubStates.course,
    "about": HubStates.about,
    "report_1": HubStates.report,
    "report_2": HubStates.report_description,
    "search_intro": HubStates.search,
    "suggest": HubStates.suggest,
    "more_files": HubStates.more_files,
    "week_list": HubStates.week_list,
    "week_category": HubStates.week_category,
}


def _fsm_state_for(session: TelegramSession) -> Any:
    """Derive the correct aiogram FSM state from the session."""
    state = _STATE_MAP.get(str(session.section))
    if state:
        return state
    return _STATE_MAP.get(str(session.level), HubStates.home)


def _validate_session(session: TelegramSession, repository: FilesystemContentRepository) -> TelegramSession:
    """State Reconciliation: Verify UI will not drift from missing context."""
    if session.level == "course":
        if not session.course_id or not repository.get_course(session.course_id):
            return session.model_copy(update={
                "level": "home", "section": "home", "course_id": None, "mode": SessionMode.HOME
            })
            
    if session.section == "week_category":
        if not session.week_number:
            return session.model_copy(update={
                "level": "course", "section": "week_list"
            })
            
    return session


def register_handlers(
    dispatcher: Dispatcher,
    repository: FilesystemContentRepository,
    navigation: NavigationService,
    delivery: DeliveryService,
    search: SearchService,
    renderer: TelegramRenderer,
    coordinator: DeliveryCoordinator,
) -> None:
    router = Router()
    labels = ButtonLabels()

    # ── HELPERS ──────────────────────────────────────────────────────

    def find_category_slug(label: str, allowed_actions: tuple[str, ...]) -> str | None:
        """Map a UI label (with or without icon) back to a category slug."""
        for action in allowed_actions:
            category = repository.categories.get(action)
            if category:
                ui_label = f"{category.icon} {category.label}".strip() if category.icon else category.label
                if category.label == label or ui_label == label:
                    return action
        return None

    # ── CORE NAVIGATION (SINGLE PATH) ───────────────────────────────

    async def navigate(message: types.Message, state: FSMContext, action: str) -> None:
        """THE transition function. ALL navigation goes through here."""
        session = await load_session(state)

        # Mutually exclusive cancellation (nav breaks delivery)
        task_registry.cancel(session.user_id, "delivery")
        if session.delivery_active:
            await coordinator.cancel_active_delivery(state)

        # Transition logic
        updated = navigation.transition(session, action)
        # Advance Execution Token
        updated = updated.model_copy(update={"execution_id": updated.execution_id + 1})
        # Validate State Integrity
        updated = _validate_session(updated, repository)
        
        # Set FSM state
        await state.set_state(_fsm_state_for(updated))
        await save_session(state, updated)

        # Render
        screen = navigation.render_screen(updated)
        await renderer.render(message, state, screen)

    @router.message(CommandStart())
    async def cmd_start(message: types.Message, state: FSMContext) -> None:
        await state.clear()
        # Create fresh session, execution_id implicitly 1 to start
        session = TelegramSession(
            user_id=message.from_user.id if message.from_user else 0,
            chat_id=message.chat.id,
            execution_id=1
        )
        task_registry.cancel(session.user_id)  # Kill all ongoing tasks
        await save_session(state, session)
        await navigate(message, state, "nav:main")

    @router.message(Command("menu"))
    async def cmd_menu(message: types.Message, state: FSMContext) -> None:
        await navigate(message, state, "nav:main")

    # ── MAIN INPUT ROUTER ───────────────────────────────────────────

    @router.message()
    async def fast_router(message: types.Message, state: FSMContext) -> None:
        if not message.text:
            return

        text = message.text.strip()
        session = await load_session(state)
        
        # 1. SPECIAL INTERRUPT: "Back" or "Main Menu" or "Exit Search"
        if text in (labels.back, labels.main_menu, labels.exit_search):
            await navigate(message, state, "nav:back" if text == labels.back else "nav:main")
            return

        # 2. GLOBAL MENU BUTTONS
        if text == labels.browse:
            await navigate(message, state, "nav:resources")
            return
        if text == labels.search:
            await navigate(message, state, "nav:search")
            return
        if text == labels.about:
            await navigate(message, state, "nav:about")
            return
        if text == labels.report:
            await navigate(message, state, "nav:report")
            return
        if text == labels.suggest:
            await navigate(message, state, "nav:suggest")
            return
        if text == labels.retry and session.retry_request:
            await handle_retry(message, state, session)
            return

        # 3. MODE ENFORCEMENT
        if session.mode == SessionMode.SEARCH:
            await handle_search_mode(message, state, text)
            return

        if session.mode == SessionMode.REPORT:
            if session.section == "report_1":
                # Normalize button text to ensure match even with icons
                clean_text = text.lower()
                cat_map = {"missing file": "Missing file", "wrong content": "Wrong content", "other": "Other"}
                matched_cat = None
                for k, v in cat_map.items():
                    if k in clean_text:
                        matched_cat = v
                        break
                
                if matched_cat:
                    await navigate(message, state, f"nav:report_category:{matched_cat}")
                else:
                    await message.answer("⚠️ Please choose a category from the menu.")
                return
            elif session.section == "report_2" and session.report_category:
                await handle_report_description(message, state, text)
                return
            elif session.section == "suggest":
                await handle_suggestion(message, state, text)
                return


        # 4. NAVIGATION LEVELS (Only for BROWSE)
        if session.mode == SessionMode.BROWSE or session.mode == SessionMode.HOME:
            matched_button = False
            
            if session.level == "resources":
                for q, label in repository.institution.quarter_labels.items():
                    if text == label:
                        await navigate(message, state, f"nav:select_quarter:{q}")
                        matched_button = True
                        break

            elif session.level == "quarter" and session.quarter is not None:
                for course in repository.list_courses(int(session.quarter)):
                    if text == course.title:
                        await navigate(message, state, f"nav:select_course:{course.id}")
                        matched_button = True
                        break

            elif session.level == "course" and session.course_id:
                course = repository.get_course(session.course_id)
                if course:
                    if text == labels.overview:
                        await navigate(message, state, "nav:overview")
                        matched_button = True
                    elif text == labels.by_week:
                        await navigate(message, state, "nav:week_list")
                        matched_button = True
                    elif text == labels.more_files:
                        await navigate(message, state, "nav:more_files")
                        matched_button = True
                    else:
                        # Check top-level or more-files categories
                        allowed = (*course.top_level_actions, *course.more_files_actions)
                        cat_slug = find_category_slug(text, allowed)
                        if cat_slug:
                            await handle_delivery(message, state, session.course_id, cat_slug)
                            matched_button = True

                    if not matched_button:
                        # Check week buttons
                        if session.section == "week_list":
                            if text.startswith("🗂 Week "):
                                num = text.split(" ")[-1]
                                await navigate(message, state, f"nav:week_category:{num}")
                                matched_button = True
                                
                        # Check week categories
                        if session.section == "week_category" and session.week_number is not None:
                            cat_slug = find_category_slug(text, course.week_actions)
                            if cat_slug:
                                await handle_delivery_week(message, state, session.course_id, session.week_number, cat_slug)
                                matched_button = True

            if not matched_button:
                # 5. INTENT CLASSIFIER / FALLBACK (Algorithm Traffic Controller)
                decision, n_score, s_score = classify_intent(text)

                if decision == IntentDecision.SEARCH or decision == IntentDecision.UNKNOWN:
                    # Reset strikes and enforce Universal Search 
                    updated = session.model_copy(update={"noise_count": 0})
                    await save_session(state, updated)
                    await handle_search_mode(message, state, text)
                else: # IntentDecision.NOISE
                    new_count = session.noise_count + 1
                    updated = session.model_copy(update={"noise_count": new_count})
                    await save_session(state, updated)
                    
                    if new_count >= 3:
                        # Escalation: 3+ Strikes routes to Search Intro politely
                        updated = updated.model_copy(update={"noise_count": 0})
                        await save_session(state, updated)
                        await navigate(message, state, "nav:search")
                        await message.answer("💡 It seems you're having trouble. You are now in Search Mode. Please type academic keywords (like 'physics week 1').")
                    else:
                        # Soft Redirect
                        await message.answer(f"💡 Unrecognized command: <code>{html.escape(text[:20])}</code>. Please use the Menu buttons or type academic keywords to search.", parse_mode="HTML")

    # ── FEATURE HANDLERS ────────────────────────────────────────────

    async def _run_delivery_task(
        user_id: int, message: types.Message, state: FSMContext, 
        files: list[Any], original_exec_id: int, retry_setup: dict, batch_caption: str
    ) -> None:
        """Isolated Delivery Coroutine executed in background."""
        outcome = await coordinator.send_bundle(
            message, state, files, original_execution_id=original_exec_id,
            phase_label=batch_caption
        )
        if not outcome.cancelled and outcome.failed_items:
            session = await load_session(state)
            if session.execution_id == original_exec_id:
                req = RetryRequest(
                    failed_paths=tuple(str(item.path) for item in outcome.failed_items),
                    scope=DeliveryScope.COURSE if retry_setup.get("action") == "course_category" else DeliveryScope.WEEK,
                    course_id=retry_setup["course_id"],
                    category_slug=retry_setup["category_slug"],
                    week_number=retry_setup.get("week_number"),
                )
                await save_session(state, session.model_copy(update={"retry_request": req}))
                await renderer.render(message, state, navigation.render_screen(await load_session(state)))

    async def handle_delivery(message: types.Message, state: FSMContext, course_id: str, category_slug: str) -> None:
        files = delivery.bundle_for_course_category(course_id, category_slug)
        if not files:
            await message.answer(EMPTY_MESSAGE)
            return
            
        course = repository.get_course(course_id)
        if not course: return
        category = repository.categories.get(category_slug)
        if not category: return
        batch_caption = TelegramRenderer.build_batch_caption(course, category)
        
        session = await load_session(state)
        coro = _run_delivery_task(
            session.user_id, message, state, files, session.execution_id,
            {"action": "course_category", "course_id": course_id, "category_slug": category_slug},
            batch_caption
        )
        task_registry.register(session.user_id, "delivery", asyncio.create_task(coro))

    async def handle_delivery_week(message: types.Message, state: FSMContext, course_id: str, week: int, category_slug: str) -> None:
        files = delivery.bundle_for_week_category(course_id, week, category_slug)
        if not files:
            await message.answer(EMPTY_MESSAGE)
            return
            
        course = repository.get_course(course_id)
        if not course: return
        category = repository.categories.get(category_slug)
        if not category: return
        batch_caption = TelegramRenderer.build_batch_caption(course, category, week)
        
        session = await load_session(state)
        coro = _run_delivery_task(
            session.user_id, message, state, files, session.execution_id,
            {"action": "week_category", "course_id": course_id, "week_number": week, "category_slug": category_slug},
            batch_caption
        )
        task_registry.register(session.user_id, "delivery", asyncio.create_task(coro))

    async def _save_incident_API(user_id: int, category: str, description: str, course_id: str | None) -> None:
        """Saves report to PostgreSQL via FastAPI for dashboard visibility."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    "http://127.0.0.1:8000/api/v1/incidents",
                    json={
                        "telegram_id": str(user_id),
                        "category": category,
                        "description": description,
                        "course_id": course_id
                    }
                )
        except Exception as e:
            log.warning(f"Failed to save incident to API: {e}")

    async def _fire_telemetry(user_id: int, action: str, metadata: dict) -> None:

        """Non-blocking telemetry push to FastAPI. Never crashes the bot."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                await client.post(
                    "http://127.0.0.1:8000/api/v1/telemetry",
                    json={"user_id": str(user_id), "action": action, "metadata": metadata}
                )
        except Exception:
            pass  # Telemetry is best-effort, never block the user

    async def handle_search_mode(message: types.Message, state: FSMContext, text: str) -> None:
        session = await load_session(state)
        task_registry.cancel(session.user_id, "delivery")

        # ── ENGINE 1: HTTP Bridge to FastAPI (PostgreSQL TSVector + pg_trgm) ──
        engine_used = "fs_fallback_hit"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    "http://127.0.0.1:8000/api/v1/search",
                    json={"query": text, "user_id": str(session.user_id)}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("results"):
                        engine_used = data.get("engine", "tsquery_hit")
                        log_event(
                            log, logging.INFO, LogCategory.SEARCH_DB_HIT,
                            "Search resolved via PostgreSQL.",
                            user_id=session.user_id, query=text,
                            engine=engine_used, result_count=len(data["results"])
                        )
                        # For V1: DB results are informational — we still resolve via filesystem
                        # because the DB may not have file paths for delivery yet
        except Exception:
            pass  # API not running or DB empty — proceed to filesystem

        # ── ENGINE 2: Filesystem Index (Primary delivery engine for V1) ──
        resolution = search.resolve(text)

        if resolution.kind == "match" and resolution.result:
            log_event(
                log, logging.INFO, LogCategory.SEARCH_FS_FALLBACK,
                "Search resolved via filesystem index.",
                user_id=session.user_id, query=text,
                course_id=resolution.result.course_id,
                score=resolution.result.score,
                engine=engine_used
            )
            res = resolution.result
            if res.action == "send_course_category":
                await handle_delivery(message, state, res.course_id, res.category_slug)
            elif res.action == "send_week_category" and res.week_number:
                await handle_delivery_week(message, state, res.course_id, res.week_number, res.category_slug)
        else:
            log_event(
                log, logging.WARNING, LogCategory.SEARCH_FAILED,
                "Search returned 0 results from all engines.",
                user_id=session.user_id, query=text,
                resolution_kind=resolution.kind
            )
            safe_msg = html.escape(resolution.message)
            
            # Feature: Interactive Disambiguation Buttons
            keyboard = None
            if resolution.suggestions:
                from academic_hub.clients.telegram.keyboards import build_reply_keyboard
                # Sort suggestions to ensure deterministic UI
                suggestion_rows = [tuple(sorted(resolution.suggestions))]
                suggestion_rows.append((labels.back, labels.main_menu))
                keyboard = build_reply_keyboard(tuple(suggestion_rows), placeholder="Choose course/category...")
            
            await message.answer(
                f"🔍 <b>Search Result</b>\n\n{safe_msg}", 
                parse_mode="HTML",
                reply_markup=keyboard
            )


        # ── TELEMETRY: Fire async (non-blocking) ──
        asyncio.create_task(_fire_telemetry(
            session.user_id, "search",
            {"query": text, "engine": engine_used, "matched": resolution.kind == "match"}
        ))

    async def handle_report_description(message: types.Message, state: FSMContext, text: str) -> None:
        if len(text.strip()) < 5:
            await message.answer("⚠️ <b>Report too short.</b> Please describe the issue with more details.")
            return

        session = await load_session(state)
        task_registry.cancel(session.user_id, "delivery")
        
        log_event(
            log, 
            logging.INFO, 
            LogCategory.COMMAND,
            "Issue report submitted.",
            user_id=session.user_id,
            category=session.report_category,
            description=text,
            course_context=session.course_id,
            section_context=session.section
        )

        admin_id = 2113497563 # @astrosol7 ID for Orbit Release
        
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
            await message.bot.send_message(
                chat_id=admin_id,
                text=report_text,
                parse_mode="HTML"
            )
        except Exception as e:
            log.warning(f"Failed to forward report to admin {admin_id}: {e}")
        
        # New: Save to Backend for Dashboard
        asyncio.create_task(_save_incident_API(
            session.user_id, 
            session.report_category or "Other", 
            text, 
            session.course_id
        ))
        
        await message.answer("✅ <b>Report received.</b> Thank you for helping us improve!")

        await navigate(message, state, "nav:main")

    async def handle_suggestion(message: types.Message, state: FSMContext, text: str) -> None:
        if len(text.strip()) < 5:
            await message.answer("⚠️ <b>Suggestion too short.</b> Please describe the resource you'd like us to add.")
            return

        session = await load_session(state)
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

        admin_id = 2113497563

        safe_text = html.escape(text)
        suggestion_text = (
            f"💡 <b>New Content Suggestion</b>\n"
            f"<b>User ID:</b> {session.user_id}\n\n"
            f"<b>Suggestion:</b>\n<i>{safe_text}</i>"
        )

        try:
            await message.bot.send_message(
                chat_id=admin_id,
                text=suggestion_text,
                parse_mode="HTML"
            )
        except Exception as e:
            log.warning(f"Failed to forward suggestion to admin {admin_id}: {e}")

        await message.answer("✅ <b>Suggestion received.</b> We'll review it and add it if valid. Thank you!")
        await navigate(message, state, "nav:main")

    async def handle_retry(message: types.Message, state: FSMContext, session: TelegramSession) -> None:
        if not session.retry_request:
            return
        
        req = session.retry_request
        failed_paths = {str(p) for p in req.failed_paths}
        
        if req.scope == DeliveryScope.COURSE:
            all_files = delivery.bundle_for_course_category(req.course_id, req.category_slug)
            retry_setup = {"action": "course_category", "course_id": req.course_id, "category_slug": req.category_slug}
        else:
            all_files = delivery.bundle_for_week_category(req.course_id, req.week_number or 0, req.category_slug)
            retry_setup = {"action": "week_category", "course_id": req.course_id, "week_number": req.week_number, "category_slug": req.category_slug}
            
        retry_files = [f for f in all_files if str(f.path) in failed_paths]
        
        course = repository.get_course(req.course_id)
        category = repository.categories.get(req.category_slug)
        batch_caption = TelegramRenderer.build_batch_caption(course, category, req.week_number) if course and category else "📦 <b>Retrying delivery...</b>"
        
        coro = _run_delivery_task(
            session.user_id, message, state, retry_files, session.execution_id, retry_setup, batch_caption
        )
        task_registry.register(session.user_id, "delivery", asyncio.create_task(coro))

    dispatcher.include_router(router)
