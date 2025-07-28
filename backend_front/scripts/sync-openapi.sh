#!/bin/bash
# 同步OpenAPI文档脚本
# 从后端API获取最新的OpenAPI规范并更新前端的openapi.json文件

BACKEND_URL="${1:-http://ai_study_backend:8000}"
OUTPUT_PATH="${2:-./openapi.json}"

echo "正在从 $BACKEND_URL/api/v1/openapi.json 获取OpenAPI规范..."

# 获取OpenAPI规范并保存到文件
if curl -s -f "$BACKEND_URL/api/v1/openapi.json" -o "$OUTPUT_PATH"; then
    echo "OpenAPI规范已成功更新到: $OUTPUT_PATH"
    echo "文件大小: $(stat -c%s "$OUTPUT_PATH") 字节"
    
    # 验证JSON格式
    if python3 -m json.tool "$OUTPUT_PATH" > /dev/null 2>&1; then
        echo "JSON格式验证通过"
        echo "同步完成!"
    else
        echo "错误: 生成的JSON文件格式无效"
        exit 1
    fi
else
    echo "错误: 获取OpenAPI规范失败"
    echo "请确保后端服务正在运行并且可以访问 $BACKEND_URL"
    exit 1
fi