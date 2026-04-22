"""
Core validation utilities for Academic Hub
"""

from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ValidationIssue:
    """Validation issue"""
    code: str
    message: str
    severity: str = "error"


@dataclass
class ValidationReport:
    """Validation report"""
    issues: List[ValidationIssue]
    is_valid: bool
    
    def __post_init__(self):
        self.is_valid = len(self.issues) == 0


class RepositoryValidator:
    """Repository validator for content structure"""
    
    def __init__(self, root_path: Path, institution: Dict[str, Any], categories: Dict[str, Any], courses: List[Dict[str, Any]]):
        self.root_path = root_path
        self.institution = institution
        self.categories = categories
        self.courses = courses
        self.issues = []
    
    def validate(self) -> ValidationReport:
        """Validate repository structure"""
        self._validate_courses()
        self._validate_directories()
        self._validate_files()
        
        return ValidationReport(
            issues=self.issues,
            is_valid=len(self.issues) == 0
        )
    
    def _validate_courses(self) -> None:
        """Validate course structure"""
        course_ids = set()
        
        for course in self.courses:
            course_id = course.get('id', '')
            
            # Check for duplicate course IDs
            if course_id in course_ids:
                self.issues.append(ValidationIssue(
                    code="duplicate_course_title",
                    message=f"Duplicate course ID: {course_id}",
                    severity="error"
                ))
            
            course_ids.add(course_id)
            
            # Check required course fields
            required_fields = ['id', 'title', 'quarter', 'folder']
            for field in required_fields:
                if field not in course:
                    self.issues.append(ValidationIssue(
                        code=f"missing_course_field_{field}",
                        message=f"Course {course_id} missing field: {field}",
                        severity="error"
                    ))
    
    def _validate_directories(self) -> None:
        """Validate required directories exist"""
        required_dirs = ['courses', 'resources']
        
        for dir_name in required_dirs:
            dir_path = self.root_path / dir_name
            if not dir_path.exists():
                self.issues.append(ValidationIssue(
                    code=f"missing_{dir_name}_dir",
                    message=f"Missing required directory: {dir_name}",
                    severity="error"
                ))
    
    def _validate_files(self) -> None:
        """Validate required files exist"""
        # Check for manifest files
        manifest_path = self.root_path / f"{self.institution.get('slug', 'institution')}.json"
        if not manifest_path.exists():
            self.issues.append(ValidationIssue(
                code="missing_manifest",
                message=f"Missing manifest file: {manifest_path.name}",
                severity="error"
            ))
        
        # Check course files
        for course in self.courses:
            course_file = course.get('folder', '')
            if course_file:
                course_path = self.root_path / 'courses' / f"{course_file}.json"
                if not course_path.exists():
                    self.issues.append(ValidationIssue(
                        code="missing_course_file",
                        message=f"Missing course file: {course_file}.json",
                        severity="error"
                    ))
