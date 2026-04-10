import unittest
import uuid
from pathlib import Path
import shutil

from academic_hub.domain.models import CategoryDefinition, CourseManifest, InstitutionManifest, Overview
from academic_hub.domain.services import NavigationService
from academic_hub.infrastructure.validation import RepositoryValidator

from tests.test_repository_and_search import build_repo


class ValidationAndNavigationTests(unittest.TestCase):
    def test_validator_catches_duplicate_titles_and_missing_dirs(self) -> None:
        root = Path("tests") / f"tmp_{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=True)
        try:
            categories = {
                "readings": CategoryDefinition(
                    slug="readings",
                    label="Readings",
                    icon="",
                    placements=("more_files",),
                    aliases=("readings",),
                    storage_folders=("readings",),
                )
            }
            overview = Overview(goal="goal", grading=(), dates=(), tools=(), focus=())
            courses = {
                "course_a": CourseManifest(
                    id="course_a",
                    title="Shared Title",
                    quarter=1,
                    folder="Course_A",
                    aliases=(),
                    search_terms=(),
                    kind="standard",
                    supports_weeks=False,
                    week_count=0,
                    top_level_actions=("overview",),
                    more_files_actions=("readings",),
                    week_actions=(),
                    overview=overview,
                ),
                "course_b": CourseManifest(
                    id="course_b",
                    title="Shared Title",
                    quarter=1,
                    folder="Course_B",
                    aliases=(),
                    search_terms=(),
                    kind="standard",
                    supports_weeks=False,
                    week_count=0,
                    top_level_actions=("overview",),
                    more_files_actions=("readings",),
                    week_actions=(),
                    overview=overview,
                ),
            }
            institution = InstitutionManifest(
                slug="sit",
                display_name="Test",
                quarter_labels={1: "Quarter 1"},
                quarter_order={1: ("course_a", "course_b")},
                course_files=(),
            )
            report = RepositoryValidator(root, institution, categories, courses).validate()
            codes = {issue.code for issue in report.issues}
            self.assertIn("duplicate_course_title", codes)
            self.assertIn("missing_quarter_dir", codes)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_navigation_service_uses_simplified_seminar_actions(self) -> None:
        repo = build_repo()
        nav = NavigationService(repo)
        seminar = nav.course("seminar")
        joined = " | ".join(" ".join(row) for row in seminar.button_rows)
        self.assertIn("By week", joined)
        self.assertIn("Readings", joined)
        self.assertNotIn("Exams", joined)
        self.assertNotIn("Lecture recordings", joined)


if __name__ == "__main__":
    unittest.main()
