### app/logger.py
# ログを作成し追跡可能にしておく
# gpt.py で４箇所でログ記入

import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def save_log(content: str, prefix: str = "log") -> str:
    """
    任意のテキストを timestamp 付きのファイルとして保存する。
    Returns: 保存されたファイルパス（str）
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = LOG_DIR / f"{prefix}_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📄 ログ保存: {filename}")
    return str(filename)

def save_json(data: dict, prefix: str = "gpt_output") -> str:
    """
    dict を JSON形式でファイル保存する。
    """
    import json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = LOG_DIR / f"{prefix}_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"📄 JSONログ保存: {filename}")
    return str(filename)
