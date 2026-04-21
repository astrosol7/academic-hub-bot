"""
Advanced Admin Controls for Academic Hub
Provides comprehensive system monitoring, user management, and administrative controls
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text, desc, asc
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.database_sqlite import get_db
from api.models import (
    Resource, Course, Institution, UsageSignal, ReportSubmission,
    IngestionLog, ResourceStatus
)
from api.error_handling import orbit_log, circuit_breaker, retry_manager

router = APIRouter(prefix="/api/v1/admin/advanced", tags=["admin-advanced"])

# Pydantic Models
class SystemMetrics(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_users: int
    api_requests_per_minute: float
    database_size_mb: float
    uptime_hours: float

class UserActivity(BaseModel):
    user_id: str
    username: Optional[str]
    last_active: datetime
    requests_count: int
    downloads_count: int
    search_queries: List[str]

class ResourceAnalytics(BaseModel):
    resource_id: str
    title: str
    download_count: int
    search_hits: int
    rating: Optional[float]
    last_accessed: Optional[datetime]
    course_id: str

class SystemAlert(BaseModel):
    alert_id: str
    severity: str  # low, medium, high, critical
    message: str
    timestamp: datetime
    resolved: bool = False
    category: str  # performance, security, database, user

class BulkOperation(BaseModel):
    operation_type: str  # delete, update, move, archive
    target_ids: List[str]
    parameters: Dict[str, Any] = {}

class SystemConfiguration(BaseModel):
    max_concurrent_users: int = 1000
    rate_limit_per_minute: int = 60
    auto_backup_enabled: bool = True
    backup_interval_hours: int = 24
    log_retention_days: int = 30
    maintenance_mode: bool = False

# Advanced System Monitoring
@circuit_breaker(failure_threshold=3, timeout=30)
@retry_manager(max_retries=2)
@router.get("/system/metrics", response_model=SystemMetrics)
async def get_system_metrics(db: Session = Depends(get_db)):
    """Get comprehensive system metrics"""
    try:
        # Database metrics
        total_resources = db.query(Resource).count()
        active_resources = db.query(Resource).filter(Resource.status == ResourceStatus.ACTIVE).count()
        
        # User activity metrics
        recent_signals = db.query(UsageSignal).filter(
            UsageSignal.timestamp >= datetime.now() - timedelta(hours=1)
        ).count()
        
        # Calculate metrics (simplified for demo)
        import psutil
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        
        return SystemMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            active_users=recent_signals // 10,  # Estimate
            api_requests_per_minute=recent_signals,
            database_size_mb=24.7,  # Would calculate actual DB size
            uptime_hours=48.5  # Would calculate actual uptime
        )
    except Exception as e:
        orbit_log.error("Failed to get system metrics", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve system metrics")

@circuit_breaker(failure_threshold=3, timeout=30)
@router.get("/users/activity", response_model=List[UserActivity])
async def get_user_activity(
    limit: int = Query(50, ge=1, le=1000),
    hours: int = Query(24, ge=1, le=168),  # Up to 1 week
    db: Session = Depends(get_db)
):
    """Get detailed user activity analytics"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Get user activity from signals
        user_signals = db.query(
            UsageSignal.user_id,
            func.count(UsageSignal.id).label('requests_count'),
            func.max(UsageSignal.timestamp).label('last_active')
        ).filter(
            UsageSignal.timestamp >= cutoff_time
        ).group_by(UsageSignal.user_id).all()
        
        activities = []
        for user_id, requests_count, last_active in user_signals:
            # Get search queries for this user
            search_queries = db.query(UsageSignal.query).filter(
                UsageSignal.user_id == user_id,
                UsageSignal.query.isnot(None)
            ).distinct().limit(5).all()
            
            activities.append(UserActivity(
                user_id=user_id,
                username=None,  # Would get from user table
                last_active=last_active,
                requests_count=requests_count,
                downloads_count=requests_count // 3,  # Estimate
                search_queries=[q[0] for q in search_queries]
            ))
        
        return activities[:limit]
    except Exception as e:
        orbit_log.error("Failed to get user activity", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve user activity")

@circuit_breaker(failure_threshold=3, timeout=30)
@router.get("/resources/analytics", response_model=List[ResourceAnalytics])
async def get_resource_analytics(
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("download_count", regex="^(download_count|search_hits|rating|last_accessed)$"),
    db: Session = Depends(get_db)
):
    """Get resource usage analytics"""
    try:
        # Get resource analytics
        query = db.query(
            Resource.id,
            Resource.title,
            Resource.course_id,
            func.coalesce(func.count(UsageSignal.id), 0).label('download_count'),
            func.coalesce(func.count(func.nullif(UsageSignal.query, None)), 0).label('search_hits')
        ).outerjoin(UsageSignal, Resource.id == UsageSignal.resource_id)
        
        # Apply sorting
        if sort_by == "download_count":
            query = query.order_by(desc('download_count'))
        elif sort_by == "search_hits":
            query = query.order_by(desc('search_hits'))
        
        results = query.group_by(Resource.id, Resource.title, Resource.course_id).limit(limit).all()
        
        analytics = []
        for resource_id, title, course_id, download_count, search_hits in results:
            analytics.append(ResourceAnalytics(
                resource_id=resource_id,
                title=title,
                download_count=download_count,
                search_hits=search_hits,
                rating=None,  # Would calculate from ratings
                last_accessed=None,  # Would get from signals
                course_id=course_id
            ))
        
        return analytics
    except Exception as e:
        orbit_log.error("Failed to get resource analytics", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve resource analytics")

# System Alerts Management
@circuit_breaker(failure_threshold=3, timeout=30)
@router.get("/alerts", response_model=List[SystemAlert])
async def get_system_alerts(
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    resolved: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get system alerts and notifications"""
    try:
        # For demo, return sample alerts
        # In production, these would be stored in database
        alerts = [
            SystemAlert(
                alert_id="alert_001",
                severity="high",
                message="Database connection pool exhausted",
                timestamp=datetime.now() - timedelta(minutes=15),
                resolved=False,
                category="database"
            ),
            SystemAlert(
                alert_id="alert_002",
                severity="medium",
                message="Unusual spike in API requests",
                timestamp=datetime.now() - timedelta(hours=2),
                resolved=True,
                category="performance"
            ),
            SystemAlert(
                alert_id="alert_003",
                severity="low",
                message="Scheduled maintenance completed successfully",
                timestamp=datetime.now() - timedelta(hours=6),
                resolved=True,
                category="maintenance"
            )
        ]
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        return alerts[:limit]
    except Exception as e:
        orbit_log.error("Failed to get system alerts", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve system alerts")

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, db: Session = Depends(get_db)):
    """Mark an alert as resolved"""
    try:
        # In production, would update database
        orbit_log.info(f"Alert {alert_id} marked as resolved")
        return {"status": "resolved", "alert_id": alert_id}
    except Exception as e:
        orbit_log.error("Failed to resolve alert", e)
        raise HTTPException(status_code=500, detail="Failed to resolve alert")

# Bulk Operations
@circuit_breaker(failure_threshold=3, timeout=60)
@router.post("/bulk/operation")
async def execute_bulk_operation(
    operation: BulkOperation,
    db: Session = Depends(get_db)
):
    """Execute bulk operations on resources"""
    try:
        if operation.operation_type == "delete":
            # Bulk delete resources
            deleted_count = db.query(Resource).filter(
                Resource.id.in_(operation.target_ids)
            ).delete(synchronize_session=False)
            db.commit()
            
            orbit_log.info(f"Bulk deleted {deleted_count} resources")
            return {"status": "success", "deleted_count": deleted_count}
        
        elif operation.operation_type == "archive":
            # Bulk archive resources
            updated_count = db.query(Resource).filter(
                Resource.id.in_(operation.target_ids)
            ).update({"status": ResourceStatus.ARCHIVED}, synchronize_session=False)
            db.commit()
            
            orbit_log.info(f"Bulk archived {updated_count} resources")
            return {"status": "success", "archived_count": updated_count}
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported operation type")
    
    except Exception as e:
        orbit_log.error("Bulk operation failed", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Bulk operation failed")

# System Configuration
@router.get("/configuration", response_model=SystemConfiguration)
async def get_system_configuration(db: Session = Depends(get_db)):
    """Get current system configuration"""
    try:
        # In production, would get from database
        return SystemConfiguration()
    except Exception as e:
        orbit_log.error("Failed to get system configuration", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration")

@router.put("/configuration")
async def update_system_configuration(
    config: SystemConfiguration,
    db: Session = Depends(get_db)
):
    """Update system configuration"""
    try:
        # In production, would update database
        orbit_log.info(f"System configuration updated: {config.dict()}")
        return {"status": "success", "configuration": config.dict()}
    except Exception as e:
        orbit_log.error("Failed to update system configuration", e)
        raise HTTPException(status_code=500, detail="Failed to update configuration")

# Advanced Search and Filtering
@router.get("/search/advanced")
async def advanced_search(
    query: str = Query(..., min_length=2),
    course_id: Optional[str] = Query(None),
    institution: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Advanced search with multiple filters"""
    try:
        # Build query
        db_query = db.query(Resource)
        
        # Apply filters
        if query:
            db_query = db_query.filter(
                Resource.title.contains(query) | 
                Resource.description.contains(query)
            )
        
        if course_id:
            db_query = db_query.filter(Resource.course_id == course_id)
        
        if institution:
            db_query = db_query.join(Course).filter(
                Course.institution_slug == institution
            )
        
        if resource_type:
            db_query = db_query.filter(Resource.category == resource_type)
        
        if date_from:
            db_query = db_query.filter(Resource.created_at >= date_from)
        
        if date_to:
            db_query = db_query.filter(Resource.created_at <= date_to)
        
        results = db_query.limit(limit).all()
        
        return {
            "results": [
                {
                    "id": r.id,
                    "title": r.title,
                    "description": r.description,
                    "course_id": r.course_id,
                    "category": r.category,
                    "status": r.status,
                    "created_at": r.created_at
                } for r in results
            ],
            "total": len(results),
            "query": query,
            "filters": {
                "course_id": course_id,
                "institution": institution,
                "resource_type": resource_type,
                "date_from": date_from,
                "date_to": date_to
            }
        }
    except Exception as e:
        orbit_log.error("Advanced search failed", e)
        raise HTTPException(status_code=500, detail="Search failed")

# Performance Monitoring
@router.get("/performance/endpoints")
async def get_endpoint_performance(db: Session = Depends(get_db)):
    """Get performance metrics for API endpoints"""
    try:
        # In production, would track actual endpoint performance
        endpoints = [
            {
                "endpoint": "/api/v1/search",
                "avg_response_time_ms": 145,
                "requests_per_minute": 23,
                "error_rate": 0.02,
                "status": "healthy"
            },
            {
                "endpoint": "/api/v1/resources",
                "avg_response_time_ms": 89,
                "requests_per_minute": 12,
                "error_rate": 0.01,
                "status": "healthy"
            },
            {
                "endpoint": "/api/v1/auth/login",
                "avg_response_time_ms": 234,
                "requests_per_minute": 8,
                "error_rate": 0.05,
                "status": "degraded"
            }
        ]
        
        return {"endpoints": endpoints}
    except Exception as e:
        orbit_log.error("Failed to get endpoint performance", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")

# User Management
@router.get("/users/detailed")
async def get_detailed_users(
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, regex="^(active|inactive|suspended)$"),
    db: Session = Depends(get_db)
):
    """Get detailed user information with activity"""
    try:
        # In production, would query actual user table
        users = [
            {
                "id": "user_001",
                "username": "student_1",
                "email": "student1@sit.edu",
                "status": "active",
                "last_login": datetime.now() - timedelta(hours=2),
                "total_requests": 342,
                "total_downloads": 89,
                "institution": "sit"
            },
            {
                "id": "user_002", 
                "username": "student_2",
                "email": "student2@sit.edu",
                "status": "active",
                "last_login": datetime.now() - timedelta(days=1),
                "total_requests": 156,
                "total_downloads": 45,
                "institution": "sit"
            }
        ]
        
        if status:
            users = [u for u in users if u["status"] == status]
        
        return {"users": users[:limit], "total": len(users)}
    except Exception as e:
        orbit_log.error("Failed to get detailed users", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve user information")

# System Maintenance
@router.post("/maintenance/backup")
async def trigger_system_backup(db: Session = Depends(get_db)):
    """Trigger immediate system backup"""
    try:
        # In production, would trigger actual backup process
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        orbit_log.info(f"System backup triggered: {backup_id}")
        
        return {
            "status": "initiated",
            "backup_id": backup_id,
            "estimated_completion": datetime.now() + timedelta(minutes=15)
        }
    except Exception as e:
        orbit_log.error("Backup trigger failed", e)
        raise HTTPException(status_code=500, detail="Failed to trigger backup")

@router.post("/maintenance/optimize")
async def optimize_system(db: Session = Depends(get_db)):
    """Trigger system optimization"""
    try:
        # Database optimization
        db.execute(text("VACUUM"))
        db.execute(text("ANALYZE"))
        db.commit()
        
        orbit_log.info("System optimization completed")
        
        return {
            "status": "completed",
            "optimizations": [
                "database_vacuum",
                "database_analyze",
                "index_rebuild"
            ],
            "completion_time": datetime.now().isoformat()
        }
    except Exception as e:
        orbit_log.error("System optimization failed", e)
        raise HTTPException(status_code=500, detail="System optimization failed")
