from typing import List
from email.message import EmailMessage
from email.header import decode_header
from email.mime.application import MIMEApplication
from email.mime.nonmultipart import MIMENonMultipart
import email
import base64
from io import BytesIO


def decode_str(s) -> str:
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value


def extract_message(message: EmailMessage):
    messages: List[EmailMessage] = []
    _extract_message(message, messages)
    return messages


def _extract_message(message: EmailMessage, messages: List[EmailMessage]):
    for attachment in message.iter_attachments():
        if attachment.get_content_type() == "message/rfc822":
            for payload in attachment.get_payload():
                _message: EmailMessage = email.message_from_bytes(
                    payload.as_bytes(), _class=EmailMessage
                )
                _extract_message(_message, messages)
        elif attachment.get_filename() != None and decode_str(
            attachment.get_filename()
        ).endswith(".eml"):
            _message: EmailMessage = email.message_from_bytes(
                base64.b64decode(attachment.get_payload()), _class=EmailMessage
            )
            _extract_message(_message, messages)
    messages.append(message)


def build_MIME(data, fil_name) -> MIMENonMultipart:
    mime = MIMEApplication(data)
    mime.add_header("Content-Description", fil_name)
    mime.add_header("Content-Disposition", "attachment", filename=fil_name)
    return mime
