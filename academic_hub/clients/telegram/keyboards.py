from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def build_reply_keyboard(
    button_rows: tuple[tuple[str, ...], ...],
    *,
    placeholder: str = "Choose...",
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=label) for label in row]
            for row in button_rows
        ],
        resize_keyboard=True,
        input_field_placeholder=placeholder,
    )
