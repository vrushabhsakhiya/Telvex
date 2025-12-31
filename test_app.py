

import sys
import os
sys.path.append(os.getcwd())
import unittest
from app import create_app, db
from models import User, Customer
from flask_login import login_user

class TaivexTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        

        import uuid
        import random
        self.random_sf = str(random.randint(100000, 999999))
        self.username = f'test_admin_{self.random_sf}'
        self.mobile = f'99988{self.random_sf}'

        with self.app.app_context():
            # Create fresh test user with unique name
            user = User(username=self.username, role='master')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)


    def test_1_login_logout(self):
        rv = self.login(self.username, 'testpass')
        self.assertIn(b'Welcome back', rv.data)
        rv = self.logout()
        self.assertIn(b'You have been logged out', rv.data)

    def test_2_dashboard_access_protected(self):
        self.logout()
        rv = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'Please log in to access this page', rv.data)

    def test_3_customer_creation(self):
        self.login(self.username, 'testpass')
        rv = self.client.post('/customers', data=dict(
            name='Test Customer',
            mobile=self.mobile,
            gender='male'
        ), follow_redirects=True)
        self.assertIn(b'Customer added successfully', rv.data)
        
        with self.app.app_context():
            c = Customer.query.filter_by(mobile=self.mobile).first()
            self.assertIsNotNone(c)
            # Cleanup only this customer if possible, or leave it (Postgres handles it)
            # db.session.delete(c) 
            # db.session.commit()

if __name__ == '__main__':
    unittest.main()
