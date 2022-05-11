from flask_jwt import JWT


def create_token(user):
    payload = {
        username: user.username.
        isAdmin: user.isAdmin or false
    }

    return jwt.sign(payload, SECRET_KEY)