from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Overview:
    goal: str
    grading: tuple[str, ...]
    dates: tuple[str, ...]
    tools: tuple[str, ...]
    focus: tuple[str, ...]


@dataclass(frozen=True)
class CategoryDefinition:
    slug: str
    label: str
    icon: str
    placements: tuple[str, ...]
    aliases: tuple[str, ...]
    storage_folders: tuple[str, ...]
    searchable: bool = True
    sendable: bool = True


@dataclass(frozen=True)
class CourseManifest:
    id: str
    title: str
    quarter: int
    folder: str
    aliases: tuple[str, ...]
    search_terms: tuple[str, ...]
    kind: str
    supports_weeks: bool
    week_count: int
    top_level_actions: tuple[str, ...]
    more_files_actions: tuple[str, ...]
    week_actions: tuple[str, ...]
    overview: Overview


@dataclass(frozen=True)
class InstitutionManifest:
    slug: str
    display_name: str
    quarter_labels: dict[int, str]
    quarter_order: dict[int, tuple[str, ...]]
    course_files: tuple[str, ...]


@dataclass(frozen=True)
class ResourceFile:
    path: Path
    label: str
    course_id: str
    category_slug: str
    week_number: int | None = None
    source_hint: str = ""


@dataclass(frozen=True)
class SearchQuery:
    raw_text: str
    tokens: tuple[str, ...]
    week_number: int | None = None
    category_slug: str | None = None
    wants_syllabus: bool = False


@dataclass(frozen=True)
class SearchResult:
    score: int
    label: str
    course_id: str
    action: str
    category_slug: str | None = None
    week_number: int | None = None
    syllabus_only: bool = False


@dataclass(frozen=True)
class SearchResolution:
    kind: str
    result: SearchResult | None = None
    message: str = ""
    course_id: str | None = None
    course_ids: tuple[str, ...] = ()
    category_slugs: tuple[str, ...] = ()
    week_number: int | None = None
    syllabus_only: bool = False


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "error")

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")


@dataclass(frozen=True)
class ScreenView:
    key: str
    text: str
    button_rows: tuple[tuple[str, ...], ...]
    placeholder: str = "Choose..."


@dataclass(frozen=True)
class TelegramSession:
    level: str = "home"
    quarter: int | None = None
    course_id: str | None = None
    section: str | None = None
    week_number: int | None = None


@dataclass
class SendOutcome:
    sent_count: int = 0
    failed_items: list[ResourceFile] = field(default_factory=list)
    cancelled: bool = False
