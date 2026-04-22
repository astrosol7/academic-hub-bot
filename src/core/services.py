"""
Core services for Academic Hub
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, List, Dict, Tuple
from enum import Enum
import re
import logging
from datetime import datetime

log = logging.getLogger(__name__)

class NavigationLevel(Enum):
    HOME = "home"
    RESOURCES = "resources"
    QUARTER = "quarter"
    COURSE = "course"
    WEEK_LIST = "week_list"
    WEEK_CATEGORY = "week_category"
    SEARCH = "search"
    ABOUT = "about"
    REPORT = "report"
    SUGGEST = "suggest"

class SearchScope(Enum):
    RESOURCES = "resources"
    COMMUNITY = "community"
    ALL = "all"

class ButtonLabels:
    """Enhanced button labels for bot with dynamic navigation"""
    # Core navigation
    HOME = "🏠 Home"
    RESOURCES = "📖 Browse Resources"
    SEARCH = "🔎 Search"
    ABOUT = "ℹ️ About"
    REPORT = "⚠️ Report Issue"
    SUGGEST = "💡 Suggest"
    BACK = "🔙 Back"
    MAIN_MENU = "🏠 Home"
    VOYAGER = "✨ Voyager"
    
    # Course navigation
    OVERVIEW = "📋 Overview"
    BY_WEEK = "🗂 By Week"
    MORE_FILES = "📂 More Files"
    
    # Search options
    SEARCH_RESOURCES = "📖 Resources"
    SEARCH_COMMUNITY = "💬 Community"
    EXIT_SEARCH = "❌ Exit Search"
    
    # Actions
    RETRY = "🔄 Retry Failed Downloads"
    
    # Dynamic labels that get updated
    browse = "📖 Browse Resources"
    search = "🔎 Search"
    voyager = "✨ Voyager"
    search_resources = "📖 Resources"
    search_community = "💬 Community"
    about = "ℹ️ About"
    report = "⚠️ Report Issue"
    suggest = "💡 Suggest"
    retry = "🔄 Retry Failed Downloads"
    overview = "📋 Course Overview"
    by_week = "🗂 By Week"
    more_files = "📂 More Files"
    exit_search = "❌ Exit Search"
    back = "🔙 Back"
    main_menu = "🏠 Home"


class DeliveryService:
    """Service for handling content delivery"""
    
    def __init__(self, repository):
        self.repository = repository
    
    def bundle_for_course_category(self, course_id: str, category_slug: str) -> list:
        """Get files for a course category delivery."""
        from src.core.models import ResourceFile
        resources = self.repository.get_category_resources(course_id, category_slug)
        files = []
        for res in resources:
            path = getattr(res, 'external_path', '')
            title = getattr(res, 'title', 'Untitled')
            if path and Path(path).exists():
                files.append(ResourceFile(
                    path=path, name=title,
                    size=Path(path).stat().st_size if Path(path).exists() else 0,
                ))
        return files

    def bundle_for_week_category(self, course_id: str, week: int, category_slug: str) -> list:
        """Get files for a week+category delivery."""
        from src.core.models import ResourceFile
        resources = self.repository.get_week_resources(course_id, week, category_slug)
        files = []
        for res in resources:
            path = getattr(res, 'external_path', '')
            title = getattr(res, 'title', 'Untitled')
            if path and Path(path).exists():
                files.append(ResourceFile(
                    path=path, name=title,
                    size=Path(path).stat().st_size if Path(path).exists() else 0,
                ))
        return files

    async def deliver_content(self, user_id: int, scope: Any) -> bool:
        """Deliver content to user"""
        return True


class NavigationService:
    """Enhanced navigation service with dynamic state management"""
    
    def __init__(self, repository):
        self.repository = repository
        self.dynamic_contexts = {}  # user_id -> context data
        
    
    def get_back_target(self, user_id: int, current_session: Any) -> Optional[str]:
        """Get intelligent back navigation target without history stack"""
        current_level = current_session.level
        
        # Smart back logic based on current level
        if current_level == "course":
            if current_session.section == "week_category":
                return "nav:week_list"
            elif current_session.section in ["report_1", "report_2"]:
                return "nav:overview"
            else:
                return "nav:select_quarter:" + str(current_session.quarter or 1)
        elif current_level == "quarter":
            return "nav:resources"
        elif current_level == "week_list":
            return "nav:overview"
        elif current_level == "resources":
            return "nav:main"
        elif current_level in ["search", "about", "report", "suggest"]:
            return "nav:main"
        else:
            return "nav:main"
    
    def get_dynamic_keyboard(self, session: Any) -> List[List[str]]:
        """Generate dynamic keyboard based on current state"""
        labels = ButtonLabels()
        keyboard = []
        
        if session.mode == "home" or session.level == "home":
            keyboard = [
                [labels.browse, labels.search, labels.voyager],
                [labels.report, labels.suggest],
                [labels.about]
            ]
            
            # Smart Resume
            resume_target = getattr(session, 'resume_target', None)
            if resume_target:
                title, action = resume_target
                keyboard.insert(0, [f"📍 Continue: {title}"])
        
        elif session.mode == "search":
            keyboard = [
                [labels.search_resources, labels.search_community],
                [labels.back, labels.main_menu]
            ]
        
        elif session.level == "report":
            if session.section == "report_1":
                # Report category buttons
                keyboard = [
                    ["🚫 Missing file", "❌ Wrong content"],
                    ["⛔ Unavailable", "❓ Other"],
                    [labels.back, labels.main_menu]
                ]
        
        elif session.level == "resources":
            # Dynamic quarter buttons
            quarter_buttons = []
            if self.repository.institution:
                for q_num, q_label in self.repository.institution.quarter_labels.items():
                    quarter_buttons.append(q_label)
                # Split into rows of 2
                keyboard = [quarter_buttons[i:i+2] for i in range(0, len(quarter_buttons), 2)]
                keyboard.append([labels.back, labels.main_menu])
        
        elif session.level == "quarter":
            if not session.course_id:
                # Dynamic course buttons
                course_buttons = []
                if session.quarter is not None:
                    courses = self.repository.list_courses(int(session.quarter))
                    for c in courses:
                        course_buttons.append(c.title)
                
                # Split into rows of 2 for better UX, but fall back to 1 if titles are long
                keyboard = []
                for i in range(0, len(course_buttons), 2):
                    row = course_buttons[i:i+2]
                    # If any title in row is very long, use single column
                    if any(len(btn) > 20 for btn in row):
                        keyboard.append([row[0]])
                        if len(row) > 1:
                            keyboard.append([row[1]])
                    else:
                        keyboard.append(row)
                keyboard.append([labels.back, labels.main_menu])
            else:
                course = self.repository.get_course(session.course_id)
                if course:
                    keyboard = [
                        [labels.overview, labels.by_week],
                        [labels.more_files],
                        [labels.back, labels.main_menu]
                    ]
        
        elif session.level == "course" and session.course_id:
            course = self.repository.get_course(session.course_id)
            if course:
                if session.section == "week_list":
                    # Dynamic week buttons
                    week_buttons = [f"🗂 Week {i}" for i in range(1, 13)]  # 12 weeks
                    keyboard = [week_buttons[i:i+3] for i in range(0, len(week_buttons), 3)]
                    keyboard.append([labels.back, labels.main_menu])
                elif session.section == "week_category":
                    # Dynamic category buttons for week, preferred order
                    preferred = ['lecture_notes', 'homework', 'exams', 'assignments']
                    available_cats = list(course.week_actions) if course.week_actions else []
                    cat_buttons = []
                    
                    for pref in preferred:
                        if pref in available_cats:
                            cat = self.repository.categories.get(pref)
                            if cat: cat_buttons.append(cat.label)
                            available_cats.remove(pref)
                            
                    for remaining in available_cats:
                        cat = self.repository.categories.get(remaining)
                        if cat: cat_buttons.append(cat.label)
                        
                    keyboard = [cat_buttons[i:i+2] for i in range(0, len(cat_buttons), 2)]
                    keyboard.append([labels.back, labels.main_menu])
                elif session.section == "more_files":
                    preferred = ['breakout_notes', 'assignments', 'homeworks', 'readings']
                    available_cats = list(course.more_files_actions) if course.more_files_actions else []
                    cat_buttons = []
                    
                    for pref in preferred:
                        if pref in available_cats:
                            cat = self.repository.categories.get(pref)
                            if cat: cat_buttons.append(cat.label)
                            available_cats.remove(pref)
                            
                    for remaining in available_cats:
                        cat = self.repository.categories.get(remaining)
                        if cat: cat_buttons.append(cat.label)
                        
                    keyboard = [cat_buttons[i:i+2] for i in range(0, len(cat_buttons), 2)]
                    keyboard.append([labels.back, labels.main_menu])
                else:
                    # Course overview with dynamic categories, preferred layout
                    preferred_row2 = ['exams', 'lecture_notes']
                    available_cats = list(course.top_level_actions) if course.top_level_actions else []
                    
                    row1 = [labels.overview, labels.by_week]
                    row2 = []
                    
                    for pref in preferred_row2:
                        if pref in available_cats:
                            cat = self.repository.categories.get(pref)
                            if cat: row2.append(cat.label)
                            available_cats.remove(pref)
                            
                    # Fill row 2 up to 2 items if needed
                    while len(row2) < 2 and available_cats:
                        cat = self.repository.categories.get(available_cats.pop(0))
                        if cat: row2.append(cat.label)
                        
                    keyboard = [row1]
                    if row2:
                        keyboard.append(row2)
                    keyboard.append([labels.more_files])
                    keyboard.append([labels.back, labels.main_menu])
        
        # Add retry button if there are failed deliveries
        if hasattr(session, 'retry_request') and session.retry_request:
            if keyboard:
                keyboard[-1].append(labels.retry)
            else:
                keyboard = [[labels.retry]]
        
        return keyboard
    
    def transition(self, session: Any, action: str) -> Any:
        """Enhanced transition with better state management"""
        # Parse action
        parts = action.split(":")
        if len(parts) < 2:
            return session
            
        action_type = parts[1]
        
        # Transition logic
        
        # Handle different action types
        if action_type == "main":
            return self._reset_to_main(session)
        elif action_type == "back":
            return self._handle_back(session)
        elif action_type == "resources":
            return self._navigate_to_resources(session)
        elif action_type == "search":
            return self._navigate_to_search(session)
        elif action_type == "search_scope":
            if len(parts) >= 3:
                return self._set_search_scope(session, parts[2])
        elif action_type == "select_quarter":
            if len(parts) >= 3:
                return self._select_quarter(session, parts[2])
        elif action_type == "select_course":
            if len(parts) >= 3:
                return self._select_course(session, parts[2])
        elif action_type == "overview":
            return self._navigate_to_overview(session)
        elif action_type == "week_list":
            return self._navigate_to_week_list(session)
        elif action_type == "week_category":
            if len(parts) >= 3:
                return self._navigate_to_week_category(session, parts[2])
        elif action_type == "more_files":
            return self._navigate_to_more_files(session)
        elif action_type == "about":
            return self._navigate_to_about(session)
        elif action_type == "report":
            return self._navigate_to_report(session)
        elif action_type == "suggest":
            return self._navigate_to_suggest(session)
        elif action_type == "report_category":
            if len(parts) >= 3:
                return self._set_report_category(session, parts[2])
                
        return session
    
    def _reset_to_main(self, session: Any) -> Any:
        """Reset to main menu"""
        return session.model_copy(update={
            "level": "home",
            "section": "home", 
            "course_id": None,
            "quarter": None,
            "week_number": None,
            "mode": "home",
            "search_target": None,
            "report_category": None,
            "retry_request": None
        })
    
    def _handle_back(self, session: Any) -> Any:
        """Intelligent back navigation"""
        user_id = getattr(session, 'user_id', 0)
        back_target = self.get_back_target(user_id, session)
        
        # Parse back target and transition accordingly
        if back_target and back_target.startswith("nav:"):
            return self.transition(session, back_target)
        
        return session
    
    def _navigate_to_resources(self, session: Any) -> Any:
        """Navigate to resources level"""
        return session.model_copy(update={
            "level": "resources",
            "section": "resources",
            "mode": "browse"
        })
    
    def _navigate_to_search(self, session: Any) -> Any:
        """Navigate to search mode"""
        return session.model_copy(update={
            "level": "search",
            "section": "search_intro",
            "mode": "search",
            "search_target": "resources"
        })
    
    def _set_search_scope(self, session: Any, scope: str) -> Any:
        """Set search scope"""
        return session.model_copy(update={
            "search_target": scope,
            "section": "search_intro"
        })
    
    def _select_quarter(self, session: Any, quarter: str) -> Any:
        """Select quarter"""
        try:
            quarter_int = int(quarter)
            return session.model_copy(update={
                "level": "quarter",
                "section": "quarter",
                "quarter": quarter_int,
                "course_id": None,
                "mode": "browse"
            })
        except ValueError:
            return session
    
    def _select_course(self, session: Any, course_id: str) -> Any:
        """Select course"""
        return session.model_copy(update={
            "level": "course",
            "section": "course",
            "course_id": course_id,
            "week_number": None,
            "mode": "browse"
        })
    
    def _navigate_to_overview(self, session: Any) -> Any:
        """Navigate to course overview"""
        return session.model_copy(update={
            "section": "course",
            "week_number": None
        })
    
    def _navigate_to_week_list(self, session: Any) -> Any:
        """Navigate to week list"""
        return session.model_copy(update={
            "section": "week_list"
        })
    
    def _navigate_to_week_category(self, session: Any, week: str) -> Any:
        """Navigate to specific week category"""
        try:
            week_int = int(week)
            return session.model_copy(update={
                "section": "week_category",
                "week_number": week_int
            })
        except ValueError:
            return session
    
    def _navigate_to_more_files(self, session: Any) -> Any:
        """Navigate to more files section"""
        return session.model_copy(update={
            "section": "more_files"
        })
    
    def _navigate_to_about(self, session: Any) -> Any:
        """Navigate to about section"""
        return session.model_copy(update={
            "level": "about",
            "section": "about",
            "mode": "home"
        })
    
    def _navigate_to_report(self, session: Any) -> Any:
        """Navigate to report section"""
        return session.model_copy(update={
            "level": "report",
            "section": "report_1",
            "mode": "report",
            "report_category": None
        })
    
    def _navigate_to_suggest(self, session: Any) -> Any:
        """Navigate to suggestion section"""
        return session.model_copy(update={
            "level": "suggest",
            "section": "suggest",
            "mode": "suggest"
        })
    
    def _set_report_category(self, session: Any, category: str) -> Any:
        """Set report category"""
        return session.model_copy(update={
            "section": "report_2",
            "report_category": category
        })
    
    def render_screen(self, session: Any) -> Any:
        """Render a ScreenView based on current navigation state."""
        from src.core.models import ScreenView

        raw_kb = self.get_dynamic_keyboard(session)
        button_rows = tuple(tuple(row) for row in raw_kb) if raw_kb else ()

        text = self._build_screen_text(session)
        key = f"{session.level}:{session.section}"

        return ScreenView(
            key=key,
            text=text,
            button_rows=button_rows,
            placeholder=self._placeholder_for(session),
        )

    def _build_screen_text(self, session: Any) -> str:
        """Build the message text for the current screen."""
        if session.level == "home":
            return (
                "\U0001f3e0 <b>Academic Hub — Main Menu</b>\n\n"
                "Welcome! Choose an option below to get started."
            )
        if session.level == "resources":
            return "\U0001f4da <b>Select a Quarter</b>\n\nChoose a quarter to browse courses."
        if session.level == "quarter":
            q = session.quarter or "?"
            courses = self.repository.list_courses(int(q)) if session.quarter else []
            if courses:
                return f"\U0001f4d6 <b>Quarter {q} — Courses</b>\n\nTap a course name below."
            return f"\U0001f4d6 <b>Quarter {q}</b>\n\nNo courses found for this quarter."
        if session.level == "course" and session.course_id:
            course = self.repository.get_course(session.course_id)
            title = course.title if course else session.course_id
            if session.section == "week_list":
                return f"🗂 <b>{title} — Weeks</b>\n\nSelect a week to browse materials."
            if session.section == "week_category":
                return f"📅 <b>{title} — Week {session.week_number}</b>\n\nChoose a category."
            if session.section == "more_files":
                return f"📂 <b>{title} — More Files</b>\n\nChoose a category."
            
            # Course Overview Content
            from src.core.course_content import get_course_overview
            return get_course_overview(session.course_id, title)
        if session.level == "search":
            return "\U0001f50d <b>Search Mode</b>\n\nType your query to search resources or community questions."
        if session.level == "about":
            return (
                "ℹ️ <b>About Academic Hub</b>\n\n"
                "Academic Hub is your one-stop platform for SIT academic resources.\n\n"
                "Powered by <b>Orbit version 1.0</b>\n"
                "Developed by Solomon Dawit Astro Soul 7\n"
                "<a href=\"https://github.com/astrosol7/academic-hub-bot\">View on GitHub</a>"
            )
        if session.level == "report":
            if session.section == "report_2":
                cat = (session.report_category or "this issue").lower()
                if "missing file" in cat:
                    prompt = "What file is missing?"
                elif "wrong content" in cat:
                    prompt = "What content is wrong?"
                else:
                    prompt = "Please describe the issue in detail."
                return f"⚠️ <b>Report Issue</b>\n\nCategory: <i>{session.report_category}</i>\n\n{prompt}"
            return (
                "\U0001f4dd <b>Report an Issue</b>\n\n"
                "What kind of issue are you experiencing?"
            )
        if session.level == "suggest":
            return "\U0001f4a1 <b>Suggest a Resource</b>\n\nDescribe the resource you'd like us to add."
        return "\U0001f3e0 <b>Academic Hub</b>\n\nUse the menu below to navigate."

    @staticmethod
    def _placeholder_for(session: Any) -> str:
        if session.mode == "search":
            return "Type your search query..."
        if session.section in ("report_2",):
            return "Describe the issue..."
        if session.section == "suggest":
            return "Describe the resource..."
        return "Choose an option..."


class SearchService:
    """Enhanced search service with better error handling"""
    
    def __init__(self, repository):
        self.repository = repository
        
    
    async def search(self, query: str, user_id: int, scope: str = "all") -> Dict[str, Any]:
        """Enhanced search with multiple strategies"""
        if len(query.strip()) < 2:
            return {
                "status": "error",
                "message": "Query too short. Please enter at least 2 characters.",
                "results": [],
                "suggestions": []
            }
        
        results = []
        suggestions = []
        engine_used = "filesystem"
        
        try:
            # Strategy 1: Exact title matches
            exact_matches = self._search_exact_titles(query)
            results.extend(exact_matches)
            
            # Strategy 2: Fuzzy matching
            if len(results) < 5:
                fuzzy_matches = self._search_fuzzy(query)
                results.extend(fuzzy_matches)
            
            # Strategy 3: Category matches
            if len(results) < 10:
                category_matches = self._search_by_category(query)
                results.extend(category_matches)
            
            # Remove duplicates and limit results
            unique_results = self._deduplicate_results(results)[:10]
            
            # Generate suggestions if no results
            if not unique_results:
                suggestions = self._generate_suggestions(query)
            
            
            return {
                "status": "success",
                "results": unique_results,
                "suggestions": suggestions,
                "engine": engine_used,
                "query": query
            }
            
        except Exception as e:
            log.error(f"Search error for query '{query}': {e}")
            return {
                "status": "error",
                "message": "Search service temporarily unavailable. Please try again.",
                "results": [],
                "suggestions": []
            }
    
    def _search_exact_titles(self, query: str) -> List[Dict]:
        """Search for exact title matches"""
        results = []
        query_lower = query.lower()
        
        # Search through all courses and their resources
        for course in self.repository.list_all_courses():
            course_resources = self.repository.get_course_resources(course.id)
            for resource in course_resources:
                if query_lower in resource.title.lower():
                    results.append({
                        "id": resource.id,
                        "title": resource.title,
                        "description": getattr(resource, 'description', ''),
                        "course_id": course.id,
                        "course_title": course.title,
                        "category": getattr(resource, 'category_slug', 'unknown'),
                        "score": 1.0,  # Exact match gets highest score
                        "match_type": "exact_title"
                    })
        
        return results
    
    def _search_fuzzy(self, query: str) -> List[Dict]:
        """Fuzzy search using simple string similarity against both course and resource"""
        results = []
        query_words = query.lower().split()
        
        for course in self.repository.list_all_courses():
            course_resources = self.repository.get_course_resources(course.id)
            course_title_lower = course.title.lower()
            
            for resource in course_resources:
                title_lower = resource.title.lower()
                cat_slug = getattr(resource, 'category_slug', '').lower()
                
                # Combine search space to catch "calculus exams" -> "Calculus I" + "Quiz 01" + "exams"
                searchable_text = f"{course_title_lower} {title_lower} {cat_slug}"
                
                matches = sum(1 for word in query_words if word in searchable_text)
                if matches >= 1: 
                    score = matches / len(query_words)
                    
                    # Boost score if they match perfectly across all terms
                    if matches >= len(query_words):
                        score *= 1.2
                        
                    results.append({
                        "id": resource.id,
                        "title": resource.title,
                        "description": getattr(resource, 'description', ''),
                        "course_id": course.id,
                        "course_title": course.title,
                        "category": cat_slug,
                        "score": score * 0.8,
                        "match_type": "fuzzy"
                    })
        
        return sorted(results, key=lambda x: x['score'], reverse=True)
    
    def _search_by_category(self, query: str) -> List[Dict]:
        """Search by category keywords and overlapping course topics"""
        results = []
        query_lower = query.lower()
        query_words = query_lower.split()
        
        # Exact mappings to Postgres category slugs
        category_keywords = {
            'lecture_notes': ['notes', 'note', 'lecture notes', 'slides', 'presentation', 'ppt'],
            'readings': ['pdf', 'document', 'reading', 'read', 'book'],
            'assignments': ['assignment', 'homework', 'task', 'project'],
            'exams': ['exam', 'test', 'quiz', 'exams']
        }
        
        matched_categories = []
        for category, keywords in category_keywords.items():
            if any(keyword in query_words for keyword in keywords):
                matched_categories.append(category)
        
        if matched_categories:
            for course in self.repository.list_all_courses():
                course_resources = self.repository.get_course_resources(course.id)
                course_title_lower = course.title.lower()
                
                # Calculate if course name was explicitly mentioned
                course_match = any(word in course_title_lower for word in query_words if word not in ['1', '2', '3', 'i', 'ii', 'iii'])
                
                for resource in course_resources:
                    cat_slug = getattr(resource, 'category_slug', '').lower()
                    if cat_slug in matched_categories:
                        
                        # Only return results if the user specifically asked for this course OR it's a very broad search
                        score = 0.6
                        if course_match:
                            score = 1.0  # High score for matched course + matched category!
                            
                        results.append({
                            "id": resource.id,
                            "title": resource.title,
                            "description": getattr(resource, 'description', ''),
                            "course_id": course.id,
                            "course_title": course.title,
                            "category": cat_slug,
                            "score": score,
                            "match_type": "category"
                        })
        
        return results
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results by ID"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                unique_results.append(result)
        
        return unique_results
    
    def _generate_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions"""
        suggestions = []
        
        # Common course codes
        course_patterns = ['calc', 'physics', 'chemistry', 'biology', 'math', 'cs']
        query_lower = query.lower()
        
        for pattern in course_patterns:
            if pattern in query_lower:
                suggestions.extend([
                    f"{pattern} week 1",
                    f"{pattern} notes",
                    f"{pattern} slides"
                ])
                break
        
        # General suggestions
        if not suggestions:
            suggestions = [
                "Try shorter keywords",
                "Check spelling",
                "Browse by institution"
            ]
        
        return suggestions[:5]  # Limit to 5 suggestions


class IntentDecision(Enum):
    """Enhanced intent decisions"""
    SEARCH = "search"
    NAVIGATION = "navigation"
    DOWNLOAD = "download"
    HELP = "help"
    NOISE = "noise"
    UNKNOWN = "unknown"

def classify_intent(text: str) -> tuple[IntentDecision, float, float]:
    """Enhanced intent classification with confidence scores"""
    text_lower = text.lower().strip()
    
    # Navigation keywords
    nav_keywords = ['home', 'main', 'menu', 'back', 'start', 'browse']
    # Search keywords  
    search_keywords = ['search', 'find', 'look for', 'show me', 'get', 'download']
    # Help keywords
    help_keywords = ['help', 'how', 'what', 'why', 'explain']
    
    nav_score = sum(1 for keyword in nav_keywords if keyword in text_lower)
    search_score = sum(1 for keyword in search_keywords if keyword in text_lower)
    help_score = sum(1 for keyword in help_keywords if keyword in text_lower)
    
    # Calculate scores
    total_keywords = len(text_lower.split())
    nav_confidence = nav_score / max(total_keywords, 1)
    search_confidence = search_score / max(total_keywords, 1)
    
    # Determine intent
    if nav_confidence > 0.3:
        return IntentDecision.NAVIGATION, nav_confidence, search_confidence
    elif search_confidence > 0.2:
        return IntentDecision.SEARCH, nav_confidence, search_confidence
    elif help_score > 0:
        return IntentDecision.HELP, nav_confidence, search_confidence
    elif len(text_lower) < 3 or text_lower.isdigit():
        return IntentDecision.NOISE, nav_confidence, search_confidence
    else:
        return IntentDecision.UNKNOWN, nav_confidence, search_confidence
