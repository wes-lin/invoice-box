import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
import email
from email.message import EmailMessage, Message
from email.header import decode_header
import base64
from io import BytesIO
from bill import Bill, PDFBill
from util import OcrManager, extract_message
import logging

logging.basicConfig(level=logging.INFO)
wechat_ocr_dir = r".\wechat-ocr\WeChatOCR.exe"
wechat_dir = r".\wechat-ocr"

ocr_manager = OcrManager(wechat_dir)


def decode_str(s):
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value


def base64_byte(s: str):
    byte_data = base64.b64decode(s)
    data = BytesIO(byte_data)
    return data


def ocr(file_base64: str):
    img_data = base64.b64decode(file_base64)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(img_data)
        result = ocr_manager.DoOCRTask(f.name)
        text = "".join(map(lambda r: r["text"], result["ocrResult"]))
        f.close()
        os.remove(f.name)
        return text


def get_bill(message: Message):
    if message.get_filename() == None:
        return None
    file_name = decode_str(message.get_filename())
    content_type = message.get_content_type()
    bill: Bill = None
    if file_name.endswith(".pdf"):
        bill = PDFBill(base64_byte(message.get_payload()))
    elif content_type.startswith("image/"):
        text = ocr(message.get_payload())
        logging.info("图片内容：" + text)
        bill = Bill(text)
    else:
        logging.error("unsupport file:{}".format(file_name))
        return None
    vars = bill.extract()
    return {
        "file_name": file_name,
        "content_type": content_type,
        # "payload": base64.b64decode(message.get_payload()),
        "vars": vars,
    }


def get_attachments(message: EmailMessage):
    tasks = []
    executor = ThreadPoolExecutor(
        max_workers=5, thread_name_prefix="GeneralTask_Thread"
    )
    for result in executor.map(get_bill, message.iter_attachments(), timeout=100):
        if result != None:
            tasks.append(result)
    return tasks


def extract_bill(message: EmailMessage):
    messages = extract_message(message)
    _bills = []
    for _message in messages:
        attachments = get_attachments(_message)
        for attachment in attachments:
            _bills.append(attachment)
    return _bills


def main():

    ocr_manager.SetExePath(wechat_ocr_dir)
    ocr_manager.StartWeChatOCR()
    email_file = open(r".\test\test.eml")
    message: EmailMessage = email.message_from_file(email_file, _class=EmailMessage)
    data = extract_bill(message)
    logging.info(data)


if __name__ == "__main__":
    main()
