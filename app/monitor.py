### app.monitor.py

import psutil
import os
import datetime

MEMORY_WARNING_THRESHOLD_MB = 500  # しきい値（MB）

def get_memory_mb() -> float:
    """現在のプロセスのメモリ使用量（MB）を返す"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # バイト → MB

def log_to_file(message: str):
    """ログをファイルに追記する"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "memory_usage.log")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def monitor_memory(tag: str = "メモリ計測"):
    """関数のメモリ使用量を測定しログ出力＋警告判定"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            before = get_memory_mb()
            print(f"[{tag}] 開始前メモリ: {before:.2f} MB")
            log_to_file(f"[{tag}] 開始前メモリ: {before:.2f} MB")

            result = func(*args, **kwargs)

            after = get_memory_mb()
            print(f"[{tag}] 終了後メモリ: {after:.2f} MB")
            log_to_file(f"[{tag}] 終了後メモリ: {after:.2f} MB")

            diff = after - before
            print(f"[{tag}] 増加量: {diff:.2f} MB")
            log_to_file(f"[{tag}] 増加量: {diff:.2f} MB")

            # メモリ使用量がしきい値を超えた場合に警告
            if after > MEMORY_WARNING_THRESHOLD_MB:
                warning = f"[{tag}] ⚠️ メモリ使用量が {MEMORY_WARNING_THRESHOLD_MB}MB を超えました！（{after:.2f} MB）"
                print(warning)
                log_to_file(warning)

            log_to_file("-" * 40)
            return result
        return wrapper
    return decorator
