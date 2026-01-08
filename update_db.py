from app import create_app, db
from sqlalchemy import text
import sys

app = create_app()

def update_db():
    with app.app_context():
        with db.engine.connect() as conn:
            # 1. Add bill_created_by to Order
            try:
                print("Attempting to add bill_created_by to order table...")
                conn.execute(text("ALTER TABLE 'order' ADD COLUMN bill_created_by VARCHAR(100)"))
                print("SUCCESS: Added bill_created_by to Order")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print("INFO: bill_created_by already exists in Order")
                else:
                    print(f"Order column error (ignoring if exists): {e}")
            
            # 2. Add bill_creators to ShopProfile
            try:
                print("Attempting to add bill_creators to shop_profile table...")
                # SQLite doesn't have JSON type but SQLAlchemy uses Text/JSON affinity. 
                # Helper for schema might handle JSON as TEXT
                conn.execute(text("ALTER TABLE shop_profile ADD COLUMN bill_creators JSON"))
                print("SUCCESS: Added bill_creators to ShopProfile")
            except Exception as e:
                # If JSON type fails in strict mode or old sqlite, try TEXT
                try:
                    conn.execute(text("ALTER TABLE shop_profile ADD COLUMN bill_creators TEXT"))
                    print("SUCCESS: Added bill_creators to ShopProfile (as TEXT)")
                except Exception as e2:
                    if "duplicate column" in str(e).lower():
                        print("INFO: bill_creators already exists in ShopProfile")
                    else:
                        print(f"ShopProfile column error: {e}")

if __name__ == "__main__":
    update_db()
