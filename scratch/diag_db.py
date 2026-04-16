import os
import sys
from pathlib import Path

# Add root project to path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Checking DATABASE_URL: {DATABASE_URL}")

from sqlalchemy.orm import sessionmaker
from backend.api.database import engine
from backend.api.models import Base, AdminUser

SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()
try:
    print("Attempting to query AdminUser...")
    user = db.query(AdminUser).first()
    print(f"Query successful. Found: {user}")
except Exception as e:
    print(f"Query failed: {e}")
finally:
    db.close()

