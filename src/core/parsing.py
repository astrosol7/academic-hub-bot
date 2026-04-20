"""
Core parsing utilities for Academic Hub
"""

import re
from pathlib import Path
from typing import Optional


def humanize_file_label(filename: str) -> str:
    """Convert filename to human-readable format"""
    # Remove common prefixes
    prefixes_to_remove = [
        'MATH_', 'CHEML_', 'PHYS_', 'BIO_', 'CS_',
        'Q1_', 'Q2_', 'Q3_', 'Q4_',
        'week', 'Week', 'WEEK'
    ]
    
    clean_name = filename
    for prefix in prefixes_to_remove:
        if clean_name.startswith(prefix):
            clean_name = clean_name[len(prefix):]
            break
    
    # Remove file extensions
    clean_name = re.sub(r'\.(pdf|docx?|xlsx?|pptx?)$', '', clean_name, flags=re.IGNORECASE)
    
    # Replace underscores and hyphens with spaces
    clean_name = re.sub(r'[_-]+', ' ', clean_name)
    
    # Capitalize words
    return ' '.join(word.capitalize() for word in clean_name.split())


def infer_category_slug(file_path: Path) -> str:
    """Infer category slug from file path"""
    filename = file_path.name.lower()
    
    # Category mapping based on keywords
    category_keywords = {
        'homework': ['homework', 'assignment', 'task', 'submission'],
        'exams': ['exam', 'quiz', 'test', 'assessment'],
        'projects': ['project', 'research', 'report'],
        'notes': ['notes', 'lecture', 'slides', 'handout'],
        'lab': ['lab', 'equipment', 'manual']
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in filename for keyword in keywords):
            return category
    
    return 'misc'


def parse_week_number(text: str) -> Optional[int]:
    """Extract week number from text"""
    # Try different patterns
    patterns = [
        r'week\s*(\d+)',           # "week 3", "week3"
        r'wk[-\s]*(\d+)',          # "wk-11", "wk 11"
        r'(\d+)\s*week',           # "3 week", "3week"
        r'quarter\s*\d+\s*week\s*(\d+)',  # "quarter 2 week 3"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None


def normalize_course_code(course_name: str) -> str:
    """Normalize course code to consistent format"""
    # Remove spaces and convert to uppercase
    return re.sub(r'\s+', '', course_name).upper()


def extract_quarter_from_path(file_path: Path) -> Optional[int]:
    """Extract quarter number from file path"""
    path_str = str(file_path).lower()
    
    # Look for quarter patterns
    patterns = [
        r'quarter[_\s]*(\d+)',
        r'q[_\s]*(\d+)',
        r'term[_\s]*(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, path_str)
        if match:
            return int(match.group(1))
    
    return None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file handling"""
    # Remove or replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:250] + ('.' + ext if ext else '')
    
    return sanitized.strip()


def is_valid_file_type(filename: str, allowed_types: list[str] = None) -> bool:
    """Check if file type is allowed"""
    if allowed_types is None:
        allowed_types = ['.pdf', '.docx', '.xlsx', '.pptx', '.txt']
    
    file_ext = Path(filename).suffix.lower()
    return file_ext in allowed_types
