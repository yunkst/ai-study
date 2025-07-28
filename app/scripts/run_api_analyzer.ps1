# Flutter API分析器运行脚本
# 使用方法: .\scripts\run_api_analyzer.ps1 [参数]

param(
    [string]$Target = "lib",
    [string]$OpenApi = "assets/openapi.json",
    [string]$Output = $null,
    [switch]$Verbose = $false,
    [switch]$Help = $false
)

# 显示帮助信息
if ($Help) {
    Write-Host "🔍 Flutter API分析器 - PowerShell脚本" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "用法:"
    Write-Host "  .\scripts\run_api_analyzer.ps1 [-Target <路径>] [-OpenApi <文档路径>] [-Output <输出文件>] [-Verbose] [-Help]"
    Write-Host ""
    Write-Host "参数:"
    Write-Host "  -Target <路径>      要分析的文件或目录 (默认: lib)"
    Write-Host "  -OpenApi <路径>     OpenAPI文档路径 (默认: assets/openapi.json)"
    Write-Host "  -Output <文件>      输出报告文件路径"
    Write-Host "  -Verbose           显示详细输出"
    Write-Host "  -Help              显示此帮助信息"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .\scripts\run_api_analyzer.ps1"
    Write-Host "  .\scripts\run_api_analyzer.ps1 -Target lib/services/api_service.dart -Verbose"
    Write-Host "  .\scripts\run_api_analyzer.ps1 -Output report.txt"
    exit 0
}

# 检查Flutter/Dart是否已安装
function Test-DartInstallation {
    try {
        $dartVersion = dart --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Dart已安装: $dartVersion" -ForegroundColor Green
            return $true
        }
    } catch {
        # Dart未安装或不在PATH中
    }
    
    Write-Host "❌ 未找到Dart命令" -ForegroundColor Red
    Write-Host "请确保已安装Flutter SDK并将其添加到系统PATH中" -ForegroundColor Yellow
    Write-Host "下载地址: https://flutter.dev/docs/get-started/install" -ForegroundColor Yellow
    return $false
}

# 检查必要文件
function Test-RequiredFiles {
    $errors = @()
    
    if (-not (Test-Path "lib/tools/api_analyzer_cli.dart")) {
        $errors += "❌ API分析器工具不存在: lib/tools/api_analyzer_cli.dart"
    }
    
    if (-not (Test-Path $OpenApi)) {
        $errors += "❌ OpenAPI文档不存在: $OpenApi"
    }
    
    if (-not (Test-Path "pubspec.yaml")) {
        $errors += "❌ Flutter项目文件不存在: pubspec.yaml"
    }
    
    if ($errors.Count -gt 0) {
        Write-Host "发现以下问题:" -ForegroundColor Red
        $errors | ForEach-Object { Write-Host $_ -ForegroundColor Red }
        return $false
    }
    
    return $true
}

# 运行API分析器
function Invoke-ApiAnalyzer {
    $args = @("run", "lib/tools/api_analyzer_cli.dart")
    
    if ($Target -ne "lib") {
        $args += @("-t", $Target)
    }
    
    if ($OpenApi -ne "assets/openapi.json") {
        $args += @("-o", $OpenApi)
    }
    
    if ($Output) {
        $args += @("--output", $Output)
    }
    
    if ($Verbose) {
        $args += @("-v")
    }
    
    Write-Host "🔍 运行API分析器..." -ForegroundColor Cyan
    Write-Host "命令: dart $($args -join ' ')" -ForegroundColor Gray
    Write-Host ""
    
    try {
        & dart @args
        $exitCode = $LASTEXITCODE
        
        Write-Host ""
        if ($exitCode -eq 0) {
            Write-Host "✅ API分析完成，未发现问题" -ForegroundColor Green
        } else {
            Write-Host "❌ API分析发现问题，退出码: $exitCode" -ForegroundColor Red
        }
        
        if ($Output -and (Test-Path $Output)) {
            Write-Host "📄 报告已保存到: $Output" -ForegroundColor Cyan
        }
        
        return $exitCode
    } catch {
        Write-Host "❌ 运行分析器时发生错误: $($_.Exception.Message)" -ForegroundColor Red
        return 1
    }
}

# 主程序
Write-Host "🔍 Flutter API分析器" -ForegroundColor Cyan
Write-Host "=" * 50

# 检查Dart安装
if (-not (Test-DartInstallation)) {
    exit 1
}

# 检查必要文件
if (-not (Test-RequiredFiles)) {
    exit 1
}

# 获取依赖（如果需要）
if (Test-Path "pubspec.yaml") {
    Write-Host "📦 检查依赖..." -ForegroundColor Cyan
    try {
        flutter pub get | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 依赖已更新" -ForegroundColor Green
        } else {
            Write-Host "⚠️  依赖更新失败，继续分析..." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  无法运行flutter pub get，继续分析..." -ForegroundColor Yellow
    }
}

# 运行分析器
$exitCode = Invoke-ApiAnalyzer
exit $exitCode