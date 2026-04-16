import csv
import os
import sys
import logging
from pathlib import Path

# Fix path so project imports work when run as script
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from academic_hub.config import load_config
from backend.api.models import Base, Institution, Student

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("seed_students")


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    # fallback to .env if present
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT_DIR / ".env")
    except Exception:
        pass
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required to seed students.")
    return url


def seed_students(csv_path: Path) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    config = load_config(require_token=False)
    database_url = _get_database_url()

    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Ensure schema exists for local/dev
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        inst = db.query(Institution).filter(Institution.slug == config.institution_slug).first()
        if not inst:
            inst = Institution(slug=config.institution_slug, display_name=config.institution_name)
            db.add(inst)
            db.commit()
            db.refresh(inst)
            log.info("Created institution %s (%s)", inst.slug, inst.id)
        else:
            if inst.display_name != config.institution_name:
                inst.display_name = config.institution_name
                db.commit()

        inserted = 0
        updated = 0
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise RuntimeError("CSV has no header row.")

            required = {"Student ID", "Student Name"}
            missing = required - set(reader.fieldnames)
            if missing:
                raise RuntimeError(f"CSV missing columns: {sorted(missing)}. Found: {reader.fieldnames}")

            for row in reader:
                student_id = (row.get("Student ID") or "").strip()
                full_name = " ".join((row.get("Student Name") or "").strip().split())
                if not student_id or not full_name:
                    continue

                existing = db.query(Student).filter(Student.id == student_id).first()
                if not existing:
                    db.add(Student(id=student_id, institution_id=inst.id, full_name=full_name))
                    inserted += 1
                else:
                    # keep institution consistent
                    changed = False
                    if existing.institution_id != inst.id:
                        existing.institution_id = inst.id
                        changed = True
                    if existing.full_name != full_name:
                        existing.full_name = full_name
                        changed = True
                    if changed:
                        updated += 1

                if (inserted + updated) % 500 == 0:
                    db.commit()

        db.commit()
        log.info("Seed complete. inserted=%s updated=%s", inserted, updated)
    finally:
        db.close()


if __name__ == "__main__":
    default_csv = ROOT_DIR / "SIT_Student_Database.csv"
    csv_path = Path(os.getenv("STUDENTS_CSV", str(default_csv)))
    seed_students(csv_path)

