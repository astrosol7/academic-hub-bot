from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from academic_hub.domain.models import CategoryDefinition, CourseManifest, InstitutionManifest


class ManifestError(RuntimeError):
    """Raised when a manifest file is missing required structure."""


def load_category_registry(manifests_root: Path) -> dict[str, CategoryDefinition]:
    raw_categories = _read_json(manifests_root / "categories.json")
    if not isinstance(raw_categories, list):
        raise ManifestError("categories.json must contain a list.")

    registry: dict[str, CategoryDefinition] = {}
    for payload in raw_categories:
        category = _validate_model(CategoryDefinition, payload, "category manifest")
        if category.slug in registry:
            raise ManifestError(f"Duplicate category slug '{category.slug}' in categories.json.")
        registry[category.slug] = category
    return registry


def load_institution_manifest(manifests_root: Path, slug: str) -> InstitutionManifest:
    return _validate_model(
        InstitutionManifest,
        _read_json(manifests_root / "institutions" / f"{slug}.json"),
        f"institution '{slug}'",
    )


def load_course_manifests(manifests_root: Path, institution: InstitutionManifest) -> dict[str, CourseManifest]:
    courses: dict[str, CourseManifest] = {}
    for relative in institution.course_files:
        course = _validate_model(
            CourseManifest,
            _read_json(manifests_root / relative),
            f"course manifest '{relative}'",
        )
        if course.id in courses:
            raise ManifestError(f"Duplicate course id '{course.id}' across manifests.")
        courses[course.id] = course
    return courses


def _read_json(path: Path) -> dict | list:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise ManifestError(f"Missing manifest file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Invalid JSON in {path}: {exc}") from exc


def _validate_model(model_type: type, payload: object, context: str):
    try:
        return model_type.model_validate(payload)
    except ValidationError as exc:
        raise ManifestError(f"{context} failed validation: {exc}") from exc
