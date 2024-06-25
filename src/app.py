import sys
import json

from util import OcrManager
import logging

logging.basicConfig(level=logging.DEBUG)
wechat_ocr_dir = r".\wechat-ocr\WeChatOCR.exe"
wechat_dir = r".\wechat-ocr"


def main():
    print(f"encode:{sys.stdout.encoding}")
    ocr_manager = OcrManager(wechat_dir)
    ocr_manager.SetExePath(wechat_ocr_dir)

    ocr_manager.StartWeChatOCR()
    result = ocr_manager.DoOCRTask(r".\test\1.jpg")
    text = "".join(map(lambda r: r["text"], result["ocrResult"]))
    print(f"识别结果:" + text)


if __name__ == "__main__":
    main()
