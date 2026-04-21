from dotenv import load_dotenv
load_dotenv()
from backend.api.database_postgresql import SessionLocal
from backend.api.models import Institution
db = SessionLocal()
inst = db.query(Institution).filter_by(slug="sit").first()
if inst:
    print("Updating quarter labels to restrict to Q1 and Q2...")
    # Preserve other metadata but restrict quarters
    meta = dict(inst.metadata_blob)
    meta["quarter_labels"] = {
        "1": "Quarter 1",
        "2": "Quarter 2"
    }
    inst.metadata_blob = meta
    db.commit()
    print("SUCCESS: Quarters restricted.")
else:
    print("ERROR: Institution not found.")
