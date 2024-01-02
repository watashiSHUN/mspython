import json
import os

# shard file into chunks in mongo
import gridfs

# interface with rabbit MQ
import pika
from auth_svc import access, validate
from bson.objectid import ObjectId
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from storage import util

server = Flask(__name__)
# Use mongo DB to store document (data, which in this case is the video)
# MONGO_URI is consumed by PyMongo

mongo_host = os.environ.get("MONGO_HOST", "localhost")

video_mongo = PyMongo(server, uri=f"mongodb://{mongo_host}:27017/video")
mp3_mongo = PyMongo(server, uri=f"mongodb://{mongo_host}:27017/mp3")

# TODO try with amazon S3
video_fs = gridfs.GridFS(video_mongo.db)
mp3_fs = gridfs.GridFS(mp3_mongo.db)

# make synchronous communication with rabbit MQ
# TODO reconnect each time before enqueue a message, since the rabbitmq-service in k8s is not stable
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=os.environ.get("RABBITMQ_HOST", "rabbitmq-service"))
)
channel = connection.channel()


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
    # NOTE: we use a function because we likely need to call this for every routes
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
        error = util.upload(f, video_fs, channel, access)
        if error:
            # error is a tuple (message, status_code)
            return error

    return "uploaded", 200


# notification service will return file_id, which is passed in again with 'GET' method
@server.route("/download", methods=["GET"])
def download():
    # NOTE: we use a function because we likely need to call this for every routes
    access, error = validate.token(request)
    # check authorization in the jwt claim
    # load convert json string to python dict(object)
    if error:
        return error

    access = json.loads(access)
    if not access["admin"]:
        return "not authorized", 403
    # authorized

    # URL query string
    fid_string = request.args.get("file_id")
    if not fid_string:
        return "missing file_id", 400

    try:
        out = mp3_fs.get(ObjectId(fid_string))
        return send_file(out, download_name=f"{fid_string}.mp3")
    except Exception as error:
        return "internal server error" + str(error), 404


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080, debug=True)
