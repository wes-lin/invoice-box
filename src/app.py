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
from datetime import datetime
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
        "content": bill.context,
        # "payload": base64.b64decode(message.get_payload()),
        "vars": vars,
    }


def get_attachments(message: EmailMessage, merge_var: bool):
    tasks = []
    executor = ThreadPoolExecutor(
        max_workers=5, thread_name_prefix="GeneralTask_Thread"
    )
    vars = {}
    for result in executor.map(get_bill, message.iter_attachments(), timeout=100):
        if result != None:
            if merge_var:
                vars.update(result["vars"])
                result["vars"] = vars
            tasks.append(result)
    return tasks


def exect(message: EmailMessage, name_format: str):
    try:
        name_format.format(money="100", date=datetime.strptime("20240801", "%Y%m%d"))
    except:
        logging.error("格式异常，使用默认格式")
        name_format = "{money}-{date:%m%d}"
    messages = extract_message(message)
    _bills = []
    for _message in messages:
        attachments = get_attachments(_message, _message != message)
        for attachment in attachments:
            print(get_new_file_name(attachment, name_format, _message != message))
            _bills.append(attachment)
    print(_bills)


def get_new_file_name(result: dict, name_format: str, merge_var: bool):
    vars: dict = result["vars"]
    money = vars.get("order_money")
    date = vars.get("order_date")
    (file, ext) = os.path.splitext(result["file_name"])
    file_name = ext
    if merge_var:
        file_name = "-" + file + ext
    if result["file_name"].startswith("滴滴出行行程报销单"):
        money = vars.get("trip_money")
        date = vars.get("trip_date")
    elif result["file_name"].startswith("滴滴电子发票"):
        money = vars.get("invoice_money")
        date = vars.get("trip_date", vars.get("invoice_date"))
    return name_format.format(money=money, date=date) + file_name


def main():

    ocr_manager.SetExePath(wechat_ocr_dir)
    ocr_manager.StartWeChatOCR()
    email_file = open(r".\test\test.eml")
    message: EmailMessage = email.message_from_file(email_file, _class=EmailMessage)
    exect(message, "Wes-{money}-{date:%m%d}")


if __name__ == "__main__":
    main()
