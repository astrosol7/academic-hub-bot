from __future__ import annotations
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

def build_reply_keyboard(
    button_rows: tuple[tuple[str, ...], ...],
    *,
    placeholder: str = "Choose...",
    voyager_url: str | None = None,
) -> ReplyKeyboardMarkup:
    keyboard = []
    for row in button_rows:
        keyboard_row = []
        for label in row:
            if "Orbit Voyager" in label and voyager_url:
                keyboard_row.append(KeyboardButton(text=label, web_app=WebAppInfo(url=voyager_url)))
            else:
                keyboard_row.append(KeyboardButton(text=label))
        keyboard.append(keyboard_row)
        
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=placeholder,
    )
