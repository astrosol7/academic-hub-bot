from backend.api.database_postgresql import SessionLocal
from backend.api.models import AdminUser
db = SessionLocal()
try:
    admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
    if admin:
        db.delete(admin)
        db.commit()
        print("TEMPORARY: Admin user deleted for verification.")
    else:
        print("No admin user found.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
