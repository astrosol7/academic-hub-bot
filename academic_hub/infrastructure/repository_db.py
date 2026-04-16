from __future__ import annotations

import logging
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Optional

from academic_hub.domain.models import (
    CategoryDefinition,
    CourseManifest,
    InstitutionManifest,
    ResourceFile,
    ValidationReport,
)
from academic_hub.infrastructure.loader import _validate_model
from backend.api.database import SessionLocal
from backend.api.models import (
    Institution, Course, ResourceCategory, Resource, ResourceStatus
)

log = logging.getLogger(__name__)

class PostgresContentRepository:
    def __init__(self, manifests_root: Path, resources_root: Path, institution_slug: str) -> None:
        self.resources_root = resources_root
        self.institution_slug = institution_slug
        self.db: Session = SessionLocal()
        
        # Load core metadata into memory for fast access (Hybrid pattern)
        self.institution: InstitutionManifest = self._load_institution()
        self.categories: dict[str, CategoryDefinition] = self._load_categories()
        self.courses: dict[str, CourseManifest] = self._load_courses()
        
        # In a real DB-backed system, we might not run a full validation report on every start,
        # but we'll return an empty one for compatibility.
        self.validation_report = ValidationReport()
        self.index_memory_bytes = 0 

    @property
    def index_memory_mb(self) -> float:
        return 0.0

    def list_quarters(self) -> list[int]:
        return sorted(self.institution.quarter_order.keys())

    def list_courses(self, quarter: int) -> list[CourseManifest]:
        return [c for c in self.courses.values() if c.quarter == quarter]

    def get_course(self, course_id: str) -> CourseManifest | None:
        return self.courses.get(course_id)

    def list_course_files(self, course_id: str, category_slug: str, *, syllabus_only: bool = False) -> list[ResourceFile]:
        query = self.db.query(Resource).filter(
            Resource.course_id == course_id,
            Resource.category_slug == category_slug,
            Resource.week_number == None,
            Resource.status == ResourceStatus.ACTIVE
        )
        
        db_resources = query.all()
        files = [self._to_resource_file(r) for r in db_resources]
        
        if syllabus_only:
            from academic_hub.utils.parsing import looks_like_syllabus
            files = [f for f in files if looks_like_syllabus(f.path)]
            
        return sorted(files, key=lambda f: f.label)

    def list_week_files(self, course_id: str, week_number: int, category_slug: str) -> list[ResourceFile]:
        query = self.db.query(Resource).filter(
            Resource.course_id == course_id,
            Resource.category_slug == category_slug,
            Resource.week_number == week_number,
            Resource.status == ResourceStatus.ACTIVE
        )
        db_resources = query.all()
        files = [self._to_resource_file(r) for r in db_resources]
        return sorted(files, key=lambda f: f.label)

    def list_weeks(self, course_id: str) -> list[int]:
        course = self.courses.get(course_id)
        if not course or not course.supports_weeks:
            return []
        return list(range(1, course.week_count + 1))

    # ── PRIVATE HELPERS ───────────────────────────────────────────

    def _load_institution(self) -> InstitutionManifest:
        db_inst = self.db.query(Institution).filter_by(slug=self.institution_slug).first()
        if not db_inst or not db_inst.metadata_blob:
            raise RuntimeError(f"Institution '{self.institution_slug}' not found in DB or has no metadata. Run sync service first.")
        return _validate_model(InstitutionManifest, db_inst.metadata_blob, f"institution '{self.institution_slug}'")

    def _load_categories(self) -> dict[str, CategoryDefinition]:
        db_cats = self.db.query(ResourceCategory).all()
        # Note: We might still need the full CategoryDefinition from categories.json 
        # if the DB ResourceCategory Table is lightweight. 
        # However, we've updated everything to be in DB.
        # But wait, placements and storage_folders might not be in the lightweight Table.
        # So we fall back to reading categories.json for the full Definition, or assume it's in a blob soon.
        # For now, we'll continue to read categories.json for the full definition if it's not and-mapped.
        # Actually, let's assume the sync service should have put everything in a blob if needed,
        # but for now we'll just read categories.json to be safe and compatible.
        
        # Actually, let's stick to the plan: Unified DB. 
        # I'll check if I added metadata_blob to ResourceCategory. No, I didn't.
        # I'll use a hybrid approach: Categories are global and small, so they can stay in JSON 
        # OR I can add a blob to them too.
        
        # For now, I'll read categories.json directly as a shortcut, 
        # but Quarters/Courses/Resources MUST come from DB.
        from academic_hub.infrastructure.loader import load_category_registry
        return load_category_registry(self.resources_root.parent / "manifests")

    def _load_courses(self) -> dict[str, CourseManifest]:
        db_courses = self.db.query(Course).filter(Course.institution_id == self._get_inst_id()).all()
        courses = {}
        for c in db_courses:
            if c.metadata_blob:
                manifest = _validate_model(CourseManifest, c.metadata_blob, f"course manifest '{c.id}'")
                courses[c.id] = manifest
        return courses

    def _get_inst_id(self):
        return self.db.query(Institution.id).filter_by(slug=self.institution_slug).scalar()

    def _to_resource_file(self, resource: Resource) -> ResourceFile:
        return ResourceFile(
            path=self.resources_root / resource.external_path,
            label=resource.title,
            course_id=resource.course_id,
            category_slug=resource.category_slug,
            week_number=resource.week_number,
            source_hint="database",
            file_hash=resource.file_hash
        )

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
