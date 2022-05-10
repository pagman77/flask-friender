import os

from flask import Flask, flash, redirect
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError


from models import db, connect_db, User, Message, Match


app = Flask(__name__)


# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ['DATABASE_URL'].replace("postgres://", "postgresql://"))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

# toolbar = DebugToolbarExtension(app)

connect_db(app)

db.create_all()


# INSERT INTO USERS (username, email, location, password, friend_radius)
# VALUES ('lyne', 'tes1t@test.com', '12346', 'plaintext','20')

# INSERT INTO USERS (username, email, location, password, friend_radius)
# VALUES ('michael', 'test@test.com', '12345', 'plaintext','20')

# INSERT INTO messages (id_to, id_from, text, timestamp) VALUES ('1','2','new message',current_timestamp)
