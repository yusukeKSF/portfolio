### app/main.py

from fastapi import FastAPI, UploadFile, File
from fastapi import Body
from app.service.ocr import extract_text_from_image
from app.service.gpt import generate_journal_entries
from app.service.sheets import write_entries_to_sheet
from app.schemas import GPTRequest, WriteRequest
from app.handlers import sales, purchase, depreciation, asset_purchase, supplies_purchase
from pydantic import BaseModel
from app.service import gpt
from app.routes import camera_ocr_router
# from app.routes import upload_and_process_router
from app.routes.camera_ocr_router import router as camera_router
# ✅ main.py の修正
from app.routes.camera_ocr_router import process_ocr_and_send



app = FastAPI()

# ルーター登録
app.include_router(sales.router, prefix="/journal")
app.include_router(purchase.router, prefix="/journal")
app.include_router(depreciation.router, prefix="/journal")
app.include_router(asset_purchase.router, prefix="/journal")
app.include_router(supplies_purchase.router, prefix="/journal")
app.include_router(gpt.router)
app.include_router(camera_ocr_router.router, prefix="/camera")
app.include_router(gpt.router, prefix="/text")
# app.include_router(upload_and_process_router.router)
app.include_router(camera_router)


class GPTRequest(BaseModel):
    text: str
    
class WriteRequest(BaseModel):
    date: str
    summary: str
    entries: list[dict]

@app.get("/")
def root():
    return {"message": "FastAPI is running."}

@app.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    contents = await file.read()
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(contents)
    text = extract_text_from_image(file_path)
    return {"text": text}

@app.post("/generate")
def generate_endpoint(req: GPTRequest):
    journal = generate_journal_entries(req.text)
    return journal

@app.post("/write")
def write_endpoint(req: WriteRequest):
    entries = [entry.dict() for entry in req.entries]
    write_entries_to_sheet(entries, req.date, req.summary)
    return {"status": "success", "message": "スプレッドシートに書き込みました"}


@app.post("/upload")
async def upload_and_process(file: UploadFile = File(...)):
    # UploadFile をそのまま camera_ocr_router に渡して処理
    return await process_ocr_and_send(file)

# @app.post("/upload")
# async def upload_and_process(file: UploadFile = File(...)):
#     temp_path = f"temp_images/{file.filename}"
#     with open(temp_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     # OCR → GPT → スプレッドシートへの書き込み処理
#     frame = cv2.imread(temp_path)
#     result = process_ocr_and_send(frame)

#     return result  # OCRテキスト、GPT結果、書き込み結果を含む



# /generate と /write を1回のPOSTで完了するため統合
# @app.post("/convert_and_write")
# def convert_and_write(req: GPTRequest):
#     journal = generate_journal_entries(req.text)
#     entries = [entry for entry in journal["entries"]]
#     write_req = WriteRequest(
#         date=journal["date"],
#         summary=journal["summary"],
#         entries=entries
#     )
# @app.post("/convert_and_write")
# def convert_and_write(req: GPTRequest):
#     return gpt.convert_and_write_from_text(req.text)
