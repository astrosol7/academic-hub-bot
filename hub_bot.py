"""
Resources → Quarter → course → tap → PDFs. Reply keyboards cannot be colored (Bot API).
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.token import validate_token
from dotenv import load_dotenv

from hub_data import (
    COURSES,
    EXTRA_FILE_LABELS,
    QUARTER_COURSES,
    TITLE_TO_ID,
    folder_from_week_button,
    iter_course_category,
    iter_course_syllabus,
    iter_course_week_files,
    iter_week_labels,
    week_label_for_ui,
)
from hub_format import head
from hub_institution import INSTITUTION_SLUG

BASE_DIR = Path(__file__).resolve().parent
_ENV_FILE = BASE_DIR / ".env"
load_dotenv(_ENV_FILE)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

TOKEN = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
if not TOKEN:
    log.error("Set TELEGRAM_BOT_TOKEN in .env — see .env.example.")
    sys.exit(1)
if not validate_token(TOKEN):
    log.error("TELEGRAM_BOT_TOKEN is invalid.")
    sys.exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


@dp.update.outer_middleware()
async def _log_failed_updates(handler, event, data):
    try:
        return await handler(event, data)
    except Exception:
        log.exception("Unhandled exception in update handler")
        raise


MAX_DOCS_BATCH = 25
BACK = "◀ Back"
MAIN = "⌂ Main menu"
RESOURCES = "📚 Resources"
STOP_NOTE = "⏹ Stopped here. If you still need those files, open that section again."
ACTION_BUTTONS = {
    "📝 Exams": "exams",
    "📘 Lecture notes": "lecture_notes",
    "📄 Syllabus": "syllabus",
    "🗓 By week": "by_week",
    "✨ Overview": "overview",
    "📂 More files": "more_files",
}
EMPTY_CATEGORY_MSG = "Nothing is here yet. Try another section."
DONE_MSG = "✅ Done."
SEND_NOTE = "Materials are not complete until you see done."
VIEW_MENU = "menu"
VIEW_QUARTERS = "quarters"
VIEW_COURSES = "courses"
VIEW_COURSE = "course"
VIEW_MORE = "more"
VIEW_HELP = "help"
VIEW_OVERVIEW = "overview"
HELP_PAGES = [
    (
        "👋 <b>About this bot</b>\n\n"
        "This is your academic hub for course materials.\n\n"
        "Use it to open exams, syllabus, notes, weekly files, and more."
    ),
    (
        "🧭 <b>How to use it</b>\n\n"
        "Tap <b>Resources</b> → choose a quarter → pick a course → open what you need."
    ),
    (
        "✨ <b>What you can get</b>\n\n"
        "Exams, syllabus, lecture notes, week files, and extra materials.\n\n"
        "Use <b>◀ Back</b> for one step back.\nUse <b>⌂ Main menu</b> to go home."
    ),
]


def _html(**kwargs) -> dict:
    """HTML replies with link previews off (cleaner UX)."""
    base = {"parse_mode": "HTML", "disable_web_page_preview": True}
    base.update(kwargs)
    return base


class HubStates(StatesGroup):
    main = State()
    pick_quarter = State()
    quarter_courses = State()
    course_menu = State()
    pick_more_category = State()
    pick_week = State()
    help_tour = State()
    overview_paging = State()


def menu_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=RESOURCES, callback_data="nav:resources")],
            [InlineKeyboardButton(text="ℹ️ Help", callback_data="nav:help")],
        ]
    )


def quarters_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1️⃣ Quarter 1", callback_data="nav:quarter:1"),
                InlineKeyboardButton(text="2️⃣ Quarter 2", callback_data="nav:quarter:2"),
            ],
            [
                InlineKeyboardButton(text="ℹ️ Help", callback_data="nav:help"),
                InlineKeyboardButton(text=MAIN, callback_data="nav:menu"),
            ],
        ]
    )


def course_list_inline_kb(quarter: int) -> InlineKeyboardMarkup:
    ids = QUARTER_COURSES[quarter]
    rows: list[list[InlineKeyboardButton]] = []
    pair: list[InlineKeyboardButton] = []
    for cid in ids:
        pair.append(InlineKeyboardButton(text=COURSES[cid]["title"], callback_data=f"nav:course:{cid}"))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    rows.append(
        [
            InlineKeyboardButton(text=BACK, callback_data="nav:resources"),
            InlineKeyboardButton(text=MAIN, callback_data="nav:menu"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def course_actions_inline_kb(course_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Exams", callback_data=f"nav:files:{course_id}:exams"),
                InlineKeyboardButton(text="📘 Lecture notes", callback_data=f"nav:files:{course_id}:lecture_notes"),
            ],
            [
                InlineKeyboardButton(text="📄 Syllabus", callback_data=f"nav:files:{course_id}:syllabus"),
                InlineKeyboardButton(text="✨ Overview", callback_data=f"nav:overview:{course_id}:0"),
            ],
            [
                InlineKeyboardButton(text="📂 More files", callback_data=f"nav:more:{course_id}"),
            ],
            [
                InlineKeyboardButton(text=BACK, callback_data="nav:back:courses"),
                InlineKeyboardButton(text=MAIN, callback_data="nav:menu"),
            ],
        ]
    )


def reply_week_picker(course_id: str) -> ReplyKeyboardMarkup:
    labels = iter_week_labels(course_id)
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for folder in labels:
        row.append(KeyboardButton(text=f"🗂 {week_label_for_ui(folder)}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=BACK), KeyboardButton(text=MAIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, input_field_placeholder="Choose a week…")


def more_files_inline_kb(course_id: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    icon_map = {
        "Lecture recordings": "🎥",
        "Homework": "🧠",
        "Readings": "📚",
        "Breakout notes": "🗒",
        "Assignments": "📌",
    }
    for slug, label in EXTRA_FILE_LABELS:
        row.append(
            InlineKeyboardButton(
                text=f"{icon_map.get(label, '📁')} {label}",
                callback_data=f"nav:files:{course_id}:{slug}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [
            InlineKeyboardButton(text=BACK, callback_data=f"nav:course:{course_id}"),
            InlineKeyboardButton(text=MAIN, callback_data="nav:menu"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def reply_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=RESOURCES)],
            [KeyboardButton(text=MAIN)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an option\u2026",
    )


def reply_quarter_pick_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1\ufe0f\u20e3 Quarter 1"), KeyboardButton(text="2\ufe0f\u20e3 Quarter 2")],
            [KeyboardButton(text=BACK), KeyboardButton(text=MAIN)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose a quarter\u2026",
    )


def reply_quarter_course_list(q: int) -> ReplyKeyboardMarkup:
    ids = QUARTER_COURSES[q]
    rows: list[list[KeyboardButton]] = []
    pair: list[KeyboardButton] = []
    for cid in ids:
        pair.append(KeyboardButton(text=COURSES[cid]["title"]))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    rows.append([KeyboardButton(text=BACK), KeyboardButton(text=MAIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, input_field_placeholder="Choose a course\u2026")


def reply_course_actions() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="\U0001f4dd Exams"), KeyboardButton(text="\U0001f4d8 Lecture notes")],
            [KeyboardButton(text="\U0001f4c4 Syllabus"), KeyboardButton(text="\U0001f5d3 By week")],
            [KeyboardButton(text="\u2728 Overview"), KeyboardButton(text="\U0001f4c2 More files")],
            [KeyboardButton(text=BACK), KeyboardButton(text=MAIN)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose what you need\u2026",
    )


def reply_extra_categories() -> ReplyKeyboardMarkup:
    icon_map = {
        "Lecture recordings": "\U0001f3a5",
        "Homework": "\U0001f9e0",
        "Readings": "\U0001f4da",
        "Breakout notes": "\U0001f5d2",
        "Assignments": "\U0001f4cc",
    }
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for _slug, label in EXTRA_FILE_LABELS:
        row.append(KeyboardButton(text=f"{icon_map.get(label, '\U0001f4c1')} {label}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=BACK), KeyboardButton(text=MAIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, input_field_placeholder="Choose a category\u2026")


def text_main() -> str:
    return (
        f"{head('Academic Hub')}\n\n"
        "Tap <b>Resources</b> to find your course materials.\n\n"
        "This bot works like a small app inside Telegram."
    )


def _strip_visual_prefix(text: str) -> str:
    return text.split(" ", 1)[1] if " " in text else text


def _pick_quarter_from_text(text: str | None) -> int | None:
    if not text:
        return None
    low = text.lower()
    if "quarter 1" in low or "quarter_1" in low:
        return 1
    if "quarter 2" in low or "quarter_2" in low:
        return 2
    return None


def _normalize_extra_label(text: str | None) -> str | None:
    if not text:
        return None
    return _strip_visual_prefix(text)


def _week_folder_from_button(text: str, course_id: str) -> str | None:
    stripped = _strip_visual_prefix(text)
    return folder_from_week_button(stripped, course_id)


def help_inline_kb(page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data=f"help:page:{max(0, page - 1)}"),
                InlineKeyboardButton(text=f"{page + 1}/{len(HELP_PAGES)}", callback_data="help:noop"),
                InlineKeyboardButton(text="➡️", callback_data=f"help:page:{min(len(HELP_PAGES) - 1, page + 1)}"),
            ],
            [
                InlineKeyboardButton(text="🔄 Restart tour", callback_data="help:restart"),
                InlineKeyboardButton(text="🏠 Menu", callback_data="help:menu"),
            ],
        ]
    )


def retry_inline_kb(scope: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Retry", callback_data=f"retry:{scope}")]
        ]
    )


def overview_sections(course_id: str) -> list[tuple[str, str]]:
    title = COURSES[course_id]["title"]
    overview = COURSES[course_id]["overview_html"].split("\n\n")
    if not overview:
        return [(title, COURSES[course_id]["overview_html"])]
    sections: list[tuple[str, str]] = []
    for idx, chunk in enumerate(overview):
        header = title if idx == 0 else f"{title} • Part {idx + 1}"
        sections.append((header, chunk))
    return sections


def overview_inline_kb(course_id: str, page: int) -> InlineKeyboardMarkup:
    total = len(overview_sections(course_id))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data=f"overview:{course_id}:page:{max(0, page - 1)}"),
                InlineKeyboardButton(text=f"{page + 1}/{total}", callback_data="overview:noop"),
                InlineKeyboardButton(text="➡️", callback_data=f"overview:{course_id}:page:{min(total - 1, page + 1)}"),
            ],
            [
                InlineKeyboardButton(text="🔄 Restart", callback_data=f"overview:{course_id}:restart"),
                InlineKeyboardButton(text="🏠 Menu", callback_data=f"overview:{course_id}:menu"),
            ],
        ]
    )


async def _edit_status(message: types.Message, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup, **_html())
    except Exception:
        pass


async def _edit_callback_message(
    query: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    if query.message:
        try:
            await query.message.edit_text(text, reply_markup=reply_markup, **_html())
        except Exception:
            pass
    await query.answer()


async def render_ui(
    state: FSMContext,
    *,
    message: types.Message | None = None,
    query: CallbackQuery | None = None,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    view: str,
) -> None:
    data = await state.get_data()
    active_message_id = data.get("ui_message_id")
    target_chat_id = None
    if query and query.message:
        target_chat_id = query.message.chat.id
    elif message:
        target_chat_id = message.chat.id

    if query and query.message:
        try:
            await query.message.edit_text(text, reply_markup=reply_markup, **_html())
            await state.update_data(ui_message_id=query.message.message_id, ui_view=view)
            await query.answer()
            return
        except Exception:
            pass

    if message and active_message_id and target_chat_id:
        try:
            await bot.edit_message_text(
                chat_id=target_chat_id,
                message_id=active_message_id,
                text=text,
                reply_markup=reply_markup,
                **_html(),
            )
            await state.update_data(ui_message_id=active_message_id, ui_view=view)
            return
        except Exception:
            pass

    if message:
        sent = await message.answer(text, reply_markup=reply_markup, **_html())
        await state.update_data(ui_message_id=sent.message_id, ui_view=view)
        return

    if query and query.message:
        sent = await query.message.answer(text, reply_markup=reply_markup, **_html())
        await state.update_data(ui_message_id=sent.message_id, ui_view=view)
        await query.answer()


def _store_retry_items(items: list[tuple[Path, str]]) -> list[tuple[str, str]]:
    return [(str(path), caption) for path, caption in items]


def _load_retry_items(data: dict, scope: str) -> list[tuple[Path, str]]:
    stored = data.get("retry_items", {})
    raw_items = stored.get(scope, [])
    return [(Path(path_str), caption) for path_str, caption in raw_items]


async def send_document_batch(
    message: types.Message,
    state: FSMContext,
    items: list[tuple[Path, str]],
    empty_msg: str,
    retry_scope: str,
) -> bool:
    if not items:
        return False

    batch = items[:MAX_DOCS_BATCH]
    status = await message.answer(
        "📦 <b>Preparing your materials...</b>",
        **_html(),
    )
    await asyncio.sleep(1)

    failed_items: list[tuple[Path, str]] = []
    sent_any = False

    for idx, (path, caption) in enumerate(batch, start=1):
        current = await state.get_data()
        if current.get("stop_sending"):
            await state.update_data(stop_sending=False)
            await _edit_status(status, f"{STOP_NOTE}\n\n<i>{SEND_NOTE}</i>")
            return sent_any

        dots = "." * ((idx - 1) % 3 + 1)
        file_size_mb = path.stat().st_size / (1024 * 1024) if path.exists() else 0
        await _edit_status(
            status,
            (
                f"📤 <b>Sending files ({idx}/{len(batch)}){dots}</b>\n"
                f"<i>{SEND_NOTE}</i>\n"
                f"<i>{file_size_mb:.1f} MB ready</i>"
            ),
        )
        await asyncio.sleep(0.8)

        sent = False
        for attempt in range(2):
            try:
                await message.answer_document(
                    FSInputFile(path),
                    caption=html.escape(caption)[:1024],
                )
                sent = True
                sent_any = True
                break
            except Exception as exc:
                log.warning("Send failed %s attempt %s: %s", path, attempt + 1, exc)
                await asyncio.sleep(0.8)

        if not sent:
            failed_items.append((path, caption))

    if failed_items:
        failed_names = ", ".join(
            html.escape(caption.split(" — ", 1)[-1].strip() or "file") for _, caption in failed_items[:3]
        )
        more = "" if len(failed_items) <= 3 else f" and {len(failed_items) - 3} more"
        data = await state.get_data()
        retry_items = data.get("retry_items", {})
        retry_items[retry_scope] = _store_retry_items(failed_items)
        await state.update_data(retry_items=retry_items, last_retry_scope=retry_scope)
        await _edit_status(
            status,
            (
                f"⚠️ <b>Some files could not be sent.</b>\n"
                f"<i>{failed_names}{more}</i>\n\n"
                "Tap retry to try again."
            ),
            reply_markup=retry_inline_kb(retry_scope),
        )
        return sent_any

    await _edit_status(status, f"{DONE_MSG}\n\n<i>{SEND_NOTE}</i>")
    return sent_any


async def go_main(message: types.Message, state: FSMContext) -> None:
    await state.set_state(HubStates.main)
    await state.update_data(stop_sending=True)
    await message.answer(text_main(), reply_markup=reply_main_kb(), **_html())


async def open_quarter_course_list(message: types.Message, state: FSMContext, q: int) -> None:
    await state.set_state(HubStates.quarter_courses)
    await state.update_data(quarter=q, stop_sending=False)
    label = "Quarter 1" if q == 1 else "Quarter 2"
    await message.answer(
        f"{head(label)}\n\n<i>Choose your course.</i>",
        reply_markup=reply_quarter_course_list(q),
        **_html(),
    )


@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(HubStates.main)
    await render_ui(
        state,
        message=message,
        text=text_main(),
        reply_markup=menu_inline_kb(),
        view=VIEW_MENU,
    )


@dp.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(HubStates.main)
    await render_ui(
        state,
        message=message,
        text=text_main(),
        reply_markup=menu_inline_kb(),
        view=VIEW_MENU,
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message, state: FSMContext) -> None:
    await state.set_state(HubStates.help_tour)
    await state.update_data(stop_sending=True, help_page=0)
    await render_ui(
        state,
        message=message,
        text=HELP_PAGES[0],
        reply_markup=help_inline_kb(0),
        view=VIEW_HELP,
    )


@dp.message(HubStates.main, F.text == RESOURCES)
async def main_resources(message: types.Message, state: FSMContext) -> None:
    await state.set_state(HubStates.pick_quarter)
    await state.update_data(stop_sending=False)
    await message.answer(
        f"{head('Resources')}\n\n<i>Choose a quarter.</i>",
        reply_markup=reply_quarter_pick_kb(),
        **_html(),
    )


@dp.message(HubStates.main, lambda message: _pick_quarter_from_text(message.text) is not None)
async def main_legacy_quarter_keyboard(message: types.Message, state: FSMContext) -> None:
    q = _pick_quarter_from_text(message.text)
    if q is None:
        return
    await open_quarter_course_list(message, state, q)


@dp.message(HubStates.pick_quarter, lambda message: _pick_quarter_from_text(message.text) is not None)
async def pick_quarter_chosen(message: types.Message, state: FSMContext) -> None:
    q = _pick_quarter_from_text(message.text)
    if q is None:
        return
    await open_quarter_course_list(message, state, q)


@dp.message(HubStates.pick_quarter, F.text == BACK)
async def pick_quarter_back(message: types.Message, state: FSMContext) -> None:
    await go_main(message, state)


@dp.message(HubStates.pick_quarter, F.text == MAIN)
async def pick_quarter_main(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await go_main(message, state)


@dp.message(HubStates.quarter_courses, F.text == BACK)
async def quarter_back_nav(message: types.Message, state: FSMContext) -> None:
    await state.set_state(HubStates.pick_quarter)
    await state.update_data(stop_sending=False)
    await message.answer(
        f"{head('Resources')}\n\n<i>Choose a quarter.</i>",
        reply_markup=reply_quarter_pick_kb(),
        **_html(),
    )


@dp.message(HubStates.quarter_courses, F.text == MAIN)
async def quarter_main(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await go_main(message, state)


@dp.message(HubStates.quarter_courses, F.text.in_(set(TITLE_TO_ID.keys())))
async def pick_course(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    q = int(data.get("quarter", 1))
    cid = TITLE_TO_ID[message.text]
    await state.set_state(HubStates.course_menu)
    await state.update_data(quarter=q, course_id=cid, stop_sending=False)
    title = COURSES[cid]["title"]
    await message.answer(
        f"{head(title)}\n\n<i>Choose what you need.</i>",
        reply_markup=reply_course_actions(),
        **_html(),
    )


@dp.message(HubStates.course_menu, F.text == BACK)
async def course_back_quarter(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    q = int(data.get("quarter", 1))
    await state.set_state(HubStates.quarter_courses)
    await state.update_data(course_id=None, stop_sending=True)
    ql = "Quarter 1" if q == 1 else "Quarter 2"
    await message.answer(
        f"{head(ql)}\n\n<i>Choose a course.</i>\n{STOP_NOTE}",
        reply_markup=reply_quarter_course_list(q),
        **_html(),
    )


@dp.message(HubStates.course_menu, F.text == MAIN)
async def course_main(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await go_main(message, state)


def _cid_quarter(state_data: dict) -> tuple[str, int] | None:
    cid = state_data.get("course_id")
    q = int(state_data.get("quarter", 1))
    if not cid or cid not in COURSES:
        return None
    return cid, q


@dp.message(HubStates.course_menu, F.text == "📝 Exams")
async def action_exams(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        log.warning("Exams: missing course context, sending main menu")
        await state.clear()
        await go_main(message, state)
        return
    cid, _q = pair
    items = iter_course_category(cid, "exams")
    if not items:
        await message.answer(EMPTY_CATEGORY_MSG, reply_markup=reply_course_actions(), **_html())
        return
    await send_document_batch(
        message,
        state,
        items,
        EMPTY_CATEGORY_MSG,
        f"course:{cid}:exams",
    )
    await message.answer(reply_markup=reply_course_actions(), text="Choose what you need next.", **_html())


@dp.message(HubStates.course_menu, F.text == "📄 Syllabus")
async def action_syllabus(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        log.warning("Syllabus: missing course context")
        await state.clear()
        await go_main(message, state)
        return
    cid, _q = pair
    items = iter_course_syllabus(cid)
    if not items:
        await message.answer(EMPTY_CATEGORY_MSG, reply_markup=reply_course_actions(), **_html())
        return
    await send_document_batch(
        message,
        state,
        items,
        EMPTY_CATEGORY_MSG,
        f"course:{cid}:syllabus",
    )
    await message.answer(reply_markup=reply_course_actions(), text="Choose what you need next.", **_html())


@dp.message(HubStates.course_menu, F.text == "📘 Lecture notes")
async def action_lecture_notes(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        log.warning("Lecture notes: missing course context")
        await state.clear()
        await go_main(message, state)
        return
    cid, _q = pair
    items = iter_course_category(cid, "lecture_notes")
    if not items:
        await message.answer(EMPTY_CATEGORY_MSG, reply_markup=reply_course_actions(), **_html())
        return
    await send_document_batch(
        message,
        state,
        items,
        EMPTY_CATEGORY_MSG,
        f"course:{cid}:lecture_notes",
    )
    await message.answer(reply_markup=reply_course_actions(), text="Choose what you need next.", **_html())


@dp.message(HubStates.course_menu, F.text == "🗓 By week")
async def action_by_week(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        log.warning("By week: missing course context")
        await state.clear()
        await go_main(message, state)
        return
    cid, _q = pair
    labels = iter_week_labels(cid)
    if not labels:
        await message.answer(
            "Nothing is here yet. Try another section.",
            reply_markup=reply_course_actions(),
            **_html(),
        )
        return
    await state.set_state(HubStates.pick_week)
    await message.answer(
        f"{head('By week')}\n\n<i>Pick a week.</i>",
        reply_markup=reply_week_picker(cid),
        **_html(),
    )


@dp.message(HubStates.pick_week, F.text == BACK)
async def week_back_course(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        await state.clear()
        await go_main(message, state)
        return
    cid, _ = pair
    await state.set_state(HubStates.course_menu)
    await state.update_data(stop_sending=True)
    await message.answer(
        f"{head(COURSES[cid]['title'])}\n\n{STOP_NOTE}",
        reply_markup=reply_course_actions(),
        **_html(),
    )


@dp.message(HubStates.pick_week, F.text == MAIN)
async def week_main(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await go_main(message, state)


@dp.message(HubStates.pick_week)
async def week_send_files(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        await state.clear()
        await go_main(message, state)
        return
    cid, _q = pair
    folder = _week_folder_from_button(message.text or "", cid)
    if not folder:
        await message.answer("Pick a week from the buttons.", reply_markup=reply_week_picker(cid), **_html())
        return
    items = iter_course_week_files(cid, folder)
    if not items:
        await message.answer(EMPTY_CATEGORY_MSG, reply_markup=reply_week_picker(cid), **_html())
        return
    await send_document_batch(message, state, items, EMPTY_CATEGORY_MSG, f"week:{cid}:{folder}")
    await message.answer("Pick another week or go back.", reply_markup=reply_week_picker(cid), **_html())


@dp.message(HubStates.course_menu, F.text == "✨ Overview")
async def action_overview(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        await state.clear()
        await go_main(message, state)
        return
    cid, _ = pair
    sections = overview_sections(cid)
    title, first_section = sections[0]
    await state.set_state(HubStates.overview_paging)
    await state.update_data(overview_course_id=cid, overview_page=0)
    await message.answer(
        f"{head(title)}\n\n{first_section}",
        reply_markup=overview_inline_kb(cid, 0),
        **_html(),
    )


@dp.message(HubStates.course_menu, F.text == "📂 More files")
async def action_more(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        await state.clear()
        await go_main(message, state)
        return
    cid, _ = pair
    await state.set_state(HubStates.pick_more_category)
    await state.update_data(stop_sending=False)
    await message.answer(
        f"{head('More files')}\n\n<i>Choose a category.</i>",
        reply_markup=reply_extra_categories(),
        **_html(),
    )


LABEL_TO_EXTRA_SLUG = {label: slug for slug, label in EXTRA_FILE_LABELS}


@dp.message(
    HubStates.pick_more_category,
    lambda message: (_normalize_extra_label(message.text) or "") in LABEL_TO_EXTRA_SLUG,
)
async def more_pick(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        await state.clear()
        await go_main(message, state)
        return
    cid, _q = pair
    label = _normalize_extra_label(message.text)
    if not label:
        await message.answer("Pick a category from the buttons.", reply_markup=reply_extra_categories(), **_html())
        return
    slug = LABEL_TO_EXTRA_SLUG[label]
    items = iter_course_category(cid, slug)
    if not items:
        await message.answer(EMPTY_CATEGORY_MSG, reply_markup=reply_extra_categories(), **_html())
        return
    await send_document_batch(
        message,
        state,
        items,
        EMPTY_CATEGORY_MSG,
        f"extra:{cid}:{slug}",
    )
    await message.answer("Choose another category or go back.", reply_markup=reply_extra_categories(), **_html())


@dp.message(HubStates.pick_more_category, F.text == BACK)
async def more_back_to_course(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        await state.clear()
        await go_main(message, state)
        return
    cid, _ = pair
    await state.set_state(HubStates.course_menu)
    await state.update_data(stop_sending=True)
    await message.answer(
        f"{head(COURSES[cid]['title'])}\n\n{STOP_NOTE}",
        reply_markup=reply_course_actions(),
        **_html(),
    )


@dp.message(HubStates.pick_more_category, F.text == MAIN)
async def more_main(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await go_main(message, state)


@dp.message(StateFilter(None), F.text == MAIN)
async def main_from_none(message: types.Message, state: FSMContext) -> None:
    await go_main(message, state)


@dp.message(HubStates.main, F.text == MAIN)
async def main_menu_button(message: types.Message, state: FSMContext) -> None:
    await go_main(message, state)


@dp.callback_query(F.data.startswith("help:"))
async def help_callback(query: CallbackQuery, state: FSMContext) -> None:
    data = query.data or ""
    if data == "help:noop":
        await query.answer()
        return
    if data == "help:restart":
        await state.set_state(HubStates.help_tour)
        await state.update_data(help_page=0)
        await _edit_callback_message(query, HELP_PAGES[0], reply_markup=help_inline_kb(0))
        return
    if data == "help:menu":
        await state.set_state(HubStates.main)
        await _edit_callback_message(query, text_main())
        return
    if data.startswith("help:page:"):
        page = int(data.rsplit(":", 1)[-1])
        page = max(0, min(len(HELP_PAGES) - 1, page))
        await state.set_state(HubStates.help_tour)
        await state.update_data(help_page=page)
        await _edit_callback_message(query, HELP_PAGES[page], reply_markup=help_inline_kb(page))
        return
    await query.answer()


@dp.callback_query(F.data.startswith("overview:"))
async def overview_callback(query: CallbackQuery, state: FSMContext) -> None:
    data = query.data or ""
    if data == "overview:noop":
        await query.answer()
        return
    if data.endswith(":menu"):
        await state.set_state(HubStates.main)
        await _edit_callback_message(query, text_main())
        return
    if data.endswith(":restart"):
        parts = data.split(":")
        course_id = parts[1]
        sections = overview_sections(course_id)
        await state.set_state(HubStates.overview_paging)
        await state.update_data(overview_course_id=course_id, overview_page=0)
        title, section = sections[0]
        await _edit_callback_message(query, f"{head(title)}\n\n{section}", reply_markup=overview_inline_kb(course_id, 0))
        return
    if ":page:" in data:
        _, course_id, _, page_str = data.split(":")
        page = int(page_str)
        sections = overview_sections(course_id)
        page = max(0, min(len(sections) - 1, page))
        title, section = sections[page]
        await state.set_state(HubStates.overview_paging)
        await state.update_data(overview_course_id=course_id, overview_page=page)
        await _edit_callback_message(query, f"{head(title)}\n\n{section}", reply_markup=overview_inline_kb(course_id, page))
        return
    await query.answer()


@dp.callback_query(F.data.startswith("retry:"))
async def retry_callback(query: CallbackQuery, state: FSMContext) -> None:
    scope = (query.data or "").split(":", 1)[-1]
    data = await state.get_data()
    items = _load_retry_items(data, scope)
    if not items:
        await query.answer("Nothing to retry.", show_alert=False)
        return
    if query.message is None:
        await query.answer()
        return
    await query.answer("Retrying...")
    await send_document_batch(query.message, state, items, EMPTY_CATEGORY_MSG, scope)


@dp.message()
async def fallback(message: types.Message, state: FSMContext) -> None:
    st = await state.get_state()
    data = await state.get_data()
    if st == HubStates.pick_quarter.state:
        await message.answer(
            "Choose a quarter.",
            reply_markup=reply_quarter_pick_kb(),
            **_html(),
        )
    elif st == HubStates.quarter_courses.state:
        q = int(data.get("quarter", 1))
        await message.answer(
            "Pick a course.",
            reply_markup=reply_quarter_course_list(q),
            **_html(),
        )
    elif st == HubStates.course_menu.state:
        await message.answer("Choose from the buttons below.", reply_markup=reply_course_actions(), **_html())
    elif st == HubStates.pick_week.state:
        cid = data.get("course_id")
        if cid and cid in COURSES:
            await message.answer("Pick a week.", reply_markup=reply_week_picker(cid), **_html())
        else:
            await state.clear()
            await go_main(message, state)
    elif st == HubStates.pick_more_category.state:
        await message.answer("Pick a category.", reply_markup=reply_extra_categories(), **_html())
    elif st == HubStates.help_tour.state:
        page = int(data.get("help_page", 0))
        await message.answer(
            HELP_PAGES[page],
            reply_markup=help_inline_kb(page),
            **_html(),
        )
    elif st == HubStates.overview_paging.state:
        cid = data.get("overview_course_id")
        page = int(data.get("overview_page", 0))
        if cid and cid in COURSES:
            sections = overview_sections(cid)
            page = max(0, min(len(sections) - 1, page))
            title, section = sections[page]
            await message.answer(
                f"{head(title)}\n\n{section}",
                reply_markup=overview_inline_kb(cid, page),
                **_html(),
            )
        else:
            await go_main(message, state)
    elif st == HubStates.main.state:
        await message.answer(
            "Tap <b>Resources</b> to find your course materials.",
            reply_markup=reply_main_kb(),
            **_html(),
        )
    else:
        await message.answer(
            "Tap <b>Resources</b> to get started.",
            reply_markup=reply_main_kb(),
            **_html(),
        )


async def main() -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start"),
            BotCommand(command="menu", description="Main menu"),
            BotCommand(command="help", description="Help"),
        ]
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
