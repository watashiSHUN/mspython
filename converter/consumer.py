import os
import sys
import time

import gridfs
import pika

# user defined
from convert import to_mp3
from pymongo import MongoClient


def main():
    client = MongoClient("host.minikube.internal", 27017)
    # mongodbs
    # gateway.server output video files here
    db_videos = client.video  # NOTE: this is the name of the database
    # converter.consumer output mp3 files here
    db_mp3s = client.mp3  # NOTE: this is the name of the database

    # gridfs
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # make synchronous communication with rabbit MQ, see gateway/server.py
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.environ.get("RABBITMQ_HOST", "rabbitmq-service")
        )
    )
    channel = connection.channel()

    def callback(channel, method, properties, message_body):
        err = to_mp3.start(message_body, fs_videos, fs_mp3s, channel)
        # nack vs ack
        if err:
            channel.basic_nack(delivery_tag=method.delivery_tag)
        else:
            channel.basic_ack(delivery_tag=method.delivery_tag)

    # When we receive the message, we call to_mp3.start to start converting
    channel.basic_consume(
        queue=os.environ.get("VIDEO_QUEUE", "video"),
        on_message_callback=callback,
    )

    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(" [*] Exiting...")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
