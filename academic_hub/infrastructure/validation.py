from __future__ import annotations

from pathlib import Path

from academic_hub.domain.models import CategoryDefinition, CourseManifest, InstitutionManifest, ValidationIssue, ValidationReport
from academic_hub.utils.parsing import is_valid_week_folder


ALLOWED_PLACEMENTS = {"top_level", "more_files", "week_level"}
SPECIAL_ACTIONS = {"overview", "by_week"}


class RepositoryValidator:
    def __init__(
        self,
        resources_root: Path,
        institution: InstitutionManifest,
        categories: dict[str, CategoryDefinition],
        courses: dict[str, CourseManifest],
    ) -> None:
        self.resources_root = resources_root
        self.institution = institution
        self.categories = categories
        self.courses = courses

    def validate(self) -> ValidationReport:
        issues: list[ValidationIssue] = []
        issues.extend(self._validate_categories())
        issues.extend(self._validate_courses())
        issues.extend(self._validate_content_tree())
        return ValidationReport(tuple(issues))

    def _validate_categories(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for category in self.categories.values():
            invalid = set(category.placements) - ALLOWED_PLACEMENTS
            if invalid:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="invalid_category_placement",
                        message=f"Category '{category.slug}' has invalid placements: {sorted(invalid)}",
                    )
                )
            if not category.label.strip():
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="empty_category_label",
                        message=f"Category '{category.slug}' is missing a display label.",
                    )
                )
        return issues

    def _validate_courses(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        title_to_id: dict[str, str] = {}
        folder_keys: set[tuple[int, str]] = set()
        valid_actions = set(self.categories) | SPECIAL_ACTIONS

        declared_ids: set[str] = set()
        for quarter, course_ids in self.institution.quarter_order.items():
            for course_id in course_ids:
                declared_ids.add(course_id)
                if course_id not in self.courses:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="unknown_course_in_quarter",
                            message=f"Institution manifest references unknown course '{course_id}' in quarter {quarter}.",
                        )
                    )

        for course_id, course in self.courses.items():
            if course.title in title_to_id:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="duplicate_course_title",
                        message=f"Course '{course_id}' shares title '{course.title}' with '{title_to_id[course.title]}'.",
                    )
                )
            title_to_id[course.title] = course_id

            folder_key = (course.quarter, course.folder)
            if folder_key in folder_keys:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="duplicate_course_folder",
                        message=f"Course '{course_id}' duplicates folder '{course.folder}' in quarter {course.quarter}.",
                    )
                )
            folder_keys.add(folder_key)

            if course_id not in declared_ids:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="course_not_ordered",
                        message=f"Course '{course_id}' is not included in institution quarter ordering.",
                    )
                )

            for action in (*course.top_level_actions, *course.more_files_actions, *course.week_actions):
                if action not in valid_actions:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="invalid_course_action",
                            message=f"Course '{course_id}' references unknown action/category '{action}'.",
                        )
                    )
            if course.supports_weeks and course.week_count <= 0:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="invalid_week_count",
                        message=f"Course '{course_id}' supports weeks but has week_count={course.week_count}.",
                    )
                )
        return issues

    def _validate_content_tree(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if not self.resources_root.is_dir():
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="missing_resources_root",
                    message=f"Resources root does not exist yet: {self.resources_root}",
                )
            )
            return issues

        expected_course_dirs = {
            (course.quarter, course.folder): course
            for course in self.courses.values()
        }
        known_folders = self._known_storage_folders()

        for quarter in self.institution.quarter_order:
            quarter_dir = self.resources_root / f"Quarter_{quarter}"
            if not quarter_dir.is_dir():
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="missing_quarter_dir",
                        message=f"Missing quarter directory: {quarter_dir}",
                    )
                )
                continue

            for directory in quarter_dir.iterdir():
                if not directory.is_dir():
                    continue
                if directory.name == "_Unsorted":
                    issues.append(
                        ValidationIssue(
                            severity="warning",
                            code="unsorted_content",
                            message=f"Unsorted content exists under {directory}.",
                        )
                    )
                    continue

                key = (quarter, directory.name)
                if key not in expected_course_dirs:
                    issues.append(
                        ValidationIssue(
                            severity="warning",
                            code="orphan_course_dir",
                            message=f"Unexpected directory in Quarter {quarter}: {directory.name}",
                        )
                    )
                    continue

                course = expected_course_dirs[key]
                week_root = directory / "weeks"
                for child in directory.iterdir():
                    if not child.is_dir():
                        continue
                    if child.name == "weeks":
                        continue
                    if child.name not in known_folders:
                        issues.append(
                            ValidationIssue(
                                severity="warning",
                                code="unexpected_category_dir",
                                message=f"Course '{course.id}' has unexpected folder '{child.name}'.",
                            )
                        )
                if week_root.is_dir():
                    for week_dir in week_root.iterdir():
                        if week_dir.is_dir() and not is_valid_week_folder(week_dir.name):
                            issues.append(
                                ValidationIssue(
                                    severity="warning",
                                    code="malformed_week_dir",
                                    message=f"Course '{course.id}' has malformed week directory '{week_dir.name}'.",
                                )
                            )

        for course in self.courses.values():
            course_dir = self.resources_root / f"Quarter_{course.quarter}" / course.folder
            if not course_dir.is_dir():
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="missing_course_dir",
                        message=f"Missing course directory for '{course.id}': {course_dir}",
                    )
                )
        return issues

    def _known_storage_folders(self) -> set[str]:
        folders = {"weeks"}
        for category in self.categories.values():
            folders.update(category.storage_folders)
        return folders

