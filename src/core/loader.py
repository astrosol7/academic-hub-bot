"""
Core loader utilities for Academic Hub
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class ManifestError(Exception):
    """Error loading manifest files"""
    pass


def load_institution_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load institution manifest from JSON file"""
    try:
        if not manifest_path.exists():
            raise ManifestError(f"Manifest file not found: {manifest_path}")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate required fields
        required_fields = ['institution', 'quarter_labels', 'courses']
        for field in required_fields:
            if field not in data:
                raise ManifestError(f"Missing required field: {field}")
        
        return data
        
    except json.JSONDecodeError as e:
        raise ManifestError(f"Invalid JSON in manifest: {e}")
    except Exception as e:
        raise ManifestError(f"Error loading manifest: {e}")


def validate_manifest_structure(data: Dict[str, Any]) -> bool:
    """Validate manifest structure"""
    try:
        # Check institution info
        if not isinstance(data.get('institution'), dict):
            return False
        
        # Check quarter labels
        quarters = data.get('quarter_labels', {})
        if not isinstance(quarters, dict):
            return False
        
        # Check courses
        courses = data.get('courses', [])
        if not isinstance(courses, list):
            return False
        
        return True
        
    except Exception:
        return False
