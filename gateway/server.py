import json
import os

# shard file into chunks in mongo
import gridfs

# interface with rabbit MQ
import pika
from auth_svc import access, validate
from flask import Flask, request
from flask_pymongo import PyMongo
from storage import util

server = Flask(__name__)
# Use mongo DB to store document (data, which in this case is the video)
# MONGO_URI is consumed by PyMongo
# TODO replace it with localhost to test locally
server.config["MONGO_URI"] = "mongodb://host.minikube.internal:27017/video"

mongo = PyMongo(server)

# TODO try with amazon S3
fs = gridfs.GridFS(mongo.db)

# make synchronous communication with rabbit MQ
# connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
# channel = connection.channel()


# NOTE: we call auth service on behalf of the user
@server.route("/login", methods=["POST"])
def login():
    # talk to auth service
    # forward the entire request
    token, error = access.login(request)

    if not error:
        return token
    else:
        return error


# NOTE: first internally validate client authn/authz with auth service
@server.route("/upload", methods=["POST"])
def upload():
    access, error = validate.token(request)
    # check authorization in the jwt claim
    # load convert json string to python dict(object)
    if error:
        return error

    access = json.loads(access)
    if not access["admin"]:
        return "not authorized", 403
    # authorized
    if len(request.files) != 1:
        return "exactly 1 file required", 400

    for _, f in request.files.items():
        pass
        # error = util.upload(f, fs, channel, access)
        # if error:
        #     # error is a tuple (message, status_code)
        #     return error

    return "uploaded", 200


@server.route("/download", methods=["GET"])
def download():
    pass


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080, debug=True)
