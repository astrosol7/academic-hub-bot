import os
import bcrypt
from dotenv import load_dotenv
load_dotenv()
from backend.api.database_postgresql import SessionLocal
from backend.api.models import AdminUser, AdminRole

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

db = SessionLocal()
try:
    username = "admin"
    password = os.getenv("BOOTSTRAP_ROOT_PASSWORD", "Orbit77!Nexus")
    
    # Check if already exists
    existing = db.query(AdminUser).filter(AdminUser.username == username).first()
    if existing:
        print(f"Admin '{username}' already exists. Updating password...")
        existing.password_hash = get_password_hash(password)
    else:
        print(f"Creating Super Admin: {username}...")
        new_admin = AdminUser(
            username=username,
            password_hash=get_password_hash(password),
            role=AdminRole.SUPER_ADMIN
        )
        db.add(new_admin)
    
    db.commit()
    print("SUCCESS: Admin account ready. You can now login with:")
    print(f"Username: {username}")
    print(f"Password: {password}")
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
