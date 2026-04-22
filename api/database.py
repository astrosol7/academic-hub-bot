"""Database session factory — shared module to prevent circular imports."""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

log = logging.getLogger("api.database")

def get_database_url():
    """Resolves database URL from various environment sources."""
    # 1. Primary: DATABASE_URL (Standard for Vercel/Railway)
    url = os.getenv("DATABASE_URL")
    if url:
        return url
        
    # 2. Fallback: Manual construction from individual variables
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "academic_hub")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"

DATABASE_URL = get_database_url()

# Configuration for Engine
is_serverless = os.getenv('VERCEL') == '1'
connect_args = {}
if "postgresql" in DATABASE_URL:
    connect_args["sslmode"] = "require" if is_serverless else "prefer"

try:
    engine = create_engine(
        DATABASE_URL, 
        pool_pre_ping=True,
        connect_args=connect_args
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    log.error(f"Failed to create SQLAlchemy engine: {e}")
    # We don't raise here to prevent import-time crashes, but get_db will fail
    engine = None
    SessionLocal = None

def get_db():
    if not SessionLocal:
        raise RuntimeError("Database not configured. Ensure DATABASE_URL is set.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
