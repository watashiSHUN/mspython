# Import smtplib for the actual sending function
import json
import os
import smtplib

# Import the email modules we'll need
from email.message import EmailMessage

import dotenv

dotenv.load_dotenv()


def notify(message_body):
    try:
        message = json.loads(message_body)
        mp3_file_id = message["mp3_file_id"]
        # non-google application to login to your gmail account
        sender_address = os.environ.get("SENDER_ADDRESS")
        sender_password = os.environ.get("SENDER_PASSWORD")
        # NOTE this is why we were asked to use email as the user name
        receiver_address = os.environ.get("RECEIVER_ADDRESS")

        user = message["username"]

        msg = EmailMessage()
        msg.set_content(
            f"{user} video has been converted to mp3: file_id:'{mp3_file_id}'"
        )
        msg["Subject"] = f"{user} video has been converted to mp3"
        msg["From"] = sender_address
        msg["To"] = receiver_address

        # connect to google smtp server and login, then send email
        session = smtplib.SMTP("smtp.gmail.com")
        # NOTE used for detailed debugging
        session.set_debuglevel(1)
        session.starttls()
        session.login(sender_address, sender_password)
        session.send_message(msg, sender_address, receiver_address)
        session.quit()

        print("Mail Sent")
    except Exception as error:
        print("Mail failed to send")
        print(error)
        # TODO move the error to error queue?
        return error


if __name__ == "__main__":
    notify('{"mp3_file_id": "5f8a6b1b9e0b7b4b9b7d3c4d","username": "shunshunxian"}')
