#!/bin/bash
set -e

echo "=== AI图表系统开发环境启动 (uv) ==="

# 设置uv镜像源
export UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
export UV_TRUSTED_HOST=mirrors.aliyun.com
echo "✓ 配置uv使用阿里云镜像源"

# 等待数据库连接
echo "等待数据库连接..."
while ! pg_isready -h "${DATABASE_HOST:-postgres}" -p "${DATABASE_PORT:-5432}" -U "${DATABASE_USER:-postgres}" -d "${DATABASE_NAME:-ai_study}"; do
    echo "等待 PostgreSQL 启动..."
    sleep 2
done
echo "✓ 数据库连接成功"

# 暂时跳过自动迁移生成，避免镜像源问题
# TODO: 修复镜像源问题后重新启用
echo "⚠️ 跳过自动迁移生成（镜像源问题）"
cd /app

# 只尝试应用现有迁移，不生成新的
echo "应用现有迁移..."
if uv run alembic upgrade head 2>/dev/null; then
    echo "✓ 迁移应用成功"
else
    echo "⚠️ 迁移应用失败，继续启动服务..."
fi

# 创建测试数据库（如果不存在）
echo "检查测试数据库..."
export PGPASSWORD="${DATABASE_PASSWORD:-postgres123}"

# 使用更简单的方法检查数据库是否存在
if psql -h "${DATABASE_HOST:-postgres}" -U "${DATABASE_USER:-postgres}" -c "SELECT 1 FROM pg_database WHERE datname='ai_study_test'" 2>/dev/null | grep -q "1 row"; then
    echo "✓ 测试数据库已存在"
else
    echo "创建测试数据库..."
    if psql -h "${DATABASE_HOST:-postgres}" -U "${DATABASE_USER:-postgres}" -c "CREATE DATABASE ai_study_test;" 2>/dev/null; then
        echo "✓ 测试数据库创建成功"
    else
        echo "⚠️ 测试数据库创建失败或已存在，继续启动..."
    fi
fi

unset PGPASSWORD

# 跳过显示迁移状态（避免uv镜像源问题）
echo "⚠️ 跳过显示迁移状态（镜像源问题）"
echo ""

# 显示开发环境信息
echo "=== 开发环境信息 ==="
echo "📊 后端API:          http://localhost:8001"
echo "🗄️  PostgreSQL:      localhost:5433 (postgres/postgres123)"
echo "🔴 Redis:            localhost:6380"
echo "⚡ Trino:            http://localhost:8081"
echo "🧪 测试数据库:       ai_chart_test"
echo ""
echo "=== 常用命令 (uv) ==="
echo "运行测试:            uv run pytest"
echo "查看覆盖率:          uv run pytest --cov=app"
echo "代码格式化:          uv run black ."
echo "类型检查:            uv run mypy ."
echo "手动生成迁移:        uv run alembic revision --autogenerate -m 'description'"
echo "查看迁移历史:        uv run alembic history"
echo "回滚迁移:            uv run alembic downgrade -1"
echo ""
echo "=== uv 包管理 ==="
echo "添加依赖:            uv add <package>"
echo "添加开发依赖:        uv add --dev <package>"
echo "移除依赖:            uv remove <package>"
echo "同步依赖:            uv sync"
echo "锁定依赖:            uv lock"
echo ""

# 启动应用（使用python直接启动，避免uv镜像源问题）
echo "启动开发服务器..."
# 设置Python路径
export PYTHONPATH=/app:$PYTHONPATH
# 直接使用python启动，避免uv问题
exec python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 "${@}"