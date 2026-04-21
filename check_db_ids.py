from dotenv import load_dotenv
load_dotenv()
from backend.api.database_postgresql import SessionLocal
from backend.api.models import Institution, TelegramLink, Course
db = SessionLocal()

# Check Institution ID
inst = db.query(Institution).filter_by(slug="sit").first()
print(f"Institution 'sit' ID: {inst.id}")

# Check TelegramLink
user_id = "2113497563"
link = db.query(TelegramLink).filter_by(telegram_id=user_id).first()
if link:
    print(f"Link ID: {link.id}, Institution ID: {link.institution_id}, Verified: {link.student_id is not None}")

# Check Unsorted Materials in Q1
courses = db.query(Course).filter_by(quarter=1).all()
print("\nQ1 Courses:")
for c in courses:
    print(f"- {c.title} (ID: {c.id})")
