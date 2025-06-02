### send_camera_image.py

import requests

# 📸 送信したい画像ファイルのパス
image_path = "images/test3.png"  # カメラで撮影した画像ファイルを指定

# 🎯 FastAPIサーバーのURL（ローカル or デプロイ先に応じて修正）
url = "http://localhost:8000/camera/convert_and_write"

# 📤 画像をmultipart/form-dataで送信
with open(image_path, "rb") as f:
    files = {"file": (image_path, f, "image/jpeg")}
    response = requests.post(url, files=files)


# 🖨 結果を表示
print("📬 サーバー応答:", response.status_code)
print(response.json())


