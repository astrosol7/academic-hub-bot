from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

from academic_hub.domain.models import CategoryDefinition, CourseManifest, InstitutionManifest, ResourceFile, ValidationReport
from academic_hub.infrastructure.loader import load_category_registry, load_course_manifests, load_institution_manifest
from academic_hub.infrastructure.validation import RepositoryValidator
from academic_hub.utils.parsing import canonical_week_folder, humanize_file_label, infer_category_slug, looks_like_syllabus, normalize_text, tokenize


log = logging.getLogger(__name__)


class FilesystemContentRepository:
    def __init__(self, manifests_root: Path, resources_root: Path, institution_slug: str) -> None:
        self.institution: InstitutionManifest = load_institution_manifest(manifests_root, institution_slug)
        self.categories: dict[str, CategoryDefinition] = load_category_registry(manifests_root)
        self.courses: dict[str, CourseManifest] = load_course_manifests(manifests_root, self.institution)
        self.resources_root = resources_root
        self.validation_report: ValidationReport = RepositoryValidator(
            resources_root,
            self.institution,
            self.categories,
            self.courses,
        ).validate()

        self._course_files: dict[str, dict[str, list[ResourceFile]]] = defaultdict(lambda: defaultdict(list))
        self._week_files: dict[str, dict[int, dict[str, list[ResourceFile]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        self._searchable_course_tokens: dict[str, tuple[str, ...]] = {}
        self._searchable_file_tokens: dict[tuple[str, str, int | None], tuple[str, ...]] = {}
        self._index_content()

    def list_quarters(self) -> list[int]:
        return sorted(self.institution.quarter_order)

    def list_courses(self, quarter: int) -> list[CourseManifest]:
        return [self.courses[course_id] for course_id in self.institution.quarter_order.get(quarter, ())]

    def get_course(self, course_id: str) -> CourseManifest | None:
        return self.courses.get(course_id)

    def list_course_files(self, course_id: str, category_slug: str, *, syllabus_only: bool = False) -> list[ResourceFile]:
        items = list(self._course_files.get(course_id, {}).get(category_slug, ()))
        if syllabus_only:
            items = [item for item in items if looks_like_syllabus(item.path)]
        return items

    def list_week_files(self, course_id: str, week_number: int, category_slug: str) -> list[ResourceFile]:
        return list(self._week_files.get(course_id, {}).get(week_number, {}).get(category_slug, ()))

    def list_weeks(self, course_id: str) -> list[int]:
        course = self.courses[course_id]
        if not course.supports_weeks:
            return []
        return list(range(1, course.week_count + 1))

    def searchable_course_tokens(self, course_id: str) -> tuple[str, ...]:
        return self._searchable_course_tokens.get(course_id, ())

    def searchable_file_tokens(
        self,
        course_id: str,
        category_slug: str,
        *,
        week_number: int | None = None,
    ) -> tuple[str, ...]:
        return self._searchable_file_tokens.get((course_id, category_slug, week_number), ())

    def _index_content(self) -> None:
        for course in self.courses.values():
            self._index_course(course)
            self._index_course_search_tokens(course)
        self._index_file_tokens()

    def _index_course(self, course: CourseManifest) -> None:
        course_dir = self.resources_root / f"Quarter_{course.quarter}" / course.folder
        if course_dir.is_dir():
            self._index_top_level_files(course, course_dir)
            self._index_week_files(course, course_dir)

    def _index_top_level_files(self, course: CourseManifest, course_dir: Path) -> None:
        for category in self.categories.values():
            if not category.sendable:
                continue
            seen: set[Path] = set()
            files: list[ResourceFile] = []
            for folder_name in category.storage_folders:
                folder = course_dir / folder_name
                for path in self._iter_files(folder):
                    resolved = path.resolve()
                    if resolved in seen:
                        continue
                    seen.add(resolved)
                    files.append(
                        ResourceFile(
                            path=path,
                            label=humanize_file_label(path.stem),
                            course_id=course.id,
                            category_slug=category.slug,
                            source_hint=folder_name,
                        )
                    )
            files.sort(key=lambda item: (normalize_text(item.label), str(item.path)))
            self._course_files[course.id][category.slug] = files

    def _index_week_files(self, course: CourseManifest, course_dir: Path) -> None:
        if not course.supports_weeks:
            return
        week_root = course_dir / "weeks"
        for week_number in range(1, course.week_count + 1):
            folder = week_root / canonical_week_folder(week_number)
            for category_slug in course.week_actions:
                self._week_files[course.id][week_number][category_slug] = []
            if not folder.is_dir():
                continue
            for path in self._iter_files(folder):
                rel = path.relative_to(folder)
                inferred = infer_category_slug(rel)
                if inferred not in self.categories:
                    inferred = "readings"
                resource = ResourceFile(
                    path=path,
                    label=humanize_file_label(path.stem),
                    course_id=course.id,
                    category_slug=inferred,
                    week_number=week_number,
                    source_hint=str(rel.parent) if rel.parent != Path(".") else "",
                )
                self._week_files[course.id][week_number][inferred].append(resource)
            for category_slug in self._week_files[course.id][week_number]:
                self._week_files[course.id][week_number][category_slug].sort(
                    key=lambda item: (normalize_text(item.label), str(item.path))
                )

    def _index_course_search_tokens(self, course: CourseManifest) -> None:
        tokens: set[str] = set(tokenize(course.title))
        for alias in course.aliases:
            tokens.update(tokenize(alias))
        for term in course.search_terms:
            tokens.update(tokenize(term))
        tokens.update(tokenize(self.institution.quarter_labels.get(course.quarter, f"Quarter {course.quarter}")))
        tokens.add(str(course.quarter))
        self._searchable_course_tokens[course.id] = tuple(sorted(tokens))

    def _index_file_tokens(self) -> None:
        for course_id, category_map in self._course_files.items():
            for category_slug, items in category_map.items():
                token_set: set[str] = set()
                for item in items:
                    token_set.update(tokenize(item.label))
                self._searchable_file_tokens[(course_id, category_slug, None)] = tuple(sorted(token_set))
        for course_id, week_map in self._week_files.items():
            for week_number, category_map in week_map.items():
                for category_slug, items in category_map.items():
                    token_set: set[str] = set()
                    for item in items:
                        token_set.update(tokenize(item.label))
                    self._searchable_file_tokens[(course_id, category_slug, week_number)] = tuple(sorted(token_set))

    @staticmethod
    def _iter_files(folder: Path) -> list[Path]:
        if not folder.is_dir():
            return []
        files: list[Path] = []
        for path in folder.rglob("*"):
            if not path.is_file():
                continue
            if path.name.startswith("."):
                continue
            if any(part.startswith(".") or part == "__pycache__" for part in path.parts):
                continue
            files.append(path)
        return files
