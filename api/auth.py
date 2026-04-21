import os
import bcrypt
import jwt
import uuid
import hmac
import hashlib
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.models import AdminUser, AdminRole, Student
from api.database import get_db
import logging

SECRET_KEY = os.getenv("JWT_SECRET", "super_secret_dev_key_never_use_in_prod")
ENV = (os.getenv("ACADEMIC_HUB_ENV") or "dev").strip().lower()
if ENV in ("prod", "production") and SECRET_KEY == "super_secret_dev_key_never_use_in_prod":
    raise RuntimeError("JWT_SECRET must be set in production.")
ALGORITHM = "HS256"

router = APIRouter()
audit_log = logging.getLogger("security.audit")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

def validate_telegram_init_data(init_data: str) -> dict:
    """
    Validates the data received from the Telegram Mini App.
    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot token not configured")
    
    vals = dict(parse_qsl(init_data))
    if "hash" not in vals:
        raise HTTPException(status_code=401, detail="Missing hash in initData")
    
    received_hash = vals.pop("hash")
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(vals.items())])
    
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if expected_hash != received_hash:
        raise HTTPException(status_code=401, detail="Invalid data signature")
        
    try:
        user_data = json.loads(vals["user"])
        return user_data
    except (KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid user data in initData")

# ── SECURITY HELPERS ───────────────────────────────────────────

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def _require_access_token(payload: dict) -> None:
    if payload.get("refresh") is True:
        raise HTTPException(status_code=401, detail="Access token required")


def _require_refresh_token(payload: dict) -> None:
    if payload.get("refresh") is not True:
        raise HTTPException(status_code=401, detail="Refresh token required")


def get_current_admin(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> AdminUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token)
    _require_access_token(payload)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(AdminUser).filter(AdminUser.id == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_super_admin(user: AdminUser = Depends(get_current_admin)) -> AdminUser:
    if user.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin required")
    return user


# ── SCHEMAS ───────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str

class TMAPayload(BaseModel):
    init_data: str

# ── HASHING UTILS (RAW BCRYPT) ────────────────────────────────

def get_password_hash(password: str) -> str:
    """Hash a password using raw bcrypt."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    to_encode.update({
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ── ENDPOINTS ─────────────────────────────────────────────────

@router.post("/api/v1/auth/bootstrap", response_model=TokenResponse)
def bootstrap_root(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Executes exactly ONCE to genesis the first Super Admin.
    Checks .env BOOTSTRAP_ROOT_PASSWORD to authenticate the generation payload.
    """
    root_exists = db.query(AdminUser).filter(AdminUser.role == AdminRole.SUPER_ADMIN).first()
    if root_exists:
        raise HTTPException(status_code=403, detail="Bootstrap locked. Root already exists.")

    env_bootstrap = os.getenv("BOOTSTRAP_ROOT_PASSWORD")
    if not env_bootstrap or payload.password != env_bootstrap:
        raise HTTPException(status_code=401, detail="Invalid Bootstrap Authentication.")

    root_user = AdminUser(
        username=payload.username,
        password_hash=get_password_hash(payload.password),
        role=AdminRole.SUPER_ADMIN
    )
    db.add(root_user)
    db.commit()
    db.refresh(root_user)

    access = create_token({"sub": str(root_user.id), "role": root_user.role.value}, timedelta(minutes=30))
    refresh = create_token({"sub": str(root_user.id), "refresh": True}, timedelta(days=7))
    audit_log.info("event=auth_bootstrap_success user=%s", root_user.username)
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/api/v1/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # 1. Try Admin Check
    user = db.query(AdminUser).filter(AdminUser.username == payload.username).first()
    if user and verify_password(payload.password, user.password_hash):
        user.last_login = datetime.utcnow()
        db.commit()
        access = create_token({"sub": str(user.id), "role": user.role.value, "name": user.username}, timedelta(minutes=30))
        refresh = create_token({"sub": str(user.id), "refresh": True, "role": user.role.value}, timedelta(days=7))
        audit_log.info("event=auth_login_success user=%s role=%s", user.username, user.role.value)
        return TokenResponse(access_token=access, refresh_token=refresh)

    # 2. Try Student Check (Demo mode: password is the ID itself or 'voyager')
    # In a real system, students would have passwords or use TMA.
    student = db.query(Student).filter(Student.id == payload.username).first()
    if student:
        # For demo purposes, we allow login if password matches ID or is 'voyager'
        if payload.password in (student.id, "voyager"):
            access = create_token({"sub": student.id, "role": "student", "name": student.full_name}, timedelta(days=1))
            refresh = create_token({"sub": student.id, "refresh": True, "role": "student"}, timedelta(days=30))
            audit_log.info("event=auth_student_login_success student_id=%s", student.id)
            return TokenResponse(access_token=access, refresh_token=refresh)

    audit_log.warning("event=auth_login_failed username=%s", payload.username)
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/api/v1/auth/refresh", response_model=TokenResponse)
def refresh_tokens(payload: RefreshRequest, db: Session = Depends(get_db)):
    claims = decode_token(payload.refresh_token)
    _require_refresh_token(claims)
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(AdminUser).filter(AdminUser.id == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access = create_token({"sub": str(user.id), "role": user.role.value}, timedelta(minutes=30))
    refresh = create_token({"sub": str(user.id), "refresh": True}, timedelta(days=7))
    audit_log.info("event=auth_refresh_success user=%s", user.username)
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/api/v1/auth/tma", response_model=TokenResponse)
def tma_login(payload: TMAPayload, db: Session = Depends(get_db)):
    """
    Identity Gateway for Students. Validates Telegram initData and issues a JWT.
    """
    user_data = validate_telegram_init_data(payload.init_data)
    telegram_id = str(user_data.get("id"))
    
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Missing telegram ID")
        
    # In Orbit v1, students don't have separate AdminUser accounts, 
    # so we issue a token with 'role':'student' and sub=telegram_id.
    access = create_token({"sub": telegram_id, "role": "student", "name": user_data.get("first_name")}, timedelta(days=1))
    refresh = create_token({"sub": telegram_id, "refresh": True, "role": "student"}, timedelta(days=30))
    
    audit_log.info("event=tma_login_success telegram_id=%s", telegram_id)
    return TokenResponse(access_token=access, refresh_token=refresh)
