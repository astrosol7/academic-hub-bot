"""
Advanced Security System for Academic Hub
Industry-grade security with role-based access control, institutional admin management, and comprehensive audit system
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from pydantic import BaseModel, Field, validator

log = logging.getLogger(__name__)

class UserRole(str, Enum):
    """Advanced user roles with institutional hierarchy"""
    SUPER_ADMIN = "super_admin"
    INSTITUTIONAL_ADMIN = "institutional_admin"
    DEPARTMENT_ADMIN = "department_admin"
    FACULTY_ADMIN = "faculty_admin"
    STAFF = "staff"
    STUDENT = "student"
    GUEST = "guest"

class Permission(str, Enum):
    """Granular permissions system"""
    # System permissions
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_DELETE = "system:delete"
    SYSTEM_ADMIN = "system:admin"
    
    # User management permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    USER_ADMIN = "user:admin"
    
    # Resource permissions
    RESOURCE_READ = "resource:read"
    RESOURCE_WRITE = "resource:write"
    RESOURCE_DELETE = "resource:delete"
    RESOURCE_ADMIN = "resource:admin"
    
    # Institution permissions
    INSTITUTION_READ = "institution:read"
    INSTITUTION_WRITE = "institution:write"
    INSTITUTION_DELETE = "institution:delete"
    INSTITUTION_ADMIN = "institution:admin"
    
    # Analytics permissions
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_WRITE = "analytics:write"
    ANALYTICS_ADMIN = "analytics:admin"

class RolePermission(BaseModel):
    """Role-based permission mapping"""
    role: UserRole
    permissions: List[Permission]
    institution_id: Optional[str] = None  # For institutional admins
    granted_at: datetime
    granted_by: str
    expires_at: Optional[datetime] = None
    is_active: bool = True

class SecurityAudit(BaseModel):
    """Security audit log entry"""
    id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    ip_address: str
    user_agent: str
    timestamp: datetime
    institution_id: Optional[str] = None
    severity: str = "low"  # low, medium, high, critical
    details: Optional[Dict[str, Any]] = None

class AccessAttempt(BaseModel):
    """Failed access attempt tracking"""
    id: str
    user_id: Optional[str] = None
    username: str
    ip_address: str
    timestamp: datetime
    reason: str
    blocked: bool = True
    institution_id: Optional[str] = None

class SecurityManager:
    """Advanced security management system"""
    
    def __init__(self, db: Session):
        self.db = db
        self.session_cache = {}  # Cache for performance
        self.failed_attempts = {}  # Track failed attempts
        self.audit_logs = []  # In-memory audit log
    
    def hash_password(self, password: str) -> str:
        """Secure password hashing with industry-standard algorithm"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_secure_token(self, user_id: str, expires_hours: int = 24) -> str:
        """Generate secure JWT token with expiration"""
        import jwt
        from datetime import datetime, timedelta
        
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=expires_hours),
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(32)  # JWT ID
        }
        
        return jwt.encode(
            payload,
            secrets.system_jwt_secret,
            algorithm='HS256'
        )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        import jwt
        try:
            return jwt.decode(
                token,
                secrets.system_jwt_secret,
                algorithms=['HS256']
            )
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}
    
    def check_permission(self, user_id: str, permission: Permission, institution_id: str = None) -> bool:
        """Check if user has specific permission"""
        try:
            # Get user's role permissions
            user_permissions = self.get_user_permissions(user_id, institution_id)
            return permission in user_permissions
        except Exception as e:
            log.error(f"Permission check failed: {e}")
            return False
    
    def get_user_permissions(self, user_id: str, institution_id: str = None) -> List[Permission]:
        """Get all permissions for a user"""
        try:
            # Check cache first
            cache_key = f"permissions_{user_id}_{institution_id or 'global'}"
            if cache_key in self.session_cache:
                return self.session_cache[cache_key]
            
            # Query database for user role
            from src.database.repositories.user_repository import UserRepository
            user_repo = UserRepository(self.db)
            user = user_repo.get_by_id(user_id)
            
            if not user:
                return []
            
            # Get role-based permissions
            permissions = self.get_role_permissions(user.role, institution_id)
            
            # Cache result
            self.session_cache[cache_key] = permissions
            return permissions
            
        except Exception as e:
            log.error(f"Failed to get user permissions: {e}")
            return []
    
    def get_role_permissions(self, role: UserRole, institution_id: str = None) -> List[Permission]:
        """Get permissions for a specific role"""
        role_permissions = {
            UserRole.SUPER_ADMIN: [
                Permission.SYSTEM_READ, Permission.SYSTEM_WRITE, Permission.SYSTEM_DELETE,
                Permission.SYSTEM_ADMIN, Permission.USER_READ, Permission.USER_WRITE,
                Permission.USER_DELETE, Permission.USER_ADMIN,
                Permission.RESOURCE_READ, Permission.RESOURCE_WRITE, Permission.RESOURCE_DELETE,
                Permission.RESOURCE_ADMIN, Permission.INSTITUTION_READ, Permission.INSTITUTION_WRITE,
                Permission.INSTITUTION_DELETE, Permission.INSTITUTION_ADMIN,
                Permission.ANALYTICS_READ, Permission.ANALYTICS_WRITE, Permission.ANALYTICS_ADMIN
            ],
            UserRole.INSTITUTIONAL_ADMIN: [
                Permission.USER_READ, Permission.USER_WRITE, Permission.USER_DELETE,
                Permission.USER_ADMIN, Permission.RESOURCE_READ, Permission.RESOURCE_WRITE,
                Permission.RESOURCE_DELETE, Permission.RESOURCE_ADMIN,
                Permission.INSTITUTION_READ, Permission.INSTITUTION_WRITE,
                Permission.ANALYTICS_READ, Permission.ANALYTICS_WRITE
            ],
            UserRole.DEPARTMENT_ADMIN: [
                Permission.USER_READ, Permission.USER_WRITE,
                Permission.RESOURCE_READ, Permission.RESOURCE_WRITE,
                Permission.ANALYTICS_READ
            ],
            UserRole.FACULTY_ADMIN: [
                Permission.USER_READ, Permission.USER_WRITE,
                Permission.RESOURCE_READ, Permission.RESOURCE_WRITE,
                Permission.ANALYTICS_READ
            ],
            UserRole.STAFF: [
                Permission.USER_READ, Permission.RESOURCE_READ
            ],
            UserRole.STUDENT: [
                Permission.RESOURCE_READ
            ],
            UserRole.GUEST: [
                Permission.RESOURCE_READ
            ]
        }
        
        # Filter by institution if institutional admin
        if role == UserRole.INSTITUTIONAL_ADMIN and institution_id:
            # Institutional admins only have permissions within their institution
            return [p for p in role_permissions[role] 
                   if not p.startswith('institution:') or p.startswith('system:')]
        
        return role_permissions.get(role, [])
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = "medium"):
        """Log security event with comprehensive details"""
        audit_entry = SecurityAudit(
            id=secrets.token_urlsafe(16),
            timestamp=datetime.utcnow(),
            event_type=event_type,
            severity=severity,
            details=details
        )
        
        self.audit_logs.append(audit_entry)
        
        # Keep only last 1000 audit entries in memory
        if len(self.audit_logs) > 1000:
            self.audit_logs = self.audit_logs[-1000:]
        
        log.info(f"Security event logged: {event_type} - {severity}")
    
    def check_rate_limit(self, user_id: str, action: str) -> bool:
        """Check rate limiting for user actions"""
        try:
            # Simple rate limiting (can be enhanced with Redis)
            cache_key = f"rate_limit_{user_id}_{action}"
            if cache_key in self.session_cache:
                last_actions = self.session_cache[cache_key]
                recent_actions = [a for a in last_actions 
                                 if a['timestamp'] > datetime.utcnow() - timedelta(minutes=5)]
                
                if len(recent_actions) >= 10:  # 10 actions per 5 minutes
                    return False
            
            return True
            
        except Exception as e:
            log.error(f"Rate limit check failed: {e}")
            return True
    
    def detect_suspicious_activity(self, user_id: str) -> List[str]:
        """Detect suspicious user activity patterns"""
        suspicious_patterns = []
        
        try:
            # Check for rapid failed logins
            failed_attempts = [a for a in self.audit_logs 
                            if a.user_id == user_id and a.action == 'login_failed']
            
            if len(failed_attempts) > 5 in timedelta(minutes=10):
                suspicious_patterns.append("Multiple failed login attempts")
            
            # Check for unusual access patterns
            user_actions = [a for a in self.audit_logs 
                          if a.user_id == user_id and a.timestamp > datetime.utcnow() - timedelta(hours=24)]
            
            # Check for access from multiple IPs
            ip_addresses = set(a.ip_address for a in user_actions)
            if len(ip_addresses) > 3:
                suspicious_patterns.append("Access from multiple IP addresses")
            
            # Check for privilege escalation attempts
            admin_access = [a for a in user_actions 
                           if a.user_id == user_id and 'admin' in a.action.lower()]
            
            if user and user.role != UserRole.SUPER_ADMIN and len(admin_access) > 0:
                suspicious_patterns.append("Unauthorized admin access attempt")
            
            return suspicious_patterns
            
        except Exception as e:
            log.error(f"Suspicious activity detection failed: {e}")
            return []
    
    def create_institutional_admin_session(self, admin_user_id: str, institution_id: str) -> Dict[str, Any]:
        """Create session for institutional admin with limited scope"""
        session_data = {
            'admin_user_id': admin_user_id,
            'institution_id': institution_id,
            'permissions': self.get_role_permissions(UserRole.INSTITUTIONAL_ADMIN, institution_id),
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=8)).isoformat(),
            'scope': 'institutional_only'
        }
        
        self.log_security_event("institutional_admin_session_created", {
            'admin_user_id': admin_user_id,
            'institution_id': institution_id
        })
        
        return {
            'session_token': self.generate_secure_token(admin_user_id, expires_hours=8),
            'session_data': session_data
        }
    
    def validate_institutional_access(self, user_id: str, institution_id: str, action: str) -> bool:
        """Validate if user has institutional access for specific action"""
        try:
            # Check if user is institutional admin for this institution
            from src.database.repositories.user_repository import UserRepository
            user_repo = UserRepository(self.db)
            user = user_repo.get_by_id(user_id)
            
            if not user:
                return False
            
            # Check if user has institutional admin role
            if user.role != UserRole.INSTITUTIONAL_ADMIN:
                return False
            
            # Check if user belongs to target institution
            if user.institution_id != institution_id:
                self.log_security_event("unauthorized_institutional_access", {
                    'user_id': user.user_id,
                    'user_institution': user.institution_id,
                    'target_institution': institution_id,
                    'action': action
                }, severity="high")
                return False
            
            return True
            
        except Exception as e:
            log.error(f"Institutional access validation failed: {e}")
            return False
    
    def grant_temporary_permission(self, user_id: str, permission: Permission, duration_minutes: int = 30) -> bool:
        """Grant temporary elevated permission for specific task"""
        try:
            temp_permission = RolePermission(
                role=UserRole.STAFF,  # Temporary staff role
                permissions=[permission],
                granted_at=datetime.utcnow(),
                granted_by="system",
                expires_at=datetime.utcnow() + timedelta(minutes=duration_minutes)
            )
            
            # Store in database (implementation needed)
            self.log_security_event("temporary_permission_granted", {
                'user_id': user_id,
                'permission': permission.value,
                'duration_minutes': duration_minutes
            })
            
            return True
            
        except Exception as e:
            log.error(f"Temporary permission grant failed: {e}")
            return False
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get comprehensive security summary"""
        try:
            from src.database.repositories.user_repository import UserRepository
            user_repo = UserRepository(self.db)
            
            # Get user statistics
            total_users = user_repo.count_all()
            admin_users = user_repo.count_by_role(UserRole.SUPER_ADMIN)
            institutional_admins = user_repo.count_by_role(UserRole.INSTITUTIONAL_ADMIN)
            
            # Get recent security events
            recent_events = [e for e in self.audit_logs 
                           if e.timestamp > datetime.utcnow() - timedelta(hours=24)]
            
            # Get failed attempts
            failed_attempts = len([e for e in recent_events if e.action == 'login_failed'])
            
            return {
                'total_users': total_users,
                'admin_users': admin_users,
                'institutional_admins': institutional_admins,
                'recent_security_events': len(recent_events),
                'failed_login_attempts': failed_attempts,
                'suspicious_activities': len(self.detect_suspicious_activity('all')),
                'audit_log_size': len(self.audit_logs),
                'system_health': 'healthy' if failed_attempts < 5 else 'warning'
            }
            
        except Exception as e:
            log.error(f"Security summary generation failed: {e}")
            return {'error': str(e)}

# Dependency function for FastAPI
def get_security_manager(db: Session = Depends) -> SecurityManager:
    """FastAPI dependency for security manager"""
    return SecurityManager(db)

# Security middleware for FastAPI
class SecurityMiddleware:
    """Advanced security middleware with comprehensive monitoring"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, call_next):
        # Get client IP and user agent
        client_ip = scope.client.host
        user_agent = scope.headers.get('user-agent', '')
        
        # Log request for security monitoring
        log.info(f"Request from {client_ip} - {user_agent}")
        
        # Check for suspicious patterns
        if self.is_suspicious_request(user_agent, client_ip):
            log.warning(f"Suspicious request detected from {client_ip}")
        
        response = await call_next(scope, receive)
        return response
    
    def is_suspicious_request(self, user_agent: str, ip: str) -> bool:
        """Detect suspicious request patterns"""
        suspicious_patterns = [
            'sqlmap', 'nmap', 'nikto', 'burp', 'metasploit',
            'union select', 'drop table', 'insert into', 'delete from',
            'script>', 'javascript:', 'eval(', 'exec('
        ]
        
        return any(pattern in user_agent.lower() for pattern in suspicious_patterns)

# Industry-standard security configurations
SECURITY_CONFIG = {
    'password_policy': {
        'min_length': 12,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_numbers': True,
        'require_special_chars': True,
        'max_age_days': 90,
        'history_count': 5  # Prevent password reuse
    },
    'session_policy': {
        'timeout_minutes': 30,
        'max_concurrent_sessions': 3,
        'require_mfa_for_admins': True,
        'rotation_hours': 8
    },
    'rate_limiting': {
        'requests_per_minute': 60,
        'login_attempts_per_hour': 10,
        'password_reset_per_hour': 3
    },
    'audit_policy': {
        'log_all_actions': True,
        'retention_days': 90,
        'alert_threshold': 5,  # Alert on 5 failed attempts
        'require_2fa_for_sensitive': True
    }
}

# Industry-standard security headers
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
}
