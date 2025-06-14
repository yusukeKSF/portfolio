### app/main.py

from fastapi import FastAPI, UploadFile, File, Request
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
from app.routes.camera_ocr_router import process_ocr_and_send

# UI 実装ステップ 
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# アクセス回数を制限
from app.extensions.limiter import limiter
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse


app = FastAPI()
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "⚠️ アクセスが制限を超えました。しばらくしてから再度お試しください。"}
    )

# 静的ファイルのマウント
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# テンプレート読み込み
templates = Jinja2Templates(directory="app/templates")

# ルーター登録
app.include_router(sales.router, prefix="/journal")
app.include_router(purchase.router, prefix="/journal")
app.include_router(depreciation.router, prefix="/journal")
app.include_router(asset_purchase.router, prefix="/journal")
app.include_router(supplies_purchase.router, prefix="/journal")
# OCR用ルーター → プレフィックスを一元管理
app.include_router(camera_ocr_router.router, prefix="/camera")
# GPT関連
app.include_router(gpt.router, prefix="/text")
# カメラ機能用（videoや画像取得など）
app.include_router(camera_router)
# app.include_router(upload_and_process_router.router)




class GPTRequest(BaseModel):
    text: str
    
class WriteRequest(BaseModel):
    date: str
    summary: str
    entries: list[dict]

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

# UIルート デプロイ用
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

