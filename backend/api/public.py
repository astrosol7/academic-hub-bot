from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.api.database import get_db
from backend.api.models import Institution, Course, ResourceCategory

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

# --- ENDPOINTS ---

@router.get("/api/v1/public/institutions", response_model=list[PublicInstitution])
def list_institutions(db: Session = Depends(get_db)):
    """Open discovery for all supported schools."""
    items = db.query(Institution).all()
    return [
        PublicInstitution(id=str(i.id), slug=i.slug, name=i.name)
        for i in items
    ]

@router.get("/api/v1/public/institutions/{slug}/courses", response_model=list[PublicCourse])
def list_courses(slug: str, db: Session = Depends(get_db)):
    """Open discovery for courses in a specific school."""
    inst = db.query(Institution).filter(Institution.slug == slug).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    courses = db.query(Course).filter(Course.institution_id == inst.id).all()
    return [
        PublicCourse(id=c.id, title=c.title, week_count=c.week_count)
        for c in courses
    ]

@router.get("/api/v1/public/categories", response_model=list[PublicCategory])
def list_categories(db: Session = Depends(get_db)):
    """List material types (Books, Exams, etc)."""
    items = db.query(ResourceCategory).all()
    return [
        PublicCategory(slug=c.slug, name=c.name, icon=c.icon)
        for c in items
    ]
