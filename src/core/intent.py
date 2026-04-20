"""
Intent classification for Academic Hub — Orbit V1.0
"""

from enum import Enum


class IntentDecision(Enum):
    """Intent decisions for free-text user input."""
    SEARCH = "search"
    NAVIGATION = "navigation"
    HELP = "help"
    NOISE = "noise"
    UNKNOWN = "unknown"


def classify_intent(text: str) -> tuple:
    """
    Classify user intent from text.
    Returns: (IntentDecision, nav_confidence, search_confidence)
    """
    text_lower = text.lower().strip()

    nav_keywords = ['home', 'main', 'menu', 'back', 'start', 'browse']
    search_keywords = ['search', 'find', 'look for', 'show me', 'get', 'download',
                       'week', 'lecture', 'quiz', 'test', 'exam', 'notes', 'homework',
                       'calculus', 'physics', 'chemistry', 'python', 'english']
    help_keywords = ['help', 'how', 'what', 'why', 'explain']

    nav_score = sum(1 for kw in nav_keywords if kw in text_lower)
    search_score = sum(1 for kw in search_keywords if kw in text_lower)
    help_score = sum(1 for kw in help_keywords if kw in text_lower)

    total_keywords = max(len(text_lower.split()), 1)
    nav_confidence = nav_score / total_keywords
    search_confidence = search_score / total_keywords

    if nav_confidence > 0.3:
        return IntentDecision.NAVIGATION, nav_confidence, search_confidence
    elif search_confidence > 0.15 or len(text_lower) >= 3:
        return IntentDecision.SEARCH, nav_confidence, search_confidence
    elif help_score > 0:
        return IntentDecision.HELP, nav_confidence, search_confidence
    elif len(text_lower) < 3 or text_lower.isdigit():
        return IntentDecision.NOISE, nav_confidence, search_confidence
    else:
        return IntentDecision.UNKNOWN, nav_confidence, search_confidence
