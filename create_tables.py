from app import create_app
from models import db, ShopProfile
import os

app = create_app()

with app.app_context():
    print("Creating all tables...")
    db.create_all()
    print("Tables created.")
    
    # Check if ShopProfile exists
    import sqlite3
    db_path = os.path.join('instance', 'taivex.db')
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shop_profile';")
        if cur.fetchone():
            print("ShopProfile table CONFIRMED exists.")
        else:
            print("ShopProfile table STILL MISSING.")
        conn.close()
