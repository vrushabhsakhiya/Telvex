from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Inspecting all tables...")
    inspector = db.inspect(db.engine)
    for table_name in inspector.get_table_names():
        print(f"\nTable: {table_name}")
        for column in inspector.get_columns(table_name):
            print(f"- {column['name']} ({column['type']})")
