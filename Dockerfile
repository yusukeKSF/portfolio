FROM python:3.10-slim

# 環境変数設定（非対話モード、バイトコード未出力、バッファリング無効）
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 必要なシステムパッケージをインストール（Chrome + Selenium 動作に必要）
RUN apt-get update && apt-get install -y \
    curl unzip gnupg2 wget \
    fonts-liberation libnss3 libxss1 libasound2 libatk-bridge2.0-0 \
    libgtk-3-0 libx11-xcb1 libgbm1 libxdamage1 libxcomposite1 \
    libu2f-udev xdg-utils ca-certificates lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Chrome 137.0.7151.70 をインストール
RUN mkdir -p /opt && \
    curl -fSL https://storage.googleapis.com/chrome-for-testing-public/137.0.7151.70/linux64/chrome-linux64.zip -o /tmp/chrome.zip && \
    unzip /tmp/chrome.zip -d /opt/ && \
    ln -s /opt/chrome-linux64/chrome /usr/bin/google-chrome && \
    rm -f /tmp/chrome.zip

# ChromeDriver 137.0.7151.70 をインストール
RUN curl -fSL https://storage.googleapis.com/chrome-for-testing-public/137.0.7151.70/linux64/chromedriver-linux64.zip -o /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver*

# 作業ディレクトリ作成
WORKDIR /app

# 依存関係のインストール（キャッシュ活用）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# FastAPI アプリを起動（本番向けには --reload を外す）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
