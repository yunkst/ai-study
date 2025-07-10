@echo off
echo ================================
echo 快速重启开发环境
echo ================================

echo 正在重启服务...
docker-compose restart

echo 重启完成!
echo 前端访问地址: http://localhost:3000
echo 后端API地址: http://localhost:8080
echo ================================
pause 