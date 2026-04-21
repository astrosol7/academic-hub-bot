from __future__ import annotations

from datetime import datetime
from typing import Optional
import re
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy import func, desc, text
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Institution, TelegramLink, Question, Answer, Vote, QAStatus
from api.utils import resolve_limit


router = APIRouter()
audit_log = logging.getLogger("security.audit")
TELEGRAM_ID_RE = re.compile(r"^\d{5,20}$")


def _require_bot_key(x_orbit_bot_key: str | None) -> None:
    import os
    expected = (os.getenv("ORBIT_BOT_API_KEY") or "").strip()
    if not expected:
        raise HTTPException(status_code=500, detail="Server misconfigured (missing ORBIT_BOT_API_KEY)")
    if not x_orbit_bot_key or x_orbit_bot_key.strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _validate_telegram_id(value: str) -> None:
    if not TELEGRAM_ID_RE.fullmatch(value):
        raise HTTPException(status_code=400, detail="Invalid telegram_id format")


def _validate_uuid(value: str, field: str) -> None:
    try:
        uuid.UUID(str(value))
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid {field} format")


class QuestionCreate(BaseModel):
    institution_slug: str
    telegram_id: str
    course_id: Optional[str] = None
    title: str = Field(min_length=4, max_length=255)
    body: str = Field(min_length=4, max_length=5000)


class QuestionItem(BaseModel):
    id: str
    course_id: Optional[str] = None
    title: str
    body: str
    status: QAStatus
    score: int = 0
    answers_count: int = 0
    created_at: datetime


class AnswerCreate(BaseModel):
    institution_slug: str
    telegram_id: str
    question_id: str
    body: str = Field(min_length=2, max_length=8000)


class AnswerItem(BaseModel):
    id: str
    question_id: str
    body: str
    is_accepted: bool
    score: int = 0
    created_at: datetime


class VoteRequest(BaseModel):
    institution_slug: str
    telegram_id: str
    question_id: Optional[str] = None
    answer_id: Optional[str] = None
    value: int = Field(description="-1 or +1")


class QASearchHit(BaseModel):
    question_id: str
    title: str
    score: float


@router.post("/api/v1/qa/questions", response_model=QuestionItem)
def create_question(
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    x_orbit_bot_key: str | None = Header(default=None),
):
    _require_bot_key(x_orbit_bot_key)
    _validate_telegram_id(payload.telegram_id)
    inst = db.query(Institution).filter(Institution.slug == payload.institution_slug).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    # require verified telegram link
    link = db.query(TelegramLink).filter(TelegramLink.telegram_id == payload.telegram_id, TelegramLink.institution_id == inst.id).first()
    if not link or not link.student_id or link.is_conflicted:
        raise HTTPException(status_code=403, detail="User not verified")

    q = Question(
        institution_id=inst.id,
        author_telegram_id=payload.telegram_id,
        course_id=(payload.course_id.strip() if payload.course_id else None),
        title=payload.title.strip(),
        body=payload.body.strip(),
        status=QAStatus.OPEN,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    # keep tsvector fresh for ranked search
    db.execute(
        text("UPDATE questions SET search_text = to_tsvector('english', coalesce(title,'') || ' ' || coalesce(body,'')) WHERE id = :qid"),
        {"qid": str(q.id)},
    )
    db.commit()
    audit_log.info("event=qa_question_created telegram_id=%s institution=%s", payload.telegram_id, payload.institution_slug)
    return QuestionItem(
        id=str(q.id),
        course_id=q.course_id,
        title=q.title,
        body=q.body,
        status=q.status,
        score=0,
        answers_count=0,
        created_at=q.created_at,
    )


@router.get("/api/v1/qa/questions/{question_id}", response_model=QuestionItem)
def get_question(question_id: str, db: Session = Depends(get_db), x_orbit_bot_key: str | None = Header(default=None)):
    _require_bot_key(x_orbit_bot_key)
    _validate_uuid(question_id, "question_id")
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Not found")

    score = db.query(func.coalesce(func.sum(Vote.value), 0)).filter(Vote.question_id == q.id).scalar() or 0
    answers_count = db.query(func.count(Answer.id)).filter(Answer.question_id == q.id).scalar() or 0
    return QuestionItem(
        id=str(q.id),
        course_id=q.course_id,
        title=q.title,
        body=q.body,
        status=q.status,
        score=int(score),
        answers_count=int(answers_count),
        created_at=q.created_at,
    )


@router.get("/api/v1/qa/questions", response_model=list[QuestionItem])
def list_questions(
    institution_slug: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    x_orbit_bot_key: str | None = Header(default=None),
):
    _require_bot_key(x_orbit_bot_key)
    inst = db.query(Institution).filter(Institution.slug == institution_slug).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    limit = resolve_limit(limit, role="public")
    qs = (
        db.query(Question)
        .filter(Question.institution_id == inst.id)
        .order_by(desc(Question.created_at))
        .limit(limit)
        .all()
    )
    out: list[QuestionItem] = []
    for q in qs:
        score = db.query(func.coalesce(func.sum(Vote.value), 0)).filter(Vote.question_id == q.id).scalar() or 0
        answers_count = db.query(func.count(Answer.id)).filter(Answer.question_id == q.id).scalar() or 0
        out.append(
            QuestionItem(
                id=str(q.id),
                course_id=q.course_id,
                title=q.title,
                body=q.body,
                status=q.status,
                score=int(score),
                answers_count=int(answers_count),
                created_at=q.created_at,
            )
        )
    return out


@router.post("/api/v1/qa/answers", response_model=AnswerItem)
def create_answer(
    payload: AnswerCreate,
    db: Session = Depends(get_db),
    x_orbit_bot_key: str | None = Header(default=None),
):
    _require_bot_key(x_orbit_bot_key)
    _validate_telegram_id(payload.telegram_id)
    _validate_uuid(payload.question_id, "question_id")
    inst = db.query(Institution).filter(Institution.slug == payload.institution_slug).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    link = db.query(TelegramLink).filter(TelegramLink.telegram_id == payload.telegram_id, TelegramLink.institution_id == inst.id).first()
    if not link or not link.student_id or link.is_conflicted:
        raise HTTPException(status_code=403, detail="User not verified")

    q = db.query(Question).filter(Question.id == payload.question_id, Question.institution_id == inst.id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    a = Answer(
        question_id=q.id,
        institution_id=inst.id,
        author_telegram_id=payload.telegram_id,
        body=payload.body.strip(),
        is_accepted=False,
    )
    db.add(a)
    q.status = QAStatus.ANSWERED
    db.commit()
    db.refresh(a)
    db.execute(
        text("UPDATE answers SET search_text = to_tsvector('english', coalesce(body,'')) WHERE id = :aid"),
        {"aid": str(a.id)},
    )
    db.commit()
    audit_log.info("event=qa_answer_created telegram_id=%s question_id=%s institution=%s", payload.telegram_id, payload.question_id, payload.institution_slug)
    return AnswerItem(
        id=str(a.id),
        question_id=str(a.question_id),
        body=a.body,
        is_accepted=a.is_accepted,
        score=0,
        created_at=a.created_at,
    )


@router.get("/api/v1/qa/questions/{question_id}/answers", response_model=list[AnswerItem])
def list_answers(question_id: str, db: Session = Depends(get_db), x_orbit_bot_key: str | None = Header(default=None)):
    _require_bot_key(x_orbit_bot_key)
    _validate_uuid(question_id, "question_id")
    
    # Answers don't have a limit param in the current signature, but we should cap them anyway
    limit = resolve_limit(50, role="public")
    answers = db.query(Answer).filter(Answer.question_id == question_id).order_by(desc(Answer.is_accepted), desc(Answer.created_at)).limit(limit).all()
    out: list[AnswerItem] = []
    for a in answers:
        score = db.query(func.coalesce(func.sum(Vote.value), 0)).filter(Vote.answer_id == a.id).scalar() or 0
        out.append(
            AnswerItem(
                id=str(a.id),
                question_id=str(a.question_id),
                body=a.body,
                is_accepted=a.is_accepted,
                score=int(score),
                created_at=a.created_at,
            )
        )
    return out


@router.post("/api/v1/qa/vote")
def cast_vote(
    payload: VoteRequest,
    db: Session = Depends(get_db),
    x_orbit_bot_key: str | None = Header(default=None),
):
    _require_bot_key(x_orbit_bot_key)
    _validate_telegram_id(payload.telegram_id)
    if payload.question_id:
        _validate_uuid(payload.question_id, "question_id")
    if payload.answer_id:
        _validate_uuid(payload.answer_id, "answer_id")
    if payload.value not in (-1, 1):
        raise HTTPException(status_code=400, detail="value must be -1 or +1")
    if bool(payload.question_id) == bool(payload.answer_id):
        raise HTTPException(status_code=400, detail="Provide exactly one of question_id or answer_id")

    inst = db.query(Institution).filter(Institution.slug == payload.institution_slug).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    link = db.query(TelegramLink).filter(TelegramLink.telegram_id == payload.telegram_id, TelegramLink.institution_id == inst.id).first()
    if not link or not link.student_id or link.is_conflicted:
        raise HTTPException(status_code=403, detail="User not verified")

    vote = Vote(
        institution_id=inst.id,
        voter_telegram_id=payload.telegram_id,
        question_id=payload.question_id,
        answer_id=payload.answer_id,
        value=int(payload.value),
    )
    db.add(vote)
    try:
        db.commit()
    except Exception:
        db.rollback()
        # if unique constraint hit, update existing vote instead
        existing = (
            db.query(Vote)
            .filter(
                Vote.institution_id == inst.id,
                Vote.voter_telegram_id == payload.telegram_id,
                Vote.question_id == payload.question_id,
                Vote.answer_id == payload.answer_id,
            )
            .first()
        )
        if not existing:
            raise HTTPException(status_code=409, detail="Vote conflict")
        existing.value = int(payload.value)
        db.commit()

    return {"status": "ok"}


@router.get("/api/v1/qa/search", response_model=list[QASearchHit])
def search_questions(
    institution_slug: str,
    query: str,
    limit: int = 8,
    db: Session = Depends(get_db),
    x_orbit_bot_key: str | None = Header(default=None),
):
    _require_bot_key(x_orbit_bot_key)
    qtext = query.strip()
    if len(qtext) < 2:
        return []
    inst = db.query(Institution).filter(Institution.slug == institution_slug).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    # Blend TS rank + vote score
    tsq = func.plainto_tsquery("english", qtext)
    
    limit = resolve_limit(limit, role="public")
    rows = (
        db.query(
            Question.id,
            Question.title,
            func.ts_rank_cd(Question.search_text, tsq).label("ts_rank"),
            func.coalesce(func.sum(Vote.value), 0).label("vote_score"),
        )
        .outerjoin(Vote, Vote.question_id == Question.id)
        .filter(Question.institution_id == inst.id)
        .filter(Question.search_text.op("@@")(tsq))
        .group_by(Question.id, Question.title, Question.search_text)
        .order_by(desc(func.ts_rank_cd(Question.search_text, tsq)), desc(func.coalesce(func.sum(Vote.value), 0)))
        .limit(limit)
        .all()
    )
    return [
        QASearchHit(question_id=str(r[0]), title=r[1], score=float(r[2] or 0.0) + float(r[3] or 0.0) * 0.1)
        for r in rows
    ]
