"""Academic Hub data: short labels, quarter-first paths, Telegram links, overviews."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TypedDict

from hub_format import overview_title, ov_goal, ov_lines_section, tiny_rule

PACKAGE_ROOT = Path(__file__).resolve().parent
RESOURCES_ROOT = PACKAGE_ROOT / "resources"

# ── Telegram links ─────────────────────────────────────────
HUB_FORUM_INVITE = "https://t.me/+q3y__foMScVmODg0"

TOPICS: dict[str, tuple[str, str]] = {
    "programming": ("https://t.me/c/3653709098/766", "Programming"),
    "academic_discussions": ("https://t.me/c/3653709098/1", "Academic Discussions"),
    "english": ("https://t.me/c/3653709098/9", "English"),
    "maths": ("https://t.me/c/3653709098/5", "Maths"),
    "resource_index": ("https://t.me/c/3653709098/1034", "Resource Index"),
    "physics": ("https://t.me/c/3653709098/7", "Physics"),
    "announcements": ("https://t.me/c/3653709098/1121", "Announcements"),
    "chemistry": ("https://t.me/c/3653709098/3", "Chemistry"),
}

# On-disk layout: resources/Quarter_<n>/<Folder>/<category>/files
# Categories used for file delivery:
FILE_CATEGORIES = (
    "exams",
    "quizzes",
    "tests",
    "readings",
    "lecture_notes",
    "lecture_recordings",
    "breakout_sessions",
    "assignments",
    "homework",
)

# Syllabus = own button. “More files” adds recordings (required), homework, etc.
EXTRA_FILE_LABELS: list[tuple[str, str]] = [
    ("lecture_recordings", "Lecture recordings"),
    ("homework", "Homework"),
    ("lecture_notes", "Lecture notes"),
    ("breakout_sessions", "Breakout notes"),
    ("assignments", "Assignments"),
]


class Course(TypedDict):
    """Internal record; students only see `title` and overview when requested."""

    title: str  # short UI name, no catalog code
    quarter: int
    folder: str  # e.g. Calculus_I — under Quarter_1/
    topic_key: str
    overview_html: str
    hub_links_blurb: str  # short reuse for Forum/Resources screen


def _link(topic_key: str) -> str:
    url, label = TOPICS[topic_key]
    return f'<a href="{url}">{label}</a>'


def _hub_blurb(topic_key: str) -> str:
    return (
        f'{_link("resource_index")} · {_link("announcements")} · '
        f'Subject: {_link(topic_key)}'
    )


def _overview_card(
    title: str,
    goal: str,
    grading: list[str],
    dates: list[str],
    tools: list[str],
    focus: list[str],
) -> str:
    """Readable on mobile: sections + bullets, subtle emoji."""
    parts = [
        overview_title(title),
        tiny_rule(),
        ov_goal("\U0001f3af", goal),
        ov_lines_section("\U0001f4ca", "Grading", grading),
        ov_lines_section("\U0001f4c5", "Key dates", dates),
        ov_lines_section("\U0001f6e0\ufe0f", "Tools", tools),
        ov_lines_section("\u2726", "Focus areas", focus),
    ]
    return "\n".join(parts)


COURSES: dict[str, Course] = {
    "calculus_i": Course(
        title="Calculus I",
        quarter=1,
        folder="Calculus_I",
        topic_key="maths",
        overview_html=_overview_card(
            "Calculus I",
            "Differentiation and integration in one variable, with engineering applications.",
            [
                "Final exam — 20%",
                "Tests — 45% (three × 15%)",
                "Quizzes — 15%",
                "Homework — 10%",
                "Projects — 10%",
            ],
            [
                "Test 1 (Ch.1–2) — weeks 2–3",
                "Test 2 (Ch.3–4) — weeks 7–8",
                "Test 3 (Ch.5–6) — weeks 11–12",
                "Final exam — week 12 (comprehensive)",
            ],
            [
                "Text: Calculus Early Transcendentals (9e), Stewart",
                "Software: Mathematica or MATLAB",
            ],
            [
                "Limits and continuity",
                "Derivative rules and related rates",
                "Optimization",
                "Fundamental theorem and integration",
            ],
        ),
        hub_links_blurb=_hub_blurb("maths"),
    ),
    "physics_i": Course(
        title="Physics I",
        quarter=1,
        folder="Physics_I",
        topic_key="physics",
        overview_html=_overview_card(
            "Physics I",
            "Calculus-based mechanics, waves, and thermodynamics.",
            [
                "Assignments — 33% (eleven group tasks)",
                "Quizzes — 24% (eight)",
                "Final exam — 23%",
                "Tests — 20% (two)",
            ],
            [
                "Exam 1 (Ch.1–3) — week 3",
                "Test 1 — week 6",
                "Exam 2 (Ch.5–16) — weeks 8–9",
                "Final exam — week 12",
            ],
            [
                "Text: Physics for Scientists and Engineers (Serway & Jewett)",
                "Strong vector fluency assumed",
            ],
            [
                "Newton’s laws and dynamics",
                "Energy and momentum",
                "Oscillations and waves",
                "Thermodynamics and kinetic theory",
            ],
        ),
        hub_links_blurb=_hub_blurb("physics"),
    ),
    "chemistry_i": Course(
        title="Chemistry I",
        quarter=1,
        folder="Chemistry_I",
        topic_key="chemistry",
        overview_html=_overview_card(
            "Chemistry I",
            "Accelerated introduction to core chemistry and lab reasoning.",
            [
                "Exams — 60% (four; lowest one dropped)",
                "Quizzes — 25% (six; lowest one dropped)",
                "Homework — 15% (twelve)",
            ],
            [
                "Exam 1 (Ch.1–4) — week 4",
                "Exam 2 (Ch.5–8) — week 8",
                "Exam 3 (Ch.9–11) — week 11",
                "Final exam — week 12",
            ],
            [
                "Text: Chemistry: A Molecular Approach (5e), Tro",
                "Lab PPE: coat, goggles, gloves (required)",
            ],
            [
                "Stoichiometry and quantities",
                "Atomic structure and bonding",
                "Thermochemistry",
                "Kinetics and equilibrium",
            ],
        ),
        hub_links_blurb=_hub_blurb("chemistry"),
    ),
    "english_comp": Course(
        title="English Composition",
        quarter=1,
        folder="English_Composition",
        topic_key="english",
        overview_html=_overview_card(
            "English Composition",
            "Foundations of academic writing, revision, and ethical source use.",
            [
                "Weights and rubrics — see syllabus PDF",
                "Due dates — announced on LMS and Hub",
            ],
            [
                "Draft checkpoints — per instructor schedule",
                "Revision windows — per syllabus",
            ],
            [
                "Program handbook and readings",
                "Discussion: Academic Hub — English topic",
            ],
            [
                "Thesis and structure",
                "Evidence and citation",
                "Revision practice",
                "Audience and clarity",
            ],
        ),
        hub_links_blurb=_hub_blurb("english"),
    ),
    "python": Course(
        title="Python",
        quarter=2,
        folder="Python",
        topic_key="programming",
        overview_html=_overview_card(
            "Python",
            "Project-based Python for algorithmic thinking and STEM workflows.",
            [
                "Projects — 40%",
                "Final exam — 20%",
                "Midterm — 15%",
                "Quizzes — 15%",
                "Exercises — 10%",
            ],
            [
                "Midterm — week 6",
                "Final project — due week 11",
                "Final exam — week 12",
            ],
            [
                "Python 3.x",
                "IDE: VS Code or PyCharm",
                "Google Colab when assigned",
            ],
            [
                "Control flow (loops, conditionals)",
                "Functions and modular code",
                "Lists, dicts, tuples",
                "Simple physical models",
            ],
        ),
        hub_links_blurb=_hub_blurb("programming"),
    ),
    "chemistry_lab": Course(
        title="Chemistry Lab",
        quarter=2,
        folder="Chemistry_Lab",
        topic_key="chemistry",
        overview_html=_overview_card(
            "Chemistry Lab",
            "Hands-on experiments, simulations, and quantitative analysis.",
            [
                "Lab reports — 60%",
                "Pre-lab assignments — 20%",
                "Final exam — 20%",
            ],
            [
                "Weekly lab sessions — ten total",
                "Final lab exam — week 12",
            ],
            [
                "PPE required (coat, goggles, gloves)",
                "Lab manual and scientific calculator",
            ],
            [
                "Safety and measurement",
                "Stoichiometry and limiting reactants",
                "Titration and equilibrium",
                "Calorimetry",
            ],
        ),
        hub_links_blurb=_hub_blurb("chemistry"),
    ),
    "writing_ii": Course(
        title="Writing & Rhetoric II",
        quarter=2,
        folder="Writing_Rhetoric_II",
        topic_key="english",
        overview_html=_overview_card(
            "Writing & Rhetoric II",
            "Advanced technical and scientific writing; professional documents.",
            [
                "White paper project — 40%",
                "Midterm and final tests — 20%",
                "Assignments — 20%",
                "Participation — 20%",
            ],
            [
                "Midterm — week 6",
                "White paper final draft — week 11",
                "Final exam — week 12",
            ],
            [
                "APA (7th) as specified",
                "Peer-reviewed databases as assigned",
            ],
            [
                "Five canons of rhetoric",
                "Audience and ethics",
                "Evidence-based argument",
                "Professional format",
            ],
        ),
        hub_links_blurb=_hub_blurb("english"),
    ),
    "calculus_ii": Course(
        title="Calculus II",
        quarter=2,
        folder="Calculus_II",
        topic_key="maths",
        overview_html=_overview_card(
            "Calculus II",
            "Integration, series, and selected multivariable tools for engineers.",
            [
                "Final exam — 20%",
                "Tests — 45% (three × 15%)",
                "Quizzes — 15%",
                "Homework — 10%",
                "Projects — 10%",
            ],
            [
                "Test 1 — weeks 2–3",
                "Test 2 — weeks 7–8",
                "Test 3 — weeks 11–12",
                "Final exam — week 12",
            ],
            [
                "Text: Calculus Early Transcendentals, Stewart",
                "Mathematica or MATLAB",
            ],
            [
                "Advanced integration techniques",
                "Improper and numerical integration",
                "Power and Taylor series",
                "Parametric, polar, and vectors",
            ],
        ),
        hub_links_blurb=_hub_blurb("maths"),
    ),
    "physics_ii": Course(
        title="Physics II",
        quarter=2,
        folder="Physics_II",
        topic_key="physics",
        overview_html=_overview_card(
            "Physics II",
            "Calculus-based E&M, Maxwell framework, and geometrical optics.",
            [
                "Exams — 60% (four)",
                "Assignments — 20% (ten)",
                "Project — 20% (one)",
            ],
            [
                "Exam 1 — week 3",
                "Exam 2 — week 6",
                "Exam 3 — week 9",
                "Final exam — week 12",
            ],
            [
                "Text: Physics for Scientists and Engineers (Serway & Jewett)",
            ],
            [
                "Electric fields and Gauss’s law",
                "Capacitance, current, resistance",
                "Magnetism and induction",
                "Waves and optics",
            ],
        ),
        hub_links_blurb=_hub_blurb("physics"),
    ),
    "seminar": Course(
        title="Seminar",
        quarter=2,
        folder="Advising_Seminar",
        topic_key="academic_discussions",
        overview_html=_overview_card(
            "Seminar",
            "Orientation to programmes, research pathways, and school culture.",
            [
                "Attendance — 100% (mandatory)",
            ],
            [
                "Saturdays 09:00–10:30",
                "Final session — week 12",
            ],
            [
                "Meetings with leadership across disciplines",
            ],
            [
                "Programme and lab exposure",
                "Careers and entrepreneurship",
                "Ethics and innovation",
                "Professional development",
            ],
        ),
        hub_links_blurb=_hub_blurb("academic_discussions"),
    ),
}

# Order within each quarter (minimal steps in UI)
QUARTER_COURSES: dict[int, list[str]] = {
    1: ["calculus_i", "physics_i", "chemistry_i", "english_comp"],
    2: ["python", "chemistry_lab", "writing_ii", "calculus_ii", "physics_ii", "seminar"],
}

TITLE_TO_ID: dict[str, str] = {COURSES[cid]["title"]: cid for cid in COURSES}


# ── Paths ──────────────────────────────────────────────────
def quarter_dir(q: int) -> Path:
    return RESOURCES_ROOT / f"Quarter_{q}"


def course_dir(course_id: str) -> Path:
    c = COURSES[course_id]
    return quarter_dir(c["quarter"]) / c["folder"]


def category_dir(course_id: str, category: str) -> Path:
    return course_dir(course_id) / category


def iter_files_in_dir(d: Path) -> list[Path]:
    if not d.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(d.rglob("*")):
        if not p.is_file() or p.name.startswith("."):
            continue
        if any(part.startswith(".") or part == "__pycache__" for part in p.parts):
            continue
        out.append(p)
    return out


def iter_quarter_category(quarter: int, category: str) -> list[tuple[Path, str]]:
    """
    All files under Quarter_q/*/category/ with display prefix from course folder.
    Returns (path, caption_base) where caption is "{Course Title} — {friendly file label}".
    """
    out: list[tuple[Path, str]] = []
    base = quarter_dir(quarter)
    if not base.is_dir():
        return out

    folder_titles = {COURSES[cid]["folder"]: COURSES[cid]["title"] for cid in COURSES if COURSES[cid]["quarter"] == quarter}

    for folder, display in sorted(folder_titles.items()):
        cat = base / folder / category
        for p in iter_files_in_dir(cat):
            friendly = human_file_label(p.stem)
            caption = f"{display} — {friendly}"
            out.append((p, caption))
    out.sort(key=lambda x: (x[1], str(x[0])))
    return out


def iter_course_category(course_id: str, category: str) -> list[tuple[Path, str]]:
    c = COURSES[course_id]
    display = c["title"]
    cat = category_dir(course_id, category)
    return [(p, f"{display} — {human_file_label(p.stem)}") for p in iter_files_in_dir(cat)]


def iter_course_syllabus(course_id: str) -> list[tuple[Path, str]]:
    """Syllabus PDFs live in syllabus/ (preferred dump) or readings/."""
    c = COURSES[course_id]
    display = c["title"]
    seen: set[Path] = set()
    out: list[tuple[Path, str]] = []
    for sub in ("syllabus", "readings"):
        for p in iter_files_in_dir(course_dir(course_id) / sub):
            r = p.resolve()
            if r in seen:
                continue
            seen.add(r)
            out.append((p, f"{display} — {human_file_label(p.stem)}"))
    out.sort(key=lambda x: (x[1], str(x[0])))
    return out


def human_file_label(stem: str) -> str:
    """Label after stripping typical COURSE_Qn_ prefix from stems."""
    stripped = re.sub(r"^[A-Za-z]+_?\d+_Q\d+_", "", stem, flags=re.I)
    raw = (stripped or stem).replace("_", " ").strip()
    if not raw:
        return "File"
    return " ".join(w.capitalize() for w in raw.split())
