"""
Telegram HTML helpers. SIT palette is for future graphics / Mini Apps only.
"""

from __future__ import annotations

import html

COLOR_PRIMARY = "#02272F"
COLOR_ACCENT = "#F15A24"
COLOR_SECONDARY_1 = "#CFDFDC"
COLOR_SECONDARY_2 = "#8AC4C7"
COLOR_SECONDARY_3 = "#EEBE41"
COLOR_SECONDARY_4 = "#EAE4D2"


def mono(s: str) -> str:
    return f"<code>{html.escape(s)}</code>"


def bq(lines: str) -> str:
    inner = html.escape(lines.strip())
    return f"<blockquote>{inner}</blockquote>"


def head(s: str) -> str:
    return f"<b>{html.escape(s)}</b>"


def subhead(s: str) -> str:
    return f"<u>{html.escape(s)}</u>"


def overview_title(course_name: str, shelf_emoji: str = "\N{BOOKS}") -> str:
    """Readable, shareable Telegram overview title."""
    return (
        f"{shelf_emoji} <b>{html.escape(course_name)}</b>\n"
        "<i>Quick overview</i>"
    )


def ov_goal(icon: str, text: str) -> str:
    return f"{icon} <b>Goal</b>\n{bq(text)}"


def ov_lines_section(icon: str, label: str, lines: list[str]) -> str:
    """Fast-scan bullet block with breathing room."""
    esc = "\n".join(f"• {html.escape(line)}" for line in lines)
    return f"{icon} <b>{html.escape(label)}</b>\n{esc}"


def tiny_rule() -> str:
    return "<tg-spoiler>────────</tg-spoiler>"


def overview_card(*parts: str) -> str:
    clean_parts = [part.strip() for part in parts if part and part.strip()]
    return "\n\n".join(clean_parts)
