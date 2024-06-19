import sys

from util import ocr


# def ocr_result_callback(img_path: str, results: dict):
#     print(f"识别成功，img_path: {img_path}")
#     print(f"识别结果:" + json.dumps(results, ensure_ascii=False, indent=2))


def main():
    print(f"encode:{sys.stdout.encoding}")
    ocr.extract_text([r".\test\1.jpg"])
    ocr.extract_text([r".\test\2.jpg"])
    ocr.extract_text([r".\test\2.jpg"])


if __name__ == "__main__":
    main()
