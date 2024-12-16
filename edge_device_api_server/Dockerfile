# 使用官方的Python基礎鏡像
FROM python:3.11.4

# 設定工作目錄
WORKDIR /app

# 將requirements.txt 複製到工作目錄
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 將目前目錄的內容複製到工作目錄
COPY server.py .

# 暴露應用的端口
EXPOSE 5555

# 設定環境變量，以便 Flask 在容器中執行
ENV DB_HOST="mysql-service.default.svc.cluster.local"

# 運行應用
CMD ["python", "server.py"]
