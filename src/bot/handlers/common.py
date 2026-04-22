import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Callable

from aiogram import types
from aiogram.fsm.context import FSMContext

from src.bot.delivery import DeliveryCoordinator
from src.bot.managers.tasks import task_registry
from src.bot.renderer import TelegramRenderer
from src.bot.session import load_session, save_session
from src.bot.state import HubStates
from src.core.services import NavigationService, DeliveryService, SearchService
from src.core.repository import PostgresContentRepository
from src.core.models import TelegramSession
from src.core.config import load_config

log = logging.getLogger(__name__)

EMPTY_MESSAGE = "📭 Nothing here yet. Check back later or choose another section."

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

@dataclass
class HandlerDeps:
    repository: PostgresContentRepository
    navigation: NavigationService
    delivery: DeliveryService
    search: SearchService
    renderer: TelegramRenderer
    coordinator: DeliveryCoordinator
    # Dynamic handlers registered during setup
    handle_retry: Any = None
    handle_search_mode: Any = None
    handle_delivery: Any = None
    handle_delivery_week: Any = None
    find_category_slug: Any = None
    _offer_ai_help: Any = None
    _user_search_attempts: dict = field(default_factory=dict)


def _fsm_state_for(session: TelegramSession) -> Any:
    """Derive the correct aiogram FSM state from the session."""
    state = _STATE_MAP.get(str(session.section))
    if state:
        return state
    return _STATE_MAP.get(str(session.level), HubStates.home)


def _validate_session(session: TelegramSession, repository: PostgresContentRepository) -> TelegramSession:
    """State Reconciliation: Verify UI will not drift from missing context."""
    if session.level == "course":
        if not session.course_id or not repository.get_course(session.course_id):
            return session.model_copy(update={
                "level": "home", "section": "home", "course_id": None, "mode": "HOME"
            })
            
    if session.section == "week_category":
        if not session.week_number:
            return session.model_copy(update={
                "level": "course", "section": "week_list"
            })
            
    return session


async def navigate(message: types.Message, state: FSMContext, action: str, deps: HandlerDeps) -> None:
    """THE transition function. ALL navigation goes through here."""
    try:
        session = await load_session(state)

        # Mutually exclusive cancellation (nav breaks delivery)
        task_registry.cancel(session.user_id, "delivery")
        if session.delivery_active:
            await deps.coordinator.cancel_active_delivery(state)

        # Transition logic
        updated = deps.navigation.transition(session, action)
        # Validate State Integrity
        updated = _validate_session(updated, deps.repository)
        
        # Smart Resume Tracking
        if updated.level == "course" and updated.course_id:
            course = deps.repository.get_course(updated.course_id)
            if course:
                title = f"{course.title}"
                if updated.section == "week_category" and updated.week_number:
                    title += f" — Week {updated.week_number}"
                elif updated.section == "week_list":
                    title += " — Weeks"
                
                # Create a specific navigate action to return to this view
                if updated.section == "week_list":
                    # Navigating back to week list requires selecting course first, 
                    # but our UI just stores the course selection
                    resume_action = f"nav:select_course:{updated.course_id}"
                elif updated.section == "week_category" and updated.week_number:
                    # We can't directly jump to week category without being in course,
                    # so we just jump to course overview for safety
                    resume_action = f"nav:select_course:{updated.course_id}"
                else:
                    resume_action = f"nav:select_course:{updated.course_id}"
                    
                updated = updated.model_copy(update={"resume_target": (title, resume_action)})

        # Set FSM state
        await state.set_state(_fsm_state_for(updated))
        await save_session(state, updated)

        # Render
        screen = deps.navigation.render_screen(updated)
        await deps.renderer.render(message, state, screen)
    except Exception as e:
        log.exception("event=navigate_error action=%s detail=%s", action, e)
        await message.answer(f"⚠️ Navigation error: {e}")

async def _fire_telemetry(user_id: int, action: str, metadata: dict) -> None:
    """Non-blocking telemetry push to FastAPI. Never crashes the bot."""
    import httpx
    import asyncio
    config = load_config(require_token=False)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(
                f"{config.backend_base_url}/api/v1/telemetry",
                json={"user_id": str(user_id), "action": action, "metadata": metadata}
            )
    except Exception:
        pass  # Telemetry is best-effort, never block the user

async def track_presence(user_id: int) -> None:
    import asyncio
    asyncio.create_task(_fire_telemetry(user_id, "presence", {}))
