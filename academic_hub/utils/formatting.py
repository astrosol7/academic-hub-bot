from __future__ import annotations

import html

from academic_hub.domain.models import Overview


def escape(value: str) -> str:
    return html.escape(value)


def bold(value: str) -> str:
    return f"<b>{escape(value)}</b>"


def italic(value: str) -> str:
    return f"<i>{escape(value)}</i>"


def render_overview(course_title: str, overview: Overview) -> str:
    sections = [
        bold(f"{course_title} Overview"),
        f"{bold('Goal')}\n{escape(overview.goal)}",
        _render_lines("Grading", overview.grading),
        _render_lines("Key dates", overview.dates),
        _render_lines("Tools", overview.tools),
        _render_lines("Focus areas", overview.focus),
    ]
    return "\n\n".join(part for part in sections if part.strip())


def _render_lines(label: str, lines: tuple[str, ...]) -> str:
    if not lines:
        return ""
    items = "\n".join(f"• {escape(line)}" for line in lines)
    return f"{bold(label)}\n{items}"

