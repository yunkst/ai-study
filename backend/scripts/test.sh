#!/bin/bash

# 测试运行脚本
# 用于运行AI图表系统的测试套件

set -e

echo "🧪 AI图表系统测试框架 (uv)"
echo "========================="

# 检查uv是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ 错误: uv 未安装"
    echo "请先安装 uv: pip install uv"
    exit 1
fi

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 虚拟环境: $VIRTUAL_ENV"
else
    echo "⚠️  警告: 未检测到虚拟环境"
fi

# 检查测试数据库URL
if [[ -z "$TEST_DATABASE_URL" ]]; then
    echo "⚠️  警告: 未设置 TEST_DATABASE_URL 环境变量"
    echo "请设置: export TEST_DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/ai_study_test"
fi

# 解析命令行参数
COMMAND="all"
COVERAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--unit)
            COMMAND="unit"
            shift
            ;;
        -a|--api)
            COMMAND="api"
            shift
            ;;
        -i|--integration)
            COMMAND="integration"
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -u, --unit        运行单元测试"
            echo "  -a, --api         运行API测试" 
            echo "  -i, --integration 运行集成测试"
            echo "  -c, --coverage    生成覆盖率报告"
            echo "  -h, --help        显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                运行所有测试"
            echo "  $0 -u             运行单元测试"
            echo "  $0 -u -c          运行单元测试并生成覆盖率报告"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 -h 查看帮助"
            exit 1
            ;;
    esac
done

# 构建pytest命令
PYTEST_CMD="uv run pytest"

# 添加覆盖率选项
if [[ "$COVERAGE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=term-missing --cov-report=html"
fi

# 根据命令类型运行测试
case $COMMAND in
    unit)
        echo "🔧 运行单元测试..."
        $PYTEST_CMD tests/unit/ -v
        ;;
    api)
        echo "🌐 运行API测试..."
        $PYTEST_CMD tests/api/ -v
        ;;
    integration)
        echo "🔗 运行集成测试..."
        $PYTEST_CMD tests/integration/ -v
        ;;
    all)
        echo "🚀 运行所有测试..."
        $PYTEST_CMD tests/ -v
        ;;
esac

# 显示覆盖率报告位置
if [[ "$COVERAGE" == true ]]; then
    echo ""
    echo "📊 覆盖率报告已生成:"
    echo "  - 终端输出: 上方显示"
    echo "  - HTML报告: htmlcov/index.html"
fi

echo ""
echo "✅ 测试完成!"