FROM python:3.10-slim

# 必須パッケージ
RUN apt-get update && apt-get install -y curl unzip && apt-get clean

# Chromeダウンロードと展開（ログ出力付き）
RUN mkdir -p /opt/ && \
    curl -fSL https://storage.googleapis.com/chrome-for-testing-public/137.0.7151.70/linux64/chrome-linux64.zip -o /tmp/chrome.zip && \
    ls -lh /tmp/chrome.zip && \
    unzip -l /tmp/chrome.zip && \
    unzip /tmp/chrome.zip -d /opt/ && \
    rm -f /usr/bin/google-chrome && \
    ln -s /opt/chrome-linux64/chrome /usr/bin/google-chrome

# ChromeDriverダウンロードと展開（ログ出力付き）
RUN curl -fSL https://storage.googleapis.com/chrome-for-testing-public/137.0.7151.70/linux64/chromedriver-linux64.zip -o /tmp/chromedriver.zip && \
    ls -lh /tmp/chromedriver.zip && \
    unzip -l /tmp/chromedriver.zip && \
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
