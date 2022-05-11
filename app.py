import os
import boto3, botocore
from flask import Flask, flash, redirect, request, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
# from flask_jwt import JWT

from models import db, connect_db, User, Message, Match


app = Flask(__name__)
from werkzeug.utils import secure_filename

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ['DATABASE_URL'].replace("postgres://", "postgresql://"))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['S3_KEY'] = os.environ['AWS_ACCESS_KEY_ID']
app.config['S3_SECRET'] = os.environ['AWS_SECRET_ACCESS_KEY']
app.config['S3_BUCKET'] = os.environ['BUCKET_NAME']
app.config['S3_LOCATION'] = 'http://{}.s3.amazonaws.com/'.format(app.config['S3_BUCKET'])
# S3_BUCKET = app.config['S3_BUCKET']

s3 = boto3.client('s3',
                    aws_access_key_id=app.config['S3_KEY'],
                    aws_secret_access_key= app.config['S3_SECRET'],
                     )

# toolbar = DebugToolbarExtension(app)

connect_db(app)
db.create_all()

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


############# USER ROUTES ############################
@app.get("/api/users")
def get_users():
    """ Get all users 
        Returns JSON like:
        {users: [{id, email, username, hobbies, interests}, ...]}
    """

    users = [user.to_dict() for user in User.query.all()]

    return jsonify(users=users)

@app.get('/api/users/<int:user_id>')
def single_user(user_id):
    """Get a single user"""

    user = User.query.get_or_404(user_id)

    user = user.to_dict()
    return jsonify(user=user)

@app.patch('/api/users/<int:user_id>')
def edit_single_user(user_id):
    """update user
       returns JSON like:
       {user: [{id, username, email, hobbies, interests...}]}
    """

    data = request.json
    user = User.query.get_or_404(user_id)

    user.hobbies = data.get('hobbies', user.hobbies)
    user.bio = data.get('bio', user.bio)
    user.interests = data.get('size', user.interests)
    user.location = data.get('size', user.location)
    user.friend_radius = data.get('size', user.friend_radius)

    db.session.add(user)
    db.session.commit()

    user = user.to_dict()
    return jsonify(user=user)

@app.delete('/api/users/<int:user_id>')
def get_photos(user_id):
    """Delete a user"""

    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()
    return jsonify(msg="deleted sucessfully")

@app.post('/api/users/<int:user_id>/match')
def match_person(user_id):
    """Match with a different person"""

    match_id = request.json.match
    match = Match.add_match(user_id,match_id)
    
    db.session.commit()
    return jsonify(msg="friended successfully")

@app.delete('/api/users/<int:user_id>/match')
def unmatch_person(user_id):
    """unmatch with a different person"""
    match_id = request.json.match

    match = Match.filter_by(user_being_followed_id=user_id and user_following_id=match_id).one()
    match.unfriended = True

    db.session.commit()
    return jsonify(msg="unfriended successfully")

############# USER PHOTO ROUTES ############################    

@app.get('/api/users/<int:user_id>/photos')
def get_photos(user_id):
    """Get all photos of a user"""

    user = User.query.get_or_404(user_id)

    images = user.images

    images = [image.to_dict() for image in images]

    return jsonify(images=images)

@app.post('/api/users/<int:user_id>/photos')
def upload_pic(user_id):
    """Upload a picture"""
    img = request.files['file']
    if img:
            filename = secure_filename(img.filename)
            img.save(filename)
            s3.upload_file(
                Bucket = app.config['S3_BUCKET'],
                Filename=filename,
                Key = filename,
                ExtraArgs={
                    "ContentType":  "image/jpeg",
                    'ACL': "public-read"
                }
            )
            msg = "Upload Done ! "
            file_path = "{}{}".format(app.config["S3_LOCATION"], img.filename)

            user = User.query.get_or_404(user_id)

            user.images.append(file_path)

            db.session.commit()

            return jsonify(file_path=file_path,msg="success")
    return jsonify(msg="no image specified")

@app.delete('/api/users/<int:user_id>/photos/<int:photo_id>')
def get_photos(user_id,photo_id):
    """Get all photos of a user"""

    image = Images.query.get_or_404(photo_id)

    db.session.delete(image)
    db.session.commit()
    return jsonify(msg="deleted sucessfully")

































# INSERT INTO USERS (username, email, location, password, friend_radius)
# VALUES ('lyne', 'tes1t@test.com', '12346', 'plaintext','20')

# INSERT INTO USERS (username, email, location, password, friend_radius)
# VALUES ('michael', 'test@test.com', '12345', 'plaintext','20')

# INSERT INTO messages (id_to, id_from, text, timestamp) VALUES ('1','2','new message',current_timestamp)
