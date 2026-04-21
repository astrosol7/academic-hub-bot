import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment
root = Path(__file__).resolve().parent.parent.parent
env_path = root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Import models & database
# We use absolute imports by adding root to sys.path
import sys
sys.path.append(str(root))

from backend.api.database_postgresql import SessionLocal
from backend.api.models import Course, Resource

def purge():
    db = SessionLocal()
    try:
        print("SEARCH: Searching for 'Unsorted Materials'...")
        # Exact title match as requested
        course = db.query(Course).filter(Course.title == "Unsorted Materials").first()
        
        if not course:
            print("❌ 'Unsorted Materials' course not found in database.")
            return

        print(f"INFO: Found course: {course.title} (ID: {course.id})")
        
        # Resources are deleted automatically if cascade is on, but let's be explicit and safe
        res_count = db.query(Resource).filter(Resource.course_id == course.id).count()
        print(f"INFO: Found {res_count} associated resources. Purging...")
        
        db.query(Resource).filter(Resource.course_id == course.id).delete()
        db.delete(course)
        
        db.commit()
        print("SUCCESS: Purge complete. Orbit stabilized.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during purge: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    purge()
