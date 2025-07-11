#!/bin/bash

# Docker 容器启动脚本
# 包含数据库迁移和应用启动

set -e  # 遇到错误时退出

echo "🐳 启动 AI 学习助手后端服务..."

# 设置工作目录
cd /app

# 等待依赖服务启动
echo "⏳ 等待依赖服务启动..."
sleep 5

# 运行数据库迁移
echo "🔄 运行数据库迁移..."
python scripts/migrate.py auto

# 检查迁移是否成功
if [ $? -eq 0 ]; then
    echo "✅ 数据库迁移成功"
else
    echo "❌ 数据库迁移失败，尝试回退到直接建表模式"
    # 如果迁移失败，仍然继续启动应用，让应用内的init_db处理
fi

# 启动应用
echo "🚀 启动 FastAPI 应用..."
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port 8080 \
    --reload \
    --log-level info 