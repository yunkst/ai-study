#!/usr/bin/env python3
"""
后端测试运行脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def run_tests():
    """运行测试套件"""
    
    # 设置测试环境
    os.environ["TESTING"] = "true"
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🧪 运行后端测试套件...")
    print(f"📁 工作目录: {project_root}")
    print()
    
    # 基础pytest命令
    pytest_cmd = [
        "python", "-m", "pytest",
        "-v",                    # 详细输出
        "--tb=short",           # 短格式错误信息
        "--cov=.",              # 代码覆盖率
        "--cov-report=term-missing",  # 显示未覆盖的行
        "--cov-report=html:htmlcov",  # HTML报告
    ]
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "unit":
            pytest_cmd.extend(["-m", "unit"])
            print("🔧 运行单元测试...")
        elif sys.argv[1] == "api":
            pytest_cmd.extend(["-m", "api"])
            print("🌐 运行API测试...")
        elif sys.argv[1] == "auth":
            pytest_cmd.extend(["-m", "auth"])
            print("🔐 运行认证测试...")
        elif sys.argv[1] == "integration":
            pytest_cmd.extend(["-m", "integration"])
            print("🔗 运行集成测试...")
        elif sys.argv[1] == "fast":
            pytest_cmd.extend(["-m", "not slow"])
            print("⚡ 运行快速测试...")
        elif sys.argv[1] == "coverage":
            pytest_cmd.extend(["--cov-fail-under=80"])
            print("📊 运行代码覆盖率检查...")
        else:
            pytest_cmd.append(sys.argv[1])
            print(f"🎯 运行指定测试: {sys.argv[1]}")
    else:
        print("🚀 运行全部测试...")
    
    print()
    
    try:
        # 运行pytest
        result = subprocess.run(pytest_cmd, check=True)
        
        print()
        print("✅ 测试完成！")
        print()
        print("📊 查看详细报告:")
        print(f"   HTML覆盖率报告: file://{project_root}/htmlcov/index.html")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print()
        print("❌ 测试失败！")
        print(f"   退出码: {e.returncode}")
        return e.returncode
    
    except KeyboardInterrupt:
        print()
        print("🛑 测试被用户中断")
        return 1

def show_help():
    """显示帮助信息"""
    print("🧪 后端测试运行器")
    print()
    print("用法:")
    print("  python test_runner.py [选项]")
    print()
    print("选项:")
    print("  unit         运行单元测试")
    print("  api          运行API测试")
    print("  auth         运行认证测试")
    print("  integration  运行集成测试")
    print("  fast         运行快速测试（跳过慢速测试）")
    print("  coverage     运行代码覆盖率检查")
    print("  <文件名>     运行指定测试文件")
    print()
    print("示例:")
    print("  python test_runner.py                    # 运行全部测试")
    print("  python test_runner.py unit               # 只运行单元测试")
    print("  python test_runner.py tests/test_auth.py # 运行认证测试文件")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        show_help()
        sys.exit(0)
    
    sys.exit(run_tests()) 