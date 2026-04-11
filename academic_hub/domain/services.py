from __future__ import annotations

from dataclasses import dataclass

from academic_hub.domain.interfaces import ContentRepository
from academic_hub.domain.models import ResourceFile, ScreenView, SearchIntent, SearchResolution, SearchResult
from academic_hub.utils.formatting import render_overview
from academic_hub.utils.parsing import normalize_text, parse_week_number, score_overlap, tokenize


@dataclass(frozen=True)
class ButtonLabels:
    resources: str = "Resources"
    back: str = "Back"
    main_menu: str = "Main menu"
    more_files: str = "More files"
    overview: str = "Overview"
    by_week: str = "By week"
    retry: str = "Retry"


class NavigationService:
    def __init__(self, repository: ContentRepository, labels: ButtonLabels | None = None) -> None:
        self.repository = repository
        self.labels = labels or ButtonLabels()

    def home(self) -> ScreenView:
        return ScreenView(
            key="home",
            text="Academic Hub\n\nTap Resources to find your course materials.",
            button_rows=((self.labels.resources,),),
        )

    def resources(self) -> ScreenView:
        return ScreenView(
            key="resources",
            text="Resources\n\nChoose a quarter.",
            button_rows=(
                tuple(self.repository.institution.quarter_labels[q] for q in self.repository.list_quarters()),
                (self.labels.back,),
            ),
        )

    def quarter_courses(self, quarter: int) -> ScreenView:
        buttons = [course.title for course in self.repository.list_courses(quarter)]
        rows = [tuple(row) for row in _chunk(buttons, 2)]
        rows.append((self.labels.back,))
        return ScreenView(
            key=f"quarter:{quarter}",
            text=f"{self.repository.institution.quarter_labels.get(quarter, f'Quarter {quarter}')}\n\nChoose your course.",
            button_rows=tuple(rows),
        )

    def course(self, course_id: str, *, retry_enabled: bool = False) -> ScreenView:
        course = self.repository.get_course(course_id)
        assert course is not None
        buttons: list[str] = []
        for action in course.top_level_actions:
            if action == "overview":
                buttons.append(self.labels.overview)
            elif action == "by_week":
                buttons.append(self.labels.by_week)
            elif action in self.repository.categories:
                buttons.append(self.repository.categories[action].label)
        if course.more_files_actions:
            buttons.append(self.labels.more_files)
        rows = [tuple(row) for row in _chunk(buttons, 2)]
        if retry_enabled:
            rows.insert(0, (self.labels.retry,))
        rows.append((self.labels.back, self.labels.main_menu))
        return ScreenView(
            key=f"course:{course_id}",
            text=f"{course.title}\n\nChoose what you need.",
            button_rows=tuple(rows),
        )

    def more_files(self, course_id: str, *, retry_enabled: bool = False) -> ScreenView:
        course = self.repository.get_course(course_id)
        assert course is not None
        buttons = [self.repository.categories[action].label for action in course.more_files_actions]
        rows = [tuple(row) for row in _chunk(buttons, 2)]
        if retry_enabled:
            rows.insert(0, (self.labels.retry,))
        rows.append((self.labels.back, self.labels.main_menu))
        return ScreenView(
            key=f"more:{course_id}",
            text=f"{course.title}\n\nChoose a category.",
            button_rows=tuple(rows),
        )

    def week_list(self, course_id: str) -> ScreenView:
        course = self.repository.get_course(course_id)
        assert course is not None
        buttons = [f"Week {week}" for week in self.repository.list_weeks(course_id)]
        rows = [tuple(row) for row in _chunk(buttons, 2)]
        rows.append((self.labels.back, self.labels.main_menu))
        return ScreenView(
            key=f"weeks:{course_id}",
            text=f"{course.title}\n\nChoose a week.",
            button_rows=tuple(rows),
        )

    def week_category(self, course_id: str, week_number: int, *, retry_enabled: bool = False) -> ScreenView:
        course = self.repository.get_course(course_id)
        assert course is not None
        buttons = [self.repository.categories[action].label for action in course.week_actions]
        rows = [tuple(row) for row in _chunk(buttons, 2)]
        if retry_enabled:
            rows.insert(0, (self.labels.retry,))
        rows.append((self.labels.back, self.labels.main_menu))
        return ScreenView(
            key=f"week:{course_id}:{week_number}",
            text=f"{course.title} • Week {week_number}\n\nChoose what you need.",
            button_rows=tuple(rows),
        )

    def overview_text(self, course_id: str) -> str:
        course = self.repository.get_course(course_id)
        assert course is not None
        return render_overview(course.title, course.overview)


class DeliveryService:
    def __init__(self, repository: ContentRepository) -> None:
        self.repository = repository

    def bundle_for_course_category(
        self,
        course_id: str,
        category_slug: str,
        *,
        syllabus_only: bool = False,
    ) -> list[ResourceFile]:
        return self.repository.list_course_files(course_id, category_slug, syllabus_only=syllabus_only)

    def bundle_for_week_category(self, course_id: str, week_number: int, category_slug: str) -> list[ResourceFile]:
        return self.repository.list_week_files(course_id, week_number, category_slug)


class SearchService:
    def __init__(self, repository: ContentRepository) -> None:
        self.repository = repository

    def parse(self, raw_text: str) -> SearchIntent:
        tokens = tokenize(raw_text)
        normalized = normalize_text(raw_text)
        wants_syllabus = "syllabus" in normalized

        return SearchIntent(
            raw_text=raw_text,
            normalized_text=normalized,
            tokens=tokens,
            week_number=parse_week_number(normalized),
            wants_syllabus=wants_syllabus,
        )

    def resolve(self, raw_text: str) -> SearchResolution:
        query = self.parse(raw_text)
        normalized_query = normalize_text(raw_text)
        course_candidates = self._rank_courses(query, normalized_query)
        if not course_candidates:
            return SearchResolution(
                kind="missing_course",
                message="Tell me the course too, like 'calculus 1 exams' or 'physics 2 lecture notes'.",
                week_number=query.week_number,
                syllabus_only=query.wants_syllabus,
            )

        top_score = course_candidates[0][1]
        tied_courses = [course_id for course_id, score in course_candidates if score == top_score]
        if len(tied_courses) > 1:
            titles = ", ".join(self.repository.courses[course_id].title for course_id in tied_courses)
            return SearchResolution(
                kind="ambiguous_course",
                message=f"I found more than one course: {titles}. Please use the exact course name.",
                course_ids=tuple(tied_courses),
                week_number=query.week_number,
                syllabus_only=query.wants_syllabus,
            )

        course_id = course_candidates[0][0]
        course = self.repository.courses[course_id]
        if query.week_number is not None and (not course.supports_weeks or query.week_number > course.week_count):
            return SearchResolution(
                kind="invalid_week",
                message=f"{course.title} does not have Week {query.week_number}. Choose a valid week from the menu.",
                course_id=course_id,
                week_number=query.week_number,
            )

        category_resolution = self._resolve_category(query, normalized_query, course_id)
        if category_resolution.kind != "match":
            return category_resolution

        category_slug = category_resolution.category_slugs[0]
        score = course_candidates[0][1]
        if query.week_number is not None:
            label = f"{course.title} • Week {query.week_number} • {self.repository.categories[category_slug].label}"
            return SearchResolution(
                kind="match",
                result=SearchResult(
                    score=score,
                    label=label,
                    course_id=course_id,
                    action="send_week_category",
                    category_slug=category_slug,
                    week_number=query.week_number,
                    syllabus_only=False,
                ),
            )

        label = f"{course.title} • {self.repository.categories[category_slug].label}"
        return SearchResolution(
            kind="match",
            result=SearchResult(
                score=score,
                label=label,
                course_id=course_id,
                action="send_course_category",
                category_slug=category_slug,
                syllabus_only=category_resolution.syllabus_only,
            ),
        )

    def search(self, raw_text: str) -> SearchResult | None:
        resolution = self.resolve(raw_text)
        return resolution.result if resolution.kind == "match" else None

    def _rank_courses(self, query: SearchIntent, normalized_query: str) -> list[tuple[str, int]]:
        scored: list[tuple[str, int]] = []
        for course_id in self.repository.courses:
            score = score_overlap(query.tokens, self.repository.searchable_course_tokens(course_id))
            score += self._phrase_bonus(course_id, normalized_query)
            if score > 0:
                scored.append((course_id, score))
        scored.sort(key=lambda item: (-item[1], item[0]))
        return scored

    def _resolve_category(self, query: SearchIntent, normalized_query: str, course_id: str) -> SearchResolution:
        if query.wants_syllabus:
            return SearchResolution(kind="match", course_id=course_id, category_slugs=("readings",), syllabus_only=True)

        allowed_categories = self._allowed_categories(course_id)
        token_set = set(query.tokens)
        if "notes" in token_set and "lecture" not in token_set and "breakout" not in token_set:
            ambiguous = tuple(
                slug for slug in ("lecture_notes", "breakout_notes")
                if slug in allowed_categories
            )
            if len(ambiguous) > 1:
                return SearchResolution(
                    kind="ambiguous_category",
                    message="`notes` is ambiguous here. Choose `Lecture notes` or `Breakout notes`.",
                    course_id=course_id,
                    category_slugs=ambiguous,
                    week_number=query.week_number,
                )

        explicit_matches: list[str] = []
        for category_slug in allowed_categories:
            category = self.repository.categories[category_slug]
            phrases = [category.label, *category.aliases]
            if any(normalize_text(phrase) in normalized_query for phrase in phrases if phrase.strip()):
                explicit_matches.append(category_slug)

        if len(explicit_matches) == 1:
            return SearchResolution(kind="match", course_id=course_id, category_slugs=(explicit_matches[0],))

        if len(explicit_matches) > 1:
            return SearchResolution(
                kind="ambiguous_category",
                message="That request matches more than one category. Choose the exact category from the menu.",
                course_id=course_id,
                    category_slugs=tuple(dict.fromkeys(explicit_matches)),
                    week_number=query.week_number,
                )

        return SearchResolution(
            kind="missing_category",
            message="I found the course, but I still need the category. Choose exactly what you need next.",
            course_id=course_id,
            week_number=query.week_number,
        )

    def _allowed_categories(self, course_id: str) -> tuple[str, ...]:
        course = self.repository.courses[course_id]
        category_slugs = [
            action
            for action in (*course.top_level_actions, *course.more_files_actions, *course.week_actions)
            if action in self.repository.categories
        ]
        return tuple(dict.fromkeys(category_slugs))

    def _phrase_bonus(self, course_id: str, normalized_query: str) -> int:
        course = self.repository.courses[course_id]
        bonus = 0
        title_phrase = normalize_text(course.title)
        if title_phrase and title_phrase in normalized_query:
            bonus += 8
        for alias in course.aliases:
            alias_phrase = normalize_text(alias)
            if not alias_phrase:
                continue
            if alias_phrase == normalized_query:
                bonus = max(bonus, 12 + len(alias_phrase.split()))
            elif alias_phrase in normalized_query:
                bonus = max(bonus, 10 + len(alias_phrase.split()))
        return bonus


def _chunk(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]
