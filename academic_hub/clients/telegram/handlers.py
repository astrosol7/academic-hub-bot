from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from aiogram import Dispatcher, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from academic_hub.clients.telegram.delivery import DeliveryCoordinator
from academic_hub.clients.telegram.managers.tasks import task_registry
from academic_hub.clients.telegram.renderer import TelegramRenderer
from academic_hub.clients.telegram.session import load_session, save_session
from academic_hub.clients.telegram.state import HubStates
from academic_hub.domain.models import RetryRequest, SessionMode, TelegramSession
from academic_hub.domain.services import ButtonLabels, DeliveryService, NavigationService, SearchService
from academic_hub.infrastructure.repository import FilesystemContentRepository
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
        if text == labels.retry and session.retry_request:
            await handle_retry(message, state, session)
            return

        # 3. MODE ENFORCEMENT
        if session.mode == SessionMode.SEARCH:
            await handle_search_mode(message, state, text)
            return

        if session.mode == SessionMode.REPORT:
            if session.section == "report_1":
                if text in ("Missing file", "Wrong content", "Other"):
                    await navigate(message, state, f"nav:report_category:{text}")
                else:
                    await message.answer("⚠️ Please choose a category from the menu.")
                return
            elif session.section == "report_2" and session.report_category:
                await handle_report_description(message, state, text)
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
                await message.answer(
                    "💡 <b>I don't understand that command.</b>\n\n"
                    "• Tap <b>📚 Browse Subjects</b> to use menus\n"
                    "• Tap <b>🔍 Search</b> for free-text search",
                    parse_mode="HTML"
                )

    # ── FEATURE HANDLERS ────────────────────────────────────────────

    async def _run_delivery_task(
        user_id: int, message: types.Message, state: FSMContext, 
        files: list[Any], original_exec_id: int, retry_setup: dict
    ) -> None:
        """Isolated Delivery Coroutine executed in background."""
        outcome = await coordinator.send_bundle(
            message, state, files, original_execution_id=original_exec_id
        )
        if not outcome.cancelled and outcome.failed_items:
            session = await load_session(state)
            if session.execution_id == original_exec_id:
                req = RetryRequest(
                    failed_paths=tuple(str(item.path) for item in outcome.failed_items),
                    **retry_setup
                )
                await save_session(state, session.model_copy(update={"retry_request": req}))
                await renderer.render(message, state, navigation.render_screen(await load_session(state)))

    async def handle_delivery(message: types.Message, state: FSMContext, course_id: str, category_slug: str) -> None:
        files = delivery.bundle_for_course_category(course_id, category_slug)
        if not files:
            await message.answer(EMPTY_MESSAGE)
            return
            
        session = await load_session(state)
        coro = _run_delivery_task(
            session.user_id, message, state, files, session.execution_id,
            {"action": "course_category", "course_id": course_id, "category_slug": category_slug}
        )
        task_registry.register(session.user_id, "delivery", asyncio.create_task(coro))

    async def handle_delivery_week(message: types.Message, state: FSMContext, course_id: str, week: int, category_slug: str) -> None:
        files = delivery.bundle_for_week_category(course_id, week, category_slug)
        if not files:
            await message.answer(EMPTY_MESSAGE)
            return
            
        session = await load_session(state)
        coro = _run_delivery_task(
            session.user_id, message, state, files, session.execution_id,
            {"action": "week_category", "course_id": course_id, "week_number": week, "category_slug": category_slug}
        )
        task_registry.register(session.user_id, "delivery", asyncio.create_task(coro))

    async def handle_search_mode(message: types.Message, state: FSMContext, text: str) -> None:
        resolution = search.resolve(text)
        
        session = await load_session(state)
        task_registry.cancel(session.user_id, "delivery")

        if resolution.kind == "match" and resolution.result:
            res = resolution.result
            if res.action == "send_course_category":
                await handle_delivery(message, state, res.course_id, res.category_slug)
            elif res.action == "send_week_category" and res.week_number:
                await handle_delivery_week(message, state, res.course_id, res.week_number, res.category_slug)
        else:
            await message.answer(f"🔍 <b>Search Result</b>\n\n{resolution.message}", parse_mode="HTML")

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
        
        await message.answer("✅ <b>Report received.</b> Thank you for helping us improve!")
        await navigate(message, state, "nav:main")

    async def handle_retry(message: types.Message, state: FSMContext, session: TelegramSession) -> None:
        if not session.retry_request:
            return
        
        req = session.retry_request
        failed_paths = {str(p) for p in req.failed_paths}
        
        if req.action == "course_category":
            all_files = delivery.bundle_for_course_category(req.course_id, req.category_slug)
            retry_setup = {"action": "course_category", "course_id": req.course_id, "category_slug": req.category_slug}
        else:
            all_files = delivery.bundle_for_week_category(req.course_id, req.week_number or 0, req.category_slug)
            retry_setup = {"action": "week_category", "course_id": req.course_id, "week_number": req.week_number, "category_slug": req.category_slug}
            
        retry_files = [f for f in all_files if str(f.path) in failed_paths]
        
        coro = _run_delivery_task(
            session.user_id, message, state, retry_files, session.execution_id, retry_setup
        )
        task_registry.register(session.user_id, "delivery", asyncio.create_task(coro))

    dispatcher.include_router(router)
