import uuid
import enum
from datetime import datetime, timezone
from functools import partial as _partial

# Timezone-aware UTC timestamp for use as SQLAlchemy column defaults
def _now(): return datetime.now(timezone.utc)

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, 
    Enum as SQLEnum, Text, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR, JSONB
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class ContentStrategy(str, enum.Enum):
    WEEK_DRIVEN = "WEEK_DRIVEN"
    TOPIC_DRIVEN = "TOPIC_DRIVEN"
    HYBRID = "HYBRID"

class ReportContextType(str, enum.Enum):
    ISSUE = "ISSUE"
    SUGGESTION = "SUGGESTION"
    FEEDBACK = "FEEDBACK"

class ReportStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"

class ResourceStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    DISABLED = "DISABLED"

class AdminRole(str, enum.Enum):
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"

class ValidationSeverity(str, enum.Enum):
    ERROR = "error"
    WARNING = "warning"

class QuarantineStatus(str, enum.Enum):
    PENDING = "PENDING"
    RECOVERED = "RECOVERED"
    IGNORED = "IGNORED"

class IdentityState(str, enum.Enum):
    """Represents the verification state of a Telegram user in the system."""
    GUEST      = "GUEST"       # No student ID bound yet
    VERIFIED   = "VERIFIED"    # Fully bound to a validated Student record
    CONFLICTED = "CONFLICTED"  # Administrative quarantine â€” disputed binding


# â”€â”€ INSTITUTIONS & COURSES â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    metadata_blob = Column(JSONB, nullable=True) # Full InstitutionManifest JSON
    
    created_at = Column(DateTime, default=_now)

    courses = relationship("Course", back_populates="institution")

class Course(Base):
    __tablename__ = "courses"

    id = Column(String(100), primary_key=True, index=True)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=False, index=True)
    quarter = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    folder_path = Column(String(255), nullable=False)
    
    # Structure typing as per Unbreakable OS rules
    content_strategy = Column(SQLEnum(ContentStrategy), default=ContentStrategy.WEEK_DRIVEN, nullable=False)
    week_count = Column(Integer, default=0)
    metadata_blob = Column(JSONB, nullable=True) # Full CourseManifest JSON
    
    created_at = Column(DateTime, default=_now)

    institution = relationship("Institution", back_populates="courses")
    resources = relationship("Resource", back_populates="course")


# â”€â”€ ACADEMIC RESOURCES â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class ResourceCategory(Base):
    __tablename__ = "resource_categories"

    slug = Column(String(100), primary_key=True, index=True)
    label = Column(String(255), nullable=False)
    icon = Column(String(50), default="")
    sendable = Column(Boolean, default=True)


class Resource(Base):
    __tablename__ = "resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(String(100), ForeignKey("courses.id"), nullable=False, index=True)
    category_slug = Column(String(100), ForeignKey("resource_categories.slug"), nullable=False, index=True)
    
    external_path = Column(String, nullable=False, unique=True)
    file_hash = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    
    # Weekly structure mapping
    week_number = Column(Integer, nullable=True, index=True)
    topic_group = Column(String(255), nullable=True, index=True)
    
    # Hybrid search index fields
    tags = Column(String, nullable=True) # comma separated
    search_text = Column(TSVECTOR)

    status = Column(SQLEnum(ResourceStatus), default=ResourceStatus.ACTIVE, nullable=False)
    source_type = Column(String(50), default="system") # e.g. "drive", "system", "admin"

    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    course = relationship("Course", back_populates="resources")
    category = relationship("ResourceCategory")

    __table_args__ = (
        Index("idx_resources_search", "search_text", postgresql_using="gin"),
    )


# â”€â”€ IDENTITY & STUDENTS & ADMINS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(AdminRole), default=AdminRole.ADMIN, nullable=False)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=True, index=True) # Null for SUPER_ADMIN resolving to global access
    
    created_at = Column(DateTime, default=_now)
    last_login = Column(DateTime, nullable=True)


class Student(Base):
    __tablename__ = "students"

    id = Column(String(100), primary_key=True, index=True)  # School ID (authoritative)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=_now)

    institution = relationship("Institution")

class TelegramLink(Base):
    __tablename__ = "telegram_links"

    telegram_id = Column(String(100), primary_key=True, index=True)  # Telegram numeric ID as string
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=False, index=True)
    telegram_username = Column(String(255), nullable=True)
    student_id = Column(String(100), ForeignKey("students.id"), nullable=True)
    
    # Conflicted lock mappings
    is_conflicted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_now)

    student = relationship("Student")
    institution = relationship("Institution")

    __table_args__ = (
        UniqueConstraint("institution_id", "student_id", name="uq_telegram_links_institution_student"),
        Index("idx_telegram_links_conflict", "institution_id", "is_conflicted"),
    )


# â”€â”€ LIFECYCLE & SYNC INCIDENTS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class ReportSubmission(Base):
    __tablename__ = "report_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=True) # Direct user tracking map bypass
    telegram_id = Column(String(100), ForeignKey("telegram_links.telegram_id"), nullable=False)
    
    context_type = Column(SQLEnum(ReportContextType), default=ReportContextType.ISSUE, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    metadata_blob = Column(JSONB, nullable=True) # Holds suggested drive links or deep context
    
    course_id = Column(String(100), nullable=True)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id"), nullable=True)
    
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.OPEN, nullable=False)
    resolution_note = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class SyncError(Base):
    __tablename__ = "sync_errors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = Column(String, nullable=False, index=True)
    reason = Column(Text, nullable=False)
    severity = Column(SQLEnum(ValidationSeverity), default=ValidationSeverity.WARNING)
    raw_metadata = Column(Text, nullable=True)
    
    status = Column(SQLEnum(QuarantineStatus), default=QuarantineStatus.PENDING)
    detected_at = Column(DateTime, default=_now)

class IngestionLog(Base):
    __tablename__ = "ingestion_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id"), nullable=True)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id"), nullable=True)
    action = Column(String(50), nullable=False) # e.g. "create", "override"
    duplicate_flag = Column(Boolean, default=False)
    context_snapshot = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=_now)

# â”€â”€ BEHAVIORAL INTELLIGENCE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class UsageSignal(Base):
    __tablename__ = "usage_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    metadata_blob = Column(JSONB, nullable=False) # e.g. {"query": "calc 1", "latency_ms": 120}
    timestamp = Column(DateTime, default=_now, index=True)
    
    __table_args__ = (
        Index("idx_usage_timestamp", "timestamp"),
    )

class UsageAggregate(Base):
    __tablename__ = "usage_aggregates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String, nullable=True, index=True)
    count = Column(Integer, default=0)
    aggregate_period = Column(String, default="daily") # daily, weekly
    created_at = Column(DateTime, default=_now)

class UsageInsight(Base):
    __tablename__ = "usage_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    insight_type = Column(String(100), nullable=False) # e.g., "top_failed_queries"
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=_now)


# â”€â”€ COMMUNITY Q&A (CORE LOOP) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class QAStatus(str, enum.Enum):
    OPEN = "OPEN"
    ANSWERED = "ANSWERED"
    CLOSED = "CLOSED"


class QAVoteValue(int, enum.Enum):
    DOWN = -1
    UP = 1


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=False, index=True)
    author_telegram_id = Column(String(100), ForeignKey("telegram_links.telegram_id"), nullable=False, index=True)

    course_id = Column(String(100), nullable=True, index=True)  # optional course slug/id
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)

    status = Column(SQLEnum(QAStatus), default=QAStatus.OPEN, nullable=False, index=True)
    created_at = Column(DateTime, default=_now, index=True)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    search_text = Column(TSVECTOR)

    institution = relationship("Institution")

    __table_args__ = (
        Index("idx_questions_search", "search_text", postgresql_using="gin"),
        Index("idx_questions_institution_created", "institution_id", "created_at"),
    )


class Answer(Base):
    __tablename__ = "answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False, index=True)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=False, index=True)
    author_telegram_id = Column(String(100), ForeignKey("telegram_links.telegram_id"), nullable=False, index=True)

    body = Column(Text, nullable=False)
    is_accepted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_now, index=True)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    search_text = Column(TSVECTOR)

    __table_args__ = (
        Index("idx_answers_search", "search_text", postgresql_using="gin"),
        Index("idx_answers_question_created", "question_id", "created_at"),
    )


class Vote(Base):
    __tablename__ = "votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=False, index=True)
    voter_telegram_id = Column(String(100), ForeignKey("telegram_links.telegram_id"), nullable=False, index=True)

    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True, index=True)
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id"), nullable=True, index=True)

    value = Column(Integer, nullable=False)  # -1 or +1
    created_at = Column(DateTime, default=_now, index=True)

    __table_args__ = (
        CheckConstraint("value IN (-1, 1)", name="ck_votes_value_range"),
        CheckConstraint(
            "(question_id IS NOT NULL AND answer_id IS NULL) OR (question_id IS NULL AND answer_id IS NOT NULL)",
            name="ck_votes_target_xor",
        ),
        UniqueConstraint("institution_id", "voter_telegram_id", "question_id", name="uq_vote_question_per_user"),
        UniqueConstraint("institution_id", "voter_telegram_id", "answer_id", name="uq_vote_answer_per_user"),
        Index("idx_votes_institution_question", "institution_id", "question_id"),
        Index("idx_votes_institution_answer", "institution_id", "answer_id"),
    )

