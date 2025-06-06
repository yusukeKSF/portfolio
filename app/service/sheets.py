### app/service/sheets.py

import os
import json
from typing import List
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9 以上対応
# メモリ使用量間使用
from app.monitor import monitor_memory

# 環境ごとの .env ファイルを読み込む（ローカル用）
env = os.getenv("ENV", "production")
dotenv_file = f".env.{env}"
if os.path.exists(dotenv_file):
    load_dotenv(dotenv_file)

# スコープと共通設定
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID_PROJECT_VISION")
SHEET_NAME = os.getenv("SHEET_NAME", "仕訳帳")

# ✅ 認証情報の切り替え（Render用JSON or ローカルファイル）
def get_credentials():
    json_str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if json_str:
        info = json.loads(json_str)
        return Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        return Credentials.from_service_account_file(creds_path, scopes=SCOPES)

@monitor_memory("スプレッドシートへの書き込み")
def write_entries_to_sheet(entries: List[dict], date: str, summary: str, bordered=False):
    print("📤 Google Sheetsへ書き込み開始", flush=True)
    
    creds = get_credentials()
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    
    # 東京時間（JST）に変換
    jst = ZoneInfo("Asia/Tokyo")
    timestamp = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

    values = []
    for i, entry in enumerate(entries):
        row = [
            date if i == 0 else "",
            entry["debit"],
            entry["amount"],
            entry["credit"],
            entry["amount"],
            summary if i == 0 else "",
            timestamp if i == 0 else ""  # 転記日時の記入
        ]
        values.append(row)

    existing_rows = len(worksheet.get_all_values())
    worksheet.append_rows(values, value_input_option="USER_ENTERED")
    print("✅ スプレッドシートに仕訳を追加しました。")

    # ✅ 罫線処理（任意）
    if bordered:
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        sheet_metadata = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()
        sheet_id = next(s["properties"]["sheetId"] for s in sheet_metadata["sheets"] if s["properties"]["title"] == SHEET_NAME)

        start_row = existing_rows + 1
        end_row = start_row + len(values)

        requests = [{
            "updateBorders": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_row - 1,
                    "endRowIndex": end_row - 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 7  # A〜G列
                },
                "top": {"style": "SOLID_MEDIUM"},
                "bottom": {"style": "SOLID_MEDIUM"},
                "left": {"style": "SOLID"},
                "right": {"style": "SOLID"},
                "innerVertical": {"style": "SOLID"}
            }
        }]
        sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": requests}).execute()
        # print("🖋️ 罫線を追加しました。")
