from __future__ import annotations

from typing import Protocol

from academic_hub.domain.models import (
    CategoryDefinition,
    CourseManifest,
    InstitutionManifest,
    ResourceFile,
    ValidationReport,
)


class ContentRepository(Protocol):
    institution: InstitutionManifest
    categories: dict[str, CategoryDefinition]
    courses: dict[str, CourseManifest]
    validation_report: ValidationReport

    def list_quarters(self) -> list[int]: ...

    def list_courses(self, quarter: int) -> list[CourseManifest]: ...

    def get_course(self, course_id: str) -> CourseManifest | None: ...

    def list_course_files(
        self,
        course_id: str,
        category_slug: str,
        *,
        syllabus_only: bool = False,
    ) -> list[ResourceFile]: ...

    def list_week_files(self, course_id: str, week_number: int, category_slug: str) -> list[ResourceFile]: ...

    def list_weeks(self, course_id: str) -> list[int]: ...

    def searchable_course_tokens(self, course_id: str) -> tuple[str, ...]: ...

    def searchable_file_tokens(
        self,
        course_id: str,
        category_slug: str,
        *,
        week_number: int | None = None,
    ) -> tuple[str, ...]: ...

