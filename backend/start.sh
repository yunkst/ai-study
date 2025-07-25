#!/bin/bash

# 等待数据库启动
echo "Waiting for database to be ready..."
while ! pg_isready -h postgres -p 5432 -U postgres; do
    echo "Database is not ready yet, waiting..."
    sleep 2
done

echo "Database is ready!"

# 执行数据库迁移检查
echo "Running database migration check..."
python manage.py auto-migrate

if [ $? -ne 0 ]; then
    echo "Database migration failed, exiting..."
    exit 1
fi

echo "Starting FastAPI application..."
# 启动应用
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload