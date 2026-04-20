
import sqlite3
import os

db_path = 'data/academic_hub.db'

def inspect_sqlite():
    if not os.path.exists(db_path):
        print(f"SQLite file not found at {db_path}")
        return
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        for table in tables:
            t_name = table[0]
            cursor.execute(f"SELECT count(*) FROM {t_name}")
            count = cursor.fetchone()[0]
            print(f"Table {t_name}: {count} rows")
            
            # Show columns for important tables
            if t_name in ['courses', 'resources', 'institutions']:
                cursor.execute(f"PRAGMA table_info({t_name})")
                cols = cursor.fetchall()
                print(f"  Columns: {[c[1] for c in cols]}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_sqlite()
