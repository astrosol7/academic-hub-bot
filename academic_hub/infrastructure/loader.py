from __future__ import annotations

import json
from pathlib import Path

from academic_hub.domain.models import CategoryDefinition, CourseManifest, InstitutionManifest, Overview


class ManifestError(RuntimeError):
    """Raised when a manifest file is missing required structure."""


def load_category_registry(manifests_root: Path) -> dict[str, CategoryDefinition]:
    raw_categories = _read_json(manifests_root / "categories.json")
    if not isinstance(raw_categories, list):
        raise ManifestError("categories.json must contain a list.")
    registry: dict[str, CategoryDefinition] = {}
    for payload in raw_categories:
        obj = _expect_dict(payload, "category")
        slug = _normalize_slug(_require_str(obj, "slug", "category"))
        category = CategoryDefinition(
            slug=slug,
            label=_require_str(obj, "label", f"category '{slug}'"),
            icon=_optional_str(obj, "icon", ""),
            placements=_string_tuple(obj.get("placements", ()), f"category '{slug}' placements"),
            aliases=_normalize_text_tuple(obj.get("aliases", ())),
            storage_folders=_normalize_path_tuple(
                obj.get("storage_folders", ()),
                f"category '{slug}' storage_folders",
            ),
            searchable=bool(obj.get("searchable", True)),
            sendable=bool(obj.get("sendable", True)),
        )
        registry[category.slug] = category
    return registry


def load_institution_manifest(manifests_root: Path, slug: str) -> InstitutionManifest:
    payload = _expect_dict(_read_json(manifests_root / "institutions" / f"{slug}.json"), f"institution '{slug}'")
    manifest_slug = _normalize_slug(_require_str(payload, "slug", f"institution '{slug}'"))
    raw_quarter_labels = _expect_dict(payload.get("quarter_labels"), f"institution '{manifest_slug}' quarter_labels")
    quarter_labels = {int(key): _require_mapping_str(raw_quarter_labels, key, f"institution '{manifest_slug}' quarter_labels") for key in raw_quarter_labels}
    raw_quarter_order = _expect_dict(payload.get("quarter_order"), f"institution '{manifest_slug}' quarter_order")
    quarter_order = {
        int(key): _string_tuple(value, f"institution '{manifest_slug}' quarter_order[{key}]")
        for key, value in raw_quarter_order.items()
    }
    return InstitutionManifest(
        slug=manifest_slug,
        display_name=_require_str(payload, "display_name", f"institution '{manifest_slug}'"),
        quarter_labels=quarter_labels,
        quarter_order=quarter_order,
        course_files=_normalize_path_tuple(_require_sequence(payload, "course_files", f"institution '{manifest_slug}'"), f"institution '{manifest_slug}' course_files"),
    )


def load_course_manifests(manifests_root: Path, institution: InstitutionManifest) -> dict[str, CourseManifest]:
    courses: dict[str, CourseManifest] = {}
    for relative in institution.course_files:
        payload = _expect_dict(_read_json(manifests_root / relative), f"course manifest '{relative}'")
        course_id = _normalize_slug(_require_str(payload, "id", f"course manifest '{relative}'"))
        overview_payload = _expect_dict(payload.get("overview"), f"course '{course_id}' overview")
        kind = _normalize_slug(_optional_str(payload, "kind", "standard")) or "standard"
        course = CourseManifest(
            id=course_id,
            title=_require_str(payload, "title", f"course '{course_id}'"),
            quarter=_require_int(payload, "quarter", f"course '{course_id}'"),
            folder=_require_str(payload, "folder", f"course '{course_id}'"),
            aliases=_normalize_text_tuple(payload.get("aliases", ())),
            search_terms=_normalize_text_tuple(payload.get("search_terms", ())),
            kind=kind,
            supports_weeks=bool(payload.get("supports_weeks", False)),
            week_count=int(payload.get("week_count", 0)),
            top_level_actions=_normalize_slug_tuple(payload.get("top_level_actions", ())),
            more_files_actions=_normalize_slug_tuple(payload.get("more_files_actions", ())),
            week_actions=_normalize_slug_tuple(payload.get("week_actions", ())),
            overview=Overview(
                goal=_require_str(overview_payload, "goal", f"course '{course_id}' overview"),
                grading=_string_tuple(overview_payload.get("grading", ()), f"course '{course_id}' overview.grading"),
                dates=_string_tuple(overview_payload.get("dates", ()), f"course '{course_id}' overview.dates"),
                tools=_string_tuple(overview_payload.get("tools", ()), f"course '{course_id}' overview.tools"),
                focus=_string_tuple(overview_payload.get("focus", ()), f"course '{course_id}' overview.focus"),
            ),
        )
        courses[course.id] = course
    return courses


def _read_json(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _expect_dict(value: object, context: str) -> dict:
    if not isinstance(value, dict):
        raise ManifestError(f"{context} must be an object.")
    return value


def _require_str(payload: dict, key: str, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{context} is missing a valid '{key}' string.")
    return value.strip()


def _optional_str(payload: dict, key: str, default: str) -> str:
    value = payload.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise ManifestError(f"Field '{key}' must be a string when provided.")
    return value.strip() or default


def _require_int(payload: dict, key: str, context: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ManifestError(f"{context} is missing a valid integer '{key}'.")
    return value


def _require_sequence(payload: dict, key: str, context: str) -> list | tuple:
    value = payload.get(key)
    if not isinstance(value, list | tuple):
        raise ManifestError(f"{context} is missing a valid '{key}' list.")
    return value


def _string_tuple(value: object, context: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list | tuple):
        raise ManifestError(f"{context} must be a list of strings.")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ManifestError(f"{context} must contain only non-empty strings.")
        items.append(item.strip())
    return tuple(dict.fromkeys(items))


def _normalize_text_tuple(value: object) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item.strip() for item in _string_tuple(value, "text list")))


def _normalize_slug_tuple(value: object) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_normalize_slug(item) for item in _string_tuple(value, "slug list")))


def _normalize_path_tuple(value: object, context: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item.replace("\\", "/").strip().strip("/") for item in _string_tuple(value, context)))


def _normalize_slug(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _require_mapping_str(payload: dict, key: str, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{context} must contain non-empty string values.")
    return value.strip()
