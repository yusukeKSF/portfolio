### camera_ocr_router.py に統合されたため現在は不要。
### 今後カメラ撮影からOCR出力を行う機能追加をする場合に必要になる可能性あり。

# upload_and_process_router.py

# from fastapi import APIRouter, UploadFile, File
# import cv2
# import numpy as np
# import os
# from app.service.ocr import extract_text_from_frame
# from app.routes.camera_ocr_router import process_ocr_and_send
# from app.routes.camera_ocr_router import generate_journal_entries, process_gpt_and_enrich
# from app.service.sheets import write_entries_to_sheet

# router = APIRouter()

# @router.post("/upload_and_process")
# async def upload_and_process(file: UploadFile = File(...)):
#     # 一時ファイルとして保存
#     temp_path = "temp_uploaded_image.jpg"
#     with open(temp_path, "wb") as f:
#         f.write(await file.read())

#     # OpenCVで画像読み込み
#     image = cv2.imread(temp_path)
#     if image is None:
#         return {"status": "error", "message": "画像の読み込みに失敗しました"}

#     # OCR処理
#     ocr_text = extract_text_from_frame(image)
#     print("📝 OCR抽出テキスト:", ocr_text)

#     # GPT処理 → 仕訳補完
#     journal = generate_journal_entries(ocr_text)
#     enriched = process_gpt_and_enrich(journal, ocr_text)

#     # Google Sheets へ書き込み
#     write_entries_to_sheet(
#         entries=enriched["entries"],
#         date=enriched["date"],
#         summary=enriched["summary"]
#     )

#     # 後片付け
#     os.remove(temp_path)

#     return {
#         "status": "success",
#         "message": "処理が完了し、スプレッドシートに書き込みました。",
#         "ocr_text": ocr_text,
#         "journal": enriched
#     }



# app/routes/upload_and_process_router.py

from fastapi import APIRouter, UploadFile, File
import shutil
import tempfile
from app.service.ocr import extract_text_from_image
from app.service.gpt import convert_and_write_from_text

router = APIRouter()

@router.post("/upload")
async def upload_and_process(file: UploadFile = File(...)):
    # 一時ファイルとして保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    # OCRテキスト抽出 → GPT変換 → スプレッドシート書き込みまで一括処理
    return convert_and_write_from_text(extract_text_from_image(temp_path))
