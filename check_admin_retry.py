import os
from dotenv import load_dotenv
load_dotenv()
from backend.api.database_postgresql import SessionLocal
from backend.api.models import AdminUser
db = SessionLocal()
try:
    admin = db.query(AdminUser).first()
    if admin:
        print(f"Username: {admin.username}")
        print(f"Role: {admin.role}")
    else:
        print("No admin user found.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
