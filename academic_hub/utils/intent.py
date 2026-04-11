import re
from enum import Enum
from typing import Tuple

class IntentDecision(Enum):
    SEARCH = "search"
    NOISE = "noise"
    UNKNOWN = "unknown"

def classify_intent(text: str) -> Tuple[IntentDecision, int, int]:
    """
    Classifies a raw text input string as SEARCH, NOISE, or UNKNOWN based
    on a deterministic 4-rule scoring algorithm.
    Returns: (IntentDecision, noise_score, search_score)
    """
    text_lower = text.lower()
    noise_score = 0
    search_score = 0
    
    # --- NOISE SCORING ---
    if len(text) < 3:
        noise_score += 1
        
    emoji_symbol_pattern = re.compile(r'^[\W_]+$')
    if emoji_symbol_pattern.match(text):
        noise_score += 2
        
    greeting_pattern = re.compile(r'\b(hi|hello|hey|how are you|test|ping|bot)\b')
    if greeting_pattern.search(text_lower):
        noise_score += 2
        
    academic_pattern = re.compile(r'\b(exam|exams|lecture|lectures|notes|week|calculus|physics|assignment|assignments|chemistry|seminar|syllabus)\b')
    if not academic_pattern.search(text_lower):
        noise_score += 1
    else:
        search_score += 2
        
    # --- SEARCH SCORING ---
    number_pattern = re.compile(r'\d+')
    if number_pattern.search(text):
        search_score += 2
        
    intent_verbs = re.compile(r'\b(find|search|show|give|materials|get)\b')
    if intent_verbs.search(text_lower):
        search_score += 1
        
    structured_phrase = re.compile(r'\b\w+\s+\w+\b') # At least two words
    if structured_phrase.search(text_lower):
        search_score += 1
        
    # --- DECISION ROUTING ---
    if search_score >= 3:
        return IntentDecision.SEARCH, noise_score, search_score
    elif noise_score >= 3:
        return IntentDecision.NOISE, noise_score, search_score
    else:
        return IntentDecision.UNKNOWN, noise_score, search_score
