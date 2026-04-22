import logging
import asyncio
from typing import Any

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from src.bot.session import load_session, save_session
from src.bot.state import HubStates
from src.bot.managers.tasks import task_registry
from src.bot.renderer import TelegramRenderer
from src.core.models import DeliveryScope, RetryRequest
from src.core.services import ButtonLabels
from src.core.repository import PostgresContentRepository
from src.core.config import load_config
from .common import HandlerDeps, navigate, track_presence, _fire_telemetry

log = logging.getLogger(__name__)

def setup_navigation(router: Router, deps: HandlerDeps) -> None:
    
    def find_category_slug(label: str, allowed_actions: tuple[str, ...]) -> str | None:
        normalized_label = label.strip().casefold()
        for action in allowed_actions:
            category = deps.repository.categories.get(action)
            if category:
                ui_label = f"{category.icon} {category.label}".strip() if category.icon else category.label
                if (
                    category.label == label
                    or ui_label == label
                    or category.label.strip().casefold() == normalized_label
                    or ui_label.strip().casefold() == normalized_label
                ):
                    return action
        return None

    async def _run_delivery_task(
        user_id: int, message: types.Message, state: FSMContext, 
        files: list[Any], original_exec_id: int, retry_setup: dict, batch_caption: str
    ) -> None:
        outcome = await deps.coordinator.send_bundle(
            message, state, files, 
            phase_label=batch_caption
        )
        if not outcome.cancelled and outcome.failed_items:
            session = await load_session(state)
            if session.delivery_active:
                req = RetryRequest(
                    failed_paths=tuple(str(item.path) for item in outcome.failed_items),
                    scope=DeliveryScope.COURSE if retry_setup.get("action") == "course_category" else DeliveryScope.WEEK,
                    course_id=retry_setup["course_id"],
                    category_slug=retry_setup["category_slug"],
                    week_number=retry_setup.get("week_number"),
                )
                await save_session(state, session.model_copy(update={"retry_request": req}))
                await deps.renderer.render(message, state, deps.navigation.render_screen(await load_session(state)))

    async def handle_delivery(message: types.Message, state: FSMContext, course_id: str, category_slug: str) -> None:
        course = deps.repository.get_course(course_id)
        if not course:
            await message.answer("⚠️ Course not found.")
            return
            
        category = deps.repository.categories.get(category_slug)
        if not category:
            await message.answer("⚠️ Category not found.")
            return
            
        files = deps.delivery.bundle_for_course_category(course_id, category_slug)
        if not files:
            await message.answer(f"📭 No {category.label.lower()} available for {course.title} yet.\n\nCheck back later or choose another section.")
            return
            
        batch_caption = TelegramRenderer.build_batch_caption(course, category)
        
        session = await load_session(state)
        coro = _run_delivery_task(
            session.user_id, message, state, files, 0,
            {"action": "course_category", "course_id": course_id, "category_slug": category_slug},
            batch_caption
        )
        task_registry.register(session.user_id, "delivery", asyncio.create_task(coro))

    async def handle_delivery_week(message: types.Message, state: FSMContext, course_id: str, week: int, category_slug: str) -> None:
        course = deps.repository.get_course(course_id)
        if not course:
            await message.answer("⚠️ Course not found.")
            return
            
        category = deps.repository.categories.get(category_slug)
        if not category:
            await message.answer("⚠️ Category not found.")
            return
            
        files = deps.delivery.bundle_for_week_category(course_id, week, category_slug)
        if not files:
            await message.answer(f"📭 No {category.label.lower()} available for {course.title} - Week {week} yet.\n\nCheck back later or choose another section.")
            return
            
        batch_caption = TelegramRenderer.build_batch_caption(course, category, week)
        
        session = await load_session(state)
        coro = _run_delivery_task(
            session.user_id, message, state, files, 0,
            {"action": "week_category", "course_id": course_id, "week_number": week, "category_slug": category_slug},
            batch_caption
        )
        task_registry.register(session.user_id, "delivery", asyncio.create_task(coro))

    async def handle_retry(message: types.Message, state: FSMContext, session: Any) -> None:
        if not session.retry_request:
            return
        
        req = session.retry_request
        failed_paths = {str(p) for p in req.failed_paths}
        
        if req.scope == DeliveryScope.COURSE:
            all_files = deps.delivery.bundle_for_course_category(req.course_id, req.category_slug)
            retry_setup = {"action": "course_category", "course_id": req.course_id, "category_slug": req.category_slug}
        else:
            all_files = deps.delivery.bundle_for_week_category(req.course_id, req.week_number or 0, req.category_slug)
            retry_setup = {"action": "week_category", "course_id": req.course_id, "week_number": req.week_number, "category_slug": req.category_slug}
            
        retry_files = [f for f in all_files if str(f.path) in failed_paths]
        
        course = deps.repository.get_course(req.course_id)
        category = deps.repository.categories.get(req.category_slug)
        batch_caption = TelegramRenderer.build_batch_caption(course, category, req.week_number) if course and category else "📦 <b>Retrying delivery...</b>"
        
        coro = _run_delivery_task(
            session.user_id, message, state, retry_files, 0, retry_setup, batch_caption
        )
        task_registry.register(session.user_id, "delivery", asyncio.create_task(coro))

    deps.find_category_slug = find_category_slug
    deps.handle_delivery = handle_delivery
    deps.handle_delivery_week = handle_delivery_week
    deps.handle_retry = handle_retry
