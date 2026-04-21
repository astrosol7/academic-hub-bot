from dotenv import load_dotenv
load_dotenv()
from backend.api.database_postgresql import SessionLocal
from backend.api.models import ResourceCategory
db = SessionLocal()
cats = db.query(ResourceCategory).all()
for c in cats:
    print(c.slug, "->", c.label)
