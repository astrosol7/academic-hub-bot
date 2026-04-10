from __future__ import annotations

from dataclasses import asdict
import logging
from typing import Any

from aiogram import Dispatcher, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from academic_hub.clients.telegram.delivery import DeliveryCoordinator
from academic_hub.clients.telegram.renderer import TelegramRenderer
from academic_hub.clients.telegram.state import HubStates
from academic_hub.domain.models import ScreenView, SearchResolution, SearchResult, TelegramSession
from academic_hub.domain.services import ButtonLabels, DeliveryService, NavigationService, SearchService
from academic_hub.infrastructure.repository import FilesystemContentRepository


log = logging.getLogger(__name__)

EMPTY_MESSAGE = "Nothing is here yet. Try another section."
HELP_TEXT = (
    "Use Resources to browse by quarter and course.\n\n"
    "You can also type searches like:\n"
    "• calculus 1 exams\n"
    "• physics 2 week 3 lecture notes\n"
    "• seminar syllabus"
)


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

    async def get_session(state: FSMContext) -> TelegramSession:
        data = await state.get_data()
        raw = data.get("session") or {}
        return TelegramSession(
            level=str(raw.get("level", "home")),
            quarter=raw.get("quarter"),
            course_id=raw.get("course_id"),
            section=raw.get("section"),
            week_number=raw.get("week_number"),
        )

    async def set_session(state: FSMContext, session: TelegramSession) -> None:
        await state.update_data(session=asdict(session))

    def category_slug_from_label(label: str, allowed_actions: tuple[str, ...]) -> str | None:
        for action in allowed_actions:
            category = repository.categories.get(action)
            if category and category.label == label:
                return action
        return None

    def overview_screen(course_id: str, retry_enabled: bool = False) -> ScreenView:
        base = navigation.course(course_id, retry_enabled=retry_enabled)
        return ScreenView(
            key=f"course:{course_id}:overview",
            text=navigation.overview_text(course_id),
            button_rows=base.button_rows,
            placeholder=base.placeholder,
        )

    def retry_screen(screen: ScreenView) -> ScreenView:
        retry_row = (labels.retry,)
        if screen.button_rows and screen.button_rows[0] == retry_row:
            return screen
        return ScreenView(
            key=screen.key,
            text=screen.text,
            button_rows=(retry_row, *screen.button_rows),
            placeholder=screen.placeholder,
        )

    async def clear_retry(state: FSMContext) -> None:
        await state.update_data(retry_request=None)

    async def render_home(message: types.Message, state: FSMContext) -> None:
        await state.set_state(HubStates.home)
        await set_session(state, TelegramSession(level="home"))
        await clear_retry(state)
        await renderer.render(message, state, navigation.home())

    async def render_resources(message: types.Message, state: FSMContext) -> None:
        await state.set_state(HubStates.resources)
        await set_session(state, TelegramSession(level="resources"))
        await clear_retry(state)
        await renderer.render(message, state, navigation.resources())

    async def render_quarter(message: types.Message, state: FSMContext, quarter: int) -> None:
        await state.set_state(HubStates.quarter)
        await set_session(state, TelegramSession(level="quarter", quarter=quarter))
        await clear_retry(state)
        await renderer.render(message, state, navigation.quarter_courses(quarter))

    async def render_course(
        message: types.Message,
        state: FSMContext,
        course_id: str,
        *,
        overview: bool = False,
        retry_enabled: bool = False,
    ) -> None:
        course = repository.get_course(course_id)
        assert course is not None
        await state.set_state(HubStates.course)
        await set_session(
            state,
            TelegramSession(
                level="course",
                quarter=course.quarter,
                course_id=course_id,
                section="overview" if overview else "course",
            ),
        )
        if not retry_enabled:
            await clear_retry(state)
        screen = overview_screen(course_id, retry_enabled=retry_enabled) if overview else navigation.course(course_id, retry_enabled=retry_enabled)
        await renderer.render(message, state, screen)

    async def render_more_files(message: types.Message, state: FSMContext, course_id: str, *, retry_enabled: bool = False) -> None:
        course = repository.get_course(course_id)
        assert course is not None
        await state.set_state(HubStates.more_files)
        await set_session(
            state,
            TelegramSession(level="course", quarter=course.quarter, course_id=course_id, section="more_files"),
        )
        if not retry_enabled:
            await clear_retry(state)
        await renderer.render(message, state, navigation.more_files(course_id, retry_enabled=retry_enabled))

    async def render_week_list(message: types.Message, state: FSMContext, course_id: str) -> None:
        course = repository.get_course(course_id)
        assert course is not None
        await state.set_state(HubStates.week_list)
        await set_session(
            state,
            TelegramSession(level="course", quarter=course.quarter, course_id=course_id, section="week_list"),
        )
        await clear_retry(state)
        await renderer.render(message, state, navigation.week_list(course_id))

    async def render_week_category(
        message: types.Message,
        state: FSMContext,
        course_id: str,
        week_number: int,
        *,
        retry_enabled: bool = False,
    ) -> None:
        course = repository.get_course(course_id)
        assert course is not None
        await state.set_state(HubStates.week_category)
        await set_session(
            state,
            TelegramSession(
                level="course",
                quarter=course.quarter,
                course_id=course_id,
                section="week_category",
                week_number=week_number,
            ),
        )
        if not retry_enabled:
            await clear_retry(state)
        await renderer.render(message, state, navigation.week_category(course_id, week_number, retry_enabled=retry_enabled))

    async def repeat_current_screen(message: types.Message, state: FSMContext) -> None:
        session = await get_session(state)
        data = await state.get_data()
        retry_enabled = bool(data.get("retry_request"))
        if session.level == "resources":
            await renderer.render(message, state, navigation.resources())
            return
        if session.level == "quarter" and session.quarter is not None:
            quarter = int(session.quarter)
            await renderer.render(message, state, navigation.quarter_courses(quarter))
            return
        if session.level == "course" and session.course_id and session.section == "course":
            await renderer.render(message, state, navigation.course(session.course_id, retry_enabled=retry_enabled))
            return
        if session.level == "course" and session.course_id and session.section == "overview":
            await renderer.render(message, state, overview_screen(session.course_id, retry_enabled=retry_enabled))
            return
        if session.level == "course" and session.course_id and session.section == "more_files":
            screen = navigation.more_files(session.course_id, retry_enabled=retry_enabled)
            await renderer.render(message, state, screen)
            return
        if session.level == "course" and session.course_id and session.section == "week_list":
            await renderer.render(message, state, navigation.week_list(session.course_id))
            return
        if session.level == "course" and session.course_id and session.section == "week_category" and session.week_number is not None:
            await renderer.render(
                message,
                state,
                navigation.week_category(session.course_id, int(session.week_number), retry_enabled=retry_enabled),
            )
            return
        await render_home(message, state)

    async def send_and_refresh(
        message: types.Message,
        state: FSMContext,
        items: list[Any],
        *,
        screen: ScreenView,
        retry_request: dict[str, Any],
        phase_label: str = "Preparing materials...",
    ) -> None:
        if not items:
            await clear_retry(state)
            await message.answer(EMPTY_MESSAGE)
            await renderer.render(message, state, screen)
            return

        outcome = await coordinator.send_bundle(message, state, items, phase_label=phase_label)
        if outcome.cancelled:
            return
        if outcome.failed_items:
            await state.update_data(
                retry_request={
                    **retry_request,
                    "failed_paths": [str(item.path) for item in outcome.failed_items],
                }
            )
            await message.answer("Some files could not be sent. Tap Retry if you want to try again.")
            await renderer.render(message, state, retry_screen(screen))
            return

        await clear_retry(state)
        if outcome.sent_count:
            await message.answer("Done.")
        await renderer.render(message, state, screen)

    async def run_retry(message: types.Message, state: FSMContext) -> None:
        data = await state.get_data()
        request = data.get("retry_request") or {}
        course_id = request.get("course_id")
        category_slug = request.get("category_slug")
        week_number = request.get("week_number")
        syllabus_only = bool(request.get("syllabus_only"))
        failed_paths = set(request.get("failed_paths", []))
        if not course_id or not category_slug or not failed_paths:
            await clear_retry(state)
            await message.answer("Nothing is pending for retry.")
            await repeat_current_screen(message, state)
            return

        if week_number is None:
            items = [
                item
                for item in delivery.bundle_for_course_category(course_id, category_slug, syllabus_only=syllabus_only)
                if str(item.path) in failed_paths
            ]
            screen = navigation.more_files(course_id) if request.get("scope") == "more" else navigation.course(course_id)
        else:
            items = [
                item
                for item in delivery.bundle_for_week_category(course_id, int(week_number), category_slug)
                if str(item.path) in failed_paths
            ]
            screen = navigation.week_category(course_id, int(week_number))

        await send_and_refresh(
            message,
            state,
            items,
            screen=screen,
            retry_request=request,
            phase_label="Retrying...",
        )

    async def apply_search_result(message: types.Message, state: FSMContext, result: SearchResult) -> None:
        course = repository.get_course(result.course_id)
        assert course is not None
        await message.answer(f"Search match: {result.label}")

        if result.action == "open_course":
            await render_course(message, state, course.id)
            return

        if result.action == "open_week":
            await render_week_category(message, state, course.id, result.week_number or 1)
            return

        if result.action == "send_course_category":
            target_slug = result.category_slug or "readings"
            retry_request = {
                "scope": "course",
                "course_id": course.id,
                "category_slug": target_slug,
                "week_number": None,
                "syllabus_only": result.syllabus_only,
            }
            if target_slug in course.more_files_actions:
                screen = navigation.more_files(course.id)
                await state.set_state(HubStates.more_files)
                await set_session(
                    state,
                    TelegramSession(level="course", quarter=course.quarter, course_id=course.id, section="more_files"),
                )
            else:
                screen = navigation.course(course.id)
                await state.set_state(HubStates.course)
                await set_session(
                    state,
                    TelegramSession(level="course", quarter=course.quarter, course_id=course.id, section="course"),
                )
            await send_and_refresh(
                message,
                state,
                delivery.bundle_for_course_category(course.id, target_slug, syllabus_only=result.syllabus_only),
                screen=screen,
                retry_request=retry_request,
            )
            return

        if result.action == "send_week_category":
            target_slug = result.category_slug or "readings"
            week_number = result.week_number or 1
            screen = navigation.week_category(course.id, week_number)
            await state.set_state(HubStates.week_category)
            await set_session(
                state,
                TelegramSession(
                    level="course",
                    quarter=course.quarter,
                    course_id=course.id,
                    section="week_category",
                    week_number=week_number,
                ),
            )
            await send_and_refresh(
                message,
                state,
                delivery.bundle_for_week_category(course.id, week_number, target_slug),
                screen=screen,
                retry_request={
                    "scope": "week",
                    "course_id": course.id,
                    "category_slug": target_slug,
                    "week_number": week_number,
                    "syllabus_only": False,
                },
            )

    async def search_or_repeat(message: types.Message, state: FSMContext) -> None:
        resolution = search.resolve(message.text or "")
        if resolution.kind == "match" and resolution.result is not None:
            log.info("event=search_hit label=%s action=%s", resolution.result.label, resolution.result.action)
            await apply_search_result(message, state, resolution.result)
            return

        if resolution.kind in {"missing_course", "ambiguous_course"}:
            await message.answer(resolution.message or "Please use the exact course name.")
            await repeat_current_screen(message, state)
            return

        if resolution.kind in {"missing_category", "ambiguous_category"} and resolution.course_id:
            await message.answer(resolution.message or "Choose the exact category from the menu.")
            if resolution.week_number is not None:
                await render_week_category(message, state, resolution.course_id, resolution.week_number)
            else:
                await render_course(message, state, resolution.course_id)
            return

        if resolution.kind == "invalid_week" and resolution.course_id:
            await message.answer(resolution.message or "Choose a valid week from the menu.")
            await render_week_list(message, state, resolution.course_id)
            return

        await message.answer("I couldn’t place that. Use the buttons or try a search like 'calculus 1 exams'.")
        await repeat_current_screen(message, state)

    async def handle_main_menu(message: types.Message, state: FSMContext) -> bool:
        if message.text != labels.main_menu:
            return False
        await coordinator.cancel_active_delivery(state)
        await render_home(message, state)
        return True

    @router.message(CommandStart())
    async def start(message: types.Message, state: FSMContext) -> None:
        await coordinator.cancel_active_delivery(state)
        await render_home(message, state)

    @router.message(Command("menu"))
    async def menu(message: types.Message, state: FSMContext) -> None:
        await coordinator.cancel_active_delivery(state)
        await render_home(message, state)

    @router.message(Command("help"))
    async def help_command(message: types.Message) -> None:
        await message.answer(HELP_TEXT)

    @router.message(HubStates.home)
    async def home_state(message: types.Message, state: FSMContext) -> None:
        if await handle_main_menu(message, state):
            return
        if message.text == labels.resources:
            await render_resources(message, state)
            return
        await search_or_repeat(message, state)

    @router.message(HubStates.resources)
    async def resources_state(message: types.Message, state: FSMContext) -> None:
        if await handle_main_menu(message, state):
            return
        if message.text == labels.back:
            await render_home(message, state)
            return
        for quarter, label in repository.institution.quarter_labels.items():
            if message.text == label:
                await render_quarter(message, state, quarter)
                return
        await search_or_repeat(message, state)

    @router.message(HubStates.quarter)
    async def quarter_state(message: types.Message, state: FSMContext) -> None:
        if await handle_main_menu(message, state):
            return
        if message.text == labels.back:
            await render_resources(message, state)
            return
        session = await get_session(state)
        quarter = int(session.quarter or 1)
        for course in repository.list_courses(quarter):
            if message.text == course.title:
                await render_course(message, state, course.id)
                return
        await search_or_repeat(message, state)

    @router.message(HubStates.course)
    async def course_state(message: types.Message, state: FSMContext) -> None:
        if await handle_main_menu(message, state):
            return
        data = await state.get_data()
        session = await get_session(state)
        course_id = session.course_id
        if not course_id:
            await render_home(message, state)
            return
        course = repository.get_course(course_id)
        assert course is not None
        if message.text == labels.back:
            await coordinator.cancel_active_delivery(state)
            await render_quarter(message, state, course.quarter)
            return
        if message.text == labels.retry and data.get("retry_request"):
            await run_retry(message, state)
            return
        if message.text == labels.overview:
            await render_course(message, state, course_id, overview=True, retry_enabled=bool(data.get("retry_request")))
            return
        if message.text == labels.by_week:
            await render_week_list(message, state, course_id)
            return
        if message.text == labels.more_files:
            await render_more_files(message, state, course_id)
            return
        action = category_slug_from_label(message.text or "", course.top_level_actions)
        if action:
            await send_and_refresh(
                message,
                state,
                delivery.bundle_for_course_category(course_id, action),
                screen=navigation.course(course_id),
                retry_request={
                    "scope": "course",
                    "course_id": course_id,
                    "category_slug": action,
                    "week_number": None,
                    "syllabus_only": False,
                },
            )
            return
        await search_or_repeat(message, state)

    @router.message(HubStates.more_files)
    async def more_files_state(message: types.Message, state: FSMContext) -> None:
        if await handle_main_menu(message, state):
            return
        data = await state.get_data()
        session = await get_session(state)
        course_id = session.course_id
        if not course_id:
            await render_home(message, state)
            return
        course = repository.get_course(course_id)
        assert course is not None
        if message.text == labels.back:
            await coordinator.cancel_active_delivery(state)
            await render_course(message, state, course_id)
            return
        if message.text == labels.retry and data.get("retry_request"):
            await run_retry(message, state)
            return
        action = category_slug_from_label(message.text or "", course.more_files_actions)
        if action:
            await send_and_refresh(
                message,
                state,
                delivery.bundle_for_course_category(course_id, action),
                screen=navigation.more_files(course_id),
                retry_request={
                    "scope": "more",
                    "course_id": course_id,
                    "category_slug": action,
                    "week_number": None,
                    "syllabus_only": False,
                },
            )
            return
        await search_or_repeat(message, state)

    @router.message(HubStates.week_list)
    async def week_list_state(message: types.Message, state: FSMContext) -> None:
        if await handle_main_menu(message, state):
            return
        session = await get_session(state)
        course_id = session.course_id
        if not course_id:
            await render_home(message, state)
            return
        if message.text == labels.back:
            await coordinator.cancel_active_delivery(state)
            await render_course(message, state, course_id)
            return
        if (message.text or "").startswith("Week "):
            raw = (message.text or "").replace("Week ", "", 1).strip()
            if raw.isdigit():
                await render_week_category(message, state, course_id, int(raw))
                return
        await search_or_repeat(message, state)

    @router.message(HubStates.week_category)
    async def week_category_state(message: types.Message, state: FSMContext) -> None:
        if await handle_main_menu(message, state):
            return
        data = await state.get_data()
        session = await get_session(state)
        course_id = session.course_id
        week_number = session.week_number
        if not course_id or week_number is None:
            await render_home(message, state)
            return
        course = repository.get_course(course_id)
        assert course is not None
        if message.text == labels.back:
            await coordinator.cancel_active_delivery(state)
            await render_week_list(message, state, course_id)
            return
        if message.text == labels.retry and data.get("retry_request"):
            await run_retry(message, state)
            return
        action = category_slug_from_label(message.text or "", course.week_actions)
        if action:
            await send_and_refresh(
                message,
                state,
                delivery.bundle_for_week_category(course_id, int(week_number), action),
                screen=navigation.week_category(course_id, int(week_number)),
                retry_request={
                    "scope": "week",
                    "course_id": course_id,
                    "category_slug": action,
                    "week_number": int(week_number),
                    "syllabus_only": False,
                },
            )
            return
        await search_or_repeat(message, state)

    @router.message()
    async def fallback(message: types.Message, state: FSMContext) -> None:
        if await handle_main_menu(message, state):
            return
        await search_or_repeat(message, state)

    dispatcher.include_router(router)
