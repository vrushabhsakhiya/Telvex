from app import create_app, db
from models import User

app = create_app()

with app.app_context():
    # Fix Admin
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print("Found admin user.")
        if not admin.is_verified:
            admin.is_verified = True
            print("Set admin to verified.")
        admin.email = 'vrushabhsakhiya@gmail.com'
        print("Set admin email.")
            
    # Fix Staff
    staff = User.query.filter_by(username='staff').first()
    if staff:
        print("Found staff user.")
        if not staff.is_verified:
            staff.is_verified = True
            print("Set staff to verified.")
        staff.email = 'vrushabhsakhiya@gmail.com'
        print("Set staff email.")

    try:
        db.session.commit()
        print("Changes committed.")
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
