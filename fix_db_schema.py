
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Check if column exists first (to avoid error if run multiple times)
        # But easier to just try adding it.
        # Postgres requires double quotes for "order" because it's a reserved keyword.
        # Also "user" might be reserved or just need quoting.
        
        print("Attempting to add 'created_by' column to 'order' table...")
        
        # Using raw SQL for migration since we don't have Flask-Migrate set up fully accessible here
        # Adding column as Nullable first
        sql = text('ALTER TABLE "order" ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES "user" (id);')
        
        db.session.execute(sql)
        db.session.commit()
        print("Column 'created_by' added successfully.")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
