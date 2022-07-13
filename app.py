import json
import os
import boto3
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from zipcode import Distance
import uuid

from models import db, connect_db, User, Message, Match, Images

app = Flask(__name__)

CORS(app)

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


s3 = boto3.client('s3',
                    aws_access_key_id=app.config['S3_KEY'],
                    aws_secret_access_key= app.config['S3_SECRET'],
                     )

# toolbar = DebugToolbarExtension(app)

jwt = JWTManager(app)
connect_db(app)
db.create_all()

#############################################################################

####################User signup/login/logout#############################


@app.route('/api/signup', methods=["POST"])
def signup():
    """Handle user signup.
    Create new user, add to db, return JWT.
    Return error message if user is already taken.
    """

    try:
        username=request.json["username"]
        email=request.json["email"]
        password=request.json["password"]
        location= request.json["location"]

        User.signup(username, email, password, location)
        db.session.commit()
        access_token = create_access_token(identity=username)

        return jsonify(access_token=access_token)

    except IntegrityError:
        return jsonify(msg = "Username already taken")


@app.route('/api/token', methods=["POST"])
def login():
    """{ username, password } => { token }
    Takes in user and password and returns JWT.
    """

    user = User.authenticate(request.json["username"],
                                 request.json["password"])

    if user:
        access_token = create_access_token(identity=user.username)
        return jsonify(access_token=access_token)

    return jsonify(msg="Could not authenticate!")



############# USER ROUTES ############################

@app.get("/api/users")
@jwt_required()
def get_users():
    """ Get all users that fall within location paramaters.
        Returns: {users: [{username, email, hobbies, bio, interests, location, friend_radius}, ...]}
    """
    username = get_jwt_identity()

    curr_user = User.query.get(username)
    users = User.query.all()

    users = [user.to_dict() for user in User.query.all() if user.username != username]

    matches = Distance.get_location_matches(curr_user.location, users, curr_user.friend_radius)

    return jsonify(matches=matches)

@app.get('/api/users/<username>')
@jwt_required()
def get_single_user(username):
    """Return a user: {username, email, hobbies, bio, interests, location, friend_radius}
    returns {msg: "User not found!"} if no user exists"""

    try:
        user = User.query.get(username)
        user = user.to_dict()
        return jsonify(user=user)
    except AttributeError:
        return jsonify({"msg": "User not found!"})


@app.patch('/api/users/<username>')
@jwt_required()
def edit_single_user(username):
    """Update a user and return user object:
    {username, email, hobbies, bio, interests, location, friend_radius}
    """

    data = request.json

    try:
        user = User.query.get(username)
        user.hobbies = data.get('hobbies', user.hobbies)
        user.bio = data.get('bio', user.bio)
        user.interests = data.get('interests', user.interests)
        user.location = data.get('location', user.location)
        user.friend_radius = data.get('friend_radius', user.friend_radius)

        db.session.add(user)
        db.session.commit()

        user = user.to_dict()
        return jsonify(user=user)

    except AttributeError:
        return jsonify({"msg": "User not found!"})


@app.delete('/api/users/<username>')
@jwt_required()
def delete_user(username):
    """Delete a user"""

    try:
        user = User.query.get(username)
        db.session.delete(user)
        db.session.commit()
        return jsonify(msg="deleted sucessfully")
    except AttributeError:
        return jsonify({"msg": "User not found!"})


@app.post('/api/users/<username>/match')
@jwt_required()
def match_person(username):
    """Match with another user. Returns message if successful."""

    match_username = request.json["match"]
    match = Match.add_match(username,match_username)
    db.session.commit()
    if match:
        return jsonify(msg="friended successfully")


@app.post('/api/users/<username>/unmatch')
@jwt_required()
def unmatch_person(username):
    """Unmatch with another user."""
    match_username = request.json["unmatch"]

    match = Match.query.filter(
        Match.user_being_followed == username,
        Match.user_following == match_username).one_or_none()

    if not match:
        return jsonify({"msg": "No match found!"})

    match.unfriended = True
    db.session.commit()
    return jsonify(msg="unfriended successfully")



############# USER PHOTO ROUTES ############################

@app.get('/api/users/<username>/photos')
@jwt_required()
def get_photos(username):
    """Get all photos of a user"""

    user = User.query.get_or_404(username)
    images = user.images
    images = [image.to_dict() for image in images]

    return jsonify(images=images)


@app.post('/api/users/<username>/photos')
@jwt_required()
def upload_pic(username):
    """Upload a picture"""

    img = request.files['file']

    if img:
        filename = secure_filename(img.filename)
        filename = str(uuid.uuid1())
        s3.put_object(
            Body=img,
            Bucket = app.config['S3_BUCKET'],
            Key = filename,
            ContentType="image/jpeg"
        )

        file_path = "{}{}".format(app.config["S3_LOCATION"], filename)

        user = User.query.get_or_404(username)
        image = Images.create_new_image(username, file_path, filename)
        user.images.append(image)
        db.session.commit()

        return jsonify(file_path=file_path,msg="success")

    return jsonify(msg="no image specified")


@app.delete('/api/users/<username>/photos/<int:photo_id>')
@jwt_required()
def delete_photos(username, photo_id):
    """Delete a user photo"""

    try:
        image = Images.query.get(photo_id)

        response = s3.delete_object(
        Bucket=app.config['S3_BUCKET'],
        Key=image.filename
)
        db.session.delete(image)
        db.session.commit()

        return jsonify(msg="deleted sucessfully")

    except AttributeError:
        return jsonify({"msg": "Image not found!"})

############# Messages ROUTES ############################

@app.get("/api/users/<username>/messages")
@jwt_required()
def get_messages(username):
    """ Get all user messages
        Returns: {messages: [{id, id_from, id_to, text, sent_at}, ...]}
    """

    user = User.query.get(username)
    messages = [message.to_dict() for message in user.messages]

    return jsonify(messages=messages)

@app.get('/api/users/<user_from>/<user_to>')
@jwt_required()
def get_messages_to_user(user_from,user_to):
    """ Get all messages between the current user and another user
        Returns: {messages: [{id, id_from, id_to, text, sent_at}, ...]}
    """
    user = User.query.get(user_from)
    messages = [message.to_dict() for message in user.messages if message.user_to == user_to or message.user_from == user_to]

    return jsonify(messages=messages)

@app.post('/api/users/<user_from>/<user_to>')
@jwt_required()
def send_message(user_from,user_to):
    """ Send a message to a user
        Returns conversation: {message: [{id, id_from, id_to, text, sent_at}, ...]}
    """

    message_data = request.json
    user = User.query.get(user_from)

    message_user_from = user_from
    message_user_to = user_to
    message_text = message_data["text"]

    new_message = Message.add_message(message_user_from,message_user_to,message_text)
    user.messages.append(new_message)
    db.session.commit()

    messages = [message.to_dict() for message in user.messages if message.user_to == user_to]

    return jsonify(messages=messages)