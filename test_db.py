from dotenv import load_dotenv
load_dotenv()
from backend.api.database_postgresql import SessionLocal
from backend.api.models import Resource
db = SessionLocal()
print(f"Total Resources in DB: {db.query(Resource).count()}")
items = db.query(Resource).limit(3).all()
for i in items:
    print(i.title, i.external_path)
