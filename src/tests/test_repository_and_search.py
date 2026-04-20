import unittest
from pathlib import Path
import json

from src.core.config import load_config
from src.core.services import SearchService
from src.core.loader import ManifestError, load_institution_manifest
from src.core.repository import FilesystemContentRepository


def build_repo() -> FilesystemContentRepository:
    config = load_config(require_token=False)
    return FilesystemContentRepository(
        manifests_root=config.manifests_root,
        resources_root=config.resources_root,
        institution_slug=config.institution_slug,
    )


class RepositoryAndSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = build_repo()
        cls.search = SearchService(cls.repo)

    def test_readings_include_syllabus_files(self) -> None:
        labels = [item.label for item in self.repo.list_course_files("physics_i", "readings")]
        self.assertTrue(any("Syllabus" in label for label in labels))

    def test_week_files_are_classified_from_flat_week_pack(self) -> None:
        lecture_notes = self.repo.list_week_files("chemistry_lab", 1, "lecture_notes")
        assignments = self.repo.list_week_files("chemistry_lab", 1, "assignments")
        projects = self.repo.list_week_files("chemistry_lab", 1, "projects")
        self.assertGreaterEqual(len(lecture_notes), 1)
        self.assertGreaterEqual(len(assignments), 1)
        self.assertGreaterEqual(len(projects), 1)

    def test_search_common_queries(self) -> None:
        cases = {
            "calculus 1 exams": ("calculus_i", "send_course_category", "exams", None),
            "physics 2 week 3 lecture notes": ("physics_ii", "send_week_category", "lecture_notes", 3),
            "seminar syllabus": ("seminar", "send_course_category", "readings", None),
        }
        for query, expected in cases.items():
            with self.subTest(query=query):
                result = self.search.search(query)
                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual((result.course_id, result.action, result.category_slug, result.week_number), expected)

    def test_search_requires_category(self) -> None:
        resolution = self.search.resolve("calculus 1")
        self.assertEqual(resolution.kind, "missing_category")
        self.assertEqual(resolution.course_id, "calculus_i")

    def test_search_flags_ambiguous_category(self) -> None:
        resolution = self.search.resolve("physics 2 week 3 notes")
        self.assertEqual(resolution.kind, "ambiguous_category")
        self.assertEqual(resolution.course_id, "physics_ii")
        self.assertEqual(resolution.week_number, 3)

    def test_search_flags_ambiguous_course(self) -> None:
        resolution = self.search.resolve("physics exams")
        self.assertEqual(resolution.kind, "ambiguous_course")
        self.assertGreaterEqual(len(resolution.course_ids), 2)

    def test_manifest_loader_requires_course_files(self) -> None:
        tmp_dir = Path("tests") / "tmp_manifest_loader"
        institutions_dir = tmp_dir / "institutions"
        institutions_dir.mkdir(parents=True, exist_ok=True)
        try:
            with (institutions_dir / "demo.json").open("w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "slug": "demo",
                        "display_name": "Demo",
                        "quarter_labels": {"1": "Quarter 1"},
                        "quarter_order": {"1": []}
                    },
                    handle,
                )
            with self.assertRaises(ManifestError):
                load_institution_manifest(tmp_dir, "demo")
        finally:
            for path in sorted(tmp_dir.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
