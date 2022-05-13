"""SQLAlchemy models for Friender."""
from flask import Flask
from flask_bcrypt import Bcrypt

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import VARCHAR

bcrypt = Bcrypt()
db = SQLAlchemy()


class Images(db.Model):
    """images of users"""

    __tablename__ = 'images'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username  = db.Column(
        db.String,
        db.ForeignKey('users.username', ondelete="cascade")
    )

    path = db.Column(
        db.Text,
        nullable=False,
    )
    filename = db.Column(
        db.Text,
        nullable=False
    )

    def to_dict(self):

        return {
            "id": self.id,
            "username": self.username,
            "path": self.path,
            "filename": self.filename
        }

    @classmethod
    def create_new_image(cls, username, path, filename):
        """ Returns a class of a new image
        {id, user_id, image_path} """

        image = Images(
            username=username,
            path=path,
            filename= filename
        )

        db.session.add(image)

        return image





class Match(db.Model):
    """Connection of a usering doing the matching <-> the user being matched."""

    __tablename__ = 'matches'

    user_being_followed = db.Column(
        db.String,
        db.ForeignKey('users.username', ondelete="cascade"),
        primary_key=True
    )

    user_following = db.Column(
        db.String,
        db.ForeignKey('users.username', ondelete="cascade"),
        primary_key=True
    )

    unfriended = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    @classmethod
    def add_match(cls, username, match_username):
        """Add a match to the database."""

        match = Match(
            user_being_followed = username,
            user_following = match_username,
            unfriended = False
        )

        db.session.add(match)
        return match



class Message(db.Model):
    """An individual message."""

    __tablename__ = 'messages'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_from = db.Column(
        db.String,
        db.ForeignKey('users.username', ondelete="cascade")
    )

    user_to  = db.Column(
        db.String,
        db.ForeignKey('users.username', ondelete="cascade")
    )

    text = db.Column(
        db.String(140),
        nullable=False,
    )

    sent_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow(),
    )

    @classmethod
    def add_message(cls, user_from, user_to, text):
        """Add a message."""

        message = Message(
            user_from = user_from,
            user_to = user_to,
            text = text
        )

        return message

    def __repr__(self):
        return f"<Message:\
        to: {self.user_to},\
        from: {self.user_from},\
        timestamp: {self.timestamp}>"

    def to_dict(self):

        return {
            "id": self.id,
            "user_from": self.user_from,
            "user_to": self.user_to,
            "text": self.text,
            "sent_at": self.sent_at
        }



class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    username = db.Column(
        db.Text,
        primary_key=True,
        nullable=False
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )


    password = db.Column(
        db.Text,
        nullable=False,
    )

    hobbies = db.Column(
        db.Text,
    )

    bio = db.Column(
        db.Text,
    )

    interests = db.Column(
        db.Text,
    )

    location = db.Column(
        db.String,
        nullable=False,
    )

    friend_radius = db.Column(
        db.Integer,
        nullable=False,
        default=50
    )

    messages = db.relationship(
        "Message",
        backref="users",
        primaryjoin=(Message.user_from == username)
    )

    followers = db.relationship(
        "User",
        secondary="matches",
        primaryjoin=(Match.user_being_followed == username),
        secondaryjoin=(Match.user_following == username)
    )

    following = db.relationship(
        "User",
        secondary="matches",
        primaryjoin=(Match.user_following == username),
        secondaryjoin=(Match.user_being_followed == username)
    )

    images = db.relationship(
        "Images",
        backref="users",
        primaryjoin=(Images.username == username)
    )

    def __repr__(self):
        return f"<User:\
        {self.username},\
        {self.email},\
        {self.bio},\
        {self.hobbies},\
        {self.interests},\
        {self.location},\
        {self.images}>"

    def is_followed_by(self, other_user):
        """Is this user followed by `other_user`?"""

        found_user_list = [
            user for user in self.followers if user == other_user]
        return len(found_user_list) == 1

    def is_following(self, other_user):
        """Is this user following `other_user`?"""

        found_user_list = [
            user for user in self.following if user == other_user]
        return len(found_user_list) == 1

    @classmethod
    def signup(cls, username, email, password, location):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            location=location
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.get(username)
        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

    def to_dict(self):

        return {
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "hobbies": self.hobbies,
            "bio": self.bio,
            "interests": self.interests,
            "location": self.location,
            "friend_radius": self.friend_radius
        }


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
