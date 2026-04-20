"""
Core models for Academic Hub — Orbit V1.0
All session models use Pydantic for serialization with aiogram FSM.
"""

from typing import Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class SessionMode(str, Enum):
    """Session modes for the bot"""
    HOME = "home"
    BROWSE = "browse"
    SEARCH = "search"
    REPORT = "report"
    SUGGEST = "suggest"
    ADMIN = "admin"


class DeliveryScope(str, Enum):
    """Delivery scope"""
    COURSE = "course"
    WEEK = "week"


class RetryRequest(BaseModel):
    """Retry request for failed deliveries"""
    failed_paths: tuple[str, ...] = ()
    scope: DeliveryScope = DeliveryScope.COURSE
    course_id: str = ""
    category_slug: str = ""
    week_number: Optional[int] = None


class TelegramSession(BaseModel):
    """Telegram session state — persisted in FSMContext via Pydantic."""
    user_id: int = 0
    chat_id: int = 0
    execution_id: int = 1

    # Navigation state
    level: str = "home"
    section: str = "home"
    mode: SessionMode = SessionMode.HOME
    quarter: Optional[int] = None
    course_id: Optional[str] = None
    week_number: Optional[int] = None

    # Search state
    search_target: Optional[str] = None
    noise_count: int = 0

    # Report state
    report_category: Optional[str] = None

    # Delivery
    delivery_active: bool = False
    delivery: Optional['DeliverySession'] = None
    retry_request: Optional[RetryRequest] = None

    # Rendering
    screen_message_id: Optional[int] = None
    screen_key: Optional[str] = None
    transient_messages: tuple[int, ...] = ()


class ScreenView(BaseModel):
    """Immutable screen data for the renderer."""
    key: str = "unknown"
    text: str = ""
    button_rows: tuple[tuple[str, ...], ...] = ()
    placeholder: str = "Choose..."


class CourseManifest(BaseModel):
    """Course manifest data for renderer caption building."""
    code: str = ""
    title: str = ""
    quarter: str = ""
    weeks: list[str] = Field(default_factory=list)


class CategoryDefinition(BaseModel):
    """Category definition for renderer."""
    slug: str = ""
    label: str = ""
    icon: str = ""
    sendable: bool = True


class ResourceFile(BaseModel):
    """Resource file for delivery."""
    path: str
    name: str
    label: str = ""
    size: int = 0
    mime_type: str = "application/pdf"

    def model_post_init(self, __context):
        if not self.label:
            self.label = self.name


class SendOutcome(BaseModel):
    """Outcome of a delivery batch."""
    success: bool = True
    cancelled: bool = False
    sent_count: int = 0
    failed_items: list[Any] = Field(default_factory=list)


class DeliverySession(BaseModel):
    """Complete delivery session state for the coordinator."""
    session_id: str = ""
    total_files: int = 0
    files_sent_count: int = 0
    cancel_requested: bool = False
    stop_notice_sent: bool = False
    sent_paths: tuple[str, ...] = ()
    failed_paths: tuple[str, ...] = ()
    user_id: int = 0
    scope: DeliveryScope = DeliveryScope.COURSE
    files: list[str] = Field(default_factory=list)
