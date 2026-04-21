from dotenv import load_dotenv
load_dotenv()
from backend.api.database_postgresql import SessionLocal
from backend.api.models import Course, Institution
db = SessionLocal()

print("--- Quarters Check ---")
inst = db.query(Institution).filter_by(slug="sit").first()
print(f"Institution Quarter Labels: {inst.metadata_blob.get('quarter_labels')}")

print("\n--- Course List Check ---")
courses = db.query(Course).order_by(Course.quarter, Course.title).all()
for c in courses:
    print(f"Q{c.quarter}: {c.title}")
