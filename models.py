from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
mail = Mail()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(256))
    
    # 2FA / OTP Fields
    otp_code = db.Column(db.String(6))
    otp_expiry = db.Column(db.DateTime)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Security / Locking
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    # Role
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    shop_profile = db.relationship('ShopProfile', backref='user', uselist=False)
    customers = db.relationship('Customer', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    measurements = db.relationship('Measurement', backref='user', lazy=True)
    reminders = db.relationship('Reminder', backref='user', lazy=True)
    categories = db.relationship('Category', backref='user', lazy=True) # Custom categories

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class ShopProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Make nullable for migration, then enforce later
    shop_name = db.Column(db.String(100))
    address = db.Column(db.Text)
    mobile = db.Column(db.String(20))
    gst_no = db.Column(db.String(20))
    terms = db.Column(db.Text)
    upi_id = db.Column(db.String(50))
    logo = db.Column(db.String(200))
    bill_creators = db.Column(db.JSON, default=list) # List of staff/creator names

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # If None, it's a System/Global Category
    name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False) # 'male', 'female'
    is_custom = db.Column(db.Boolean, default=False)
    fields_json = db.Column(db.JSON, default=list) # List of measurement labels

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(20), unique=True, nullable=False)
    alt_mobile = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    area = db.Column(db.String(100))
    whatsapp = db.Column(db.Boolean, default=False)
    gender = db.Column(db.String(10))
    photo = db.Column(db.String(200))
    notes = db.Column(db.Text)
    style_pref = db.Column(db.String(200))
    birthday = db.Column(db.Date)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_visit = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship('Order', backref='customer', lazy=True)
    measurements = db.relationship('Measurement', backref='customer', lazy=True)

    @property
    def total_pending(self):
        return sum(o.balance for o in self.orders)

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    measurements_json = db.Column(db.JSON, nullable=False) # Key-Value pairs
    remarks = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    category = db.relationship('Category', backref='measurements', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    items = db.Column(db.JSON, nullable=False) # List of dicts: {name, qty, cost, etc}
    
    start_date = db.Column(db.Date)
    delivery_date = db.Column(db.Date)
    
    work_status = db.Column(db.String(20), default='Working') # Working, Ready, Delivered
    payment_status = db.Column(db.String(20), default='Pending') # Pending, Partial, Paid
    
    total_amt = db.Column(db.Float, default=0.0)
    advance = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float, default=0.0)
    payment_mode = db.Column(db.String(50)) # Cash, UPI, Card
    bill_created_by = db.Column(db.String(100)) # Name of staff who created bill
    
    trial_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    type = db.Column(db.String(50)) # 'measurement', 'delivery', 'payment'
    due_date = db.Column(db.Date)
    due_time = db.Column(db.Time)
    message = db.Column(db.String(255))
    status = db.Column(db.String(20), default='Pending') # Pending, Sent, Dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer_rel = db.relationship('Customer', backref='reminders')
    order_rel = db.relationship('Order', backref='reminders')
