from dotenv import load_dotenv
load_dotenv()
from backend.api.database_postgresql import SessionLocal
from backend.api.models import Course
db = SessionLocal()
courses = db.query(Course).filter_by(quarter=1).all()
print("Q1 Course Titles:")
for c in courses:
    print(f"'{c.title}'")
