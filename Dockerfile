FROM python:3.10-slim

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxss1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libgtk-3-0 \
    libu2f-udev \
    lsb-release \
    jq \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Google Chrome のリポジトリ追加
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable

# ✅ Chrome のバージョンに対応した ChromeDriver を自動で取得
# Chrome のバージョン確認
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+') && \
    DRIVER_VERSION=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json \
        | jq -r --arg ver "$CHROME_VERSION" '.versions[] | select(.version == $ver) | .downloads.chromedriver[] | select(.platform == "linux64") | .url') && \
    echo "Downloading chromedriver from $DRIVER_VERSION" && \
    wget -O /tmp/chromedriver.zip "$DRIVER_VERSION" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# 作業ディレクトリ・アプリケーションのコピー
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# ポートと実行コマンド
ENV PORT=8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
