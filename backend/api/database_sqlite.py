import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# SQLite Configuration
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT_DIR / "data" / "academic_hub.db"

# Ensure data directory exists
DB_PATH.parent.mkdir(exist_ok=True)

# Create SQLite engine with optimized settings for production
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={
        "check_same_thread": False,
        "timeout": 20,
        "isolation_level": None
    },
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Enable WAL mode for better concurrency
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))
    conn.execute(text("PRAGMA synchronous=NORMAL"))
    conn.execute(text("PRAGMA cache_size=10000"))
    conn.execute(text("PRAGMA temp_store=memory"))
    conn.execute(text("PRAGMA mmap_size=268435456"))  # 256MB

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

log = logging.getLogger("database")

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        log.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """Initialize database with all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        log.info("Database initialized successfully")
        return True
    except Exception as e:
        log.error(f"Database initialization failed: {e}")
        return False

def get_database_info():
    """Get database information for monitoring"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT count(*) FROM sqlite_master WHERE type='table'"))
            table_count = result.scalar()
            
            # Get database size
            db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
            
            return {
                "type": "SQLite",
                "path": str(DB_PATH),
                "tables": table_count,
                "size_bytes": db_size,
                "size_mb": round(db_size / (1024 * 1024), 2)
            }
    except Exception as e:
        log.error(f"Failed to get database info: {e}")
        return {"error": str(e)}
