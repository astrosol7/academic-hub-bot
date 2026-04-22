"""
Core repository for Academic Hub
"""

import json
import os
from pathlib import Path
from typing import Any, List, Optional, Dict


class FilesystemContentRepository:
    """Filesystem-based content repository"""
    
    def __init__(self, manifests_root: str, resources_root: str, institution_slug: str):
        self.manifests_root = Path(manifests_root)
        self.resources_root = Path(resources_root)
        self.institution_slug = institution_slug
        self._courses_cache = None
        self._manifest_cache = None
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load institution manifest"""
        if self._manifest_cache is None:
            manifest_path = self.manifests_root / f"{self.institution_slug}.json"
            from src.core.loader import load_institution_manifest
            self._manifest_cache = load_institution_manifest(manifest_path)
        return self._manifest_cache
    
    def _load_courses(self) -> List[Dict[str, Any]]:
        """Load courses from manifest"""
        if self._courses_cache is None:
            manifest = self._load_manifest()
            self._courses_cache = manifest.get('courses', [])
        return self._courses_cache
    
    def list_all_courses(self) -> List[Dict[str, Any]]:
        """Get all courses"""
        return self._load_courses()
    
    def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get specific course by ID"""
        courses = self._load_courses()
        for course in courses:
            if course.get('id') == course_id:
                return course
        return None
    
    def get_course_resources(self, course_id: str) -> List[Any]:
        """Get resources for a course"""
        course = self.get_course(course_id)
        if not course:
            return []
        
        # Mock resource objects for now
        resources = []
        week_data = course.get('weeks', {})
        
        for week_num, week_content in week_data.items():
            if isinstance(week_content, dict):
                for category, items in week_content.items():
                    if isinstance(items, list):
                        for item in items:
                            resource = {
                                'id': f"{course_id}_{week_num}_{category}_{len(resources)}",
                                'title': item.get('title', f'Week {week_num} {category}'),
                                'description': item.get('description', ''),
                                'category': category,
                                'week_number': int(week_num),
                                'course_id': course_id,
                                'path': item.get('path', ''),
                                'type': item.get('type', 'file')
                            }
                            resources.append(resource)
        
        return resources
    
    def search_resources(self, query: str) -> List[Dict[str, Any]]:
        """Search resources by title"""
        resources = []
        query_lower = query.lower()
        
        for course in self._load_courses():
            course_resources = self.get_course_resources(course.get('id', ''))
            for resource in course_resources:
                if query_lower in resource.get('title', '').lower():
                    resources.append(resource)
        
        return resources


class PostgresContentRepository:
    """PostgreSQL content repository with SQLAlchemy integration"""
    
    def __init__(self, engine=None):
        from api.database import get_engine, get_session_local
        from api.models import Institution, Course, Resource, ResourceCategory

        self.engine = engine or get_engine()
        self.SessionLocal = get_session_local()
        self.models = {
            'Institution': Institution,
            'Course': Course,
            'Resource': Resource,
            'ResourceCategory': ResourceCategory
        }
        self._institution_cache = None
        self._categories_cache = None

    @property
    def institution(self):
        """Lazy load and cache the primary institution"""
        if self._institution_cache is None:
            # We assume a single institution for this orbit deployment
            from src.core.config import load_config
            config = load_config(require_token=False)
            slug = os.getenv("INSTITUTION_SLUG", "sit")
            
            with self.SessionLocal() as db:
                inst = db.query(self.models['Institution']).filter_by(slug=slug).first()
                if inst:
                    # Map metadata_blob to a dot-accessible object if needed
                    # For now, we manually bridge the expected attributes
                    self._institution_cache = inst
                    # Ensure quarter_labels exists (mocked structure for navigation logic)
                    if not hasattr(self._institution_cache, 'quarter_labels'):
                        blob = getattr(inst, 'metadata_blob', {}) or {}
                        self._institution_cache.quarter_labels = blob.get('quarter_labels', {
                            1: "Quarter 1", 2: "Quarter 2", 3: "Quarter 3", 4: "Quarter 4"
                        })
        return self._institution_cache

    @property
    def categories(self):
        """Cache resource categories for rapid lookup"""
        if self._categories_cache is None:
            with self.SessionLocal() as db:
                cats = db.query(self.models['ResourceCategory']).all()
                self._categories_cache = {c.slug: c for c in cats}
        return self._categories_cache

    def list_all_courses(self) -> List[Any]:
        """Get all courses ranked by quarter"""
        with self.SessionLocal() as db:
            return db.query(self.models['Course']).order_by(self.models['Course'].quarter, self.models['Course'].id).all()
            
    def list_courses(self, quarter: int) -> List[Any]:
        """Get courses for a specific quarter"""
        with self.SessionLocal() as db:
            return db.query(self.models['Course']).filter_by(quarter=quarter).order_by(self.models['Course'].id).all()

    def get_course(self, course_id: str) -> Optional[Any]:
        """Get specific course by ID with metadata support"""
        with self.SessionLocal() as db:
            course = db.query(self.models['Course']).filter_by(id=course_id).first()
            if course:
                # Bridge for navigation service expectations
                blob = getattr(course, 'metadata_blob', {}) or {}
                if not hasattr(course, 'top_level_actions'):
                    course.top_level_actions = tuple(blob.get('top_level_actions', []))
                if not hasattr(course, 'more_files_actions'):
                    course.more_files_actions = tuple(blob.get('more_files_actions', []))
                if not hasattr(course, 'week_actions'):
                    course.week_actions = tuple(blob.get('week_actions', []))
            return course

    def get_course_resources(self, course_id: str) -> List[Any]:
        """Get all active resources for a course"""
        from api.models import ResourceStatus
        with self.SessionLocal() as db:
            return db.query(self.models['Resource']).filter_by(
                course_id=course_id, 
                status=ResourceStatus.ACTIVE
            ).all()

    def get_week_resources(self, course_id: str, week_number: int, category_slug: str) -> List[Any]:
        """Get resources for a specific week and category"""
        from api.models import ResourceStatus
        with self.SessionLocal() as db:
            return db.query(self.models['Resource']).filter_by(
                course_id=course_id,
                week_number=week_number,
                category_slug=category_slug,
                status=ResourceStatus.ACTIVE
            ).all()

    def get_category_resources(self, course_id: str, category_slug: str) -> List[Any]:
        """Get resources for a course and category (non-weekly)"""
        from api.models import ResourceStatus
        with self.SessionLocal() as db:
            return db.query(self.models['Resource']).filter_by(
                course_id=course_id,
                category_slug=category_slug,
                status=ResourceStatus.ACTIVE
            ).all()

    async def search_resources(self, query: str) -> List[Any]:
        """Hybrid search bridging SQL and core logic"""
        # This mirrors the API logic but stays in-process for the bot's repository
        from api.models import ResourceStatus
        from sqlalchemy import func
        
        query_text = query.strip()
        if not query_text or len(query_text) < 2:
            return []
            
        with self.SessionLocal() as db:
            # Full-text search
            results = db.query(self.models['Resource']).filter(
                self.models['Resource'].status == ResourceStatus.ACTIVE,
                self.models['Resource'].search_text.op("@@")(func.plainto_tsquery("english", query_text))
            ).limit(10).all()
            
            if not results:
                # Similarity fallback
                results = db.query(self.models['Resource']).filter(
                    self.models['Resource'].status == ResourceStatus.ACTIVE,
                    func.similarity(self.models['Resource'].title, query_text) > 0.3
                ).order_by(func.similarity(self.models['Resource'].title, query_text).desc()).limit(10).all()
                
            return results
