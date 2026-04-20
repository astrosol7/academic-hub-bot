"""
PostgreSQL Database Configuration for Academic Hub
Industry-standard database implementation with advanced features
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import psycopg2.pool

# PostgreSQL Configuration
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'academic_hub'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'password'),
    'minconn': 1,
    'maxconn': 20,
    'options': '-c timezone=UTC'
}

# Create connection pool
try:
    connection_pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=POSTGRES_CONFIG['minconn'],
        maxconn=POSTGRES_CONFIG['maxconn'],
        **{k: v for k, v in POSTGRES_CONFIG.items() if k not in ['minconn', 'maxconn', 'options']}
    )
except Exception as e:
    logging.error(f"Failed to create connection pool: {e}")
    connection_pool = None

# Create SQLAlchemy engine with PostgreSQL
DATABASE_URL = f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=False,
    connect_args={
        "application_name": "academic_hub_api"
    }
)

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
    """Initialize PostgreSQL database with all tables and extensions"""
    try:
        # Create database if it doesn't exist
        conn = psycopg2.connect(
            host=POSTGRES_CONFIG['host'],
            port=POSTGRES_CONFIG['port'],
            user=POSTGRES_CONFIG['user'],
            password=POSTGRES_CONFIG['password'],
            database='postgres'  # Connect to default database
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (POSTGRES_CONFIG['database'],))
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {POSTGRES_CONFIG['database']}")
            log.info(f"Database {POSTGRES_CONFIG['database']} created")
        
        cursor.close()
        conn.close()
        
        # Connect to the target database and create extensions
        with engine.connect() as conn:
            # Enable PostgreSQL extensions for advanced features
            extensions = [
                'uuid-ossp',
                'pg_trgm',  # For text search
                'unaccent',  # For accent-insensitive search
                'btree_gin',  # For GIN indexes
                'btree_gist'  # For GiST indexes
            ]
            
            for ext in extensions:
                try:
                    conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS \"{ext}\""))
                    log.info(f"Extension {ext} enabled")
                except Exception as e:
                    log.warning(f"Could not enable extension {ext}: {e}")
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            log.info("Database initialized successfully")
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_resources_title_gin ON resources USING gin(to_tsvector('english', title))",
                "CREATE INDEX IF NOT EXISTS idx_resources_description_gin ON resources USING gin(to_tsvector('english', description))",
                "CREATE INDEX IF NOT EXISTS idx_resources_course_id ON resources(course_id)",
                "CREATE INDEX IF NOT EXISTS idx_resources_status ON resources(status)",
                "CREATE INDEX IF NOT EXISTS idx_usage_signals_user_id ON usage_signals(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_usage_signals_timestamp ON usage_signals(timestamp)"
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    log.info(f"Index created: {index_sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    log.warning(f"Could not create index: {e}")
        
        return True
        
    except Exception as e:
        log.error(f"Database initialization failed: {e}")
        return False

def get_database_info():
    """Get comprehensive database information for monitoring"""
    try:
        with engine.connect() as conn:
            # Get database size
            size_result = conn.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """))
            db_size = size_result.scalar()
            
            # Get table counts
            table_count = conn.execute(text("""
                SELECT count(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)).scalar()
            
            # Get connection count
            conn_count = conn.execute(text("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE state = 'active'
            """)).scalar()
            
            # Get index usage
            index_stats = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC
                LIMIT 10
            """)).fetchall()
            
            return {
                "type": "PostgreSQL",
                "version": conn.execute(text("SELECT version()")).scalar(),
                "database": POSTGRES_CONFIG['database'],
                "host": POSTGRES_CONFIG['host'],
                "port": POSTGRES_CONFIG['port'],
                "size": db_size,
                "tables": table_count,
                "active_connections": conn_count,
                "connection_pool": {
                    "min": POSTGRES_CONFIG['minconn'],
                    "max": POSTGRES_CONFIG['maxconn'],
                    "current": len(connection_pool._pool) if connection_pool else 0
                },
                "extensions": [
                    'uuid-ossp', 'pg_trgm', 'unaccent', 
                    'btree_gin', 'btree_gist'
                ],
                "performance": {
                    "top_indexes": [dict(row) for row in index_stats]
                }
            }
    except Exception as e:
        log.error(f"Failed to get database info: {e}")
        return {"error": str(e)}

def health_check():
    """Perform comprehensive database health check"""
    try:
        with engine.connect() as conn:
            # Test basic connectivity
            conn.execute(text("SELECT 1"))
            
            # Check table existence
            tables = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """)).fetchall()
            
            # Check database locks
            locks = conn.execute(text("""
                SELECT count(*) FROM pg_locks
                WHERE granted = false
            """)).scalar()
            
            # Check long-running queries
            long_queries = conn.execute(text("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE state = 'active' 
                AND query_start < now() - interval '5 minutes'
            """)).scalar()
            
            return {
                "status": "healthy",
                "tables": len(tables),
                "blocked_locks": locks,
                "long_queries": long_queries,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        log.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

def backup_database(backup_path: str = None):
    """Create database backup using pg_dump"""
    try:
        import subprocess
        from datetime import datetime
        
        if not backup_path:
            backup_path = f"backups/academic_hub_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        # Ensure backup directory exists
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Create backup command
        cmd = [
            'pg_dump',
            f"--host={POSTGRES_CONFIG['host']}",
            f"--port={POSTGRES_CONFIG['port']}",
            f"--username={POSTGRES_CONFIG['user']}",
            f"--dbname={POSTGRES_CONFIG['database']}",
            '--verbose',
            '--clean',
            '--no-owner',
            '--no-privileges',
            '--file=' + backup_path
        ]
        
        # Set password in environment
        env = os.environ.copy()
        env['PGPASSWORD'] = POSTGRES_CONFIG['password']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            log.info(f"Database backup created: {backup_path}")
            return {"success": True, "path": backup_path}
        else:
            log.error(f"Backup failed: {result.stderr}")
            return {"success": False, "error": result.stderr}
            
    except Exception as e:
        log.error(f"Backup failed: {e}")
        return {"success": False, "error": str(e)}

def optimize_database():
    """Optimize database performance"""
    try:
        with engine.connect() as conn:
            # Update table statistics
            conn.execute(text("ANALYZE"))
            
            # Rebuild indexes
            conn.execute(text("REINDEX DATABASE"))
            
            # Clean up dead tuples
            conn.execute(text("VACUUM ANALYZE"))
            
            log.info("Database optimization completed")
            return {"success": True}
    except Exception as e:
        log.error(f"Database optimization failed: {e}")
        return {"success": False, "error": str(e)}

# Advanced search functions
def create_search_function():
    """Create advanced search function with full-text search"""
    search_function_sql = """
    CREATE OR REPLACE FUNCTION search_resources(query_text TEXT)
    RETURNS TABLE(id VARCHAR, title VARCHAR, description TEXT, rank REAL) AS $$
    BEGIN
        RETURN QUERY
        SELECT 
            r.id,
            r.title,
            r.description,
            ts_rank(search_vector, plainto_tsquery('english', query_text)) as rank
        FROM resources r
        WHERE search_vector @@ plainto_tsquery('english', query_text)
        ORDER BY rank DESC;
    END;
    $$ LANGUAGE plpgsql;
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(search_function_sql))
            log.info("Advanced search function created")
    except Exception as e:
        log.error(f"Failed to create search function: {e}")

# Connection pool management
def get_pool_status():
    """Get connection pool status"""
    if not connection_pool:
        return {"status": "not_initialized"}
    
    return {
        "status": "active",
        "min_connections": POSTGRES_CONFIG['minconn'],
        "max_connections": POSTGRES_CONFIG['maxconn'],
        "current_connections": len(connection_pool._pool) if connection_pool else 0,
        "available_connections": connection_pool._pool.maxlen if connection_pool else 0
    }
