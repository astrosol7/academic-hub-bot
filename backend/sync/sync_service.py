import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Fix path to ensure 'backend' and 'academic_hub' are found
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.api.database import engine as db_engine
from backend.api.models import (
    Base, Institution, Course, ResourceCategory, Resource,
    ContentStrategy, SyncError, ValidationSeverity, ResourceStatus
)
from academic_hub.config import load_config
from academic_hub.infrastructure.loader import (
    load_category_registry, load_institution_manifest, load_course_manifests
)
from academic_hub.utils.parsing import (
    infer_category_slug, humanize_file_label, parse_week_number, canonical_week_folder
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("sync_service")

# Load configuration
config = load_config(require_token=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

SUPPORTED_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".doc", ".docx", ".zip"}

class SyncPipeline:
    def __init__(self, manifests_root: Path, resources_root: Path):
        self.db = SessionLocal()
        self.manifests_root = manifests_root
        self.resources_root = resources_root
        self.errors = []
        
    def run(self):
        log.info("🚀 Starting Hardened Sync Pipeline...")
        try:
            category_registry = load_category_registry(self.manifests_root)
            institution_manifest = load_institution_manifest(self.manifests_root, config.institution_slug)
            course_manifests = load_course_manifests(self.manifests_root, institution_manifest)

            self._sync_categories(category_registry)
            self._sync_institution(institution_manifest)
            self._sync_courses(course_manifests, institution_manifest)
            
            log.info("✨ Sync complete.")
        except Exception as e:
            log.exception(f"💥 Sync failed: {e}")
            self.db.rollback()
        finally:
            self.db.close()

    def _sync_categories(self, registry: dict):
        log.info("⚙️ Syncing categories...")
        for slug, cat in registry.items():
            db_cat = self.db.query(ResourceCategory).filter_by(slug=slug).first()
            if not db_cat:
                db_cat = ResourceCategory(
                    slug=slug,
                    label=cat.label,
                    icon=cat.icon,
                    sendable=cat.sendable
                )
                self.db.add(db_cat)
            else:
                db_cat.label = cat.label
                db_cat.icon = cat.icon
                db_cat.sendable = cat.sendable
        self.db.commit()

    def _sync_institution(self, manifest):
        log.info(f"⚙️ Syncing institution: {manifest.slug}")
        inst = self.db.query(Institution).filter_by(slug=manifest.slug).first()
        if not inst:
            inst = Institution(
                slug=manifest.slug,
                display_name=manifest.display_name,
                metadata_blob=manifest.model_dump(mode="json")
            )
            self.db.add(inst)
            self.db.commit()
            self.db.refresh(inst)
        else:
            inst.display_name = manifest.display_name
            inst.metadata_blob = manifest.model_dump(mode="json")
            self.db.commit()
        return inst

    def _sync_courses(self, manifests: dict, institution_manifest):
        inst = self.db.query(Institution).filter_by(slug=institution_manifest.slug).first()
        
        for course_id, manifest in manifests.items():
            log.info(f"📚 Syncing course: {course_id} ({manifest.title})")
            course = self.db.query(Course).filter_by(id=course_id).first()
            
            strategy = ContentStrategy.WEEK_DRIVEN if manifest.supports_weeks else ContentStrategy.TOPIC_DRIVEN
            
            if not course:
                course = Course(
                    id=course_id,
                    institution_id=inst.id,
                    quarter=manifest.quarter,
                    title=manifest.title,
                    folder_path=manifest.folder,
                    content_strategy=strategy,
                    week_count=manifest.week_count,
                    metadata_blob=manifest.model_dump(mode="json")
                )
                self.db.add(course)
            else:
                course.title = manifest.title
                course.quarter = manifest.quarter
                course.folder_path = manifest.folder
                course.content_strategy = strategy
                course.week_count = manifest.week_count
                course.metadata_blob = manifest.model_dump(mode="json")
            
            self.db.flush()
            self._sync_course_resources(course, manifest)
        
        self.db.commit()

    def _sync_course_resources(self, course: Course, manifest):
        # 1. Top-level files
        course_dir = self.resources_root / f"Quarter_{course.quarter}" / manifest.folder
        if not course_dir.is_dir():
            log.warning(f"⚠️ Course directory not found: {course_dir}")
            return

        # Simple crawl matching legacy logic
        self._crawl_directory(course, course_dir, week_number=None)
        
        # 2. Weekly files
        if manifest.supports_weeks:
            week_root = course_dir / "weeks"
            for week_num in range(1, manifest.week_count + 1):
                week_dir = week_root / canonical_week_folder(week_num)
                if week_dir.is_dir():
                    self._crawl_directory(course, week_dir, week_number=week_num)

    def _crawl_directory(self, course: Course, directory: Path, week_number: Optional[int]):
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if path.name.startswith(".") or "__pycache__" in path.parts:
                continue
                
            rel_path = str(path.relative_to(self.resources_root))
            file_hash = str(path.stat().st_mtime)
            
            # Use bot's inference logic
            category_slug = infer_category_slug(path)
            title = humanize_file_label(path.stem)
            
            res = self.db.query(Resource).filter_by(external_path=rel_path).first()
            if not res:
                res = Resource(
                    course_id=course.id,
                    category_slug=category_slug,
                    external_path=rel_path,
                    title=title,
                    week_number=week_number,
                    file_hash=file_hash,
                    status=ResourceStatus.ACTIVE,
                    source_type="system"
                )
                self.db.add(res)
                log.debug(f"Added resource: {title}")
            else:
                res.title = title
                res.category_slug = category_slug
                res.week_number = week_number
                res.file_hash = file_hash
                res.status = ResourceStatus.ACTIVE

if __name__ == "__main__":
    pipeline = SyncPipeline(
        manifests_root=config.manifests_root,
        resources_root=config.resources_root
    )
    pipeline.run()
