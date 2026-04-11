import os
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.models import AdminUser, AdminRole
from backend.api.database import get_db

SECRET_KEY = os.getenv("JWT_SECRET", "super_secret_dev_key_never_use_in_prod")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    username: str
    password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

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
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/api/v1/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login = datetime.utcnow()
    db.commit()

    access = create_token({"sub": str(user.id), "role": user.role.value}, timedelta(minutes=30))
    refresh = create_token({"sub": str(user.id), "refresh": True}, timedelta(days=7))
    return TokenResponse(access_token=access, refresh_token=refresh)
