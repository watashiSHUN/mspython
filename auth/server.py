import datetime
import os

import jwt
from dotenv import load_dotenv
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

# TODO(shunxian): will this override environment set by "docker.manifest"
load_dotenv()

app = Flask(__name__)
# connect to db, not starting db server
# mysql://username:password@localhost/db_name
mysql_user = os.environ.get("MYSQL_USER")
mysql_password = os.environ.get("MYSQL_PASSWORD")
mysql_host = os.environ.get("MYSQL_HOST")
# TODO SQLALCHEMY_DATABASE_URI is consumed by SQLAlchemy?
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"mysql://{mysql_user}:{mysql_password}@{mysql_host}/auth"
db = SQLAlchemy(app)


# TODO, use this model to build the DB instead of init.sql
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return "<User %r>" % self.username


@app.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers.get("Authorization")
    if not encoded_jwt:
        return "missing authorization header", 401

    # [0] = Bearer, [1] = token
    encoded_jwt = encoded_jwt.split(" ")[1]

    try:
        decoded = jwt.decode(
            encoded_jwt, os.environ.get("JWT_SECRET"), algorithms=["HS256"]
        )
    except:
        return "not authorized", 403

    return decoded, 200


@app.route("/login", methods=["POST"])
def login():
    # we can get authorization.username and authorization.password
    auth = request.authorization
    if not auth:
        # if auth header does not exist
        return "missing credentials", 401

    # check db for username and password
    user = User.query.filter_by(username=auth.username).first()
    if not user or user.password != auth.password:
        return "invalid credentials", 401

    # authenticated against the server
    # response is the JWT token, used for subsequent
    # request instead of passing username and password everytime

    # jwt is signed using the secret key
    # NOTE: JWT can use sym key or asym key
    # auth service can validate the token (when user send it back)

    # TODO, read secret key from env
    return createJWT(auth.username, os.environ.get("JWT_SECRET"), True)


def createJWT(username, secret, auth_permission):
    return jwt.encode(
        {
            "username": username,
            # expiration time needs to be a string
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            "admin": auth_permission,
        },
        secret,
        algorithm="HS256",
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
    # docker container (like a machine) will have an IP address
    # NOTE, with a docker network?

    # IP address will locate a server
    # => but we have many processes
    # the docker container will have a process
