import json
import os
import tempfile

import moviepy.editor
import pika
from bson.objectid import ObjectId


def start(message, fs_videos, fs_mp3s, channel):
    # json to python object
    message = json.loads(message)
    tf = tempfile.NamedTemporaryFile()
    out = fs_videos.get(ObjectId(message["video_file_id"]))
    tf.write(out.read())
    audio = moviepy.editor.VideoFileClip(tf.name).audio
    tf.close()

    # TODO why do we need a temp file?
    tf_path = tempfile.gettempdir() + f"/{message['video_file_id']}.mp3"
    print("temporary file path:" + tf_path)
    audio.write_audiofile(tf_path)

    f = open(tf_path, "rb")
    data = f.read()
    fid = fs_mp3s.put(data)
    f.close()
    os.remove(tf_path)

    message["mp3_file_id"] = str(fid)

    try:
        channel.basic_publish(
            exchange="",
            # queue name
            routing_key=os.environ.get("MP3_QUEUE", "mp3"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as error:
        fs_mp3s.delete(fid)
        return "internal server error" + str(error), 500
