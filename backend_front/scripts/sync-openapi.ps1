#!/usr/bin/env pwsh
# 同步OpenAPI文档脚本
# 从后端API获取最新的OpenAPI规范并更新前端的openapi.json文件

param(
    [string]$BackendUrl = "http://ai_study_backend:8000",
    [string]$OutputPath = "../openapi.json"
)

# 设置错误处理
$ErrorActionPreference = "Stop"

Write-Host "正在从 $BackendUrl/api/v1/openapi.json 获取OpenAPI规范..." -ForegroundColor Green

try {
    # 获取OpenAPI规范
    $response = Invoke-RestMethod -Uri "$BackendUrl/api/v1/openapi.json" -Method Get -ContentType "application/json"
    
    # 转换为格式化的JSON
    $jsonContent = $response | ConvertTo-Json -Depth 100
    
    # 获取输出文件的绝对路径
    $outputFile = Resolve-Path $OutputPath -ErrorAction SilentlyContinue
    if (-not $outputFile) {
        $outputFile = Join-Path (Get-Location) $OutputPath
    }
    
    # 写入文件
    $jsonContent | Out-File -FilePath $outputFile -Encoding UTF8
    
    Write-Host "OpenAPI规范已成功更新到: $outputFile" -ForegroundColor Green
    Write-Host "文件大小: $((Get-Item $outputFile).Length) 字节" -ForegroundColor Cyan
    
    # 验证JSON格式
    try {
        $null = Get-Content $outputFile | ConvertFrom-Json
        Write-Host "JSON格式验证通过" -ForegroundColor Green
    } catch {
        Write-Error "生成的JSON文件格式无效: $_"
        exit 1
    }
    
} catch {
    Write-Error "获取OpenAPI规范失败: $_"
    Write-Host "请确保后端服务正在运行并且可以访问 $BackendUrl" -ForegroundColor Yellow
    exit 1
}

Write-Host "同步完成!" -ForegroundColor Green