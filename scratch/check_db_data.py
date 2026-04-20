
import os
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'academic_hub')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

def check_data():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Check institutions
            inst_count = conn.execute(text("SELECT count(*) FROM institutions")).scalar()
            print(f"Institutions: {inst_count}")
            
            # Check courses
            course_count = conn.execute(text("SELECT count(*) FROM courses")).scalar()
            print(f"Courses: {course_count}")
            
            # Check resources
            res_count = conn.execute(text("SELECT count(*) FROM resources")).scalar()
            print(f"Resources: {res_count}")
            
            if inst_count > 0:
                inst = conn.execute(text("SELECT slug FROM institutions LIMIT 1")).scalar()
                print(f"Sample Institution Slug: {inst}")
                
            return True
    except Exception as e:
        print(f"Error checking data: {e}")
        return False

if __name__ == "__main__":
    check_data()
