import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Checking DATABASE_URL: {DATABASE_URL}")

from sqlalchemy.orm import sessionmaker
from backend.api.models import AdminUser

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

