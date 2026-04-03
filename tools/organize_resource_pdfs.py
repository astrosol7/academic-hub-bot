"""
Put loose PDFs into resources/Quarter_*/<Course>/<category>/[subfolder]/
by reading the filename (course code, type: syllabus / exam / quiz / test).

Exam files are sorted into subfolders when the name contains Exam 1, Final, Midterm, etc.

Run from project root:
  python tools/organize_resource_pdfs.py
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "resources"

PREFIX_MAP: dict[str, tuple[str, str]] = {
    "MATH_1110": ("Quarter_1", "Calculus_I"),
    "PHYS_1310": ("Quarter_1", "Physics_I"),
    "CHEM_1210": ("Quarter_1", "Chemistry_I"),
    "ENGL_1610": ("Quarter_1", "English_Composition"),
    "COMP_1210": ("Quarter_2", "Python"),
    "CHEML_1211": ("Quarter_2", "Chemistry_Lab"),
    "CHEML1211": ("Quarter_2", "Chemistry_Lab"),
    "ENGL_1720": ("Quarter_2", "Writing_Rhetoric_II"),
    "MATH_1120": ("Quarter_2", "Calculus_II"),
    "PHYS_1320": ("Quarter_2", "Physics_II"),
    "SEM_100": ("Quarter_2", "Advising_Seminar"),
    "SEM100": ("Quarter_2", "Advising_Seminar"),
}


def top_category(rest_lower: str) -> str:
    if "syllabus" in rest_lower:
        return "syllabus"
    if "homework" in rest_lower or rest_lower.startswith("hw_") or "_hw_" in rest_lower:
        return "homework"
    if any(
        k in rest_lower
        for k in (
            "recording",
            "lecture_capture",
            "panopto",
            "echo360",
            "zoom_rec",
        )
    ):
        return "lecture_recordings"
    if "quiz" in rest_lower:
        return "quizzes"
    if "midterm" in rest_lower or "final" in rest_lower:
        return "exams"
    if "exam" in rest_lower:
        return "exams"
    if "test" in rest_lower:
        return "tests"
    return "readings"


def exam_subpath(rest: str) -> Path:
    """Under exams/ — e.g. Exam_1/, Final/, Midterm/, or flat."""
    low = rest.lower()
    if "final" in low:
        return Path("Final")
    if "midterm" in low:
        return Path("Midterm")
    m = re.search(r"exam[_\s-]*(\d+)", low)
    if m:
        return Path(f"Exam_{m.group(1)}")
    if "exam" in low:
        return Path("General")
    return Path()


def parse_prefix(filename: str) -> tuple[str, str, str] | None:
    p = Path(filename)
    stem = p.stem
    if p.suffix.lower() != ".pdf":
        return None
    ext = p.suffix
    m = re.match(r"^([A-Za-z]+_?\d+)_Q(\d)_(.+)$", stem)
    if m:
        prefix = m.group(1).upper().replace("CHEML1211", "CHEML_1211")
        rest = m.group(3)
        return prefix, rest, ext
    m2 = re.match(r"^([A-Za-z]+_?\d+)_(.+)$", stem)
    if m2:
        return m2.group(1).upper(), m2.group(2), ext
    return None


def dest_dir_for(prefix: str, rest: str) -> Path | None:
    if prefix not in PREFIX_MAP:
        return None
    q_dir, course_dir = PREFIX_MAP[prefix]
    rest_l = rest.lower()
    cat = top_category(rest_l)
    base = ROOT / q_dir / course_dir / cat
    if cat == "exams":
        sub = exam_subpath(rest)
        if sub.parts:
            base = base / sub
    base.mkdir(parents=True, exist_ok=True)
    return base


def move_file(src: Path) -> str | None:
    parsed = parse_prefix(src.name)
    if not parsed:
        return None
    prefix, rest, _ext = parsed
    dest_d = dest_dir_for(prefix, rest)
    if dest_d is None:
        return None
    dest = dest_d / src.name
    if dest.resolve() == src.resolve():
        return "skip"
    if dest.exists():
        dest = dest_d / f"{Path(src).stem}_dup{src.suffix}"
    shutil.move(str(src), str(dest))
    return f"{src.name} -> {dest.relative_to(ROOT)}"


def _under_quarter_tree(p: Path) -> bool:
    try:
        rel = p.relative_to(ROOT).parts
    except ValueError:
        return False
    return bool(rel) and rel[0].startswith("Quarter_")


def main() -> None:
    moved = 0
    for src in sorted(ROOT.rglob("*.pdf")):
        if _under_quarter_tree(src):
            continue
        res = move_file(src)
        if res and res != "skip":
            print(res)
            moved += 1
    print(f"Done. Moved: {moved}")


if __name__ == "__main__":
    main()
