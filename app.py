from flask import Flask
from config import Config
from models import db
from routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Plugins
    db.init_app(app)

    # --- I18n / Translations ---
    translations = {
        'en': {
            'dashboard': 'Dashboard',
            'customers': 'Customers',
            'orders': 'Orders',
            'bills': 'Bills',
            'measurements': 'Measurements',
            'reminders': 'Reminders',
            'users': 'Users',
            'history': 'History',
            'settings': 'Settings',
            'sign_out': 'Sign Out',
            'total_customers': 'Total Customers',
            'all_time_revenue': 'All Time Revenue',
            'pending_balance': 'Pending Balance',
            'due_today': 'Due Today',
            'recent_activity': 'Recent Activity',
            'today_customers': 'Today',
            'this_week': 'This Week',
            # Common
            'name': 'Name',
            'mobile': 'Mobile',
            'status': 'Status',
            'date': 'Date',
            'actions': 'Actions',
            'search': 'Search',
            'add_new': 'Add New',
            'delete': 'Delete',
            'edit': 'Edit',
            'save': 'Save',
            'cancel': 'Cancel',
            'id': 'ID',
            'photo': 'Photo',
            'gender': 'Gender',
            # Customers
            'last_visit': 'Last Visit',
            'total_orders': 'Total Orders',
            'male': 'Male',
            'female': 'Female',
            'all_paid': 'All Paid',
            # Orders
            'order_id': 'Order ID',
            'delivery_date': 'Delivery Date',
            'items': 'Items',
            'total_amount': 'Total Amount',
            'advance': 'Advance',
            'balance': 'Balance',
            'worker': 'Worker',
            'delivered': 'Delivered',
            'working': 'Working',
            'cancelled': 'Cancelled'
        },
        'hi': {
            'dashboard': 'डैशबोर्ड',
            'customers': 'ग्राहक',
            'orders': 'ऑर्डर',
            'bills': 'बिल',
            'measurements': 'माप',
            'reminders': 'रिमाइंडर',
            'users': 'कर्मचारी',
            'history': 'इतिहास',
            'settings': 'सेटिंग्स',
            'sign_out': 'साइन आउट',
            'total_customers': 'कुल ग्राहक',
            'all_time_revenue': 'कुल कमाई',
            'pending_balance': 'बकाया राशि',
            'due_today': 'आज की डिलीवरी',
            'recent_activity': 'हाल की गतिविधि',
            'today_customers': 'आज',
            'this_week': 'इस सप्ताह',
            # Common
            'name': 'नाम',
            'mobile': 'मोबाइल',
            'status': 'स्थिति',
            'date': 'दिनांक',
            'actions': 'क्रियाएँ',
            'search': 'खोजें',
            'add_new': 'नया जोड़ें',
            'delete': 'हटाएं',
            'edit': 'संपादित करें',
            'save': 'सहेजें',
            'cancel': 'रद्द करें',
            'id': 'आईडी',
            'photo': 'फोटो',
            'gender': 'लिंग',
            # Customers
            'last_visit': 'अंतिम विजिट',
            'total_orders': 'कुल ऑर्डर',
            'male': 'पुरुष',
            'female': 'महिला',
            'all_paid': 'पूर्ण भुगतान',
            # Orders
            'order_id': 'ऑर्डर आईडी',
            'delivery_date': 'डिलीवरी दिनांक',
            'items': 'आइटम',
            'total_amount': 'कुल राशि',
            'advance': 'एडवांस',
            'balance': 'बकाया',
            'worker': 'कारीगर',
            'delivered': 'डिलीवर किया',
            'working': 'कार्य प्रगति पर',
            'cancelled': 'रद्द'
        },
        'gu': {
            'dashboard': 'ડેશબોર્ડ',
            'customers': 'ગ્રાહકો',
            'orders': 'ઓર્ડર',
            'bills': 'બિલ',
            'measurements': 'માપ',
            'reminders': 'રિમાઇન્ડર',
            'users': 'વપરાશકર્તાઓ',
            'history': 'ઇતિહાસ',
            'settings': 'સેટિંગ્સ',
            'sign_out': 'લૉગ આઉટ',
            'total_customers': 'કુલ ગ્રાહકો',
            'all_time_revenue': 'કુલ આવક',
            'pending_balance': 'બાકી રકમ',
            'due_today': 'આજે આપવાનાં',
            'recent_activity': 'તાજેતરની પ્રવૃત્તિ',
            'today_customers': 'આજે',
            'this_week': 'આ અઠવાડિયે',
            # Common
            'name': 'નામ',
            'mobile': 'મોબાઇલ',
            'status': 'સ્થિતિ',
            'date': 'તારીખ',
            'actions': 'ક્રિયાઓ',
            'search': 'શોધો',
            'add_new': 'નવું ઉમેરો',
            'delete': 'કાઢી નાખો',
            'edit': 'ફેરફાર કરો',
            'save': 'સાચવો',
            'cancel': 'રદ કરો',
            'id': 'આઈડી',
            'photo': 'ફોટો',
            'gender': 'લિંગ',
            # Customers
            'last_visit': 'છેલ્લી મુલાકાત',
            'total_orders': 'કુલ ઓર્ડર',
            'male': 'પુરુષ',
            'female': 'સ્ત્રી',
            'all_paid': 'બધું ચૂકવાઈ ગયું',
            # Orders
            'order_id': 'ઓર્ડર આઈડી',
            'delivery_date': 'ડિલિવરી તારીખ',
            'items': 'વસ્તુઓ',
            'total_amount': 'કુલ રકમ',
            'advance': 'એડવાન્સ',
            'balance': 'બાકી',
            'worker': 'કારીગર',
            'delivered': 'ડિલિવર થયું',
            'working': 'કામ ચાલુ',
            'cancelled': 'રદ થયેલ'
        }
    }

    @app.context_processor
    def inject_i18n():
        from flask import session, request
        # Get lang from Query or Session, default 'en'
        lang = request.args.get('lang', session.get('lang', 'en'))
        session['lang'] = lang # Persist
        
        def t(key):
            return translations.get(lang, translations['en']).get(key, key)
        
        return dict(t=t, current_lang=lang)
    
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
