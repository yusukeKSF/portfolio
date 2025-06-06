### app/service/ocr.py

import io
import os
from google.cloud import vision
import cv2
import numpy as np
# デプロイようにAPIの読み込みについて追加修正
import tempfile
# メモリ使用量間使用
from app.monitor import monitor_memory


# 環境変数に保存されたJSON文字列を取得
credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

if credentials_json:
    # 一時ファイルに書き出してから認証に使用
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as temp_json_file:
        temp_json_file.write(credentials_json)
        temp_json_file_path = temp_json_file.name

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_json_file_path

client = vision.ImageAnnotatorClient()

@monitor_memory("OCR処理")
def extract_text_from_frame(frame: np.ndarray) -> str:
    # OpenCV画像をJPEGに変換
    _, encoded_image = cv2.imencode('.jpg', frame)
    content = encoded_image.tobytes()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    if response.error.message:
        raise Exception(f"Vision API error: {response.error.message}")

    # テキストを一つにまとめる
    text = response.text_annotations[0].description if response.text_annotations else ""
    return text.strip()


def extract_text_from_image(image_path: str) -> str:
    print(f"🖼 OCR処理開始: {image_path}")
    client = vision.ImageAnnotatorClient()

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    if response.error.message:
        raise Exception(f"OCRエラー: {response.error.message}")

    texts = response.text_annotations
    extracted = texts[0].description if texts else ''
    print("📝 OCR抽出テキスト:", extracted)
    return extracted
