from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


SPACE_RE = re.compile(r"\s+")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
COURSE_PREFIX_RE = re.compile(r"^[A-Za-z]+_?\d+_Q\d+_", re.I)
GENERIC_PREFIX_RE = re.compile(
    r"^(?:weekpack|readings?|lecture|lecture_notes|lecnotes|recordings?|"
    r"breakout|breakout_notes|syllabus)_",
    re.I,
)
LEADING_WEEK_RE = re.compile(r"^(?:W\d{1,2}|Week[_ -]?\d{1,2})_", re.I)
WEEK_IN_TEXT_RE = re.compile(r"(?i)\b(?:week|wk)[\s_-]*(\d{1,2})\b|\bw(\d{1,2})\b")
SYLLABUS_RE = re.compile(r"syllabus", re.I)


def normalize_text(value: str) -> str:
    cleaned = NON_ALNUM_RE.sub(" ", value.casefold())
    return SPACE_RE.sub(" ", cleaned).strip()


def tokenize(value: str) -> tuple[str, ...]:
    normalized = normalize_text(value)
    if not normalized:
        return ()
    return tuple(part for part in normalized.split(" ") if part)


def chunked(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def parse_week_number(value: str) -> int | None:
    match = WEEK_IN_TEXT_RE.search(value)
    if not match:
        return None
    raw = match.group(1) or match.group(2)
    if not raw:
        return None
    number = int(raw)
    if 1 <= number <= 52:
        return number
    return None


def canonical_week_folder(week_number: int) -> str:
    return f"Week_{week_number:02d}"


def is_valid_week_folder(name: str) -> bool:
    return bool(re.fullmatch(r"Week_\d{2}", name))


def looks_like_syllabus(path: Path | str) -> bool:
    blob = str(path)
    return bool(SYLLABUS_RE.search(blob))


def humanize_file_label(stem: str) -> str:
    value = COURSE_PREFIX_RE.sub("", stem)
    while True:
        updated = GENERIC_PREFIX_RE.sub("", value)
        updated = LEADING_WEEK_RE.sub("", updated)
        if updated == value:
            break
        value = updated
    value = re.sub(r"_(?:dup\d+|docx|pptx|pdf)$", "", value, flags=re.I)
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value).strip(" -_")
    return value or stem.replace("_", " ")


def infer_category_slug(path: Path, *, default_slug: str = "readings") -> str:
    blob = normalize_text(" ".join(path.parts))
    if "syllabus" in blob:
        return "readings"
    if "project" in blob:
        return "projects"
    if "breakout" in blob or "discussion" in blob:
        return "breakout_notes"
    if any(token in blob for token in ("recording", "panopto", "zoom", "video")):
        return "lecture_recordings"
    if "homework" in blob or re.search(r"\bhw\b", blob):
        return "homework"
    if "assignment" in blob:
        return "assignments"
    if any(token in blob for token in ("quiz", "exam", "test", "midterm", "final")):
        return "exams"
    if any(token in blob for token in ("lecture", "notes", "slides", "chapter", "ppt", "powerpoint")):
        return "lecture_notes"
    return default_slug


def score_overlap(query_tokens: Iterable[str], candidate_tokens: Iterable[str]) -> int:
    candidate_set = set(candidate_tokens)
    return sum(1 for token in query_tokens if token in candidate_set)
