### app/utils.py
# 日付補完　 会計期間や決算日の補完が行われる

import re
from datetime import datetime

# 会計期間パターン（MM-DD）の抽出（start/endのみ）
def extract_fiscal_mmdd_period(text: str) -> tuple[str | None, str | None]:
    """
    例：「4月1日から3月31日までの会計年度」のような文から、
    開始・終了日（MM-DD形式）を抽出。
    Returns: (start_mmdd, end_mmdd)
    """
    pattern = r"(\d{1,2})月(\d{1,2})日から(\d{1,2})月(\d{1,2})日"
    match = re.search(pattern, text)
    if match:
        start = f"{int(match.group(1)):02d}-{int(match.group(2)):02d}"
        end = f"{int(match.group(3)):02d}-{int(match.group(4)):02d}"
        return start, end
    return None, None

# 初年度の決算日を導出
def derive_calc_closing_date(acquisition_date: str, fiscal_end_mmdd: str) -> str | None:
    """
    資産取得日と会計期間の終了MM-DDから、
    初年度の決算日（YYYY-MM-DD）を導出。
    - 会計年度が1月開始以外の場合、決算年は「期首の年 + 1」
    """
    try:
        acq_date = datetime.strptime(acquisition_date, "%Y-%m-%d")
        fiscal_month, fiscal_day = map(int, fiscal_end_mmdd.split("-"))
        closing_year = acq_date.year

        # 会計期間の終了日が 1月〜12月以外 → 翌年を決算年とする
        # 例：2025-04-01 取得 → 決算日 2026-03-31
        if acq_date.month > fiscal_month or (acq_date.month == fiscal_month and acq_date.day > fiscal_day):
            closing_year += 1
        else:
            closing_year = acq_date.year

        return f"{closing_year}-{fiscal_month:02d}-{fiscal_day:02d}"

    except Exception as e:
        print(f"❌ calc_closing_date 推定失敗: {e}")
        return None


# GPT→FastAPIデータ変換に fiscal dates を補完
def merge_fiscal_dates_into_gpt(gpt_data: dict, ocr_text: str):
    _, fiscal_end = extract_fiscal_mmdd_period(ocr_text)
    if gpt_data.get("type") == "depreciation":
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

    return gpt_data


def convert_entries(debit_entries, credit_entries):
    entries = []

    # 借方が複数、貸方が1つ → 金額ごとに分割対応
    if len(credit_entries) == 1 and len(debit_entries) >= 1:
        credit = credit_entries[0]
        for debit in debit_entries:
            entries.append({
                "debit": debit["account"],
                "credit": credit["account"],
                "amount": debit["amount"]
            })

    # 貸方が複数、借方が1つ → 同様に対応
    elif len(debit_entries) == 1 and len(credit_entries) >= 1:
        debit = debit_entries[0]
        for credit in credit_entries:
            entries.append({
                "debit": debit["account"],
                "credit": credit["account"],
                "amount": credit["amount"]
            })

    # 上記以外 → 借方・貸方をそれぞれ単体で entry に
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

    return entries

    