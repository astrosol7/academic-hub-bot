"""
Production-grade Database Configuration
Strictly environment-driven, Lazy-initialized, No fallbacks.
"""
import os
import logging
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
        url = os.getenv("DATABASE_URL")
        if not url:
            # We fail LOUDLY but only when the system actually tries to use the DB
            raise RuntimeError(
                "\n" + "="*60 + "\n"
                "CRITICAL CONFIGURATION ERROR:\n"
                "DATABASE_URL is missing from the environment.\n"
                "Production systems MUST have this variable set.\n"
                "="*60
            )
        
        # Strip whitespace (common copy-paste error)
        url = url.strip()
        
        # SSL and Pooling configuration
        is_serverless = os.getenv('VERCEL') == '1'
        connect_args = {}
        if "postgresql" in url:
            # Require SSL in production environments
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
