"""
Production-grade Database Configuration
Strictly environment-driven, Lazy-initialized, No fallbacks.
"""
import os
import logging
from urllib.parse import urlparse
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

log = logging.getLogger("api.database")

# Globals for lazy initialization
_engine = None
_SessionLocal = None
Base = declarative_base()

def get_engine():
    """Lazy initialization of the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        # 1. Try standard DATABASE_URL
        url = os.getenv("DATABASE_URL")
        
        # 2. Fallback to POSTGRES_URL (common on Vercel/Railway)
        if not url:
            url = os.getenv("POSTGRES_URL")
            
        # 3. Fallback to individual components
        if not url:
            user = os.getenv("POSTGRES_USER")
            password = os.getenv("POSTGRES_PASSWORD")
            host = os.getenv("POSTGRES_HOST")
            port = os.getenv("POSTGRES_PORT", "5432")
            db_name = os.getenv("POSTGRES_DB") or os.getenv("POSTGRES_DATABASE")
            
            if all([user, password, host, db_name]):
                url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
                log.info("Constructed DATABASE_URL from individual POSTGRES_* variables")

        if not url:
            # We fail LOUDLY but only when the system actually tries to use the DB
            env_keys = sorted(os.environ.keys())
            # Find similar keys to help spot typos
            similar_keys = [k for k in env_keys if "DB" in k.upper() or "POSTGRES" in k.upper() or "URL" in k.upper()]
            
            raise RuntimeError(
                "\n" + "="*60 + "\n"
                "CRITICAL CONFIGURATION ERROR:\n"
                "DATABASE_URL (or POSTGRES_URL/components) is missing from the environment.\n"
                "Production systems MUST have this variable set.\n"
                f"\nDetected similar keys: {', '.join(similar_keys) if similar_keys else 'None'}\n"
                f"All Environment Keys: {', '.join(env_keys)}\n"
                "="*60
            )
        
        # Strip whitespace and literal quotes (common copy-paste error from .env files)
        url = url.strip().strip('"').strip("'")
        
        # Log the connection target (masked password) for verification
        try:
            parsed = urlparse(url)
            log.info(f"Database connection target: {parsed.hostname}:{parsed.port or 5432}")
        except Exception:
            log.warning("Could not parse DATABASE_URL for logging purposes")

        # SSL and Pooling configuration
        is_serverless = (os.getenv('VERCEL') == '1' or os.getenv('RAILWAY_STATIC_URL') is not None)
        connect_args = {}
        if "postgresql" in url:
            # Require SSL in production environments (Supabase/Railway require this)
            connect_args["sslmode"] = "require" if is_serverless else "prefer"
            
        _engine = create_engine(
            url, 
            pool_pre_ping=True,
            pool_size=5 if is_serverless else 10,
            max_overflow=20,
            connect_args=connect_args
        )
        log.info("SQLAlchemy engine initialized (Lazy)")
        
    return _engine

def get_session_local():
    """Lazy initialization of the Session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal

def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for database sessions."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        log.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database metadata (tables)."""
    engine = get_engine()
    from api.models import Base as ModelsBase
    # Ensure all models are registered
    ModelsBase.metadata.create_all(bind=engine)
    log.info("Database metadata initialized.")
