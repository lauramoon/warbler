"""User view tests"""

# For explanatory notes on setup, see comments in test_message_views

import os
from urllib.parse import urlparse
from unittest import TestCase
from models import db, connect_db, Message, User
from flask import jsonify

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

USER_2_DATA = {
    "email": "test2@test.com",
    "username": "test2user",
    "password": "HASHED_PASSWORD"
}

app.config['WTF_CSRF_ENABLED'] = False


class UserViewsTestCase(TestCase):
    """Test user views"""

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

    def test_view_user_page(self):
        """Test that signed-in viewer can view own page"""

        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.testuser.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@testuser</h4>', html)

    def test_view_other_user_page(self):
        """Test that signed-in viewer can view another user's page"""

        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            new_user = User(**USER_DATA)
            db.session.add(new_user)
            db.session.commit()

            resp = c.get(f'/users/{new_user.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@testnewuser</h4>', html)

    def test_view_own_following(self):
        """Test that signed-in viewer can view those user is following"""

        with self.client as c:
            other_user = User(**USER_DATA)
            db.session.add(other_user)
            db.session.commit()

            self.testuser.following.append(other_user)
            db.session.commit()

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.testuser.id}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@testuser</h4>', html)
            self.assertIn('<p>@testnewuser</p>', html)
            self.assertIn('<button class="btn btn-primary btn-sm">Unfollow</button>', html)
            self.assertNotIn('<button class="btn btn-outline-primary btn-sm">Follow</button>', html)

    def test_view_own_followed_by(self):
        """Test that signed-in viewer can view those user is followed by"""

        with self.client as c:
            other_user = User(**USER_DATA)
            db.session.add(other_user)
            db.session.commit()

            self.testuser.followers.append(other_user)
            db.session.commit()

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.testuser.id}/followers')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@testuser</h4>', html)
            self.assertIn('<p>@testnewuser</p>', html)
            self.assertNotIn('<button class="btn btn-primary btn-sm">Unfollow</button>', html)
            self.assertIn('<button class="btn btn-outline-primary btn-sm">Follow</button>', html)

    def test_view_other_following(self):
        """Test that signed-in viewer can view those another user is following"""

        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            other_user = User(**USER_DATA)
            other_user_2 = User(**USER_2_DATA)
            db.session.add_all([other_user, other_user_2])
            db.session.commit()

            other_user.following.append(other_user_2)
            db.session.commit()

            resp = c.get(f'/users/{other_user.id}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@testnewuser</h4>', html)
            self.assertIn('<p>@test2user</p>', html)
            self.assertNotIn('<button class="btn btn-primary btn-sm">Unfollow</button>', html)
            self.assertIn('<button class="btn btn-outline-primary btn-sm">Follow</button>', html)

    def test_view_other_followers(self):
        """Test that signed-in viewer can view those another user is followed by"""

        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            other_user = User(**USER_DATA)
            other_user_2 = User(**USER_2_DATA)
            db.session.add_all([other_user, other_user_2])
            db.session.commit()

            other_user.following.append(other_user_2)
            db.session.commit()

            resp = c.get(f'/users/{other_user_2.id}/followers')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@test2user</h4>', html)
            self.assertIn('<p>@testnewuser</p>', html)
            self.assertNotIn('<button class="btn btn-primary btn-sm">Unfollow</button>', html)
            self.assertIn('<button class="btn btn-outline-primary btn-sm">Follow</button>', html)

    def test_no_view_following_logged_out(self):
        """Test that a 'following' page cannot be viewed if the viewer is logged out"""

        with self.client as c:

            resp = c.get(f'/users/{self.testuser.id}/following')

            self.assertEqual(resp.status_code, 302)

    def test_no_view_following_logged_out_redirect(self):
        """Test that a 'following' page redirects to home if the viewer is logged out"""

        with self.client as c:

            resp = c.get(f'/users/{self.testuser.id}/following', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

    def test_no_view_followers_logged_out(self):
        """Test that a 'followers' page cannot be viewed if the viewer is logged out"""

        with self.client as c:

            resp = c.get(f'/users/{self.testuser.id}/followers')

            self.assertEqual(resp.status_code, 302)

    def test_no_view_followers_logged_out_redirect(self):
        """Test that a 'followers' page redirects to home if the viewer is logged out"""

        with self.client as c:

            resp = c.get(f'/users/{self.testuser.id}/followers', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

    def test_click_follow_on_user_list(self):
        """Test that clicking 'follow' adds to following and redirects"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            testuser = User.query.filter(User.username=='testuser').one()
            other_user = User(**USER_DATA)
            db.session.add(other_user)
            db.session.commit()

            resp = c.post(f'/users/follow/{other_user.id}', 
                          data={"url_redirect": "/fake_redirect"})
            
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(urlparse(resp.location).path, "/fake_redirect")

            self.assertIn(other_user, testuser.following)
            self.assertIn(testuser, other_user.followers)

    def test_click_follow_on_user_list_redirect(self):
        """Test that clicking 'follow' on '/users' redirects to followed user's page"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            other_user = User(**USER_DATA)
            db.session.add(other_user)
            db.session.commit()

            # without the line below, get detached instance error
            # only needed when follow_redirect=True
            other_user = User.query.filter(User.username=='testnewuser').one()

            resp = c.post(f'/users/follow/{other_user.id}', 
                        data={"url_redirect": f"/users/{other_user.id}"}, 
                        follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@testnewuser</h4>', html)
            self.assertIn('<button class="btn btn-primary btn-sm">Unfollow</button>', html)
            self.assertNotIn('<button class="btn btn-outline-primary btn-sm">Follow</button>', html)


    def test_follow_url_on_user_detail(self):
        """Check for 'follow' option on user card on different user's following page"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            other_user = User(**USER_DATA)
            other_user_2 = User(**USER_2_DATA)
            db.session.add_all([other_user, other_user_2])
            db.session.commit()

            other_user.following.append(other_user_2)
            db.session.commit()

            url = f'/users/{other_user.id}/following'
            resp = c.get(url)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@testnewuser</h4>', html)
            self.assertIn('<p>@test2user</p>', html)
            self.assertNotIn('<button class="btn btn-primary btn-sm">Unfollow</button>', html)
            self.assertIn('<button class="btn btn-outline-primary btn-sm">Follow</button>', html)
            self.assertIn(f'<input type="hidden" name="url_redirect" value="{url}">', html)


    def test_click_follow_on_user_detail_redirects(self):
        """Test click 'follow' on user card on different user's following page 
        redirects to same page"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            other_user = User(**USER_DATA)
            other_user_2 = User(**USER_2_DATA)
            db.session.add_all([other_user, other_user_2])
            db.session.commit()

            other_user.following.append(other_user_2)
            db.session.commit()

            url = f'/users/{other_user.id}/following'
            resp = c.post(f'/users/follow/{other_user.id}', 
                        data={"url_redirect": url}, 
                        follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@testnewuser</h4>', html)
            self.assertIn('<button class="btn btn-primary btn-sm">Unfollow</button>', html)
            self.assertIn('<button class="btn btn-outline-primary btn-sm">Follow</button>', html)
            self.assertIn(f'<input type="hidden" name="url_redirect" value="{url}">', html)
