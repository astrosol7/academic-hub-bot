"""
Institutional Configuration Management
Handles multi-tenant institutional setup with role-based access control and customization
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
import yaml

log = logging.getLogger(__name__)

class InstitutionType(str, Enum):
    """Types of educational institutions"""
    UNIVERSITY = "university"
    COLLEGE = "college"
    VOCATIONAL = "vocational"
    HIGH_SCHOOL = "high_school"
    MIDDLE_SCHOOL = "middle_school"
    ELEMENTARY = "elementary"
    CORPORATE_TRAINING = "corporate_training"
    RESEARCH_INSTITUTE = "research_institute"

class InstitutionTheme(str, Enum):
    """Predefined themes for institutions"""
    DEFAULT = "default"
    ACADEMIC = "academic"
    PROFESSIONAL = "professional"
    MODERN = "modern"
    CORPORATE = "corporate"
    RESEARCH = "research"

class Feature(str, Enum):
    """Feature flags for institutions"""
    RESOURCE_SHARING = "resource_sharing"
    COLLABORATIVE_WORKSPACE = "collaborative_workspace"
    ADVANCED_ANALYTICS = "advanced_analytics"
    CUSTOM_BRANDING = "custom_branding"
    INTEGRATED_CALENDAR = "integrated_calendar"
    EXTERNAL_INTEGRATIONS = "external_integrations"
    MULTI_LANGUAGE_SUPPORT = "multi_language_support"
    CUSTOM_WORKFLOWS = "custom_workflows"

@dataclass
class InstitutionConfig:
    """Configuration for a single institution"""
    id: str
    name: str
    type: InstitutionType
    domain: str
    theme: InstitutionTheme
    features: List[Feature]
    custom_settings: Dict[str, Any]
    branding: Dict[str, str]
    admin_users: List[str]  # Super admin users
    created_at: str
    updated_at: str
    is_active: bool = True

@dataclass
class SystemFeature:
    """System-wide feature configuration"""
    name: Feature
    enabled: bool
    description: str
    settings: Dict[str, Any]
    rollout_percentage: float = 0.0

class InstitutionalConfigManager:
    """Manages institutional configurations and multi-tenant setup"""
    
    def __init__(self, config_path: str = "config/institutions.yaml"):
        self.config_path = config_path
        self.institutions: Dict[str, InstitutionConfig] = {}
        self.system_features: Dict[str, SystemFeature] = {}
        self.load_configurations()
    
    def load_configurations(self):
        """Load all institutional configurations"""
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                
                for inst_data in config_data.get('institutions', []):
                    institution = InstitutionConfig(**inst_data)
                    self.institutions[institution.id] = institution
                    log.info(f"Loaded institution: {institution.name} ({institution.type})")
                
                # Load system features
                for feature_data in config_data.get('features', []):
                    feature = SystemFeature(**feature_data)
                    self.system_features[feature.name] = feature
                    log.info(f"Loaded feature: {feature.name} - {feature.enabled}")
                
        except Exception as e:
            log.error(f"Failed to load configurations: {e}")
    
    def save_configurations(self):
        """Save all configurations to file"""
        try:
            config_data = {
                'institutions': [
                    {
                        'id': inst.id,
                        'name': inst.name,
                        'type': inst.type.value,
                        'domain': inst.domain,
                        'theme': inst.theme.value,
                        'features': inst.features,
                        'branding': inst.branding,
                        'admin_users': inst.admin_users,
                        'created_at': inst.created_at,
                        'updated_at': inst.updated_at,
                        'is_active': inst.is_active
                    } for inst in self.institutions.values()
                ],
                'features': [
                    {
                        'name': feature.name,
                        'enabled': feature.enabled,
                        'description': feature.description,
                        'settings': feature.settings,
                        'rollout_percentage': feature.rollout_percentage
                    } for feature in self.system_features.values()
                ]
            }
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
                log.info("Configurations saved successfully")
                
        except Exception as e:
            log.error(f"Failed to save configurations: {e}")
    
    def get_institution(self, institution_id: str) -> Optional[InstitutionConfig]:
        """Get institution configuration by ID"""
        return self.institutions.get(institution_id)
    
    def get_all_institutions(self) -> List[InstitutionConfig]:
        """Get all institution configurations"""
        return list(self.institutions.values())
    
    def create_institution(self, config: InstitutionConfig) -> str:
        """Create new institution configuration"""
        institution_id = f"inst_{len(self.institutions) + 1:03d}"
        
        self.institutions[institution_id] = config
        config.created_at = datetime.utcnow().isoformat()
        config.updated_at = config.created_at
        
        self.save_configurations()
        log.info(f"Created institution: {config.name} ({config.type})")
        return institution_id
    
    def update_institution(self, institution_id: str, updates: Dict[str, Any]) -> bool:
        """Update institution configuration"""
        if institution_id not in self.institutions:
            log.error(f"Institution {institution_id} not found")
            return False
        
        institution = self.institutions[institution_id]
        
        for key, value in updates.items():
            if hasattr(institution, key):
                setattr(institution, key, value)
        
        institution.updated_at = datetime.utcnow().isoformat()
        self.save_configurations()
        log.info(f"Updated institution: {institution.name}")
        return True
    
    def delete_institution(self, institution_id: str) -> bool:
        """Delete institution configuration"""
        if institution_id not in self.institutions:
            log.error(f"Institution {institution_id} not found")
            return False
        
        del self.institutions[institution_id]
        self.save_configurations()
        log.info(f"Deleted institution: {institution_id}")
        return True
    
    def get_institution_users(self, institution_id: str) -> List[str]:
        """Get admin users for specific institution"""
        institution = self.get_institution(institution_id)
        return institution.admin_users if institution else []
    
    def add_institution_admin(self, institution_id: str, user_id: str) -> bool:
        """Add admin user to institution"""
        institution = self.get_institution(institution_id)
        if not institution:
            log.error(f"Institution {institution_id} not found")
            return False
        
        if user_id not in institution.admin_users:
            institution.admin_users.append(user_id)
            institution.updated_at = datetime.utcnow().isoformat()
            self.save_configurations()
            log.info(f"Added admin user {user_id} to institution {institution_id}")
            return True
        
        log.warning(f"User {user_id} already admin for institution {institution_id}")
        return False
    
    def remove_institution_admin(self, institution_id: str, user_id: str) -> bool:
        """Remove admin user from institution"""
        institution = self.get_institution(institution_id)
        if not institution:
            log.error(f"Institution {institution_id} not found")
            return False
        
        if user_id in institution.admin_users:
            institution.admin_users.remove(user_id)
            institution.updated_at = datetime.utcnow().isoformat()
            self.save_configurations()
            log.info(f"Removed admin user {user_id} from institution {institution_id}")
            return True
        
        log.warning(f"User {user_id} not admin for institution {institution_id}")
        return False
    
    def get_institution_theme(self, institution_id: str) -> InstitutionTheme:
        """Get institution theme"""
        institution = self.get_institution(institution_id)
        return institution.theme if institution else InstitutionTheme.DEFAULT
    
    def get_institution_features(self, institution_id: str) -> List[Feature]:
        """Get enabled features for institution"""
        institution = self.get_institution(institution_id)
        return institution.features if institution else []
    
    def is_feature_enabled(self, feature: Feature, institution_id: str = None) -> bool:
        """Check if feature is enabled for institution"""
        if institution_id:
            institution = self.get_institution(institution_id)
            return feature in institution.features
        else:
            # Check system-wide feature
            system_feature = self.system_features.get(feature.value)
            return system_feature.enabled if system_feature else False
    
    def enable_feature(self, feature: Feature, institution_id: str = None, settings: Dict[str, Any] = None) -> bool:
        """Enable feature for institution or system-wide"""
        if institution_id:
            institution = self.get_institution(institution_id)
            if feature not in institution.features:
                institution.features.append(feature)
            institution.updated_at = datetime.utcnow().isoformat()
        else:
            # Enable system-wide feature
            system_feature = self.system_features.get(feature.value)
            if system_feature:
                system_feature.enabled = True
                system_feature.settings = settings or {}
                system_feature.rollout_percentage = 100.0
        
        self.save_configurations()
        log.info(f"Enabled feature: {feature.value}")
        return True
    
    def disable_feature(self, feature: Feature, institution_id: str = None) -> bool:
        """Disable feature for institution or system-wide"""
        if institution_id:
            institution = self.get_institution(institution_id)
            if feature in institution.features:
                institution.features.remove(feature)
            institution.updated_at = datetime.utcnow().isoformat()
        else:
            # Disable system-wide feature
            system_feature = self.system_features.get(feature.value)
            if system_feature:
                system_feature.enabled = False
        
        self.save_configurations()
        log.info(f"Disabled feature: {feature.value}")
        return True
    
    def get_institution_branding(self, institution_id: str) -> Dict[str, str]:
        """Get institution branding configuration"""
        institution = self.get_institution(institution_id)
        return institution.branding if institution else {}
    
    def update_institution_branding(self, institution_id: str, branding: Dict[str, str]) -> bool:
        """Update institution branding"""
        institution = self.get_institution(institution_id)
        if not institution:
            log.error(f"Institution {institution_id} not found")
            return False
        
        institution.branding.update(branding)
        institution.updated_at = datetime.utcnow().isoformat()
        self.save_configurations()
        log.info(f"Updated branding for institution {institution_id}")
        return True
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        return {
            'total_institutions': len(self.institutions),
            'active_institutions': len([inst for inst in self.institutions.values() if inst.is_active]),
            'total_features': len(self.system_features),
            'enabled_features': len([f for f in self.system_features.values() if f.enabled]),
            'system_health': 'healthy',
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def validate_institution_access(self, user_id: str, institution_id: str, required_permission: str) -> bool:
        """Validate if user has access to institution"""
        institution = self.get_institution(institution_id)
        if not institution:
            log.error(f"Institution {institution_id} not found")
            return False
        
        # Check if user is institution admin
        if user_id in institution.admin_users:
            return True
        
        log.warning(f"User {user_id} lacks required permission: {required_permission}")
        return False
    
    def get_feature_settings(self, feature: Feature, institution_id: str = None) -> Dict[str, Any]:
        """Get settings for specific feature"""
        if institution_id:
            institution = self.get_institution(institution_id)
            for inst_feature in institution.features:
                if inst_feature.name == feature.value:
                    return inst_feature.settings or {}
        
        # Check system-wide feature
        system_feature = self.system_features.get(feature.value)
        return system_feature.settings if system_feature else {}
    
    def update_feature_settings(self, feature: Feature, institution_id: str = None, settings: Dict[str, Any]) -> bool:
        """Update settings for specific feature"""
        if institution_id:
            institution = self.get_institution(institution_id)
            for i, inst_feature in enumerate(institution.features):
                if inst_feature.name == feature.value:
                    institution.features[i] = SystemFeature(
                        name=feature,
                        enabled=True,
                        description=inst_feature.description,
                        settings=settings
                    )
                    institution.updated_at = datetime.utcnow().isoformat()
                    break
        else:
            # Update system-wide feature
            system_feature = self.system_features.get(feature.value)
            if system_feature:
                system_feature.settings = settings
                system_feature.updated_at = datetime.utcnow().isoformat()
        
        self.save_configurations()
        log.info(f"Updated settings for feature: {feature.value}")
        return True
    
    def export_config(self, institution_id: str = None) -> Dict[str, Any]:
        """Export configuration for backup or migration"""
        data = {
            'institutions': {},
            'features': {},
            'export_timestamp': datetime.utcnow().isoformat()
        }
        
        if institution_id:
            institution = self.get_institution(institution_id)
            data['institutions'][institution_id] = {
                'id': institution.id,
                'name': institution.name,
                'type': institution.type.value,
                'domain': institution.domain,
                'theme': institution.theme.value,
                'features': [
                    {
                        'name': f.name,
                        'enabled': True,
                        'description': f.description,
                        'settings': f.settings or {}
                    } for f in institution.features
                ],
                'branding': institution.branding,
                'admin_users': institution.admin_users,
                'created_at': institution.created_at,
                'updated_at': institution.updated_at,
                'is_active': institution.is_active
            }
        else:
            # Export all institutions
            for inst_id, inst in self.institutions.items():
                data['institutions'][inst_id] = {
                    'id': inst.id,
                    'name': inst.name,
                    'type': inst.type.value,
                    'domain': inst.domain,
                    'theme': inst.theme.value,
                    'features': [
                        {
                            'name': f.name,
                            'enabled': True,
                            'description': f.description,
                            'settings': f.settings or {}
                        } for f in inst.features
                    ],
                    'branding': inst.branding,
                    'admin_users': inst.admin_users,
                    'created_at': inst.created_at,
                    'updated_at': inst.updated_at,
                    'is_active': inst.is_active
                }
        
        # Export all system features
        for feature_name, feature in self.system_features.items():
            data['features'][feature_name] = {
                'name': feature.name,
                'enabled': feature.enabled,
                'description': feature.description,
                'settings': feature.settings,
                'rollout_percentage': feature.rollout_percentage
            }
        
        return data
    
    def import_config(self, config_data: Dict[str, Any]) -> bool:
        """Import configuration from data"""
        try:
            # Import institutions
            for inst_data in config_data.get('institutions', []):
                institution = InstitutionConfig(**inst_data)
                self.institutions[institution.id] = institution
                log.info(f"Imported institution: {institution.name}")
            
            # Import system features
            for feature_data in config_data.get('features', []):
                feature = SystemFeature(**feature_data)
                self.system_features[feature.name] = feature
                log.info(f"Imported feature: {feature.name}")
            
            self.save_configurations()
            log.info("Configuration imported successfully")
            return True
            
        except Exception as e:
            log.error(f"Failed to import configuration: {e}")
            return False

# Default configurations
DEFAULT_INSTITUTIONS = [
    {
        'id': 'demo_university',
        'name': 'Demo University',
        'type': InstitutionType.UNIVERSITY,
        'domain': 'demo.edu',
        'theme': InstitutionTheme.ACADEMIC,
        'features': [
            Feature.RESOURCE_SHARING,
            Feature.COLLABORATIVE_WORKSPACE,
            Feature.ADVANCED_ANALYTICS
        ],
        'branding': {
            'primary_color': '#3b82f6',
            'secondary_color': '#6c757d',
            'logo_url': 'https://example.com/logo.png',
            'custom_css': ''
        },
        'admin_users': ['admin001', 'admin002'],
        'created_at': '2026-01-01T00:00:00Z',
        'updated_at': '2026-01-01T00:00:00Z',
        'is_active': True
    }
]

DEFAULT_FEATURES = [
    {
        'name': Feature.RESOURCE_SHARING,
        'enabled': True,
        'description': 'Allow students to share resources with peers',
        'settings': {
            'share_with_public': True,
            'require_approval': False,
            'share_analytics': True
        },
        'rollout_percentage': 100.0
    },
    {
        'name': Feature.COLLABORATIVE_WORKSPACE,
        'enabled': True,
        'description': 'Enable collaborative study spaces and group projects',
        'settings': {
            'max_group_size': 50,
            'allow_external_collaborators': False,
            'auto_save_interval': 300
        },
        'rollout_percentage': 100.0
    },
    {
        'name': Feature.ADVANCED_ANALYTICS,
        'enabled': True,
        'description': 'Advanced learning analytics and progress tracking',
        'settings': {
            'track_learning_paths': True,
            'generate_recommendations': True,
            'export_reports': True,
            'retention_days': 365
        },
        'rollout_percentage': 75.0
    }
]

# Factory function
def create_config_manager(config_path: str = "config/institutions.yaml") -> InstitutionalConfigManager:
    """Create institutional config manager with default setup"""
    manager = InstitutionalConfigManager(config_path)
    
    # Initialize with defaults if no config exists
    import os
    if not os.path.exists(config_path):
        log.info("No existing configuration found, creating defaults")
        
        # Create default institutions
        for inst_config in DEFAULT_INSTITUTIONS:
            institution = InstitutionConfig(**inst_config)
            manager.institutions[institution.id] = institution
        
        # Initialize default features
        for feature_config in DEFAULT_FEATURES:
            feature = SystemFeature(**feature_config)
            manager.system_features[feature.name] = feature
        
        # Save initial configuration
        manager.save_configurations()
        log.info("Default configuration created")
    
    return manager
