"""User signup and login view tests"""

# For explanatory notes on setup, see comments in test_message_views

import os
from unittest import TestCase
from models import db, connect_db, Message, User
from sqlalchemy.exc import IntegrityError, InvalidRequestError

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

# Data for creating new user
USER_DATA = {
    "email": "newtest@test.com",
    "username": "testnewuser",
    "password": "password",
    "image_url": "static/images/test.png"
}

USER_DATA_DUP = {
    "email": "newtest@test.com",
    "username": "testuser",
    "password": "password"
}

app.config['WTF_CSRF_ENABLED'] = False


class UserSignupLoginViewsTestCase(TestCase):
    """Test user sign up and log in views"""

    def setUp(self):
        """Create test client, add sample data."""

        db.session.rollback()
        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_get_signup_form(self):
        """Test sign-up form"""

        with self.client as c:
            with c.session_transaction() as sess:
                if CURR_USER_KEY in sess:
                    del sess[CURR_USER_KEY]

            resp = c.get("/signup")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)
            self.assertIn('<button class="btn btn-primary btn-lg btn-block">Sign me up!</button>', html)

    def test_add_user_success(self):
        """Test post valid data to signup form"""

        with self.client as c:
            with c.session_transaction() as sess:
                if CURR_USER_KEY in sess:
                    del sess[CURR_USER_KEY]

            resp = c.post("/signup", data=USER_DATA)

            self.assertEqual(resp.status_code, 302)

            users = User.query.all()
            self.assertEqual(len(users), 2)

    def test_add_user_success_redirect(self):
        """Test post valid data to signup form"""

        with self.client as c:
            with c.session_transaction() as sess:
                if CURR_USER_KEY in sess:
                    del sess[CURR_USER_KEY]

            resp = c.post("/signup", data=USER_DATA, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>@testnewuser</p>', html)

    def test_add_user_duplicate_username(self):
        """Test attempt to signup with duplicate username"""

        with self.client as c:
            with c.session_transaction() as sess:
                if CURR_USER_KEY in sess:
                    del sess[CURR_USER_KEY]

            with self.assertRaises(InvalidRequestError):

                resp = c.post("/signup", data=USER_DATA_DUP)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn ('<div class="alert alert-danger">Username already taken</div>', html)

                users = User.query.all()
                self.assertEqual(len(users), 1)


    def test_login_form_get(self):
        """Test login form loads"""

        with self.client as c:
            resp = c.get("/login")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Welcome back.</h2>', html)
            
    def test_login_valid_credentials(self):
        """Test login post with valid credentials"""

        with self.client as c:
            resp = c.post("/login", data={ "username": "testuser", "password": "testuser" })

            self.assertEqual(resp.status_code, 302)

    def test_login_valid_credentials_redirect(self):
        """Test login post with valid credentials, follow redirect"""

        with self.client as c:
            resp = c.post("/login", 
                          data={ "username": "testuser", "password": "testuser" },
                          follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn ('<div class="alert alert-success">Hello, testuser!</div>', html)
            self.assertIn('<p>@testuser</p>', html)

    def test_login_invalid_credentials(self):
        """Test login post with invalid credentials"""

        with self.client as c:
            resp = c.post("/login", data={ "username": "testuser", "password": "incorrect" })
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn ('<div class="alert alert-danger">Invalid credentials.</div>', html)
            self.assertIn('<h2 class="join-message">Welcome back.</h2>', html)
