### app/service/ocr.py

import io
import os
from google.cloud import vision
from dotenv import load_dotenv
from pathlib import Path
from PIL import Image
import io
from google.cloud import vision
import cv2
import numpy as np


env = os.getenv("ENV", "production")
dotenv_file = f".env.{env}"
load_dotenv(dotenv_file)
# 相対パス → 絶対パスに変換
# cred_path = Path(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")).resolve()
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(cred_path)


client = vision.ImageAnnotatorClient()

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
