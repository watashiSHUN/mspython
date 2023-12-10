import json

import pika


def upload(file, file_system, channel, access):
    # update the file to mongodb
    # put message to rabbit MQ
    try:
        file_id = file_system.put(file)
    except Exception as error:
        return "internal server error", 500

    message = {
        "video_file_id": str(file_id),
        "mp3_file_id": None,
        # uniquely identify the user
        "username": access["username"],
    }

    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            # dumps convert python dict to json string
            body=json.dumps(message),
            # force the message to write to disk
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as error:
        # remove the file, if we fail to send message to rabbit MQ
        # make the system consistent
        file_system.delete(file_id)
