from flask import current_app
from itsdangerous import URLSafeTimedSerializer

def generate_bill_token(bill_id):
    """Generates a secure token for sharing a bill."""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(bill_id, salt='bill-view')

def verify_bill_token(token, max_age=2592000): # 30 days
    """Verifies the bill token and returns bill_id if valid."""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        bill_id = s.loads(token, salt='bill-view', max_age=max_age)
        return bill_id
    except:
        return None
