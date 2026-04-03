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
    """Institutional card title."""
    return f"{shelf_emoji} <b>{html.escape(course_name)}</b>\n<i>At-a-glance</i>"


def ov_goal(icon: str, text: str) -> str:
    return f"{icon} <b>Goal</b>\n{bq(text)}"


def ov_lines_section(icon: str, label: str, lines: list[str]) -> str:
    """Fast-scan bullet block."""
    esc = "\n".join(f"  \u25b8 {html.escape(line)}" for line in lines)
    return f"{icon} <b>{html.escape(label)}</b>\n{esc}"


def tiny_rule() -> str:
    return "<i>-- -- --</i>"
