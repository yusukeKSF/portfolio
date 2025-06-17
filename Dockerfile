FROM python:3.10-slim

# 基本的なツールをインストール
RUN apt-get update && apt-get install -y curl unzip && apt-get clean

# ChromeとDriverのインストール
RUN mkdir -p /opt/ && \
    curl -fSL https://storage.googleapis.com/chrome-for-testing-public/137.0.7151.70/linux64/chrome-linux64.zip -o /tmp/chrome.zip && \
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
