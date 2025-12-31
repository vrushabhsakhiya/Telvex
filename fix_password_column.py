
import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import create_engine, text
from config import Config

def fix_column():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    with engine.connect() as conn:
        with conn.begin():
            # Check length if possible, or just force alter
            print("Altering user table password_hash column length...")
            conn.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(256);'))
            print("Done.")

if __name__ == '__main__':
    fix_column()
