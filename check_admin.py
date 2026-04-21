from backend.api.database_postgresql import SessionLocal
from backend.api.models import AdminUser
db = SessionLocal()
admin = db.query(AdminUser).first()
if admin:
    print(f"Username: {admin.username}")
    print(f"Role: {admin.role}")
else:
    print("No admin user found.")
