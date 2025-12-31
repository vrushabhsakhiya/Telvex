from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    columns = [
        'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS email VARCHAR(120)',
        'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS reset_otp VARCHAR(6)',
        'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS reset_otp_expiry TIMESTAMP',
        'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE'
    ]
    
    with db.engine.connect() as conn:
        for sql in columns:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"Executed: {sql}")
            except Exception as e:
                print(f"Skipped {sql}: {e}")
                # Check for transaction failure wrapper if needed
                try: 
                    conn.rollback()
                except:
                    pass
