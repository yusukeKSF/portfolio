### app/service/sheets.py

import os
from typing import List
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

env = os.getenv("ENV", "production")
dotenv_file = f".env.{env}"
load_dotenv(dotenv_file)


SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID_PROJECT_VISION")
SHEET_NAME = os.getenv("SHEET_NAME", "仕訳帳")


def write_entries_to_sheet(entries: List[dict], date: str, summary: str, bordered=False):
    print("📤 Google Sheetsへ書き込み開始")
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

    values = []
    for i, entry in enumerate(entries):
        row = [
            date if i == 0 else "",
            entry["debit"],
            entry["amount"],
            entry["credit"],
            entry["amount"],
            summary if i == 0 else ""
        ]
        values.append(row)
    
    # # 現在の最終行取得（1-indexed）
    # start_row = len(worksheet.get_all_values()) + 1
    # worksheet.append_rows(values, value_input_option="USER_ENTERED")
    # print("✅ スプレッドシートに仕訳を追加しました。")

    # ✅ 罫線処理が必要な場合
    # 1. 書き込み前に現在の行数を取得
    existing_rows = len(worksheet.get_all_values())

    # 2. 行の追加
    worksheet.append_rows(values, value_input_option="USER_ENTERED")
    print("✅ スプレッドシートに仕訳を追加しました。")

    # 3. 必要なら罫線を追加
    if bordered:
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        sheet_metadata = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()
        sheet_id = next(s["properties"]["sheetId"] for s in sheet_metadata["sheets"] if s["properties"]["title"] == SHEET_NAME)

        start_row = existing_rows + 1
        end_row = start_row + len(values)

        requests = [{
        # {
            "updateBorders": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_row - 1,
                    "endRowIndex": end_row -1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 6  # A〜F列に対応
                },
                "top": {"style": "SOLID_MEDIUM"},
                "bottom": {"style": "SOLID_MEDIUM"},
                "left": {"style": "SOLID"},
                "right": {"style": "SOLID"},
                # "innerHorizontal": {"style": "SOLID"},
                "innerVertical": {"style": "SOLID"}
            }
        # },

        }]
        sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": requests}).execute()
        print("🖋️ 罫線を追加しました。")




