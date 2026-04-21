import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'academic_hub'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'password123')
}

DATABASE_URL = f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    count = conn.execute(text('SELECT COUNT(*) FROM students')).scalar()
    print(f"Students count: {count}")
    results = conn.execute(text('SELECT id, full_name FROM students LIMIT 5')).fetchall()
    print("Sample students:", results)
