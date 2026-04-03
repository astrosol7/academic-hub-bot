"""
Academic Hub — Quarter → Courses → Exams / Syllabus / Quizzes / Tests / …

Files are sent with Telegram's sendDocument: the bot reads PDFs from disk
(FSInputFile) and uploads them to the chat. Nothing is "hosted inside Telegram"
except the delivered copy.

Reply keyboards cannot be colored (Bot API limitation).
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
from aiogram.types import BotCommand, FSInputFile, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.token import validate_token
from dotenv import load_dotenv

from hub_data import (
    COURSES,
    EXTRA_FILE_LABELS,
    HUB_FORUM_INVITE,
    QUARTER_COURSES,
    TITLE_TO_ID,
    TOPICS,
    iter_course_category,
    iter_course_syllabus,
)
from hub_format import head

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

WELCOME_PHOTO = BASE_DIR / "assets" / "welcome.jpg"
WELCOME_PHOTO_URL = "https://images.unsplash.com/photo-1557683316-973673baf926?w=1280&q=80"

MAX_DOCS_BATCH = 25
BACK_TO_COURSES = "« Courses"
MAIN = "Main menu"


class HubStates(StatesGroup):
    main = State()
    quarter_courses = State()  # listing courses for a quarter
    course_menu = State()  # picked a course; data: quarter, course_id
    pick_more_category = State()


def reply_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Quarter 1"), KeyboardButton(text="Quarter 2")]],
        resize_keyboard=True,
        input_field_placeholder="Quarter…",
    )


def reply_quarter_course_list(quarter: int) -> ReplyKeyboardMarkup:
    ids = QUARTER_COURSES[quarter]
    rows: list[list[KeyboardButton]] = []
    pair: list[KeyboardButton] = []
    for cid in ids:
        pair.append(KeyboardButton(text=COURSES[cid]["title"]))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    rows.append(
        [KeyboardButton(text="Hub links"), KeyboardButton(text=MAIN)],
    )
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, input_field_placeholder="Course…")


def reply_course_actions() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Exams"), KeyboardButton(text="Syllabus")],
            [KeyboardButton(text="Quizzes"), KeyboardButton(text="Tests")],
            [KeyboardButton(text="Overview"), KeyboardButton(text="More files")],
            [KeyboardButton(text=BACK_TO_COURSES), KeyboardButton(text=MAIN)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose…",
    )


def reply_extra_categories() -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for _slug, label in EXTRA_FILE_LABELS:
        row.append(KeyboardButton(text=label))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=BACK_TO_COURSES), KeyboardButton(text=MAIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def text_main() -> str:
    inv = html.escape(HUB_FORUM_INVITE, quote=True)
    return (
        f"{head('Academic Hub')}\n\n"
        f'<a href="{inv}">Forum invite</a>\n\n'
        f"{head('Pick a quarter, then a course.')}"
    )


def text_hub_links(quarter: int) -> str:
    r_url, _ = TOPICS["resource_index"]
    a_url, _ = TOPICS["announcements"]
    inv = html.escape(HUB_FORUM_INVITE, quote=True)
    q = "Quarter 1" if quarter == 1 else "Quarter 2"
    return (
        f"{head('Hub links')} — {html.escape(q)}\n\n"
        f'<a href="{inv}">Academic Hub invite</a>\n'
        f'<a href="{html.escape(r_url, quote=True)}">Resource Index</a>\n'
        f'<a href="{html.escape(a_url, quote=True)}">Announcements</a>\n\n'
        "<i>Official grades and private info stay on the LMS.</i>"
    )


def mono_path(quarter: int, folder: str, sub: str) -> str:
    return (
        f"<code>resources/Quarter_{quarter}/{html.escape(folder)}/{html.escape(sub)}/</code>"
    )


async def maybe_welcome_photo(message: types.Message) -> None:
    try:
        if WELCOME_PHOTO.is_file():
            await message.answer_photo(FSInputFile(WELCOME_PHOTO))
        else:
            await message.answer_photo(WELCOME_PHOTO_URL)
    except Exception as exc:
        log.info("Welcome photo skipped: %s", exc)


async def send_document_batch(
    message: types.Message,
    items: list[tuple[Path, str]],
    empty_msg: str,
) -> None:
    if not items:
        await message.answer(empty_msg, parse_mode="HTML")
        return
    batch = items[:MAX_DOCS_BATCH]
    if len(items) > MAX_DOCS_BATCH:
        await message.answer(
            f"<i>Sending {MAX_DOCS_BATCH} of {len(items)} files.</i>",
            parse_mode="HTML",
        )
    for path, caption in batch:
        try:
            await message.answer_document(
                FSInputFile(path),
                caption=html.escape(caption)[:1024],
            )
        except Exception as exc:
            log.warning("Send failed %s: %s", path, exc)
            await message.answer(f"<code>{html.escape(path.name)}</code> — send failed.", parse_mode="HTML")


async def go_main(message: types.Message, state: FSMContext) -> None:
    await state.set_state(HubStates.main)
    await message.answer(text_main(), reply_markup=reply_main_kb(), parse_mode="HTML")


@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await maybe_welcome_photo(message)
    await go_main(message, state)


@dp.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await go_main(message, state)


@dp.message(HubStates.main, F.text.in_(["Quarter 1", "Quarter 2"]))
async def open_quarter_courses(message: types.Message, state: FSMContext) -> None:
    q = 1 if message.text == "Quarter 1" else 2
    await state.set_state(HubStates.quarter_courses)
    await state.update_data(quarter=q)
    label = "Quarter 1" if q == 1 else "Quarter 2"
    await message.answer(
        f"{head(label)}\n<i>Choose a course.</i>",
        reply_markup=reply_quarter_course_list(q),
        parse_mode="HTML",
    )


@dp.message(HubStates.quarter_courses, F.text == MAIN)
async def quarter_main(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await go_main(message, state)


@dp.message(HubStates.quarter_courses, F.text == "Hub links")
async def quarter_links(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    q = int(data.get("quarter", 1))
    await message.answer(
        text_hub_links(q),
        reply_markup=reply_quarter_course_list(q),
        parse_mode="HTML",
    )


@dp.message(HubStates.quarter_courses, F.text.in_(set(TITLE_TO_ID.keys())))
async def pick_course(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    q = int(data.get("quarter", 1))
    cid = TITLE_TO_ID[message.text]
    await state.set_state(HubStates.course_menu)
    await state.update_data(quarter=q, course_id=cid)
    title = COURSES[cid]["title"]
    await message.answer(
        f"{head(title)}\n<i>Exams / syllabus / quizzes / tests — tap a button.</i>",
        reply_markup=reply_course_actions(),
        parse_mode="HTML",
    )


@dp.message(HubStates.course_menu, F.text == BACK_TO_COURSES)
async def course_back_quarter(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    q = int(data.get("quarter", 1))
    await state.set_state(HubStates.quarter_courses)
    await state.update_data(course_id=None)
    ql = "Quarter 1" if q == 1 else "Quarter 2"
    await message.answer(
        f"{head(ql)}\n<i>Choose a course.</i>",
        reply_markup=reply_quarter_course_list(q),
        parse_mode="HTML",
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


@dp.message(HubStates.course_menu, F.text == "Exams")
async def action_exams(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        await state.clear()
        await go_main(message, state)
        return
    cid, q = pair
    c = COURSES[cid]
    items = iter_course_category(cid, "exams")
    await send_document_batch(
        message,
        items,
        f"No exam PDFs yet. Add under {mono_path(q, c['folder'], 'exams')} "
        f"(subfolders e.g. <code>Exam_1</code> are ok). Run "
        f"<code>python tools/organize_resource_pdfs.py</code> after dropping files.",
    )
    await message.answer("<i>Done.</i>", reply_markup=reply_course_actions(), parse_mode="HTML")


@dp.message(HubStates.course_menu, F.text == "Syllabus")
async def action_syllabus(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        await state.clear()
        await go_main(message, state)
        return
    cid, q = pair
    c = COURSES[cid]
    items = iter_course_syllabus(cid)
    await send_document_batch(
        message,
        items,
        f"No syllabus PDFs. Drop files in {mono_path(q, c['folder'], 'syllabus')} "
        f"(or <code>readings</code>).",
    )
    await message.answer("<i>Done.</i>", reply_markup=reply_course_actions(), parse_mode="HTML")


@dp.message(HubStates.course_menu, F.text.in_(["Quizzes", "Tests"]))
async def action_quiz_test(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        await state.clear()
        await go_main(message, state)
        return
    cid, q = pair
    c = COURSES[cid]
    cat = "quizzes" if message.text == "Quizzes" else "tests"
    items = iter_course_category(cid, cat)
    await send_document_batch(
        message,
        items,
        f"No <b>{html.escape(cat)}</b> yet. Path: "
        f"{mono_path(q, c['folder'], cat)}.",
    )
    await message.answer("<i>Done.</i>", reply_markup=reply_course_actions(), parse_mode="HTML")


@dp.message(HubStates.course_menu, F.text == "Overview")
async def action_overview(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        await state.clear()
        await go_main(message, state)
        return
    cid, _ = pair
    await message.answer(
        COURSES[cid]["overview_html"],
        reply_markup=reply_course_actions(),
        parse_mode="HTML",
    )


@dp.message(HubStates.course_menu, F.text == "More files")
async def action_more(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        await state.clear()
        await go_main(message, state)
        return
    cid, _ = pair
    await state.set_state(HubStates.pick_more_category)
    await message.answer(
        f"{head('More files')} — {html.escape(COURSES[cid]['title'])}",
        reply_markup=reply_extra_categories(),
        parse_mode="HTML",
    )


LABEL_TO_EXTRA_SLUG = {label: slug for slug, label in EXTRA_FILE_LABELS}


@dp.message(HubStates.pick_more_category, F.text.in_(set(LABEL_TO_EXTRA_SLUG.keys())))
async def more_pick(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        await state.clear()
        await go_main(message, state)
        return
    cid, q = pair
    slug = LABEL_TO_EXTRA_SLUG[message.text]
    c = COURSES[cid]
    items = iter_course_category(cid, slug)
    await send_document_batch(
        message,
        items,
        f"Empty. Path: {mono_path(q, c['folder'], slug)}.",
    )
    await message.answer(
        f"{head('More files')} — {html.escape(c['title'])}",
        reply_markup=reply_extra_categories(),
        parse_mode="HTML",
    )


@dp.message(HubStates.pick_more_category, F.text == BACK_TO_COURSES)
async def more_back_to_course(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    pair = _cid_quarter(data)
    if not pair:
        await state.clear()
        await go_main(message, state)
        return
    cid, q = pair
    await state.set_state(HubStates.course_menu)
    await message.answer(
        f"{head(COURSES[cid]['title'])}",
        reply_markup=reply_course_actions(),
        parse_mode="HTML",
    )


@dp.message(HubStates.pick_more_category, F.text == MAIN)
async def more_main(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await go_main(message, state)


@dp.message(StateFilter(None), F.text == MAIN)
async def main_from_none(message: types.Message, state: FSMContext) -> None:
    await go_main(message, state)


@dp.message()
async def fallback(message: types.Message, state: FSMContext) -> None:
    st = await state.get_state()
    data = await state.get_data()
    if st == HubStates.quarter_courses.state:
        q = int(data.get("quarter", 1))
        await message.answer(
            "Pick a course or Hub links.",
            reply_markup=reply_quarter_course_list(q),
        )
    elif st == HubStates.course_menu.state:
        await message.answer("Use the buttons below.", reply_markup=reply_course_actions())
    elif st == HubStates.pick_more_category.state:
        await message.answer("Pick a category.", reply_markup=reply_extra_categories())
    else:
        await message.answer(
            "Use /start — pick <b>Quarter 1</b> or <b>Quarter 2</b>.",
            reply_markup=reply_main_kb(),
            parse_mode="HTML",
        )


async def main() -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Hub"),
            BotCommand(command="menu", description="Main menu"),
        ]
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
