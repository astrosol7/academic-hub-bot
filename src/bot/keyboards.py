from __future__ import annotations
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

def build_reply_keyboard(
    button_rows: tuple[tuple[str, ...], ...],
    *,
    placeholder: str = "Choose...",
    voyager_url: str | None = None,
) -> ReplyKeyboardMarkup:
    keyboard = []
    for row in button_rows:
        keyboard_row = [KeyboardButton(text=label) for label in row]
        keyboard.append(keyboard_row)
        
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=placeholder,
    )
