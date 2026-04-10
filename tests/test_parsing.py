import unittest
from pathlib import Path

from academic_hub.utils.parsing import humanize_file_label, infer_category_slug, parse_week_number


class ParsingTests(unittest.TestCase):
    def test_humanize_file_label_strips_ingest_prefixes(self) -> None:
        self.assertEqual(humanize_file_label("MATH_1110_Q1_Quiz_01"), "Quiz 01")
        self.assertEqual(
            humanize_file_label("CHEML_1211_Q2_weekpack_W01_Research_Project_Instructions_Suggested_Prompts"),
            "Research Project Instructions Suggested Prompts",
        )

    def test_infer_category_slug_for_week_files(self) -> None:
        self.assertEqual(
            infer_category_slug(Path("Week_01") / "Homework_-_Research_Topic_Submission_Format.pdf"),
            "homework",
        )
        self.assertEqual(
            infer_category_slug(Path("Week_01") / "Lab_Equipment_Quiz_-_CHEML_1211.pdf"),
            "exams",
        )
        self.assertEqual(
            infer_category_slug(Path("Week_01") / "Research_Project_Instructions.pdf"),
            "projects",
        )

    def test_parse_week_number(self) -> None:
        self.assertEqual(parse_week_number("physics 2 week 3 lecture notes"), 3)
        self.assertEqual(parse_week_number("wk-11 chemistry"), 11)
        self.assertIsNone(parse_week_number("physics 2 lecture notes"))
