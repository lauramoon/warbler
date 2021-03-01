"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from models import db, User, Message, Follows
from forms import UserEditForm
from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

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


class UserModelTestCase(TestCase):
    """Test user model."""

    def setUp(self):
        """Clear any errors, clear tables, create test client."""

        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(**USER_1_DATA)

        db.session.add(u)
        db.session.commit()

        # User should have no messages, no followers, no following, and no likes
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.following), 0)
        self.assertEqual(len(u.likes), 0)

        # User should have the default image and header image
        self.assertEqual(u.image_url, "/static/images/default-pic.png")
        self.assertEqual(u.header_image_url, "/static/images/warbler-hero.jpg")

        # Check user __repr__
        self.assertEqual(repr(u), f"<User #{u.id}: test1user, test@test.com>")

    def test_user_follows(self):
        """Do user folows/following work?"""

        # set up user 1 to follow user 2
        u1 = User(**USER_1_DATA)
        u2 = User(**USER_2_DATA)
        u1.following = [u2]

        db.session.add_all([u1,u2])
        db.session.commit()

        self.assertIn(u2, u1.following)
        self.assertIn(u1, u2.followers)
        self.assertTrue(u1.is_following(u2))
        self.assertTrue(u2.is_followed_by(u1))
        self.assertNotIn(u2, u1.followers)
        self.assertNotIn(u1, u2.following)
        self.assertFalse(u1.is_followed_by(u2))
        self.assertFalse(u2.is_following(u1))

    def test_user_update(self):
        """Does the update function work?"""

        u = User(**USER_1_DATA)

        db.session.add(u)
        db.session.commit()

        with app.test_request_context('/'):
            form = UserEditForm(obj=u)
            form.location.data = "Planet Earth"
            form.email.data = "new_test@test.com"
            u.update(form)
            db.session.commit()

            # check that u updated with new data, other data unaffected
            self.assertEqual(u.email, "new_test@test.com")
            self.assertEqual(u.location, "Planet Earth")
            self.assertEqual(u.username, "test1user")
            self.assertEqual(u.image_url, "/static/images/default-pic.png")

    def test_user_signup_valid(self):
        """Does the signup function work with valid credentials?"""

        u = User.signup('signup_test', 'signup@test.com', 'password', '/static/images/test.jpg')
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

        # User should have the default header image
        self.assertEqual(u.header_image_url, "/static/images/warbler-hero.jpg")

        # And the provided user image
        self.assertEqual(u.image_url, '/static/images/test.jpg')

        # Check user __repr__
        self.assertEqual(repr(u), f"<User #{u.id}: signup_test, signup@test.com>")

    def test_user_signup_missing(self):
        """Does the signup fail with required field missing?"""

        with self.assertRaises(ValueError):
            u = User.signup('signup_test', 'signup@test.com', '', "/static/images/default-pic.png")

    def test_user_signup_duplicate_username(self):
        """Does the signup fail with non-unique username?"""

        u1 = User(**USER_1_DATA)
        db.session.add(u1)
        db.session.commit()

        with self.assertRaises(IntegrityError):
            u = User.signup('test1user', 'signup@test.com', 'password', "/static/images/default-pic.png")
            db.session.commit()

    def test_user_authenticate_valid(self):
        """Does authenticate work with valid credentials"""

        # Need to have real hashed and salted password in database
        u = User.signup('auth_test', 'test@test.com', 'password', '/static/images/test.jpg')
        db.session.add(u)
        db.session.commit()

        u1 = User.authenticate('auth_test', 'password')

        self.assertEqual(u1.username, 'auth_test')
        self.assertEqual(u1.email, 'test@test.com')
        self.assertEqual(u1.header_image_url, "/static/images/warbler-hero.jpg")

    def test_user_authenticate_invalid_username(self):
        """Does authenticate fail with invalid username"""

        # Need to have real hashed and salted password in database
        u = User.signup('auth_test', 'test@test.com', 'password', '/static/images/test.jpg')
        db.session.add(u)
        db.session.commit()

        u1 = User.authenticate('auth_test_no', 'password')

        self.assertFalse(u1)

    def test_user_authenticate_invalid_password(self):
        """Does authenticate fail with invalid password"""

        # Need to have real hashed and salted password in database
        u = User.signup('auth_test', 'test@test.com', 'password', '/static/images/test.jpg')
        db.session.add(u)
        db.session.commit()

        u1 = User.authenticate('auth_test', 'passwordy')

        self.assertFalse(u1)