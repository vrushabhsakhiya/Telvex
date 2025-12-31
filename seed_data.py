from app import create_app, db
from models import Customer, Order, Category, Measurement
from datetime import datetime, timedelta
import random

def seed():
    app = create_app()
    with app.app_context():
        # Clear existing? 
        # db.drop_all() 
        # db.create_all()
        # Better just add to existing if empty.
        
        # 100k Bulk Seed
        import random
        import string

        print("Seeding 100,000 Sample Data...")
        
        batch_size = 1000
        total_records = 100000
        
        statuses = ['Working', 'Ready to Deliver', 'Delivered']
        
        customers_batch = []
        orders_batch = []
        
        for i in range(total_records):
            # Random Data
            name = f"Customer {random.randint(1000000, 9999999)}"
            mobile = f"{random.randint(6000000000, 9999999999)}"
            gender = random.choice(['male', 'female'])
            
            # Date: Random in last 2 years
            days_ago = random.randint(0, 730)
            created = datetime.utcnow() - timedelta(days=days_ago)
            
            c = Customer(
                name=name,
                mobile=mobile,
                gender=gender,
                created_date=created,
                address=f"Address {i}, City",
                notes="Bulk Seed"
            )
            customers_batch.append(c)
            
            # Create Order for this customer
            status = random.choice(statuses)
            start_date = created.date()
            delivery = start_date + timedelta(days=random.randint(3, 15))
            
            total = random.randint(500, 20000)
            advance = total if status == 'Delivered' else total // 2
            balance = total - advance
            
            # We need customer ID for order, but valid bulk insert with relationships is tricky without flush.
            # Efficient way for massive data: 
            # 1. Add customers, commit. 
            # 2. But to link orders, we need IDs. 
            # Simpler approach: Add both to session, flush/commit in batches.
            
            db.session.add(c)
            
            # Flush every batch to get IDs? No, too slow.
            # Alternative: Just add objects, SQLAlchemy handles FKs if we assign object to relationship?
            # Yes: Order(customer=c)
            
            o = Order(
                customer=c, # Relationship assignment
                items=[{"name": "Shirt" if gender == 'male' else "Kurti", "qty": 1, "cost": total}],
                start_date=start_date,
                delivery_date=delivery,
                work_status=status,
                total_amt=total,
                advance=advance,
                balance=balance,
                created_at=created + timedelta(minutes=30)
            )
            db.session.add(o)
            
            if i % batch_size == 0:
                db.session.commit()
                print(f"Committed {i} records...")
                
        db.session.commit()
        print(f"Successfully added {total_records} customers and orders.")

if __name__ == '__main__':
    seed()
