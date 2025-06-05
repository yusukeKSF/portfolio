### app/service/gpt.py

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from app.service.sheets import write_entries_to_sheet
from app.service.depreciation_calc import calculate_depreciation_by_year
from app.utils import extract_fiscal_mmdd_period, derive_calc_closing_date, convert_entries
from app import logger
from fastapi import APIRouter
import numpy as np
from datetime import datetime
import re
# from collections import defaultdict


env = os.getenv("ENV", "production")
dotenv_file = f".env.{env}"
load_dotenv(dotenv_file)

api_key = os.getenv("OPENAI_API_KEY_PROJECT_VISION")
project_id = os.getenv("OPENAI_PROJECT_ID")


if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY が読み込まれていません。")
if not project_id:
    raise RuntimeError("❌ OPENAI_PROJECT_ID が読み込まれていません。")

client = OpenAI(api_key=api_key, project=project_id)

class GPTRequest(BaseModel):
    text: str
    
class WriteRequest(BaseModel):
    date: str
    summary: str
    entries: list[dict]


def generate_journal_entries(text: str) -> dict:
    print("🧠 GPTに問い合わせ中...")
    prompt = f"""
以下の日本語文はOCRで抽出された会計取引の記録です。
この文書から取引内容を読み取り、JSON形式で会計仕訳を出力してください。

# 出力ルール：
- 出力は JSON のみ。説明や注釈は含めないでください。
- 取引日付を必ず `date` フィールドに "YYYY-MM-DD" 形式で含めてください。省略しないでください。
- 金額（amount）は半角数値、カンマは使用しないこと。
- `entries` の配列に、借方（debit）と貸方（credit）を分けて記述してください。
- `"depreciation"`についての金額はシステムが後で計算するため、`amount: 0` で構いません。それ以外は `amount: 0` の出力を禁止。

# 取引タイプ判定：
以下の type のいずれかを判定し、出力に含めてください。

- `"purchase"`：仕入取引
- `"sales"`：売上取引
- `"supplies_purchase"`：消耗品など即時費用処理の購入
- `"asset_purchase"`：備品などの固定資産購入（減価償却対象）
- `"depreciation"`：減価償却（固定資産の年次償却）
- `"unknown"`：該当なしまたは不明

# 以下の勘定科目ルールに従ってください：

- 「手形を受け取った」「手形で受け取った」は "受取手形" を使用
- 「手形で支払った」「手形で支払う」は "支払手形" を使用
- 「手形受取」「手形支払」などの曖昧な語は使わないでください

# 補足ルール：

- 「〇〇を仕入れた」→ type: `"purchase"`、debit: `"仕入"`
- 「〇〇を購入した」→ contextに応じて `"supplies_purchase"` か `"asset_purchase"` に分類
- 「掛け払い」「未払い」等があれば：
- purchase系は credit: `"買掛金"`（それ以外は `"未払金"`）
- sales系は credit: `"売掛金"`
- 支払・受取方法の記載がない場合、現金処理とする
- 手形の受け取りは debit: `"受取手形"`
- 手形による支払いは credit:`"支払手形"`
- 減価償却時は debit: `"減価償却費"`, credit: `"減価償却累計額"`
- 売上取引（type: "sales"）では、「売上」は必ず `credit_entries` に含めてください
- 金額が20万円を超える`"supplies_purchase"`の場合は、`"備品"`に分類する

---

# JSON出力形式（全タイプ共通）：

{{
  "type": "purchase"｜"sales"｜"depreciation"｜"supplies_purchase"｜"asset_purchase"｜"unknown",
  "date": "YYYY-MM-DD",
  "summary": "取引の概要（簡潔に）",
  "supplier": "仕入先名（任意）",
  "customer": "顧客名（任意）",
  "asset_name": "資産名（必要な場合）",
  "acquisition_date": "取得日（固定資産用）",
  "calc_closing_date": "初年度決算日（減価償却用）",
  "target_year": "償却対象年度末（減価償却用）",
  "closing_date": "target_yearと同じ値を設定（必須）",
  "method": "償却方法（例：定額法、200%定率法、級数法、生産高比例法）",
  "amount": 資産原価（数値）,
  "life": 耐用年数（整数）,
  "current_volume": 生産量（生産高比例法時のみ）,
  "total_volume": 総生産可能量（同上）,
  "debit_entries": [ {{"account": "勘定科目", "amount": 金額}} ],
  "credit_entries": [ {{"account": "勘定科目", "amount": 金額}} ]
}}

---

# 減価償却取引（type: "depreciation"）に関する特別指示：

- `summary`: 例「機械の減価償却」など簡潔に記述
- `asset_name`: 対象資産（例："機械", "車両運搬具"）
- `acquisition_date`: 資産の取得日（YYYY-MM-DD）
- `calc_closing_date`: 初年度の決算日（取得年度末）
- `target_year`: 今回取得したい償却年度末（例：2025-03-31）
- `closing_date`: `target_year` と同一に設定すること
- `method`: 償却方法（"定率法" → "200%定率法" に変換）
- `amount`: 取得価格（半角数値）
- `life`: 耐用年数（整数）
- `entries`: 金額は `0` で良い（後でシステム計算）

## 生産高比例法の場合：
- `method`: "生産高比例法"
- `current_volume`: 当期生産量（整数）
- `total_volume`: 総生産可能量（整数）
- `amount`: 取得原価

注意事項：
- `calc_closing_date` は資産を取得した初年度の決算日でフォームに入力する決算日です（通常は取得日の年 + 会計年度末）。
- `target_year` はテーブルから減価償却費を取得したい年度の決算日です（例：2025-03-31）。
---

以下が対象の取引文です：

{text}
"""


    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "あなたは会計士です。JSONだけを出力してください。余計な説明を含めないでください。"},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content
    print("📥 GPT応答:", content)
    # ログを保存
    logger.save_log(prompt, prefix="gpt_prompt")
    logger.save_log(content, prefix="gpt_response")

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("❌ GPTの出力がJSONとして解析できませんでした。\n出力:\n" + content)
    


# 減価償却費の自動取得 (会計年度補正)→ 金額反映 → スプレッドシート書き込みまで一貫
def process_gpt_and_enrich(gpt_data: dict, ocr_text: str) -> dict:
    _, fiscal_end = extract_fiscal_mmdd_period(ocr_text)
    if not fiscal_end:
        fiscal_end = "03-31"

    logger.save_log(ocr_text, prefix="ocr_text")
    
    if gpt_data.get("type") == "depreciation":
        # 減価償却 → 特別処理（単一entry構造）
        acquisition_date = gpt_data.get("acquisition_date")
        if acquisition_date and fiscal_end:
            gpt_data["calc_closing_date"] = derive_calc_closing_date(acquisition_date, fiscal_end)

        # closing_date（当期末）と target_year（当期）を抽出
        fiscal_year_match = re.search(r"(\d{4})年.*?(\d{4})年(\d{1,2})月(\d{1,2})日", ocr_text)
        if fiscal_year_match:
            _, year, month, day = fiscal_year_match.groups()
            gpt_data["closing_date"] = f"{year}-{int(month):02d}-{int(day):02d}"
            gpt_data["target_year"] = gpt_data["closing_date"]

        # fiscal year補完（必要な場合）
        if not gpt_data.get("closing_date"):
            gpt_data["closing_date"] = gpt_data.get("calc_closing_date")
        if not gpt_data.get("target_year"):
            gpt_data["target_year"] = gpt_data.get("closing_date")
            
        # 減価償却方法の変換：定率法 → 200%定率法
        gpt_method = gpt_data.get("method", "")
        if gpt_method == "定率法":
            gpt_data["method"] = "200%定率法"
            
    
        # 減価償却費の自動取得（最優先）
        try:
            dep = calculate_depreciation_by_year(
                starting_date=gpt_data.get("acquisition_date"),
                calc_closing_date=gpt_data.get("calc_closing_date"),
                method=gpt_data.get("method"),
                price=gpt_data.get("amount"),
                life=gpt_data.get("life"),
                target_year=gpt_data.get("target_year"),
                current_volume=gpt_data.get("current_volume"),
                total_volume=gpt_data.get("total_volume")
            )
            
        except Exception as e:
            print(f"❌ 減価償却費取得エラー: {e}")
            dep = None

        # 資産名付き減価償却累計額として帳簿を記録する
        credit_title = f"{gpt_data.get('asset_name', '')}減価償却累計額"
        gpt_data["entries"] = [{
            "debit": "減価償却費",
            "credit": credit_title,
            "amount": dep if dep is not None else 0
        }]
    else:
        # 複数明細処理 勘定科目の合算は行わない
        debit_entries = gpt_data.get("debit_entries", [])
        credit_entries = gpt_data.get("credit_entries", [])
        entries = []
        
        # 対応：貸方が1件なら繰り返して複数借方に対応
        if len(credit_entries) == 1 and len(debit_entries) > 1:
            credit = credit_entries[0]
            for debit in debit_entries:
                entries.append({
                    "debit": debit["account"],
                    "credit": credit["account"],
                    "amount": debit["amount"]
                })
        elif len(debit_entries) == 1 and len(credit_entries) > 1:
            debit = debit_entries[0]
            for credit in credit_entries:
                entries.append({
                    "debit": debit["account"],
                    "credit": credit["account"],
                    "amount": credit["amount"]
                })
        else:
            for debit in debit_entries:
                entries.append({
                    "debit": debit["account"],
                    "credit": "",
                    "amount": debit["amount"]
                })
            for credit in credit_entries:
                entries.append({
                    "debit": "",
                    "credit": credit["account"],
                    "amount": credit["amount"]
                })

        # 共通entries生成（convert_entriesを使う） 余分な金額表示を防止
        entries = convert_entries(debit_entries, credit_entries)

        gpt_data["entries"] = entries
        


    logger.save_json(gpt_data, prefix="gpt_enriched")
    
    return gpt_data



# 仕訳の生成からシートへの書き込み
def convert_and_write_from_text(text: str):
    gpt_data = generate_journal_entries(text)
    enriched = process_gpt_and_enrich(gpt_data, text)
    
    target_year = enriched.get("target_year")
    if not target_year or not isinstance(target_year, str) or len(target_year) < 8:
        target_year = None

    # ✅ 減価償却は target_year 優先、それ以外は date 優先
    if enriched.get("type") == "depreciation":
        date = (
            enriched.get("target_year") or
            enriched.get("closing_date") or
            enriched.get("calc_closing_date") or
            enriched.get("date") or
            enriched.get("acquisition_date") or
            datetime.now().strftime("%Y-%m-%d")
        )
    else:
        date = (
            enriched.get("date") or
            datetime.now().strftime("%Y-%m-%d")
        )

    print("📄 書き込み内容:")
    print(f"🕓 使用する記帳日付: {date}")
    for e in enriched["entries"]:
        print(f"- {e}")

    write_entries_to_sheet(
        entries=enriched["entries"],
        date=date,
        summary=enriched["summary"],
        bordered=True
    )

    # ✅ enriched を返す
    return {
        "status": "success",
        "message": "スプレッドシートに書き込みました",
        "journal": enriched
    }

router = APIRouter()

@router.post("/convert_and_write")
def convert_and_write_endpoint(req: GPTRequest):
    return convert_and_write_from_text(req.text)
