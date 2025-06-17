FROM python:3.10-slim

# 環境変数（インタラクティブでない設定、pipキャッシュ無効）
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 基本ツール・Selenium用ライブラリ・Chromeに必要なパッケージ
RUN apt-get update && apt-get install -y \
    curl unzip gnupg2 wget \
    fonts-liberation libnss3 libxss1 libasound2 libatk-bridge2.0-0 \
    libgtk-3-0 libx11-xcb1 libgbm1 libxdamage1 libxcomposite1 \
    libu2f-udev xdg-utils ca-certificates lsb-release \
    && rm -rf /var/lib/apt/lists/*

# ChromeとChromeDriverのバージョン固定 (137.0.7151.70)
RUN mkdir -p /opt/ && \
    echo "📦 Chrome ダウンロード開始..." && \
    curl -fSL https://storage.googleapis.com/chrome-for-testing-public/137.0.7151.70/linux64/chrome-linux64.zip -o /tmp/chrome.zip && \
    unzip /tmp/chrome.zip -d /opt/ && \
    ln -s /opt/chrome-linux64/chrome /usr/bin/google-chrome && \
    echo "✅ Chrome インストール完了" && \
    \
    echo "📦 ChromeDriver ダウンロード開始..." && \
    curl -fSL https://storage.googleapis.com/chrome-for-testing-public/137.0.7151.70/linux64/chromedriver-linux64.zip -o /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    echo "✅ ChromeDriver インストール完了" && \
    rm -rf /tmp/*

# 作業ディレクトリ作成
WORKDIR /app

# requirements を先にコピー・インストール（キャッシュ効率のため）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードをすべてコピー
COPY . .

# FastAPI起動 (必要に応じて uvicorn のオプションを調整)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
