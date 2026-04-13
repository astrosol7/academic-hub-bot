"""
Database Ignition Switch (The "Ignitor")
Purpose: 
1. Enable pg_trgm extension
2. Create all tables defined in models.py
3. Verify existence of admin_users table
4. Idempotent and safe to re-run.
"""
import sys
import logging
from pathlib import Path
from sqlalchemy import text, inspect

# Add root project to path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ── LOGGING SETUP ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("ignitor")

# ── CRITICAL IMPORTS ───────────────────────────────────────────
# Must import models BEFORE create_all() to register them with Base
from backend.api.database import engine
from backend.api.models import Base
import backend.api.models as models

def ignite():
    log.info("🚀 Starting Database Ignition...")

    with engine.connect() as conn:
        # Step 1: Enable extensions
        log.info("⚙️ Step 1: Enabling extensions...")
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            conn.commit()
            log.info("✅ Extension 'pg_trgm' enabled.")
        except Exception as e:
            log.error(f"❌ Failed to enable extension: {e}")
            return

        # Step 2: Create Tables
        log.info("🏗️ Step 2: Creating tables defined in models.py...")
        try:
            Base.metadata.create_all(engine)
            log.info("✅ Database schema initialized.")
        except Exception as e:
            log.error(f"❌ Table creation failed: {e}")
            return

        # Step 3: Verification
        log.info("🔍 Step 3: Verifying ignition...")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ["admin_users", "institutions", "courses", "resources"]
        missing = [t for t in required_tables if t not in tables]
        
        if missing:
            log.warning(f"⚠️ Some expected tables are missing: {missing}")
        else:
            log.info(f"✨ Ignition Verified! Total tables found: {len(tables)}")
            log.info("🔥 The system is now ready for bootstrapping.")

if __name__ == "__main__":
    ignite()
