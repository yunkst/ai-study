@echo off
echo 🚀 测试AI学习助手服务状态...

echo 📱 测试前端服务 (端口3000)...
curl -s http://localhost:3000/health >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ 前端服务正常
) else (
    echo ❌ 前端服务异常
)

echo 🔧 测试后端API服务 (端口8080)...
curl -s http://localhost:8080/api/health >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ 后端API服务正常
) else (
    echo ❌ 后端API服务异常
)

echo 💾 测试数据库连接 (端口5432)...
netstat -an | find ":5432" >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ 数据库端口开放
) else (
    echo ❌ 数据库端口未开放
)

echo 🔄 测试Redis连接 (端口6379)...
netstat -an | find ":6379" >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Redis端口开放
) else (
    echo ❌ Redis端口未开放
)

echo.
echo 🌐 访问地址：
echo   前端应用: http://localhost:3000
echo   后端API: http://localhost:8080/docs
echo.
pause 