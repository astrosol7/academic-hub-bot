import csv
import os
import sys
import logging
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Fix path to ensure 'backend' and 'academic_hub' are found
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.api.models import Student

# Setup logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("bootstrap")

def bootstrap(csv_path: str):
    load_dotenv(ROOT_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        log.error("DATABASE_URL not found in .env")
        return

    cosmic_path = Path(csv_path)
    if not cosmic_path.exists():
        log.error(f"CSV file not found: {csv_path}")
        return

    # Database setup
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        log.info(f"Opening {csv_path} for ingestion...")
        with open(cosmic_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate headers
            expected_headers = ['Student ID', 'Student Name']
            if not all(h in reader.fieldnames for h in expected_headers):
                log.error(f"CSV missing required headers. Found: {reader.fieldnames}")
                return

            records_count = 0
            for row in reader:
                student_id = row['Student ID'].strip()
                full_name = row['Student Name'].strip()
                
                if not student_id or not full_name:
                    continue

                # Upsert logic
                existing = db.query(Student).filter_by(id=student_id).first()
                if existing:
                    existing.full_name = full_name
                else:
                    new_student = Student(id=student_id, full_name=full_name)
                    db.add(new_student)
                
                records_count += 1
                if records_count % 50 == 0:
                    log.info(f"Processed {records_count} records...")

            db.commit()
            log.info(f"✅ Success! Successfully ingested {records_count} student records into the database.")
            
    except Exception as e:
        db.rollback()
        log.error(f"❌ Critical Failure during ingestion: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Default to the file in the project root if it exists
    default_csv = str(ROOT_DIR / "SIT_Student_Database.csv")
    csv_file = sys.argv[1] if len(sys.argv) > 1 else default_csv
    bootstrap(csv_file)
