from flask import Flask
from config import Config
from models import db
from routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Plugins
    db.init_app(app)
    
    from models import mail
    mail.init_app(app)
    
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)
    
    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Routes
    with app.app_context():
        register_routes(app)
        
        # Create DB Tables if they don't exist
        db.create_all()
        
        # --- Seed Data ---
        from models import Category, User
        if not Category.query.first():
            print("Seeding Categories...")
            categories = [
                Category(name='Shirt', gender='male', fields_json=['Length', 'Chest', 'Shoulder', 'Sleeve', 'Collar', 'Cuff']),
                Category(name='Pant', gender='male', fields_json=['Length', 'Waist', 'Seat', 'Thigh', 'Knee', 'Bottom']),
                Category(name='Kurta', gender='male', fields_json=['Length', 'Chest', 'Shoulder', 'Sleeve']),
                Category(name='Blouse', gender='female', fields_json=['Length', 'Chest', 'Waist', 'Shoulder', 'Sleeve', 'Front Depth', 'Back Depth']),
                Category(name='Kurti', gender='female', fields_json=['Length', 'Chest', 'Waist', 'Hip', 'Shoulder']),
                Category(name='Salwar', gender='female', fields_json=['Length', 'Waist', 'Hip', 'Bottom'])
            ]
            db.session.bulk_save_objects(categories)
            db.session.commit()
            
        if not User.query.filter_by(username='admin').first():
            # In production use hashed passwords!
            master = User(username='admin', role='master')
            master.set_password('admin123')
            db.session.add(master)
            db.session.commit()

        if not User.query.filter_by(username='staff').first():
            staff = User(username='staff', role='staff')
            staff.set_password('staff123')
            db.session.add(staff)
            db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
