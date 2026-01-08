import sqlite3
import os

db_path = 'instance/talvex.db'
if not os.path.exists(db_path):
    db_path = 'talvex.db'

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    # try root
    if os.path.exists('talvex.db'):
        db_path = 'talvex.db'

print(f"Checking DB: {db_path}")
try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("PRAGMA table_info(customer)")
    cols = [row[1] for row in c.fetchall()]
    print("Columns:", cols)
    
    if 'photo' not in cols:
        print("Adding photo column...")
        c.execute("ALTER TABLE customer ADD COLUMN photo VARCHAR(200)")
        conn.commit()
        print("Photo column added.")
    else:
        print("Photo column exists.")

    # Also check if user complains about duplicate mobile
    # We can't drop unique constraint easily in SQLite, 
    # but we can advise user if that's the issue.
    
except Exception as e:
    print("Error:", e)
finally:
    if 'conn' in locals():
        conn.close()
