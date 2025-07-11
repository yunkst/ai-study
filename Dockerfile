# 后端Docker构建文件 (开发模式 - 支持热重载)
FROM python:3.12.7

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 升级pip和setuptools以支持现代包管理
RUN pip install --upgrade pip setuptools wheel

# 设置工作目录
WORKDIR /app

# 复制项目文件（包含pyproject.toml和源码）
COPY app/backend/pyproject.toml ./

# 安装依赖（生产环境）
RUN pip install .

COPY app/backend/ ./

# 创建必要的目录
RUN mkdir -p data config logs

# 暴露端口
EXPOSE 8080

# 复制启动脚本
COPY app/backend/start.sh ./
RUN chmod +x start.sh

# 使用启动脚本（包含自动迁移）
CMD ["./start.sh"] 