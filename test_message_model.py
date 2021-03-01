"""Message model tests"""

import os
from unittest import TestCase
from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app
db.create_all()

# Data for creating test users

USER_1_DATA = {
    "email": "test@test.com",
    "username": "test1user",
    "password": "HASHED_PASSWORD"
}

USER_2_DATA = {
    "email": "test2@test.com",
    "username": "test2user",
    "password": "HASHED_PASSWORD"
}


class MessageModelTestCase(TestCase):
    """Test message model."""

    def setUp(self):
        """Clear any errors, clear tables, create test client."""

        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Message.query.delete()

        self.client = app.test_client()

    def test_message_model(self):
        """Does the basic model work?"""

        u = User(**USER_1_DATA)
        db.session.add(u)
        db.session.commit()

        m = Message(text="Test message", user_id=u.id)
        db.session.add(m)
        db.session.commit()

        self.assertEqual(m.text, "Test message")
        self.assertEqual(m.user_id, u.id)
        self.assertEqual(m.user, u)
        self.assertTrue(m.timestamp)
        self.assertTrue(m.id)

    def test_message_like(self):
        """Test one user liking another user's message"""

        u1 = User(**USER_1_DATA)
        u2 = User(**USER_2_DATA)
        db.session.add_all([u1, u2])
        db.session.commit()

        m = Message(text="Test message", user_id=u1.id)
        u2.likes.append(m)
        db.session.commit()

        likes = Likes.query.all()

        self.assertIn(m, u2.likes)
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].user_id, u2.id)
        self.assertEqual(likes[0].message_id, m.id)
        self.assertIn(u2, m.liked_by)
        self.assertNotIn(u1, m.liked_by)

    def test_message_unlike(self):
        """Test that removing message from user's likes removes the Like"""

        u1 = User(**USER_1_DATA)
        u2 = User(**USER_2_DATA)
        db.session.add_all([u1, u2])
        db.session.commit()

        m = Message(text="Test message", user_id=u1.id)
        u2.likes.append(m)
        db.session.commit()

        # The above tested to show message liked by u2; now remove and test
        u2.likes.remove(m)
        db.session.commit()

        likes = Likes.query.all()

        self.assertNotIn(m, u2.likes)
        self.assertEqual(len(likes), 0)
        self.assertNotIn(u2, m.liked_by)
