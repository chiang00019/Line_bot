# 使用 Python 3.10
FROM python:3.10

# 設定工作目錄
WORKDIR /app

# 複製依賴檔案
COPY requirements.txt requirements.txt

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Playwright
RUN playwright install

# 複製程式碼
COPY . .

# 啟動 FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
