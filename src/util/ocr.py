from typing import List
import json
from wechat_ocr.ocr_manager import OcrManager, OCR_MAX_TASK_ID

wechat_ocr_dir = r".\wechat-ocr\WeChatOCR.exe"
wechat_dir = r".\wechat-ocr"


class OCR:
    def __init__(self):
        ocr_manager = OcrManager(wechat_dir)
        ocr_manager.SetExePath(wechat_ocr_dir)
        ocr_manager.SetUsrLibDir(wechat_dir)
        ocr_manager.SetOcrResultCallback(
            lambda path, res: print(
                "".join(
                    map(lambda r: r["text"], sorted(res["ocrResult"], key=self.sort))
                )
            )
        )
        self.m_ocr_manager = ocr_manager

    def sort(self, e):
        return (e["pos"]["y"], e["pos"]["x"])

    def extract_text(self, img_paths: List[str]):
        if not self.m_ocr_manager.m_wechatocr_running:
            self.m_ocr_manager.StartWeChatOCR()
        for img_path in img_paths:
            self.m_ocr_manager.DoOCRTask(img_path)
        while not self.m_ocr_manager.m_task_id.full():
            pass

    def __del__(self):
        self.m_ocr_manager.KillWeChatOCR()


ocr = OCR()
