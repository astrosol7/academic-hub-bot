from dotenv import load_dotenv
load_dotenv()
from backend.api.database_postgresql import SessionLocal
from backend.api.models import Resource
db = SessionLocal()
items = db.query(Resource).limit(10).all()
for i in items:
    print(i.title, i.category_slug)
