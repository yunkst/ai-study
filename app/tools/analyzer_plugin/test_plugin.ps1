Write-Host "🧪 测试 API 验证插件结构..." -ForegroundColor Green

$allTestsPassed = $true

# 检查插件文件结构
Write-Host "`n📁 检查插件文件结构..." -ForegroundColor Yellow

$files = @(
    "bin\plugin.dart",
    "lib\api_validator_plugin.dart",
    "lib\utils\openapi_loader.dart",
    "lib\rules\api_path_rule.dart",
    "lib\rules\api_schema_rule.dart",
    "lib\rules\api_method_rule.dart",
    "pubspec.yaml",
    "README.md"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file (缺失)" -ForegroundColor Red
        $allTestsPassed = $false
    }
}

# 检查主项目配置
Write-Host "`n🔧 检查主项目配置..." -ForegroundColor Yellow

$analysisFile = "..\..\analysis_options.yaml"
if (Test-Path $analysisFile) {
    $content = Get-Content $analysisFile -Raw
    if ($content -match "tools/analyzer_plugin") {
        Write-Host "✅ analysis_options.yaml 已配置插件" -ForegroundColor Green
    } else {
        Write-Host "❌ analysis_options.yaml 未配置插件" -ForegroundColor Red
        $allTestsPassed = $false
    }
} else {
    Write-Host "❌ analysis_options.yaml 不存在" -ForegroundColor Red
    $allTestsPassed = $false
}

# 检查依赖配置
Write-Host "`n📦 检查依赖配置..." -ForegroundColor Yellow

if (Test-Path "pubspec.yaml") {
    $content = Get-Content "pubspec.yaml" -Raw
    
    if ($content -match "analyzer") {
        Write-Host "✅ 依赖 analyzer 已配置" -ForegroundColor Green
    } else {
        Write-Host "❌ 依赖 analyzer 未配置" -ForegroundColor Red
        $allTestsPassed = $false
    }
    
    if ($content -match "analyzer_plugin") {
        Write-Host "✅ 依赖 analyzer_plugin 已配置" -ForegroundColor Green
    } else {
        Write-Host "❌ 依赖 analyzer_plugin 未配置" -ForegroundColor Red
        $allTestsPassed = $false
    }
} else {
    Write-Host "❌ pubspec.yaml 不存在" -ForegroundColor Red
    $allTestsPassed = $false
}

# 输出测试结果
Write-Host "`n==================================================" -ForegroundColor Cyan

if ($allTestsPassed) {
    Write-Host "🎉 所有测试通过！插件结构完整。" -ForegroundColor Green
    Write-Host "📋 下一步: 配置 Flutter/Dart 环境后运行 flutter analyze" -ForegroundColor Yellow
} else {
    Write-Host "❌ 部分测试失败，请检查上述错误。" -ForegroundColor Red
    exit 1
}

Write-Host "🔧 手动验证: 创建错误API调用测试文件，运行 flutter analyze" -ForegroundColor Yellow