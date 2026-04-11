from enum import Enum
from pathlib import Path
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field

class LayoutType(str, Enum):
    STANDARD = "standard"
    SEMINAR = "seminar"

class CategoryPlacement(str, Enum):
    TOP_LEVEL = "top_level"
    MORE_FILES = "more_files"
    WEEK_LEVEL = "week_level"

class CategoryDefinition(BaseModel):
    slug: str
    label: str
    icon: str
    placement: CategoryPlacement
    searchable: bool = True
    sendable: bool = True
    course_specific: bool = False

class Overview(BaseModel):
    goal: str
    grading: List[str]
    dates: List[str]
    tools: List[str]
    focus: List[str]

class CourseManifest(BaseModel):
    id: str
    title: str
    aliases: List[str] = []
    quarter: int
    folder: str
    layout: LayoutType = LayoutType.STANDARD
    enabled_categories: List[str]
    has_weeks: bool = Field(default=False, alias="weeks")
    overview: Overview
    last_updated: Optional[str] = "auto"

class InstitutionManifest(BaseModel):
    slug: str
    name: str
    quarters: List[int]
    admin_chat_id: Optional[int] = None

class ResourceFile(BaseModel):
    path: Path
    caption: str

class ScreenView(BaseModel):
    text: str
    reply_markup: Optional[Any] = None

class SearchQuery(BaseModel):
    text: str
    tokens: List[str]

class SearchResult(BaseModel):
    course_id: str
    category_slug: Optional[str] = None
    week_num: Optional[int] = None
    score: float = 0.0

class SearchStatus(str, Enum):
    CLEAR = "clear"
    AMBIGUOUS = "ambiguous"
    MISSING = "missing"

class SearchResolution(BaseModel):
    status: SearchStatus
    results: List[SearchResult] = []

# Alias for backward compatibility during migration
SearchIntent = SearchResult