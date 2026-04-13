from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _normalize_slug(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def _normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip().strip("/")


def _normalize_text_tuple(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if not isinstance(values, (list, tuple)):
        raise TypeError("Expected a list or tuple of strings.")
    items = [_normalize_text(str(value)) for value in values if str(value).strip()]
    return tuple(dict.fromkeys(items))


def _normalize_slug_tuple(values: Any) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_normalize_slug(value) for value in _normalize_text_tuple(values)))


def _normalize_path_tuple(values: Any) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_normalize_path(value) for value in _normalize_text_tuple(values)))


def _normalize_int_tuple(values: Any) -> tuple[int, ...]:
    if values is None:
        return ()
    if not isinstance(values, (list, tuple)):
        raise TypeError("Expected a list or tuple of integers.")
    normalized: list[int] = []
    for value in values:
        if isinstance(value, bool):
            raise TypeError("Boolean values are not valid integers here.")
        normalized.append(int(value))
    return tuple(dict.fromkeys(normalized))


class HubEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class CourseKind(HubEnum):
    STANDARD = "standard"
    SEMINAR = "seminar"


class CategoryPlacement(HubEnum):
    TOP_LEVEL = "top_level"
    MORE_FILES = "more_files"
    WEEK_LEVEL = "week_level"


class SearchAction(HubEnum):
    OPEN_COURSE = "open_course"
    OPEN_WEEK = "open_week"
    SEND_COURSE_CATEGORY = "send_course_category"
    SEND_WEEK_CATEGORY = "send_week_category"


class SearchResolutionKind(HubEnum):
    MATCH = "match"
    MISSING_COURSE = "missing_course"
    AMBIGUOUS_COURSE = "ambiguous_course"
    MISSING_CATEGORY = "missing_category"
    AMBIGUOUS_CATEGORY = "ambiguous_category"
    INVALID_WEEK = "invalid_week"
    NO_MATCH = "no_match"


class ValidationSeverity(HubEnum):
    ERROR = "error"
    WARNING = "warning"


class SessionLevel(HubEnum):
    HOME = "home"
    RESOURCES = "resources"
    QUARTER = "quarter"
    COURSE = "course"


class SessionMode(HubEnum):
    HOME = "home"
    BROWSE = "browse"
    SEARCH = "search"
    REPORT = "report"


class SessionSection(HubEnum):
    HOME = "home"
    RESOURCES = "resources"
    COURSE_MENU = "course_menu"
    OVERVIEW = "overview"
    MORE_FILES = "more_files"
    WEEK_LIST = "week_list"
    WEEK_CATEGORY = "week_category"
    ABOUT = "about"
    REPORT = "report"
    SUGGEST = "suggest"


class NavigationAction(HubEnum):
    GO_HOME = "go_home"
    GO_RESOURCES = "go_resources"
    GO_QUARTER = "go_quarter"
    GO_COURSE = "go_course"
    SHOW_OVERVIEW = "show_overview"
    GO_MORE_FILES = "go_more_files"
    GO_WEEK_LIST = "go_week_list"
    GO_WEEK_CATEGORY = "go_week_category"


class DeliveryScope(HubEnum):
    COURSE = "course"
    MORE = "more"
    WEEK = "week"


class Overview(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    goal: str
    grading: tuple[str, ...] = ()
    dates: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    focus: tuple[str, ...] = ()

    @field_validator("goal", mode="before")
    @classmethod
    def normalize_goal(cls, value: Any) -> str:
        text = _normalize_text(str(value))
        if not text:
            raise ValueError("Overview goal cannot be empty.")
        return text

    @field_validator("grading", "dates", "tools", "focus", mode="before")
    @classmethod
    def normalize_lines(cls, value: Any) -> tuple[str, ...]:
        return _normalize_text_tuple(value)


class CategoryDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    slug: str
    label: str
    icon: str = ""
    placements: tuple[CategoryPlacement, ...]
    aliases: tuple[str, ...] = ()
    storage_folders: tuple[str, ...]
    searchable: bool = True
    sendable: bool = True
    course_specific: bool = False

    @field_validator("slug", mode="before")
    @classmethod
    def normalize_slug(cls, value: Any) -> str:
        slug = _normalize_slug(str(value))
        if not slug:
            raise ValueError("Category slug cannot be empty.")
        return slug

    @field_validator("label", mode="before")
    @classmethod
    def normalize_label(cls, value: Any) -> str:
        label = _normalize_text(str(value))
        if not label:
            raise ValueError("Category label cannot be empty.")
        return label

    @field_validator("icon", mode="before")
    @classmethod
    def normalize_icon(cls, value: Any) -> str:
        return "" if value is None else str(value)

    @field_validator("placements", mode="before")
    @classmethod
    def normalize_placements(cls, value: Any) -> tuple[CategoryPlacement, ...]:
        if not isinstance(value, (list, tuple)):
            raise TypeError("Category placements must be a list or tuple.")
        placements = [CategoryPlacement(str(item).strip()) for item in value]
        deduped = tuple(dict.fromkeys(placements))
        if not deduped:
            raise ValueError("Category placements cannot be empty.")
        return deduped

    @field_validator("aliases", mode="before")
    @classmethod
    def normalize_aliases(cls, value: Any) -> tuple[str, ...]:
        return _normalize_text_tuple(value)

    @field_validator("storage_folders", mode="before")
    @classmethod
    def normalize_storage_folders(cls, value: Any) -> tuple[str, ...]:
        folders = _normalize_path_tuple(value)
        if not folders:
            raise ValueError("Category storage_folders cannot be empty.")
        return folders


class CourseManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title: str
    quarter: int
    folder: str
    aliases: tuple[str, ...] = ()
    search_terms: tuple[str, ...] = ()
    kind: CourseKind = CourseKind.STANDARD
    supports_weeks: bool = False
    week_count: int = 0
    top_level_actions: tuple[str, ...] = ()
    more_files_actions: tuple[str, ...] = ()
    week_actions: tuple[str, ...] = ()
    overview: Overview

    @field_validator("id", mode="before")
    @classmethod
    def normalize_id(cls, value: Any) -> str:
        slug = _normalize_slug(str(value))
        if not slug:
            raise ValueError("Course id cannot be empty.")
        return slug

    @field_validator("title", "folder", mode="before")
    @classmethod
    def normalize_text_fields(cls, value: Any) -> str:
        text = _normalize_text(str(value))
        if not text:
            raise ValueError("Course text fields cannot be empty.")
        return text

    @field_validator("quarter", mode="before")
    @classmethod
    def normalize_quarter(cls, value: Any) -> int:
        if isinstance(value, bool):
            raise TypeError("Quarter must be an integer.")
        quarter = int(value)
        if quarter <= 0:
            raise ValueError("Quarter must be positive.")
        return quarter

    @field_validator("aliases", "search_terms", mode="before")
    @classmethod
    def normalize_text_lists(cls, value: Any) -> tuple[str, ...]:
        return _normalize_text_tuple(value)

    @field_validator("top_level_actions", "more_files_actions", "week_actions", mode="before")
    @classmethod
    def normalize_action_lists(cls, value: Any) -> tuple[str, ...]:
        return _normalize_slug_tuple(value)

    @field_validator("week_count", mode="before")
    @classmethod
    def normalize_week_count(cls, value: Any) -> int:
        if value is None or value == "":
            return 0
        if isinstance(value, bool):
            raise TypeError("Week count must be an integer.")
        return int(value)

    @model_validator(mode="after")
    def validate_weeks(self) -> "CourseManifest":
        if self.supports_weeks and self.week_count <= 0:
            raise ValueError("Courses with supports_weeks=True must define a positive week_count.")
        if not self.supports_weeks and self.week_count != 0:
            object.__setattr__(self, "week_count", 0)
        return self


class InstitutionManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    slug: str
    display_name: str
    quarter_labels: dict[int, str]
    quarter_order: dict[int, tuple[str, ...]]
    course_files: tuple[str, ...]

    @field_validator("slug", mode="before")
    @classmethod
    def normalize_slug(cls, value: Any) -> str:
        slug = _normalize_slug(str(value))
        if not slug:
            raise ValueError("Institution slug cannot be empty.")
        return slug

    @field_validator("display_name", mode="before")
    @classmethod
    def normalize_display_name(cls, value: Any) -> str:
        name = _normalize_text(str(value))
        if not name:
            raise ValueError("Institution display_name cannot be empty.")
        return name

    @field_validator("quarter_labels", mode="before")
    @classmethod
    def normalize_quarter_labels(cls, value: Any) -> dict[int, str]:
        if not isinstance(value, dict):
            raise TypeError("quarter_labels must be a mapping.")
        normalized: dict[int, str] = {}
        for raw_key, raw_value in value.items():
            normalized[int(raw_key)] = _normalize_text(str(raw_value))
        if not normalized:
            raise ValueError("quarter_labels cannot be empty.")
        return normalized

    @field_validator("quarter_order", mode="before")
    @classmethod
    def normalize_quarter_order(cls, value: Any) -> dict[int, tuple[str, ...]]:
        if not isinstance(value, dict):
            raise TypeError("quarter_order must be a mapping.")
        normalized: dict[int, tuple[str, ...]] = {}
        for raw_key, raw_value in value.items():
            normalized[int(raw_key)] = _normalize_slug_tuple(raw_value)
        return normalized

    @field_validator("course_files", mode="before")
    @classmethod
    def normalize_course_files(cls, value: Any) -> tuple[str, ...]:
        files = _normalize_path_tuple(value)
        if not files:
            raise ValueError("course_files cannot be empty.")
        return files


class ResourceFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    path: Path
    label: str
    course_id: str
    category_slug: str
    week_number: int | None = None
    source_hint: str = ""
    file_hash: str = ""

    @field_validator("label", "source_hint", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: Any) -> str:
        return "" if value is None else _normalize_text(str(value))

    @field_validator("course_id", "category_slug", mode="before")
    @classmethod
    def normalize_ids(cls, value: Any) -> str:
        return _normalize_slug(str(value))


class SearchIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    raw_text: str
    normalized_text: str
    tokens: tuple[str, ...] = ()
    course_terms: tuple[str, ...] = ()
    category_terms: tuple[str, ...] = ()
    week_number: int | None = None
    wants_syllabus: bool = False

    @field_validator("raw_text", "normalized_text", mode="before")
    @classmethod
    def normalize_query_text(cls, value: Any) -> str:
        return _normalize_text(str(value))

    @field_validator("tokens", "course_terms", "category_terms", mode="before")
    @classmethod
    def normalize_tokens(cls, value: Any) -> tuple[str, ...]:
        return _normalize_text_tuple(value)


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    score: int
    label: str
    course_id: str
    action: SearchAction
    category_slug: str | None = None
    week_number: int | None = None
    syllabus_only: bool = False

    @field_validator("label", mode="before")
    @classmethod
    def normalize_result_label(cls, value: Any) -> str:
        return _normalize_text(str(value))

    @field_validator("course_id", "category_slug", mode="before")
    @classmethod
    def normalize_result_ids(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _normalize_slug(str(value))


class SearchResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: SearchResolutionKind
    result: SearchResult | None = None
    message: str = ""
    course_id: str | None = None
    course_ids: tuple[str, ...] = ()
    category_slugs: tuple[str, ...] = ()
    suggestions: tuple[str, ...] = ()
    week_number: int | None = None

    syllabus_only: bool = False

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: Any) -> str:
        return "" if value is None else _normalize_text(str(value))

    @field_validator("course_id", mode="before")
    @classmethod
    def normalize_course_id(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _normalize_slug(str(value))

    @field_validator("course_ids", "category_slugs", mode="before")
    @classmethod
    def normalize_slug_lists(cls, value: Any) -> tuple[str, ...]:
        return _normalize_slug_tuple(value)


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    severity: ValidationSeverity
    code: str
    message: str
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: Any) -> str:
        code = _normalize_slug(str(value))
        if not code:
            raise ValueError("Validation issue code cannot be empty.")
        return code

    @field_validator("message", mode="before")
    @classmethod
    def normalize_issue_message(cls, value: Any) -> str:
        message = _normalize_text(str(value))
        if not message:
            raise ValueError("Validation issue message cannot be empty.")
        return message


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    issues: tuple[ValidationIssue, ...] = ()

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR)

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING)

    def with_issue(self, issue: ValidationIssue) -> "ValidationReport":
        return self.model_copy(update={"issues": (*self.issues, issue)})

    def with_issues(self, issues: list[ValidationIssue] | tuple[ValidationIssue, ...]) -> "ValidationReport":
        return self.model_copy(update={"issues": (*self.issues, *tuple(issues))})


class ScreenView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str
    text: str
    button_rows: tuple[tuple[str, ...], ...]
    placeholder: str = "Choose..."

    @field_validator("key", "text", "placeholder", mode="before")
    @classmethod
    def normalize_screen_text(cls, value: Any) -> str:
        return str(value)

    @field_validator("button_rows", mode="before")
    @classmethod
    def normalize_button_rows(cls, value: Any) -> tuple[tuple[str, ...], ...]:
        if not isinstance(value, (list, tuple)):
            raise TypeError("button_rows must be a list or tuple.")
        rows: list[tuple[str, ...]] = []
        for row in value:
            rows.append(_normalize_text_tuple(row))
        return tuple(rows)


class RetryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: DeliveryScope
    course_id: str
    category_slug: str
    week_number: int | None = None
    syllabus_only: bool = False
    failed_paths: tuple[str, ...] = ()
    sent_paths: tuple[str, ...] = ()

    @field_validator("course_id", "category_slug", mode="before")
    @classmethod
    def normalize_retry_ids(cls, value: Any) -> str:
        return _normalize_slug(str(value))

    @field_validator("failed_paths", "sent_paths", mode="before")
    @classmethod
    def normalize_paths(cls, value: Any) -> tuple[str, ...]:
        return _normalize_path_tuple(value)


class DeliverySession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    total_files: int = 0
    files_sent_count: int = 0
    failed_paths: tuple[str, ...] = ()
    sent_paths: tuple[str, ...] = ()
    cancel_requested: bool = False
    stop_notice_sent: bool = False

    @field_validator("failed_paths", "sent_paths", mode="before")
    @classmethod
    def normalize_delivery_paths(cls, value: Any) -> tuple[str, ...]:
        return _normalize_path_tuple(value)


class TelegramSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int = 0
    chat_id: int = 0
    level: SessionLevel = SessionLevel.HOME
    quarter: int | None = None
    course_id: str | None = None
    section: SessionSection = SessionSection.HOME
    week_number: int | None = None
    screen_message_id: int | None = None
    screen_key: str | None = None
    transient_messages: tuple[int, ...] = ()
    retry_request: RetryRequest | None = None
    execution_id: int = 0
    delivery: DeliverySession | None = None
    history: list[str] = Field(default_factory=lambda: ["nav:main"])
    delivery_active: bool = False
    mode: SessionMode = SessionMode.HOME
    report_category: str | None = None
    noise_count: int = 0

    @field_validator("course_id", "screen_key", mode="before")
    @classmethod
    def normalize_optional_ids(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value)
        return text if text.startswith("course:") or ":" in text else _normalize_slug(text)

    @field_validator("transient_messages", mode="before")
    @classmethod
    def normalize_transients(cls, value: Any) -> tuple[int, ...]:
        return _normalize_int_tuple(value)


class SendOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    sent_count: int = 0
    failed_items: tuple[ResourceFile, ...] = ()
    cancelled: bool = False
