import os
import csv
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.api.models import (
    Base, Institution, Course, ResourceCategory, Resource, 
    Student, ContentStrategy, SyncError, ValidationSeverity, QuarantineStatus
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sync_service")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password123@localhost:5432/academic_hub")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def recreate_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    log.info("Database recreated successfully.")

class SyncPipeline:
    def __init__(self, manifests_root: Path, resources_root: Path):
        self.db = SessionLocal()
        self.manifests_root = manifests_root
        self.resources_root = resources_root
        self.errors = []
        
    def run(self):
        try:
            self._ingest_students()
            self._ingest_metadata()
            self._ingest_resources()
            self._evaluate_errors()
        finally:
            self.db.close()

    def _log_quarantine(self, path: Path, reason: str, metadata: dict = None, severity=ValidationSeverity.WARNING):
        error = SyncError(
            file_path=str(path),
            reason=reason,
            severity=severity,
            raw_metadata=json.dumps(metadata) if metadata else None
        )
        self.db.add(error)
        self.db.commit()
        self.errors.append(error)

    def _evaluate_errors(self):
        if len(self.errors) >= 3:
            log.warning(f"THRESHOLD EXCEEDED: {len(self.errors)} files failed validation and were quarantined. Triggering Admin Alert.")
        else:
            log.info(f"Sync complete. {len(self.errors)} anomalies quarantined.")

    def _ingest_students(self):
        # Database now seeded directly from Dashboard UI. Passing test record.
        test_student_id = "test_123"
        if not self.db.query(Student).filter_by(id=test_student_id).first():
            student = Student(id=test_student_id, full_name="Admin Verified User")
            self.db.add(student)
            self.db.commit()
            log.info("Student Verification DB seeded with Admin User.")

    def _ingest_metadata(self):
        # Maps categories and institutions into the core tables.
        cat_file = self.manifests_root / "categories.json"
        with open(cat_file, 'r', encoding='utf-8') as f:
            for cat in json.load(f):
                if not self.db.query(ResourceCategory).filter_by(slug=cat['slug']).first():
                    rc = ResourceCategory(
                        slug=cat['slug'], 
                        label=cat['label'], 
                        icon=cat.get('icon', ''),
                        sendable=cat.get('sendable', True)
                    )
                    self.db.add(rc)

        # Ingest Institutions
        sit = Institution(id="sit", display_name="Singapore Institute of Technology")
        self.db.merge(sit)
        self.db.commit()
        
    def _ingest_resources(self):
        # We parse Quarter 1 -> Courses -> Files strictly through Validation Gates.
        sit = self.db.query(Institution).filter_by(id="sit").first()
        quarter_root = self.resources_root / "Quarter_1"
        if not quarter_root.exists():
            return
            
        for folder in quarter_root.iterdir():
            if not folder.is_dir():
                continue
                
            course_id = folder.name.lower().replace(" ", "_")
            course = self.db.query(Course).filter_by(id=course_id).first()
            if not course:
                # Validate and Recover: Assume folder name is course title
                course = Course(
                    id=course_id, institution_id=sit.id, quarter=1, 
                    title=folder.name.replace("_", " ").title(),
                    folder_path=str(folder.relative_to(self.resources_root)),
                    content_strategy=ContentStrategy.WEEK_DRIVEN
                )
                self.db.add(course)
                self.db.flush()

            self._traverse_course_drive(course, folder)
        self.db.commit()

    def _traverse_course_drive(self, course: Course, folder: Path):
        for path in folder.rglob("*"):
            if path.is_dir() or path.name.startswith("."):
                continue
                
            # Validation Layer
            file_hash = str(path.stat().st_mtime)
            title = path.stem.replace("_", " ")
            parent = path.parent.name.lower()
            
            # Simple heuristic mapping
            category_slug = "readings"
            if "exam" in parent: category_slug = "exams"
            elif "note" in parent: category_slug = "lecture_notes"
            elif "assignment" in parent: category_slug = "assignments"
            
            week_num = None
            if parent.startswith("week_"):
                try:
                    week_num = int(parent.split("_")[1])
                except ValueError:
                    self._log_quarantine(path, "Malformed week folder structure.", metadata={"inferred_course": course.id})
                    continue
                    
            res = self.db.query(Resource).filter_by(external_path=str(path)).first()
            if not res:
                res = Resource(
                    course_id=course.id, category_slug=category_slug, external_path=str(path),
                    title=title, week_number=week_num, file_hash=file_hash,
                    tags=None
                )
                self.db.add(res)
            elif res.file_hash != file_hash:
                res.file_hash = file_hash
                res.updated_at = datetime.utcnow()

if __name__ == "__main__":
    recreate_db()
    
    root = Path("..").resolve().parent
    SyncPipeline(
        manifests_root=root / "academic_hub" / "manifests",
        resources_root=root / "resources" / "institutions" / "sit"
    ).run()
