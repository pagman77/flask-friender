import os

from flask import Flask, flash, redirect
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from flask_jwt import JWT

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

##############################################################################
# User signup/login/logout

# @app.before_request
# def verifyToken():
#     """Verify the incoming token is valid"""

#     token = request.token

#     if CURR_USER_KEY in session:
#         g.user = User.query.get(session[CURR_USER_KEY])

#     else:
#         g.user = None


# @app.route('/signup', methods=["POST"])
# def signup():
#     """Handle user signup.

#     Create new user and add to DB.

#     If the there already is a user with that username: flash message
#     and re-present form.
#     """

#     user_info = res.body

#     try:
#         new_user = User.signup(user_info)
#     except IntegrityError:
#         return ("Username already taken").json()

#         do_login(user)

# @app.route('/token', methods=["POST"])
# def login():
#     """POST /auth/token:  { username, password } => { token }
#     Returns JWT token which can be used to authenticate further requests. 
#     Authorization required: none"""


#         user = User.authenticate(form.username.data,
#                                  form.password.data)

#         if user:
#             do_login(user)
#             flash(f"Hello, {user.username}!", "success")
#             return redirect("/")

#         flash("Invalid credentials.", 'danger')

#     return render_template('users/login.html', form=form)

@app.get("api/users")
def get_users():
    """ Get all users 
        Returns JSON like:
        {users: [{id, email, username, hobbies, interests}, ...]}
    """

    users = [user.to_dict() for user in User.query.all()]

    return jsonify(users=users)

@app.get('api/users/<int:user_id>')
def single_user(user_id):
    """Get a single user"""

    user = User.query.get_or_404(user_id)

    user = user.to_dict()
    return jsonify(user=user)

@app.patch('api/users/<int:user_id>')
def single_user(user_id):
    """update user"""

    data = request.json
    user = User.query.get_or_404(user_id)

    # cupcake.flavor = data.get('flavor', cupcake.flavor)
    # cupcake.rating = data.get('rating', cupcake.rating)
    # cupcake.size = data.get('size', cupcake.size)

    user = user.to_dict()
    return jsonify(user=user)





























db.create_all()


# INSERT INTO USERS (username, email, location, password, friend_radius)
# VALUES ('lyne', 'tes1t@test.com', '12346', 'plaintext','20')

# INSERT INTO USERS (username, email, location, password, friend_radius)
# VALUES ('michael', 'test@test.com', '12345', 'plaintext','20')

# INSERT INTO messages (id_to, id_from, text, timestamp) VALUES ('1','2','new message',current_timestamp)
