import sys
import os
sys.path.append(os.getcwd())
from app import create_app, db
from sqlalchemy import text

app = create_app()

def check_connection():
    print("Testing PostgreSQL Connection...")
    with app.app_context():
        try:
            # 1. Connection Check
            db.session.execute(text('SELECT 1'))
            print("✅ Database Connection: SUCCESS")
            
            # 2. Configuration Check
            uri = app.config['SQLALCHEMY_DATABASE_URI']
            if 'postgresql' in uri:
                print(f"✅ Protocol Check: Using PostgreSQL ({uri.split('@')[1]})")
            else:
                print(f"❌ Protocol Check: NOT using PostgreSQL! ({uri})")
                
            # 3. Table Check
            result = db.session.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"))
            count = result.scalar()
            print(f"✅ Schema Check: Found {count} tables in public schema.")
            
        except Exception as e:
            print(f"❌ CONNECTION FAILED: {e}")

if __name__ == "__main__":
    check_connection()
