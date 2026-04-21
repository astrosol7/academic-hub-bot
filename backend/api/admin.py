from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, desc, text
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.auth import get_current_admin
from backend.api.utils import resolve_limit
from backend.api.models import (
    AdminUser,
    AdminRole,
    Institution,
    Student,
    TelegramLink,
    ReportSubmission,
    ReportStatus,
    UsageSignal,
    SyncError,
    QuarantineStatus,
    Resource,
    ResourceStatus,
)


router = APIRouter()


def _institution_scope(db: Session, user: AdminUser, institution_slug: str | None) -> Institution:
    if user.role == AdminRole.SUPER_ADMIN:
        if not institution_slug:
            raise HTTPException(status_code=400, detail="institution_slug required for super admin")
        inst = db.query(Institution).filter(Institution.slug == institution_slug).first()
        if not inst:
            raise HTTPException(status_code=404, detail="Institution not found")
        return inst

    if not user.institution_id:
        raise HTTPException(status_code=403, detail="Admin user not scoped to an institution")
    inst = db.query(Institution).filter(Institution.id == user.institution_id).first()
    if not inst:
        raise HTTPException(status_code=403, detail="Institution scope invalid")
    return inst


class OverviewResponse(BaseModel):
    institution_slug: str
    students_total: int
    links_total: int
    conflicts_total: int
    incidents_open: int
    incidents_in_progress: int
    incidents_resolved: int
    quarantine_pending: int


@router.get("/api/v1/admin/overview", response_model=OverviewResponse)
def admin_overview(
    institution_slug: Optional[str] = None,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin),
):
    inst = _institution_scope(db, user, institution_slug)

    students_total = db.query(func.count(Student.id)).filter(Student.institution_id == inst.id).scalar() or 0
    links_total = db.query(func.count(TelegramLink.telegram_id)).filter(TelegramLink.institution_id == inst.id).scalar() or 0
    conflicts_total = (
        db.query(func.count(TelegramLink.telegram_id))
        .filter(TelegramLink.institution_id == inst.id, TelegramLink.is_conflicted.is_(True))
        .scalar()
        or 0
    )
    incidents_open = (
        db.query(func.count(ReportSubmission.id))
        .filter(ReportSubmission.status == ReportStatus.OPEN)
        .scalar()
        or 0
    )
    incidents_in_progress = (
        db.query(func.count(ReportSubmission.id))
        .filter(ReportSubmission.status == ReportStatus.IN_PROGRESS)
        .scalar()
        or 0
    )
    incidents_resolved = (
        db.query(func.count(ReportSubmission.id))
        .filter(ReportSubmission.status == ReportStatus.RESOLVED)
        .scalar()
        or 0
    )
    quarantine_pending = (
        db.query(func.count(SyncError.id))
        .filter(SyncError.status == QuarantineStatus.PENDING)
        .scalar()
        or 0
    )

    return OverviewResponse(
        institution_slug=inst.slug,
        students_total=int(students_total),
        links_total=int(links_total),
        conflicts_total=int(conflicts_total),
        incidents_open=int(incidents_open),
        incidents_in_progress=int(incidents_in_progress),
        incidents_resolved=int(incidents_resolved),
        quarantine_pending=int(quarantine_pending),
    )


class IncidentItem(BaseModel):
    id: str
    telegram_id: str
    category: str
    description: str
    course_id: Optional[str] = None
    status: ReportStatus
    created_at: datetime
    updated_at: datetime
    resolution_note: Optional[str] = None


@router.get("/api/v1/admin/incidents", response_model=list[IncidentItem])
def list_incidents(
    status: Optional[ReportStatus] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin),
):
    # incidents are global v1; later can be institution-scoped by joining telegram_links
    _ = user
    q = db.query(ReportSubmission)
    if status:
        q = q.filter(ReportSubmission.status == status)
    
    limit = resolve_limit(limit, role="admin")
    items = q.order_by(desc(ReportSubmission.created_at)).offset(offset).limit(limit).all()
    return [
        IncidentItem(
            id=str(i.id),
            telegram_id=str(i.telegram_id),
            category=i.category,
            description=i.description,
            course_id=i.course_id,
            status=i.status,
            created_at=i.created_at,
            updated_at=i.updated_at,
            resolution_note=i.resolution_note,
        )
        for i in items
    ]


class IncidentUpdate(BaseModel):
    status: ReportStatus
    resolution_note: Optional[str] = None


@router.patch("/api/v1/admin/incidents/{incident_id}", response_model=IncidentItem)
def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin),
):
    _ = user
    inc = db.query(ReportSubmission).filter(ReportSubmission.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc.status = payload.status
    inc.resolution_note = payload.resolution_note
    db.commit()
    db.refresh(inc)
    return IncidentItem(
        id=str(inc.id),
        telegram_id=str(inc.telegram_id),
        category=inc.category,
        description=inc.description,
        course_id=inc.course_id,
        status=inc.status,
        created_at=inc.created_at,
        updated_at=inc.updated_at,
        resolution_note=inc.resolution_note,
    )


class StudentRow(BaseModel):
    student_id: str
    full_name: str
    telegram_id: Optional[str] = None
    is_conflicted: bool = False


@router.get("/api/v1/admin/students", response_model=list[StudentRow])
def list_students(
    q: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    institution_slug: Optional[str] = None,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin),
):
    inst = _institution_scope(db, user, institution_slug)
    query = db.query(Student).filter(Student.institution_id == inst.id)
    if q:
        needle = q.strip()
        if needle:
            query = query.filter(
                (Student.id.ilike(f"%{needle}%")) | (Student.full_name.ilike(f"%{needle}%"))
            )
    
    limit = resolve_limit(limit, role="admin")
    students = query.order_by(Student.id.asc()).offset(offset).limit(limit).all()

    # fetch links for these students
    ids = [s.id for s in students]
    links = (
        db.query(TelegramLink)
        .filter(TelegramLink.institution_id == inst.id, TelegramLink.student_id.in_(ids))
        .all()
    )
    link_map = {l.student_id: l for l in links if l.student_id}

    return [
        StudentRow(
            student_id=s.id,
            full_name=s.full_name,
            telegram_id=(link_map.get(s.id).telegram_id if link_map.get(s.id) else None),
            is_conflicted=bool(link_map.get(s.id).is_conflicted) if link_map.get(s.id) else False,
        )
        for s in students
    ]


class UnbindRequest(BaseModel):
    institution_slug: Optional[str] = None
    telegram_id: Optional[str] = None
    school_id: Optional[str] = None
    clear_conflict: bool = True


@router.post("/api/v1/admin/links/unbind")
def admin_unbind(
    payload: UnbindRequest,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin),
):
    inst = _institution_scope(db, user, payload.institution_slug)
    if not payload.telegram_id and not payload.school_id:
        raise HTTPException(status_code=400, detail="telegram_id or school_id required")

    q = db.query(TelegramLink).filter(TelegramLink.institution_id == inst.id)
    if payload.telegram_id:
        q = q.filter(TelegramLink.telegram_id == payload.telegram_id)
    if payload.school_id:
        q = q.filter(TelegramLink.student_id == payload.school_id)

    links = q.all()
    if not links:
        raise HTTPException(status_code=404, detail="Link not found")

    for link in links:
        link.student_id = None
        if payload.clear_conflict:
            link.is_conflicted = False
    db.commit()
    return {"status": "ok", "count": len(links)}


class TelemetryRow(BaseModel):
    query: str
    count: int


@router.get("/api/v1/admin/telemetry/top-queries", response_model=list[TelemetryRow])
def telemetry_top_queries(
    limit: int = 20,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin),
):
    _ = user
    # Postgres JSONB aggregation via raw SQL for speed.
    sql = text(
        """
        SELECT
          COALESCE(metadata_blob->>'query', '') AS query,
          COUNT(*)::int AS count
        FROM usage_signals
        WHERE action = 'search'
          AND metadata_blob ? 'query'
          AND COALESCE(metadata_blob->>'query', '') <> ''
        GROUP BY COALESCE(metadata_blob->>'query', '')
        ORDER BY COUNT(*) DESC
        LIMIT :limit
        """
    )
    rows = db.execute(sql, {"limit": min(limit, 100)}).fetchall()
    return [TelemetryRow(query=r[0], count=int(r[1])) for r in rows]


@router.get("/api/v1/admin/telemetry/failed-queries", response_model=list[TelemetryRow])
def telemetry_failed_queries(
    limit: int = 20,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin),
):
    _ = user
    sql = text(
        """
        SELECT
          COALESCE(metadata_blob->>'query', '') AS query,
          COUNT(*)::int AS count
        FROM usage_signals
        WHERE action = 'search'
          AND metadata_blob ? 'query'
          AND COALESCE(metadata_blob->>'matched', 'true') = 'false'
          AND COALESCE(metadata_blob->>'query', '') <> ''
        GROUP BY COALESCE(metadata_blob->>'query', '')
        ORDER BY COUNT(*) DESC
        LIMIT :limit
        """
    )
    rows = db.execute(sql, {"limit": min(limit, 100)}).fetchall()
    return [TelemetryRow(query=r[0], count=int(r[1])) for r in rows]


class QuarantineItem(BaseModel):
    id: str
    file_path: str
    reason: str
    severity: Any
    status: QuarantineStatus
    detected_at: datetime


@router.get("/api/v1/admin/quarantine", response_model=list[QuarantineItem])
def list_quarantine(
    status: QuarantineStatus = QuarantineStatus.PENDING,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin),
):
    _ = user
    items = (
        db.query(SyncError)
        .filter(SyncError.status == status)
        .order_by(desc(SyncError.detected_at))
        .offset(offset)
        .limit(resolve_limit(limit, role="admin"))
        .all()
    )
    return [
        QuarantineItem(
            id=str(i.id),
            file_path=i.file_path,
            reason=i.reason,
            severity=i.severity,
            status=i.status,
            detected_at=i.detected_at,
        )
        for i in items
    ]


class QuarantineUpdate(BaseModel):
    status: QuarantineStatus


@router.patch("/api/v1/admin/quarantine/{error_id}")
def update_quarantine(
    error_id: str,
    payload: QuarantineUpdate,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin),
):
    _ = user
    err = db.query(SyncError).filter(SyncError.id == error_id).first()
    if not err:
        raise HTTPException(status_code=404, detail="Not found")
    err.status = payload.status
    db.commit()
    return {"status": "ok"}


class ResourceRow(BaseModel):
    id: str
    title: str
    course_id: str
    category_slug: str
    status: ResourceStatus


@router.get("/api/v1/admin/resources", response_model=list[ResourceRow])
def list_resources(
    course_id: Optional[str] = None,
    status: Optional[ResourceStatus] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin),
):
    _ = user
    q = db.query(Resource)
    if course_id:
        q = q.filter(Resource.course_id == course_id)
    if status:
        q = q.filter(Resource.status == status)
    
    limit = resolve_limit(limit, role="admin")
    items = q.order_by(desc(Resource.created_at)).offset(offset).limit(limit).all()
    return [
        ResourceRow(
            id=str(r.id),
            title=r.title,
            course_id=r.course_id,
            category_slug=r.category_slug,
            status=r.status,
        )
        for r in items
    ]


class AdminRow(BaseModel):
    id: str
    username: str
    role: AdminRole
    institution_id: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None


@router.get("/api/v1/admin/admins", response_model=list[AdminRow])
def list_admins(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin),
):
    if user.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin required")
    
    limit = resolve_limit(limit, role="admin")
    admins = db.query(AdminUser).order_by(AdminUser.created_at.desc()).limit(limit).all()
    return [
        AdminRow(
            id=str(a.id),
            username=a.username,
            role=a.role,
            institution_id=str(a.institution_id) if a.institution_id else None,
            created_at=a.created_at,
            last_login=a.last_login,
        )
        for a in admins
    ]


class AdminCreate(BaseModel):
    username: str
    password: str
    role: AdminRole = AdminRole.ADMIN
    institution_slug: Optional[str] = None


@router.post("/api/v1/admin/admins", response_model=AdminRow)
def create_admin(
    payload: AdminCreate,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_admin),
):
    if user.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin required")
    if db.query(AdminUser).filter(AdminUser.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")

    from backend.api.auth import get_password_hash

    inst_id = None
    if payload.role != AdminRole.SUPER_ADMIN:
        if not payload.institution_slug:
            raise HTTPException(status_code=400, detail="institution_slug required for non-super admins")
        inst = db.query(Institution).filter(Institution.slug == payload.institution_slug).first()
        if not inst:
            raise HTTPException(status_code=404, detail="Institution not found")
        inst_id = inst.id

    admin = AdminUser(
        username=payload.username,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        institution_id=inst_id,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return AdminRow(
        id=str(admin.id),
        username=admin.username,
        role=admin.role,
        institution_id=str(admin.institution_id) if admin.institution_id else None,
        created_at=admin.created_at,
        last_login=admin.last_login,
    )
