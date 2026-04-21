
import json
import os
import uuid
import re
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load bot-layer config
load_dotenv()

# We use the models defined in the backend
from backend.api.database_postgresql import engine, SessionLocal, init_database
from backend.api.models import Institution, Course, Resource, ResourceCategory, ResourceStatus, ContentStrategy

def get_quarter_from_path(path: str) -> int:
    match = re.search(r'Quarter_(\d+)', path)
    if match:
        return int(match.group(1))
    return 1

def slugify(text: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]', '_', text).lower().strip('_')

def bootstrap():
    print("🚀 Starting Orbital Data Ignition...")
    
    # 1. Initialize Schema
    if not init_database():
        print("❌ Database initialization failed.")
        return
    
    db = SessionLocal()
    
    try:
        # 2. Create Institution
        inst_slug = os.getenv("INSTITUTION_SLUG", "sit")
        institution = db.query(Institution).filter_by(slug=inst_slug).first()
        if not institution:
            institution = Institution(
                slug=inst_slug,
                display_name="SIT Academic Hub",
                metadata_blob={
                    "quarter_labels": {
                        1: "Quarter 1",
                        2: "Quarter 2"
                    }
                }
            )
            db.add(institution)
            db.flush()
            print(f"Created Institution: {inst_slug}")
        
        # 3. Load Meta Cache
        meta_cache_path = Path("resources/institutions/sit/.meta_cache.json")
        if not meta_cache_path.exists():
            print(f"Meta cache not found at {meta_cache_path}")
            return
            
        with open(meta_cache_path, 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
        
        print(f"Loaded {len(meta_data)} resource metadata entries.")
        
        # 4. Process Courses and Resources
        courses_map = {} # title -> Course
        categories_map = {} # label -> ResourceCategory
        
        # First pass: Create Categories
        unique_categories = set()
        for res_data in meta_data.values():
            unique_categories.add(res_data.get('category_label', 'Unknown'))
            
        for cat_label in unique_categories:
            slug = slugify(cat_label)
            category = db.query(ResourceCategory).filter_by(slug=slug).first()
            if not category:
                category = ResourceCategory(
                    slug=slug,
                    label=cat_label,
                    icon="", # Icons can be mapped later
                    sendable=True
                )
                db.add(category)
            categories_map[cat_label] = slug
        db.flush()
        
        # Second pass: Create Courses and Resources
        count_courses = 0
        count_resources = 0
        
        for path, res_data in meta_data.items():
            course_title = res_data.get('course_title', 'General')
            
            # [STABILIZATION] Purge Unsorted Materials filter
            if "Unsorted Materials" in course_title:
                continue
                
            quarter = get_quarter_from_path(path)
            
            # [STABILIZATION] Quarter cap filter
            if quarter > 2:
                continue
            
            course_key = f"{course_title}_{quarter}"
            if course_key not in courses_map:
                course_id = slugify(course_key)
                course = db.query(Course).filter_by(id=course_id).first()
                if not course:
                    # Determine strategy
                    strategy = ContentStrategy.WEEK_DRIVEN if res_data.get('week_number') else ContentStrategy.TOPIC_DRIVEN
                    
                    course = Course(
                        id=course_id,
                        institution_id=institution.id,
                        quarter=quarter,
                        title=course_title,
                        folder_path=str(Path(path).parent.parent),
                        content_strategy=strategy,
                        week_count=12, # Standard quarter
                        metadata_blob={
                            "top_level_actions": ["syllabus", "lecture_notes", "exams"],
                            "more_files_actions": ["readings", "assignments", "projects"],
                            "week_actions": ["lecture_notes", "homework", "exams"]
                        }
                    )
                    db.add(course)
                courses_map[course_key] = course
                count_courses += 1
            
            course = courses_map[course_key]
            cat_slug = categories_map.get(res_data.get('category_label', 'Unknown'), 'unknown')
            
            # Create Resource
            # Use path hash for uniqueness if needed, but here we just add
            # Check if exists
            existing_res = db.query(Resource).filter_by(external_path=path).first()
            if not existing_res:
                resource = Resource(
                    course_id=course.id,
                    category_slug=cat_slug,
                    external_path=path,
                    file_hash="legacy_" + uuid.uuid4().hex[:12],
                    title=res_data.get('label', 'Untitled Resource'),
                    week_number=res_data.get('week_number'),
                    status=ResourceStatus.ACTIVE,
                    source_type="system"
                )
                db.add(resource)
                count_resources += 1
                
                # Report progress
                if count_resources % 100 == 0:
                    print(f"... Migrated {count_resources} resources")
        
        db.commit()
        print(f"🏁 Bootstrap Complete!")
        print(f"📊 Courses: {count_courses}")
        print(f"📊 Resources: {count_resources}")
        
    except Exception as e:
        print(f"💥 Bootstrap Failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    bootstrap()
