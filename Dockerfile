FROM python:3.10-slim

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
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
    && rm -rf /var/lib/apt/lists/*

# Chrome & ChromeDriver を v122 に固定でインストール
RUN curl -sSL https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/122.0.6261.111/linux64/chrome-linux64.zip -o /tmp/chrome.zip && \
    unzip /tmp/chrome.zip -d /opt/ && \
    ln -s /opt/chrome-linux64/chrome /usr/bin/google-chrome && \
    chmod +x /usr/bin/google-chrome && \
    rm /tmp/chrome.zip

RUN curl -sSL https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/122.0.6261.111/linux64/chromedriver-linux64.zip -o /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# 必要パッケージのインストール（seleniumなど）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリをコピー
COPY . /app
WORKDIR /app

# 起動コマンド（例）
CMD ["python", "main.py"]
