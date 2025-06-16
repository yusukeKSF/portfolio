FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

# 🧰 必要パッケージのインストール
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg jq \
    libnss3 libatk-bridge2.0-0 libxss1 libasound2 libgtk-3-0 \
    libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libdrm2 \
    fonts-liberation \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# ✅ 最新のGoogle Chromeの安定版をインストール
RUN curl -O https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb

# ✅ Chromeのバージョンを取得して、それに合うChromeDriverをダウンロード
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+') && \
    echo "🌐 Installed Chrome version: $CHROME_VERSION" && \
    DRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json \
      | jq -r --arg ver "$CHROME_VERSION" '.versions[] | select(.version == $ver) | .downloads.chromedriver[] | select(.platform == "linux64") | .url') && \
    echo "🌐 ChromeDriver URL: $DRIVER_URL" && \
    wget -O /tmp/chromedriver.zip "$DRIVER_URL" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver.zip

# 🐍 Python依存のインストール
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
