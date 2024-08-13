import os
from typing import List
import tempfile
from concurrent.futures import ThreadPoolExecutor
import imaplib
import smtplib
import email
from email.message import EmailMessage, Message
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr
import base64
from io import BytesIO
from bill import Bill, PDFBill
from util import OcrManager, extract_message, decode_str, build_MIME
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
wechat_ocr_dir = r".\wechat-ocr\WeChatOCR.exe"
wechat_dir = r".\wechat-ocr"

ocr_manager = OcrManager(wechat_dir)


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
    elif content_type.startswith("image/") or file_name.endswith(
        ("jpg", "png", "jpeg", "bmp")
    ):
        text = ocr(message.get_payload())
        # logging.info("图片内容：" + text)
        bill = Bill(text)
    else:
        logging.error("unsupport file:{}".format(file_name))
        return None
    vars = bill.extract()
    return {
        "file_name": file_name,
        "content_type": content_type,
        "payload": base64.b64decode(message.get_payload()),
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


def send_result_messag(_from: str, attachments: List, content: MIMEBase):
    mm = MIMEMultipart()
    mm["From"] = os.getenv("EMAIL_USER")
    mm["To"] = _from
    mm["Subject"] = Header(
        "Invoice Report {}".format(datetime.now().strftime("%Y%m%d%H%M%S")), "utf-8"
    )
    mm.attach(content)

    for attachment in attachments:
        mm.attach(
            build_MIME(
                attachment["payload"],
                attachment["new_file_name"],
            )
        )
    obj = smtplib.SMTP(os.getenv("SMTP_URL"))
    obj.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
    obj.send_message(mm)
    obj.quit()
    logging.warning("发送成功")


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
            attachment["new_file_name"] = get_new_file_name(
                attachment, name_format, _message != message
            )
            _bills.append(attachment)
    # 发送处理结果
    content = MIMEText("这是报销单据", "plain", "utf-8")
    _from = parseaddr(message.get("From"))
    send_result_messag(_from[1], _bills, content)


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
    logging.warning("开始读取邮件")
    if os.environ.get("environment") == "DEV":
        email_file = open(r".\test\android-outlook.eml")
        message: EmailMessage = email.message_from_file(email_file, _class=EmailMessage)
        exect(message, "Wes-{money}-{date:%m%d}")
    else:
        mail = imaplib.IMAP4_SSL(os.getenv("IMAP_URL"), 993)
        mail.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
        mail.select("inbox")
        status, uids = mail.search(None, "UNSEEN")
        if status != "OK":
            raise Exception("读取异常")
        for uid in uids[0].split():
            status, data = mail.fetch(uid, "(RFC822)")
            if status == "OK":
                email_message = email.message_from_bytes(
                    data[0][1], _class=EmailMessage
                )
                exect(email_message, decode_str(email_message.get("subject")))
                # 标记为已读
                mail.store(uid, "+FLAGS", "\Seen")
    logging.warning("执行结束")


if __name__ == "__main__":
    main()
