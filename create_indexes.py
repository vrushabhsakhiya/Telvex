from app import app, db
from sqlalchemy import text

def create_indexes():
    with app.app_context():
        print("Creating indexes...")
        try:
            # Order Indexes
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_order_delivery_status ON "order" (delivery_date, work_status)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_order_created_at ON "order" (created_at DESC)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_customer_total_spend ON "order" (customer_id, total_amt)'))
            
            # Commit
            db.session.commit()
            print("Successfully created indexes.")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating indexes: {e}")

if __name__ == "__main__":
    create_indexes()
