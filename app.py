import json
import os
from urllib import response
import boto3, botocore
from flask import Flask, flash, redirect, request, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager

from models import db, connect_db, User, Message, Match, Images


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


s3 = boto3.client('s3',
                    aws_access_key_id=app.config['S3_KEY'],
                    aws_secret_access_key= app.config['S3_SECRET'],
                     )

toolbar = DebugToolbarExtension(app)

jwt = JWTManager(app)
connect_db(app)
db.create_all()

#############################################################################

####################User signup/login/logout#############################


@app.route('/api/signup', methods=["POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    try:
        username=request.json["username"]
        email=request.json["email"]
        password=request.json["password"]
        location= request.json["location"]

        new_user = User.signup(username, email, password, location)
        db.session.commit()

        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)

    except IntegrityError:
        return jsonify(msg = "Username already taken")



@app.route('/api/token', methods=["POST"])
def login():
    """POST /auth/token:  { username, password } => { token }
    Returns JWT token which can be used to authenticate further requests.
    Authorization required: none"""

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
    """ Get all users
        Returns JSON like:
        {users: [{id, email, username, hobbies, interests}, ...]}
    """
    # current_user = get_jwt_identity()

    users = [user.to_dict() for user in User.query.all()]

    return jsonify(users=users)

@app.get('/api/users/<int:user_id>')
@jwt_required()
def get_single_user(user_id):
    """Get a single user
    returns {msg: "User not found!"} if no user exists"""

    try:
        user = User.query.get(user_id)
        user = user.to_dict()
        return jsonify(user=user)
    except AttributeError:
        return jsonify({"msg": "User not found!"})


@app.patch('/api/users/<int:user_id>')
@jwt_required()
def edit_single_user(user_id):
    """update user
       returns JSON like:
       {user: [{id, username, email, hobbies, interests...}]}
    """

    data = request.json

    try:
        user = User.query.get(user_id)
        user.hobbies = data.get('hobbies', user.hobbies)
        user.bio = data.get('bio', user.bio)
        user.interests = data.get('size', user.interests)
        user.location = data.get('size', user.location)
        user.friend_radius = data.get('size', user.friend_radius)

        db.session.add(user)
        db.session.commit()

        user = user.to_dict()
        return jsonify(user=user)

    except AttributeError:
        return jsonify({"msg": "User not found!"})


@app.delete('/api/users/<int:user_id>')
@jwt_required()
def delete_user(user_id):
    """Delete a user"""

    try:
        user = User.query.get(user_id)
        db.session.delete(user)
        db.session.commit()
        return jsonify(msg="deleted sucessfully")
    except AttributeError:
        return jsonify({"msg": "User not found!"})


@app.post('/api/users/<int:user_id>/match')
@jwt_required()
def match_person(user_id):
    """Match with a different person"""

    print(request.json)

    match_id = request.json["match"]
    match = Match.add_match(user_id,match_id)

    db.session.commit()
    return jsonify(msg="friended successfully")


@app.post('/api/users/<int:user_id>/unmatch')
@jwt_required()
def unmatch_person(user_id):
    """unmatch with a different person"""
    match_id = request.json["unmatch"]

    match = Match.query.filter(
        Match.user_being_followed_id == user_id,
        Match.user_following_id == match_id).one_or_none()

    if not match:
        return jsonify({"msg": "No match found!"})

    match.unfriended = True
    db.session.commit()
    return jsonify(msg="unfriended successfully")



############# USER PHOTO ROUTES ############################

@app.get('/api/users/<int:user_id>/photos')
@jwt_required()
def get_photos(user_id):
    """Get all photos of a user"""

    user = User.query.get_or_404(user_id)

    images = user.images

    images = [image.to_dict() for image in images]

    return jsonify(images=images)

@app.post('/api/users/<int:user_id>/photos')
@jwt_required()
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
            image = Images.create_new_image(user.id, file_path, img.filename)

            user.images.append(image)

            db.session.commit()

            return jsonify(file_path=file_path,msg="success")

    return jsonify(msg="no image specified")


@app.delete('/api/users/<int:user_id>/photos/<int:photo_id>')
@jwt_required()
def delete_photos(user_id, photo_id):
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
































# INSERT INTO USERS (username, email, location, password, friend_radius)
# VALUES ('lyne', 'tes1t@test.com', '12346', 'plaintext','20')

# INSERT INTO USERS (username, email, location, password, friend_radius)
# VALUES ('michael', 'test@test.com', '12345', 'plaintext','20')

# INSERT INTO messages (id_to, id_from, text, timestamp) VALUES ('1','2','new message',current_timestamp)
