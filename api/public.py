from __future__ import annotations

from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from api.database import get_db
from api.models import (
    Course,
    Institution,
    Resource,
    ResourceCategory,
    ResourceStatus,
)
from api.utils import resolve_limit


router = APIRouter()

# --- SCHEMAS ---

class PublicInstitution(BaseModel):
    id: str
    slug: str
    name: str

class PublicCourse(BaseModel):
    id: str
    title: str
    week_count: Optional[int] = None

class PublicCategory(BaseModel):
    slug: str
    name: str
    icon: Optional[str] = None


class PublicResource(BaseModel):
    id: str
    title: str
    course_id: str
    course_title: str
    institution_slug: str
    institution_name: str
    category_slug: str
    category_name: str
    week_number: Optional[int] = None
    topic_group: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    source_type: str
    created_at: datetime
    access_url: Optional[str] = None
    available_in_web: bool = False


def _split_tags(raw_tags: Optional[str]) -> list[str]:
    if not raw_tags:
        return []
    return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]


def _safe_access_url(path: str) -> Optional[str]:
    parsed = urlparse(path)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return path
    return None


def _serialize_resource(resource: Resource) -> PublicResource:
    course = resource.course
    institution = course.institution if course else None
    category = resource.category
    access_url = _safe_access_url(resource.external_path)

    return PublicResource(
        id=str(resource.id),
        title=resource.title,
        course_id=resource.course_id,
        course_title=course.title if course else resource.course_id,
        institution_slug=institution.slug if institution else "",
        institution_name=institution.display_name if institution else "",
        category_slug=resource.category_slug,
        category_name=category.label if category else resource.category_slug,
        week_number=resource.week_number,
        topic_group=resource.topic_group,
        tags=_split_tags(resource.tags),
        source_type=resource.source_type,
        created_at=resource.created_at,
        access_url=access_url,
        available_in_web=access_url is not None,
    )


def _query_public_resources(
    db: Session,
    *,
    institution_slug: Optional[str] = None,
    course_id: Optional[str] = None,
    category_slug: Optional[str] = None,
    week_number: Optional[int] = None,
    limit: int = 24,
) -> list[PublicResource]:
    query = (
        db.query(Resource)
        .options(
            joinedload(Resource.course).joinedload(Course.institution),
            joinedload(Resource.category),
        )
        .filter(Resource.status == ResourceStatus.ACTIVE)
    )

    if institution_slug:
        query = query.join(Course, Resource.course_id == Course.id).join(
            Institution, Course.institution_id == Institution.id
        )
        query = query.filter(Institution.slug == institution_slug)

    if course_id:
        query = query.filter(Resource.course_id == course_id)

    if category_slug:
        query = query.filter(Resource.category_slug == category_slug)

    if week_number is not None:
        query = query.filter(Resource.week_number == week_number)

    limit = resolve_limit(limit, role="public")
    items = (
        query.order_by(Resource.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_serialize_resource(item) for item in items]

# --- ENDPOINTS ---

@router.get("/api/v1/public/institutions", response_model=list[PublicInstitution])
def list_institutions(db: Session = Depends(get_db)):
    """Open discovery for all supported schools."""
    items = db.query(Institution).order_by(Institution.display_name.asc()).all()
    return [
        PublicInstitution(id=str(i.id), slug=i.slug, name=i.display_name)
        for i in items
    ]

@router.get("/api/v1/public/institutions/{slug}/courses", response_model=list[PublicCourse])
def list_courses(slug: str, db: Session = Depends(get_db)):
    """Open discovery for courses in a specific school."""
    inst = db.query(Institution).filter(Institution.slug == slug).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    courses = (
        db.query(Course)
        .filter(Course.institution_id == inst.id)
        .order_by(Course.title.asc())
        .all()
    )
    return [
        PublicCourse(id=c.id, title=c.title, week_count=c.week_count)
        for c in courses
    ]

@router.get("/api/v1/public/categories", response_model=list[PublicCategory])
def list_categories(db: Session = Depends(get_db)):
    """List material types (Books, Exams, etc)."""
    items = db.query(ResourceCategory).order_by(ResourceCategory.label.asc()).all()
    return [
        PublicCategory(slug=c.slug, name=c.label, icon=c.icon)
        for c in items
    ]


@router.get("/api/v1/public/resources", response_model=list[PublicResource])
def list_public_resources(
    institution_slug: Optional[str] = None,
    course_id: Optional[str] = None,
    category_slug: Optional[str] = None,
    week_number: Optional[int] = None,
    limit: int = 24,
    db: Session = Depends(get_db),
):
    """Browse the latest active resources for the student app."""
    return _query_public_resources(
        db,
        institution_slug=institution_slug,
        course_id=course_id,
        category_slug=category_slug,
        week_number=week_number,
        limit=limit,
    )


@router.get("/api/v1/public/courses/{course_id}/resources", response_model=list[PublicResource])
def list_course_resources(
    course_id: str,
    category_slug: Optional[str] = None,
    week_number: Optional[int] = None,
    limit: int = 24,
    db: Session = Depends(get_db),
):
    """Browse active resources for one course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return _query_public_resources(
        db,
        course_id=course_id,
        category_slug=category_slug,
        week_number=week_number,
        limit=limit,
    )
