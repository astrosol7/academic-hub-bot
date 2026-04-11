import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, 
    Enum as SQLEnum, Text, Index
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

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

# ── INSTITUTIONS & COURSES ──────────────────────────────────────

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String(50), primary_key=True, index=True)
    display_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    courses = relationship("Course", back_populates="institution")

class Course(Base):
    __tablename__ = "courses"

    id = Column(String(100), primary_key=True, index=True)
    institution_id = Column(String(50), ForeignKey("institutions.id"), nullable=False)
    quarter = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    folder_path = Column(String(255), nullable=False)
    
    # Structure typing as per Unbreakable OS rules
    content_strategy = Column(SQLEnum(ContentStrategy), default=ContentStrategy.WEEK_DRIVEN, nullable=False)
    week_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="courses")
    resources = relationship("Resource", back_populates="course")


# ── ACADEMIC RESOURCES ──────────────────────────────────────────

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

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("Course", back_populates="resources")
    category = relationship("ResourceCategory")

    __table_args__ = (
        Index("idx_resources_search", "search_text", postgresql_using="gin"),
    )


# ── IDENTITY & STUDENTS & ADMINS ────────────────────────────────

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(AdminRole), default=AdminRole.ADMIN, nullable=False)
    institution_id = Column(String(50), ForeignKey("institutions.id"), nullable=True) # Null for SUPER_ADMIN resolving to global access
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class Student(Base):
    __tablename__ = "students"

    id = Column(String(100), primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TelegramLink(Base):
    __tablename__ = "telegram_links"

    telegram_id = Column(String(100), primary_key=True, index=True)
    telegram_username = Column(String(255), nullable=True)
    student_id = Column(String(100), ForeignKey("students.id"), nullable=True, unique=True)
    
    # Conflicted lock mappings
    is_conflicted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")


# ── LIFECYCLE & SYNC INCIDENTS ──────────────────────────────────

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
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SyncError(Base):
    __tablename__ = "sync_errors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = Column(String, nullable=False, index=True)
    reason = Column(Text, nullable=False)
    severity = Column(SQLEnum(ValidationSeverity), default=ValidationSeverity.WARNING)
    raw_metadata = Column(Text, nullable=True)
    
    status = Column(SQLEnum(QuarantineStatus), default=QuarantineStatus.PENDING)
    detected_at = Column(DateTime, default=datetime.utcnow)

class IngestionLog(Base):
    __tablename__ = "ingestion_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id"), nullable=True)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id"), nullable=True)
    action = Column(String(50), nullable=False) # e.g. "create", "override"
    duplicate_flag = Column(Boolean, default=False)
    context_snapshot = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ── BEHAVIORAL INTELLIGENCE ─────────────────────────────────────

class UsageSignal(Base):
    __tablename__ = "usage_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    metadata_blob = Column(JSONB, nullable=False) # e.g. {"query": "calc 1", "latency_ms": 120}
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("idx_usage_timestamp", "timestamp"),
    )

class UsageAggregate(Base):
    __tablename__ = "usage_aggregates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String, nullable=True, index=True)
    count = Column(Integer, default=0)
    aggregate_period = Column(String, default="daily") # daily, weekly
    created_at = Column(DateTime, default=datetime.utcnow)

class UsageInsight(Base):
    __tablename__ = "usage_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    insight_type = Column(String(100), nullable=False) # e.g., "top_failed_queries"
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

