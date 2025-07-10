#!/bin/bash

echo "🚀 测试AI学习助手服务状态..."

# 测试前端服务
echo "📱 测试前端服务 (端口3000)..."
if curl -s http://localhost:3000/health > /dev/null; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端服务异常"
fi

# 测试后端API
echo "🔧 测试后端API服务 (端口8080)..."
if curl -s http://localhost:8080/api/health > /dev/null; then
    echo "✅ 后端API服务正常"
else
    echo "❌ 后端API服务异常"
fi

# 测试数据库连接
echo "💾 测试数据库连接 (端口5432)..."
if nc -z localhost 5432; then
    echo "✅ 数据库连接正常"
else
    echo "❌ 数据库连接异常"
fi

# 测试Redis连接
echo "🔄 测试Redis连接 (端口6379)..."
if nc -z localhost 6379; then
    echo "✅ Redis连接正常"
else
    echo "❌ Redis连接异常"
fi

echo ""
echo "🌐 访问地址："
echo "  前端应用: http://localhost:3000"
echo "  后端API: http://localhost:8080/docs"
echo "" 