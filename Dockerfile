FROM python:3.10-slim

# 基本ツールとライブラリのインストール
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgbm1 \
    libasound2 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    ffmpeg \
    tesseract-ocr \
    fonts-liberation \
    xdg-utils \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Google Chromeの安定版をインストール（バイナリを直接）
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable

# ✅ ChromeDriver（バージョンをChromeに合わせる）
RUN CHROME_VERSION=$(google-chrome-stable --version | grep -oP '[0-9.]+' | head -1) && \
    DRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" | grep -B 10 "\"version\": \"$CHROME_VERSION\"" | grep "linux64" | grep "chromedriver" | head -1 | cut -d '"' -f 4) && \
    wget -O /tmp/chromedriver.zip "$DRIVER_VERSION" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# 作業ディレクトリとアプリコピー
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
