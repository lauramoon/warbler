"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
            self.assertEqual(msg.user_id, self.testuser.id)

    def test_add_message_redirect(self):
        """After adding a message, what happens?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<a href="/users/profile" class="btn btn-outline-secondary">Edit Profile</a>', html)
            self.assertIn(f'<h4 id="sidebar-username">@{self.testuser.username}</h4>', html)
            self.assertIn('<p>Hello</p>', html)

    def test_add_message_loggedout(self):
        """Test that no message added if no logged-in user"""

        with self.client as c:
            with c.session_transaction() as sess:
                if CURR_USER_KEY in sess:
                    del sess[CURR_USER_KEY]

            resp = c.post("/messages/new", data={"text": "Hello"})
            self.assertEqual(resp.status_code, 302)

            msgs = Message.query.all()
            self.assertEqual(len(msgs), 0)

    def test_add_message_loggedout_redirect(self):
        """Test that attempt to add message if not logged in leads to homepage with flash msg"""
        
        with self.client as c:
            with c.session_transaction() as sess:
                if CURR_USER_KEY in sess:
                    del sess[CURR_USER_KEY]

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

    def test_view_message(self):
        """Test view message"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Add test message to display
            m = Message(text="Test message", user_id=self.testuser.id)
            db.session.add(m)
            db.session.commit()
            
            resp = c.get(f'/messages/{m.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            # Logged-in user viewing own message has delete option
            self.assertIn('<button class="btn btn-outline-danger">Delete</button>', html)
            self.assertIn('<p class="single-message">Test message</p>', html)

    def test_delete_message_success(self):
        """Test successfully deleting message"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Add test message to delete
            m = Message(text="Test message", user_id=self.testuser.id)
            db.session.add(m)
            db.session.commit()

            resp = c.post(f'/messages/{m.id}/delete')
            
            self.assertEqual(resp.status_code, 302)
            
            msgs = Message.query.all()
            self.assertEqual(len(msgs), 0)

    def test_delete_message_success_redirect(self):
        """Test successfully deleting message"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Add test message to delete
            m = Message(text="Test message", user_id=self.testuser.id)
            db.session.add(m)
            db.session.commit()

            resp = c.post(f'/messages/{m.id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<a href="/users/profile" class="btn btn-outline-secondary">Edit Profile</a>', html)
            self.assertIn(f'<h4 id="sidebar-username">@{self.testuser.username}</h4>', html)
            self.assertNotIn('<p>Hello</p>', html)

    def test_delete_message_fail(self):
        """Test message not deleted if user not signed in"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Add test message to try to delete
            m = Message(text="Test message", user_id=self.testuser.id)
            db.session.add(m)
            db.session.commit()
            
            # log out current user
            with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]            

            m = Message.query.all()[0]
            resp = c.post(f'/messages/{m.id}/delete')
            
            self.assertEqual(resp.status_code, 302)
            
            msgs = Message.query.all()
            self.assertEqual(len(msgs), 1)

    def test_delete_message_fail_redirect(self):
        """Test redirect to home on delete attempt if user not signed in"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Add test message to try to delete
            m = Message(text="Test message", user_id=self.testuser.id)
            db.session.add(m)
            db.session.commit()
            
            # log out current user
            with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]            

            m = Message.query.all()[0]
            resp = c.post(f'/messages/{m.id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
