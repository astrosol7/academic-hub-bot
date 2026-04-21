from dotenv import load_dotenv
load_dotenv()
from backend.api.database_postgresql import SessionLocal
from backend.api.models import Course, Institution, TelegramLink
db = SessionLocal()

# Check user verification
user_id = "2113497563" # Found in logs
print(f"--- Verification Check for {user_id} ---")
links = db.query(TelegramLink).filter_by(telegram_id=user_id).all()
for l in links:
    print(f"Link: inst={l.institution_id}, student={l.student_id}, conflicted={l.is_conflicted}")

# Check Quarters
print("\n--- Courses by Quarter ---")
courses = db.query(Course.quarter, Course.title).order_by(Course.quarter).all()
for c in courses:
    print(f"Q{c.quarter}: {c.title}")

# Check Quarter Labels
inst = db.query(Institution).first()
if inst:
    print(f"\n--- Institution Metadata ({inst.slug}) ---")
    print(inst.metadata_blob)
