# 后端Docker构建文件 (开发模式 - 支持热重载)
FROM python:3.12.7

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制Python依赖文件
COPY app/backend/requirements.txt ./

# 安装Python依赖 (包括开发依赖)
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p data config logs

# 暴露端口
EXPOSE 8080

# 开发模式启动命令 (支持热重载)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload", "--reload-dir", "/app"] 