import os
import sys
import time

# only need access to rabbitmq, not mongodb
import pika

# user defined
from send import gmail


def main():
    # make synchronous communication with rabbit MQ, see gateway/server.py
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.environ.get("RABBITMQ_HOST", "rabbitmq-service")
        )
    )
    channel = connection.channel()

    def callback(channel, method, properties, message_body):
        err = gmail.notify(message_body)
        # nack vs ack
        if err:
            channel.basic_nack(delivery_tag=method.delivery_tag)
        else:
            channel.basic_ack(delivery_tag=method.delivery_tag)

    # When we receive the message, we call to_mp3.start to start converting
    channel.basic_consume(
        queue=os.environ.get("MP3_QUEUE", "mp3"),
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
