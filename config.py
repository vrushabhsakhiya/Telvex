import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key_taivex'
    # Use SQLite for local development, PostgreSQL for production
    # TO USE POSTGRES: Uncomment the line below and fill in your details:
    # NOTE: Password '@VrU(846)' contains special chars, so we use URL encoding (%40 for @)
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:%40VrU(846)@localhost/taivex'
    
    
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail Settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    # Replace with your actual Gmail credentials
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your-email@gmail.com' 
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your-app-password'
