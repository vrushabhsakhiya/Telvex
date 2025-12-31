from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    print("--- Current Users ---")
    users = User.query.all()
    for u in users:
        print(f"User: {u.username}, Role: {u.role}, ID: {u.id}")

    print("\n--- Resetting Admin Password ---")
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.set_password('admin123')
        db.session.commit()
        print("Success: Password for 'admin' reset to 'admin123'.")
    else:
        print("Error: User 'admin' not found. Creating it...")
        admin = User(username='admin', role='master')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Success: User 'admin' created with password 'admin123'.")
