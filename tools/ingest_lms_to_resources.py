"""
Copy PDFs from lms/pdfs/ into resources/institutions/<slug>/Quarter_*/…

Week folders in the LMS path (e.g. …/Week 3/…, Week_05, wk-2) are mirrored under:
  …/<course>/weeks/Week_NN/[optional subfolders]/file.pdf

Only PDFs are copied; empty week folders never appear. Original LMS tree is unchanged.

Run: python tools/ingest_lms_to_resources.py [--dry-run]
.env: LMS_IGNORE_SUBMISSION_NAMES=…
.env: HUB_INSTITUTION_SLUG=sit  (optional)
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from hub_institution import INSTITUTION_SLUG, resources_root

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass

LMS_ROOT = ROOT_DIR / "lms" / "pdfs"
DEST_ROOT = resources_root()

COURSE_HINTS: list[tuple[str, str, str, int]] = [
    ("calculus ii", "MATH_1120", "Calculus_II", 2),
    ("calculus i", "MATH_1110", "Calculus_I", 1),
    ("calculus", "MATH_1110", "Calculus_I", 1),
    ("physics ii", "PHYS_1320", "Physics_II", 2),
    ("physics i", "PHYS_1310", "Physics_I", 1),
    ("physics", "PHYS_1310", "Physics_I", 1),
    ("chemistry lab", "CHEML_1211", "Chemistry_Lab", 2),
    ("cheml", "CHEML_1211", "Chemistry_Lab", 2),
    ("chemistry i", "CHEM_1210", "Chemistry_I", 1),
    ("chemistry", "CHEM_1210", "Chemistry_I", 1),
    ("english composition", "ENGL_1610", "English_Composition", 1),
    ("writing", "ENGL_1720", "Writing_Rhetoric_II", 2),
    ("rhetoric", "ENGL_1720", "Writing_Rhetoric_II", 2),
    ("python", "COMP_1210", "Python", 2),
    ("comp_1210", "COMP_1210", "Python", 2),
    ("seminar", "SEM_100", "Advising_Seminar", 2),
    ("advising", "SEM_100", "Advising_Seminar", 2),
]
COURSE_HINTS.sort(key=lambda x: len(x[0]), reverse=True)

SUBMISSION_RE = re.compile(
    r"assignsubmission|submission_file|my\s*submission|your\s*submission|"
    r"feedback\s*on\s*your|graded\s*submission|peer\s*review\s*submission|"
    r"upload\s*assignment|draft\s*submission",
    re.I,
)
DROP_HOMEWORK_IF = re.compile(
    r"graded|feedback\s*copy|instructor\s*comment|latesubmission|resubmission", re.I
)

INVALID_FS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_dir_name(name: str, max_len: int = 80) -> str:
    name = INVALID_FS.sub("_", name.strip())
    name = re.sub(r"\s+", " ", name).strip(". ")
    return (name or "folder")[:max_len]


def _load_ignore_names() -> list[str]:
    raw = os.environ.get("LMS_IGNORE_SUBMISSION_NAMES", "")
    return [x.strip().lower() for x in raw.split(",") if x.strip()]


def should_skip_path(path: Path, rel: Path) -> bool:
    blob = "/".join(rel.parts).lower() + " " + path.name.lower()
    if SUBMISSION_RE.search(blob):
        return True
    for frag in _load_ignore_names():
        if frag in blob:
            return True
    if "assignsubmission" in blob or "submissionstatus" in blob:
        return True
    return False


def match_course(rel: Path, stem: str) -> tuple[str, str, str, int] | None:
    blob = "/".join(rel.parts).lower() + " " + stem.lower()
    for hint, prefix, folder, quarter in COURSE_HINTS:
        if hint in blob:
            return prefix, folder, f"Quarter_{quarter}", quarter
    return None


def parse_week_directory_name(dirname: str) -> int | None:
    """If *dirname* is a week folder label, return week index 1..52."""
    s = dirname.strip()
    m = re.match(r"(?i)^week[_\s-]*(\d{1,2})$", s)
    if m:
        n = int(m.group(1))
        return n if 1 <= n <= 52 else None
    m = re.match(r"(?i)^wk[_\s-]*(\d{1,2})$", s)
    if m:
        n = int(m.group(1))
        return n if 1 <= n <= 52 else None
    m = re.match(r"(?i)^week(\d{2})$", s)
    if m:
        n = int(m.group(1))
        return n if 1 <= n <= 52 else None
    m = re.match(r"(?i)^week(\d{1,2})$", s)
    if m:
        n = int(m.group(1))
        return n if 1 <= n <= 52 else None
    return None


def extract_lms_week_path(rel: Path) -> tuple[int, tuple[str, ...]] | None:
    """
    Find first path segment that names a week folder; return week number and
    directory names *under* that week (excluding the file name).
    Example: Course/Week 3/Slides/a.pdf -> (3, ('Slides',))
    """
    parts = rel.parts
    if len(parts) < 2:
        return None
    dirs = list(parts[:-1])
    for i, d in enumerate(dirs):
        wn = parse_week_directory_name(d)
        if wn is not None:
            under = tuple(sanitize_dir_name(x) for x in dirs[i + 1 :])
            return wn, under
    return None


def looks_like_lecture_notes(blob: str) -> bool:
    low = blob.lower()
    return any(
        k in low
        for k in (
            "lecture note",
            "lecture_notes",
            "lecnotes",
            "class note",
            "slides",
            "slide deck",
            "handout",
            "chapter",
            "ppt",
            "lecture ",
        )
    )


def extract_week_number(blob: str) -> int | None:
    low = blob.lower()
    for pat in (
        r"week[_\s-]*(\d{1,2})",
        r"wk[_\s-]*(\d{1,2})",
        r"(?<![a-z])w(\d{1,2})(?![a-z0-9])",
        r"week(\d{2})",
    ):
        m = re.search(pat, low)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 52:
                return n
    return None


def infer_kind_and_subpath(blob: str) -> tuple[str, Path]:
    low = blob.lower()
    if "syllabus" in low:
        return "syllabus", Path()
    if re.search(r"\bweek\s*\d+|\bwk\s*\d+|week[_\s-]*\d+|(?<![a-z])w\d\d?(?![a-z])", low):
        m = (
            re.search(r"week[_\s-]*(\d+)", low)
            or re.search(r"wk[_\s-]*(\d+)", low)
            or re.search(r"\bw(\d+)\b", low)
        )
        n = int(m.group(1)) if m else 0
        if n > 0:
            return "weeks", Path(f"Week_{n:02d}")
    if any(k in low for k in ("midterm", "final exam", "final_exam")) or re.search(
        r"(?<![a-z])(exam|quiz|test)(?![a-z])", low
    ):
        sub = Path()
        if "final" in low:
            sub = Path("Final")
        elif "midterm" in low:
            sub = Path("Midterm")
        else:
            m = re.search(r"exam[_\s-]*(\d+)", low)
            if m:
                sub = Path(f"Exam_{m.group(1)}")
        return "exams", sub
    if looks_like_lecture_notes(blob):
        if "homework" in low or re.search(r"\bhw\d", low):
            return "homework", Path()
        return "lecture_notes", Path()
    if any(
        k in low
        for k in (
            "lecture",
            "slide",
            "slides",
            "chapter",
            "notes",
            "handout",
            "reading",
            "textbook",
        )
    ):
        if "homework" in low or re.search(r"\bhw\d", low):
            return "homework", Path()
        return "lecture_notes", Path()
    if "homework" in low or re.search(r"\bhw[_\s-]?\d", low) or low.startswith("hw"):
        return "homework", Path()
    if "recording" in low or "lecture_capture" in low or "panopto" in low:
        return "lecture_recordings", Path()
    if "breakout" in low or ("discussion" in low and "sheet" in low):
        return "breakout_sessions", Path()
    if "assignment" in low or "assign" in low:
        return "assignments", Path()
    return "readings", Path()


def safe_stem(s: str, max_len: int = 70) -> str:
    s = re.sub(r"[^\w\-]+", "_", s, flags=re.UNICODE).strip("_")
    return s[:max_len] or "file"


def kind_token(category: str) -> str:
    return {
        "lecture_notes": "lecnotes",
        "exams": "exams",
        "syllabus": "syllabus",
        "readings": "readings",
        "homework": "hw",
        "weeks": "weekpack",
        "lecture_recordings": "recordings",
        "breakout_sessions": "breakout",
        "assignments": "assign",
    }.get(category, category)


def build_filename_non_week(
    prefix: str,
    quarter: int,
    category: str,
    sub: Path,
    original_stem: str,
    blob: str,
) -> str:
    parts: list[str] = [prefix, f"Q{quarter}", kind_token(category)]
    wk = extract_week_number(blob + " " + original_stem)
    if category in ("lecture_notes", "readings") and looks_like_lecture_notes(blob):
        if wk is not None:
            parts.append(f"W{wk:02d}")
    elif category == "weeks" and sub.parts:
        m = re.match(r"(?i)week[_\s-]*(\d+)", sub.parts[0])
        if m:
            parts.append(f"W{int(m.group(1)):02d}")
    elif category == "exams" and sub.parts:
        parts.append(safe_stem(sub.parts[0], 40))
    elif wk is not None and category not in ("exams", "syllabus"):
        parts.append(f"W{wk:02d}")
    parts.append(safe_stem(original_stem))
    return "_".join(parts) + ".pdf"


def build_filename_week_row(
    prefix: str,
    quarter: int,
    week_num: int,
    under_week: tuple[str, ...],
    original_stem: str,
) -> str:
    parts: list[str] = [prefix, f"Q{quarter}", "weekpack", f"W{week_num:02d}"]
    for seg in under_week:
        if seg:
            parts.append(safe_stem(seg, 50))
    parts.append(safe_stem(original_stem))
    return "_".join(parts) + ".pdf"


def dest_path_for(
    quarter_name: str,
    course_folder: str,
    category: str,
    sub: Path,
    filename: str,
) -> Path:
    base = DEST_ROOT / quarter_name / course_folder / category
    if sub.parts:
        base = base / sub
    base.mkdir(parents=True, exist_ok=True)
    return base / filename


def ingest_one(src: Path, rel: Path, dry_run: bool) -> str | None:
    if src.suffix.lower() != ".pdf":
        return None
    if should_skip_path(src, rel):
        return f"skip submission-like: {rel}"
    matched = match_course(rel, src.stem)
    if not matched:
        prefix = "MISC"
        course_folder = "_Unsorted"
        quarter_name = "Quarter_1"
        quarter = 1
    else:
        prefix, course_folder, quarter_name, quarter = matched

    blob = "/".join(rel.parts) + " " + src.stem

    week_path = extract_lms_week_path(rel)
    if week_path is not None:
        week_num, under_week = week_path
        category = "weeks"
        sub = Path(f"Week_{week_num:02d}")
        for seg in under_week:
            if seg:
                sub = sub / seg
        fname = build_filename_week_row(prefix, quarter, week_num, under_week, src.stem)
        dest = dest_path_for(quarter_name, course_folder, category, sub, fname)
    else:
        category, sub = infer_kind_and_subpath(blob)
        if category == "readings" and looks_like_lecture_notes(blob):
            category = "lecture_notes"
        if category == "homework" and DROP_HOMEWORK_IF.search(blob.lower()):
            return f"skip graded/feedback homework copy: {rel}"
        fname = build_filename_non_week(prefix, quarter, category, sub, src.stem, blob)
        dest = dest_path_for(quarter_name, course_folder, category, sub, fname)

    if dest.exists():
        stem = dest.stem
        suf = dest.suffix
        n = 1
        while dest.exists():
            dest = dest.parent / f"{stem}_dup{n}{suf}"
            n += 1
    if dry_run:
        return f"copy -> {dest.relative_to(DEST_ROOT)}"
    shutil.copy2(src, dest)
    return f"ok: {dest.relative_to(DEST_ROOT)}"


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Ingest lms/pdfs into resources/institutions/<slug>/Quarter_*/ (copy + rename)."
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not LMS_ROOT.is_dir():
        print(f"LMS folder not found: {LMS_ROOT}")
        return
    DEST_ROOT.mkdir(parents=True, exist_ok=True)
    copied = 0
    skipped = 0
    for src in sorted(LMS_ROOT.rglob("*.pdf")):
        try:
            rel = src.relative_to(LMS_ROOT)
        except ValueError:
            continue
        if ".lms_download_state" in rel.parts:
            continue
        msg = ingest_one(src, rel, args.dry_run)
        if not msg:
            continue
        if msg.startswith("skip"):
            skipped += 1
            print(msg)
        else:
            copied += 1
            print(msg)
    print(f"Done. dest={DEST_ROOT} (slug={INSTITUTION_SLUG}) copied={copied} skipped={skipped}")


if __name__ == "__main__":
    main()
