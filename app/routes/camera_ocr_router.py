#  app/routes/camera_ocr_router.py

from fastapi import APIRouter, UploadFile, File, Request
from app.main import limiter
import shutil
import tempfile
from app.service.ocr import extract_text_from_image
from app.service.gpt import convert_and_write_from_text 
from fastapi import HTTPException

MAX_FILE_SIZE_MB = 8  # 上限サイズ（MB）
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


router = APIRouter()


@router.post("/convert_and_write")
@limiter.limit("5/minute")  # IP単位で1分間に最大5リクエスト
async def process_ocr_and_send(request: Request, file: UploadFile = File(...)):
    
    # ✅ ファイルサイズをチェック
    file.file.seek(0, 2)  # ファイルの終端へ移動
    file_size = file.file.tell()
    file.file.seek(0)  # 読み込み位置を先頭に戻す

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"ファイルサイズが大きすぎます。{MAX_FILE_SIZE_MB}MB以下にしてください。"
        )
    
    # ✅ 一時ファイルに保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_file_path = temp_file.name

    # ✅ OCRテキスト抽出
    text = extract_text_from_image(temp_file_path)

    # ✅ GPT→enrich→スプレッドシート書き込みを一括処理
    return convert_and_write_from_text(text)


#============================================================================
# 開発段階のバックアップ

# # ✅画像ファイル受信 → OCR → GPT → スプレッドシート書き込み処理
# @router.post("/convert_and_write")
# async def process_ocr_and_send(file: UploadFile = File(...)):
#     # ✅ 一時ファイルに保存
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
#         shutil.copyfileobj(file.file, temp_file)
#         temp_file_path = temp_file.name

#     # ✅ OCRテキスト抽出
#     text = extract_text_from_image(temp_file_path)

#     # # ✅ GPTで仕訳生成
#     # gpt_data = generate_journal_entries(text)

#     # # ✅ 減価償却補完など enrich 処理
#     # enriched = process_gpt_and_enrich(gpt_data, text)

#     # # ✅ Google Sheets 書き込み
#     # write_entries_to_sheet(
#     #     entries=enriched["entries"],
#     #     date=enriched["date"],
#     #     summary=enriched["summary"]
#     # )

#     # ✅　gpt.py 側の共通処理関数で一括処理（target_year対応含む） 
#     #　　　　 共通ロジックを活用し、減価償却の日付処理も含めて統一
#     return convert_and_write_from_text(text)



# ==============================================================================
###  OpenCVなどからカメラフレームを直接処理したい場合に 必要。

# import numpy as np
# from app.service.ocr import extract_text_from_frame

# ### 処理を1つの関数にカプセル化
# # この関数で 画像からOCR出力　→ GPTに送信 → 減価償却の金額の補完 → Google Sheets への書き込み → ログ保存
# def process_ocr_and_send(frame: np.ndarray):
#     # OCR処理
#     ocr_text = extract_text_from_frame(frame)
#     print("📝 OCR抽出テキスト:", ocr_text)

#     # GPT処理
#     journal = generate_journal_entries(ocr_text)

#     # enrich（減価償却など）
#     enriched = process_gpt_and_enrich(journal, ocr_text)

#     # 書き込み処理
#     write_entries_to_sheet(
#         entries=enriched["entries"],
#         date=enriched["date"],
#         summary=enriched["summary"]
#     )

#     return {
#         "status": "success",
#         "message": "スプレッドシートに書き込みました",
#         "ocr_text": ocr_text,
#         "journal": enriched
#     }

