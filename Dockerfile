# ベースイメージ
FROM python:3.10-slim

# 環境変数（Chromeの警告抑制）
ENV DEBIAN_FRONTEND=noninteractive

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    jq \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libdrm2 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# ✅ Google Chrome 最新版をインストール
RUN wget -O chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && apt install -y ./chrome.deb && rm chrome.deb

# ✅ Chrome のバージョンを取得して一致する ChromeDriver を自動取得
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+') && \
    echo "Detected Chrome version: $CHROME_VERSION" && \
    DRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json \
    | jq -r --arg ver "$CHROME_VERSION" '.versions[] | select(.version == $ver) | .downloads.chromedriver[] | select(.platform == "linux64") | .url') && \
    echo "Downloading ChromeDriver from $DRIVER_URL" && \
    wget -O /tmp/chromedriver.zip "$DRIVER_URL" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# Python依存パッケージインストール
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコピー
COPY . .

# ポート指定（Renderでは 8000 が必要）
EXPOSE 8000

# アプリの起動コマンド（適宜変更）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
