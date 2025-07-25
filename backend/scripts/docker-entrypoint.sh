#!/bin/bash
set -e

echo "=== AI图表系统后端启动 (uv) ==="

# 等待数据库连接
echo "等待数据库连接..."
while ! pg_isready -h "${DATABASE_HOST:-postgres}" -p "${DATABASE_PORT:-5432}" -U "${DATABASE_USER:-postgres}" -d "${DATABASE_NAME:-ai_study}"; do
    echo "等待 PostgreSQL 启动..."
    sleep 2
done
echo "✓ 数据库连接成功"

# 自动检查、生成并应用迁移
cd /app
source /app/scripts/migration-utils.sh
main "auto" "Auto-generated production migration at $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 启动应用
echo "启动FastAPI应用..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 "${@}"