import logging
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables before any other imports (Force override on reload)
load_dotenv(override=True)

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.models import (
    Resource, ResourceStatus, Course, ResourceCategory,
    IngestionLog, UsageSignal, ReportSubmission, ReportContextType, ReportStatus
)
from backend.api.auth import router as auth_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("api")

app = FastAPI(title="Academic Hub - Orbit V1 API")

# CORS for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# ── REQUEST/RESPONSE MODELS ────────────────────────────────────

class CISIngestRequest(BaseModel):
    course_id: str
    category_slug: str
    week_number: Optional[int] = None
    title: str
    link: HttpUrl
    tags: Optional[str] = None

class CISIngestResponse(BaseModel):
    status: str
    resource_id: Optional[str] = None
    warnings: list[str] = []

class SearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = None

class SearchResultItem(BaseModel):
    resource_id: str
    title: str
    course_id: str
    category_slug: str
    week_number: Optional[int] = None
    score: float = 0.0

class SearchResponse(BaseModel):
    results: list[SearchResultItem] = []
    engine: str = "none"  # tsquery_hit | trigram_hit | none

class TelemetryEvent(BaseModel):
    user_id: str
    action: str
    metadata: dict = {}

class IncidentCreate(BaseModel):
    telegram_id: str
    category: str
    description: str
    course_id: Optional[str] = None
    context_type: ReportContextType = ReportContextType.ISSUE


# ── SEARCH ENDPOINT (HTTP BRIDGE) ──────────────────────────────

@app.post("/api/v1/search", response_model=SearchResponse)
def search_resources(payload: SearchRequest, db: Session = Depends(get_db)):
    """
    Dual-engine search: TSVector first, pg_trgm fallback.
    Returns ranked results for the Telegram bot to render.
    """
    query_text = payload.query.strip()
    if not query_text or len(query_text) < 2:
        return SearchResponse(results=[], engine="none")

    # Engine 1: TSVector full-text search
    try:
        ts_results = db.query(Resource).filter(
            Resource.status == ResourceStatus.ACTIVE,
            Resource.search_text.op("@@")(func.plainto_tsquery("english", query_text))
        ).limit(10).all()

        if ts_results:
            items = [
                SearchResultItem(
                    resource_id=str(r.id),
                    title=r.title,
                    course_id=r.course_id,
                    category_slug=r.category_slug,
                    week_number=r.week_number,
                    score=1.0
                ) for r in ts_results
            ]
            return SearchResponse(results=items, engine="tsquery_hit")
    except Exception as e:
        log.warning(f"TSVector search failed (likely no data yet): {e}")

    # Engine 2: pg_trgm similarity fallback
    try:
        trgm_results = db.query(Resource).filter(
            Resource.status == ResourceStatus.ACTIVE,
            func.similarity(Resource.title, query_text) > 0.3
        ).order_by(
            func.similarity(Resource.title, query_text).desc()
        ).limit(10).all()

        if trgm_results:
            items = [
                SearchResultItem(
                    resource_id=str(r.id),
                    title=r.title,
                    course_id=r.course_id,
                    category_slug=r.category_slug,
                    week_number=r.week_number,
                    score=round(float(db.execute(
                        func.similarity(Resource.title, query_text)
                    ).scalar() or 0), 2)
                ) for r in trgm_results
            ]
            return SearchResponse(results=items, engine="trigram_hit")
    except Exception as e:
        log.warning(f"pg_trgm search failed (extension may not be enabled): {e}")

    return SearchResponse(results=[], engine="none")

# ── TELEMETRY ENDPOINT ─────────────────────────────────────────

@app.post("/api/v1/telemetry")
def log_telemetry(event: TelemetryEvent, db: Session = Depends(get_db)):
    """Fire-and-forget behavioral signal capture."""
    try:
        signal = UsageSignal(
            user_id=event.user_id,
            action=event.action,
            metadata_blob=event.metadata,
        )
        db.add(signal)
        db.commit()
        return {"status": "recorded"}
    except Exception as e:
        log.warning(f"Telemetry write failed: {e}")
        db.rollback()
        return {"status": "dropped"}

# ── INCIDENT REPORTING ENDPOINT ────────────────────────────────
@app.post("/api/v1/incidents")
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    """Capture student issue reports for dashboard triage."""
    try:
        report = ReportSubmission(
            telegram_id=payload.telegram_id,
            category=payload.category,
            description=payload.description,
            course_id=payload.course_id,
            context_type=payload.context_type,
            status=ReportStatus.OPEN
        )
        db.add(report)
        db.commit()
        return {"status": "created", "id": str(report.id)}
    except Exception as e:
        log.error(f"Failed to create incident: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to record incident.")


# ── CIS INGESTION ENDPOINT ─────────────────────────────────────

@app.post("/api/v1/cis/ingest", response_model=CISIngestResponse)
def ingest_resource(payload: CISIngestRequest, db: Session = Depends(get_db)):
    """
    Controlled Ingestion System (V1 Drive Link Only).
    Auto-Approves directly to ACTIVE after strict validation.
    """
    warnings = []

    # 1. Structure Check
    course = db.query(Course).filter(Course.id == payload.course_id).first()
    if not course:
        raise HTTPException(status_code=400, detail="Invalid Structure: Course does not exist.")

    category = db.query(ResourceCategory).filter(ResourceCategory.slug == payload.category_slug).first()
    if not category:
        raise HTTPException(status_code=400, detail="Invalid Structure: Category does not exist.")

    if payload.week_number is not None and not course.week_count:
        warnings.append(f"Course {payload.course_id} has no week structure, but a week was provided.")

    # 2. Duplicate Detection (Exact URL block + Fuzzy title warning)
    existing_file = db.query(Resource).filter(Resource.external_path == str(payload.link)).first()
    if existing_file:
        raise HTTPException(status_code=409, detail="Duplicate: A resource with this exact link already exists.")

    duplicate_flag = False
    try:
        similar = db.query(Resource).filter(
            Resource.course_id == payload.course_id,
            func.similarity(Resource.title, payload.title) > 0.85
        ).first()
        if similar:
            duplicate_flag = True
            warnings.append(f"Fuzzy Duplicate: Found similar asset '{similar.title}'")
    except Exception:
        pass  # pg_trgm may not be enabled yet

    # 3. Build resource
    fake_hash = "drive_" + str(payload.link).split("/")[-1][:16]
    resource = Resource(
        course_id=payload.course_id,
        category_slug=payload.category_slug,
        week_number=payload.week_number,
        title=payload.title,
        external_path=str(payload.link),
        file_hash=fake_hash,
        status=ResourceStatus.ACTIVE,
        source_type="drive",
        tags=payload.tags
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    # 4. Audit log
    ingestion_log = IngestionLog(
        resource_id=resource.id,
        action="create",
        duplicate_flag=duplicate_flag,
        context_snapshot={"title": payload.title, "link": str(payload.link), "tags": payload.tags}
    )
    db.add(ingestion_log)
    db.commit()

    log.info(f"CIS: Resource '{payload.title}' added to {course.title} [ACTIVE]")

    return CISIngestResponse(
        status="ACTIVE",
        resource_id=str(resource.id),
        warnings=warnings
    )

# ── HEALTH CHECK ───────────────────────────────────────────────

@app.get("/api/v1/health")
def health_check():
    return {"status": "operational", "version": "1.0.0", "release": "orbit"}

if __name__ == "__main__":
    import uvicorn
    # Configuration for Orbit V1 Deployment
    uvicorn.run(
        "backend.api.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
