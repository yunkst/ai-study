@echo off
echo ================================
echo 系统架构设计师学习辅助平台
echo 开发环境启动脚本
echo ================================

echo 正在停止现有容器...
docker-compose down

echo 正在清理构建缓存...
docker-compose build --no-cache

echo 正在启动开发环境...
docker-compose up

echo 开发环境已启动!
echo 前端访问地址: http://localhost:3000
echo 后端API地址: http://localhost:8080
echo ================================
pause 