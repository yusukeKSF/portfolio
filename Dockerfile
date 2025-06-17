FROM python:3.10-slim

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    jq \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# ChromeとChromeDriverのインストール（v137.0.7151.70）
RUN curl -fSL https://storage.googleapis.com/chrome-for-testing-public/137.0.7151.70/linux64/chrome-linux64.zip -o /tmp/chrome.zip && \
    ls -lh /tmp/chrome.zip && \
    unzip /tmp/chrome.zip -d /opt/ && \
    ln -s /opt/chrome-linux64/chrome /usr/bin/google-chrome && \
    curl -fSL https://storage.googleapis.com/chrome-for-testing-public/137.0.7151.70/linux64/chromedriver-linux64.zip -o /tmp/chromedriver.zip && \
    ls -lh /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/*.zip


# 作業ディレクトリ
WORKDIR /app

# Python依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリコードの追加
COPY . .

CMD ["python", "main.py"]
