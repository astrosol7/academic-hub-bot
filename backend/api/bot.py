import os
import re
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.api.database import get_db
from backend.api.models import Institution, Student, TelegramLink


router = APIRouter()
audit_log = logging.getLogger("security.audit")
TELEGRAM_ID_RE = re.compile(r"^\d{5,20}$")
SCHOOL_ID_RE = re.compile(r"^[A-Za-z0-9\-]{4,64}$")


def _require_bot_key(x_orbit_bot_key: str | None) -> None:
    expected = (os.getenv("ORBIT_BOT_API_KEY") or "").strip()
    if not expected:
        # fail closed
        raise HTTPException(status_code=500, detail="Server misconfigured (missing ORBIT_BOT_API_KEY)")
    if not x_orbit_bot_key or x_orbit_bot_key.strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class LinkStatusResponse(BaseModel):
    is_linked: bool
    is_conflicted: bool = False
    student_id: Optional[str] = None
    student_name: Optional[str] = None


class BindRequest(BaseModel):
    institution_slug: str
    telegram_id: str
    school_id: str


def _validate_ids(telegram_id: str, school_id: str | None = None) -> None:
    if not TELEGRAM_ID_RE.fullmatch(telegram_id):
        raise HTTPException(status_code=400, detail="Invalid telegram_id format")
    if school_id is not None and not SCHOOL_ID_RE.fullmatch(school_id):
        raise HTTPException(status_code=400, detail="Invalid school_id format")


@router.get("/api/v1/bot/link-status", response_model=LinkStatusResponse)
def bot_link_status(
    institution_slug: str,
    telegram_id: str,
    db: Session = Depends(get_db),
    x_orbit_bot_key: str | None = Header(default=None),
):
    _require_bot_key(x_orbit_bot_key)
    _validate_ids(telegram_id)

    inst = db.query(Institution).filter(Institution.slug == institution_slug).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    link = (
        db.query(TelegramLink)
        .filter(TelegramLink.telegram_id == telegram_id, TelegramLink.institution_id == inst.id)
        .first()
    )
    if not link or not link.student_id:
        return LinkStatusResponse(is_linked=False, is_conflicted=bool(link and link.is_conflicted))

    student = db.query(Student).filter(Student.id == link.student_id).first()
    return LinkStatusResponse(
        is_linked=True,
        is_conflicted=bool(link.is_conflicted),
        student_id=link.student_id,
        student_name=student.full_name if student else None,
    )


@router.post("/api/v1/bot/bind", response_model=LinkStatusResponse)
def bot_bind(
    payload: BindRequest,
    db: Session = Depends(get_db),
    x_orbit_bot_key: str | None = Header(default=None),
):
    """
    Bind a Telegram numeric ID to an institution student ID.
    Conflict policy: if school ID already linked to a different telegram account, we lock conflict.
    """
    _require_bot_key(x_orbit_bot_key)

    inst = db.query(Institution).filter(Institution.slug == payload.institution_slug).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    school_id = payload.school_id.strip()
    telegram_id = payload.telegram_id.strip()
    if not school_id or not telegram_id:
        raise HTTPException(status_code=400, detail="Missing school_id or telegram_id")
    _validate_ids(telegram_id, school_id)

    student = db.query(Student).filter(Student.id == school_id, Student.institution_id == inst.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student ID not found")

    # Load/create link row for this telegram ID
    link = (
        db.query(TelegramLink)
        .filter(TelegramLink.telegram_id == telegram_id, TelegramLink.institution_id == inst.id)
        .first()
    )
    if not link:
        link = TelegramLink(telegram_id=telegram_id, institution_id=inst.id, is_conflicted=False)
        db.add(link)
        db.flush()

    # If already linked, return deterministic status
    if link.student_id == school_id and not link.is_conflicted:
        return LinkStatusResponse(is_linked=True, is_conflicted=False, student_id=student.id, student_name=student.full_name)

    # If this telegram is linked to someone else, block unless admin unbinds
    if link.student_id and link.student_id != school_id:
        link.is_conflicted = True
        db.commit()
        audit_log.warning("event=bind_conflict_telegram_rebind telegram_id=%s institution=%s", telegram_id, payload.institution_slug)
        raise HTTPException(status_code=409, detail="This Telegram account is already linked to a different School ID.")

    # Check if the school_id is already linked to another telegram in this institution
    existing_school_link = (
        db.query(TelegramLink)
        .filter(TelegramLink.institution_id == inst.id, TelegramLink.student_id == school_id)
        .first()
    )
    if existing_school_link and existing_school_link.telegram_id != telegram_id:
        existing_school_link.is_conflicted = True
        link.is_conflicted = True
        db.commit()
        audit_log.warning("event=bind_conflict_school_claim school_id=%s institution=%s", school_id, payload.institution_slug)
        raise HTTPException(status_code=409, detail="School ID already linked to another Telegram account (conflict locked).")

    # Bind now
    link.student_id = school_id
    link.is_conflicted = False
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Binding conflict. Try again or contact admin.")

    audit_log.info("event=bind_success telegram_id=%s school_id=%s institution=%s", telegram_id, school_id, payload.institution_slug)
    return LinkStatusResponse(is_linked=True, is_conflicted=False, student_id=student.id, student_name=student.full_name)

