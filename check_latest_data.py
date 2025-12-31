
import sys
import os
sys.path.append(os.getcwd())
try:
    from app import create_app
    from models import Customer, Order, User
    from sqlalchemy import text
except ImportError:
    # If app import fails, try manual setup (fallback)
    pass

app = create_app()

def check_data():
    with app.app_context():
        print("-" * 50)
        print("CONNECTING TO DATABASE: " + app.config['SQLALCHEMY_DATABASE_URI'])
        print("-" * 50)
        
        # 1. Check Row Counts
        user_count = User.query.count()
        cust_count = Customer.query.count()
        order_count = Order.query.count()
        
        print(f"Total Users:      {user_count}")
        print(f"Total Customers:  {cust_count}")
        print(f"Total Orders:     {order_count}")
        print("-" * 50)

        # 2. Show Latest Customers
        print("LATEST 5 CUSTOMERS:")
        recent_customers = Customer.query.order_by(Customer.id.desc()).limit(5).all()
        if not recent_customers:
            print("  (No customers found)")
        for c in recent_customers:
            print(f"  [ID: {c.id}] Name: {c.name} | Mobile: {c.mobile}")

        print("-" * 50)
        
        # 3. Show Latest Orders
        print("LATEST 5 ORDERS:")
        recent_orders = Order.query.order_by(Order.id.desc()).limit(5).all()
        if not recent_orders:
            print("  (No orders found)")
        for o in recent_orders:
            cust_name = o.customer.name if o.customer else "Unknown"
            print(f"  [ID: {o.id}] Cust: {cust_name} | Status: {o.work_status} | Bal: {o.balance}")
            
if __name__ == "__main__":
    check_data()
