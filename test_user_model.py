"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
# from typing_extensions import TypeVarTuple
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from models import db, User, Message, Images, Match

os.environ['DATABASE_URL'] = "postgresql:///friender_test"
os.environ['SECRET_KEY'] = "itsasecret"
from app import app

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Images.query.delete()
        Match.query.delete()

        self.client = app.test_client()

        u = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            zipcode=12345
        )

        u2 = User.signup(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2",
            zipcode=54321
        )

        db.session.add_all([u,u2])
        db.session.commit()

        self.u_id = u.id
        self.u2_id = u2.id

    def tearDown(self):
        """Remove all session commits."""
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User.query.get(self.u_id)

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.images), 0)
