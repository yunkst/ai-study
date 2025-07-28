FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装uv
RUN pip install uv -i https://mirrors.aliyun.com/pypi/simple/

# 配置uv使用阿里云源
ENV UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV UV_TRUSTED_HOST=mirrors.aliyun.com

# 安装必要的系统依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    curl \
    # 数据库客户端
    postgresql-client \
    # 构建工具（Python包编译需要）
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制项目配置文件和 README
COPY pyproject.toml .
COPY README.md .

# 直接在系统环境中安装依赖（不使用虚拟环境）
RUN uv pip install -e . --system

# 复制项目文件
COPY . .

# 重新同步依赖以确保所有文件都正确
RUN uv pip install -e . --system

# 创建开发用的脚本目录
RUN mkdir -p /app/scripts

# 确保启动脚本存在并有执行权限
RUN chmod +x /app/scripts/dev-entrypoint.sh

# 创建便捷脚本
RUN echo '#!/bin/bash\n\
echo "=== AI图表系统开发环境 (uv) ==="\n\
echo "可用命令:"\n\
echo "  uv run pytest              - 运行测试"\n\
echo "  uv run pytest --cov        - 运行测试并生成覆盖率报告"\n\
echo "  uv run black .             - 格式化代码"\n\
echo "  uv run isort .             - 整理导入"\n\
echo "  uv run flake8 .            - 代码检查"\n\
echo "  uv run mypy .              - 类型检查"\n\
echo "  uv run bandit -r .         - 安全检查"\n\
echo "  uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000 - 启动开发服务器"\n\
echo ""\n\
echo "uv 命令:"\n\
echo "  uv add <package>           - 添加依赖"\n\
echo "  uv remove <package>        - 移除依赖"\n\
echo "  uv pip install -e . --system - 安装项目到系统环境"\n\
echo "  uv lock                    - 锁定依赖版本"\n\
echo ""\n\
echo "数据库连接测试:"\n\
echo "  psql -h postgres_dev -U postgres -d ai_chart"\n\
echo "  redis-cli -h redis_dev"\n\
echo ""\n\
echo "当前目录: $(pwd)"\n\
echo "Python版本: $(python --version)"\n\
echo "uv版本: $(uv --version)"\n\
' > /app/scripts/dev-info.sh && chmod +x /app/scripts/dev-info.sh

# 创建测试脚本
RUN echo '#!/bin/bash\n\
echo "运行完整测试套件..."\n\
uv run pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing\n\
echo ""\n\
echo "测试报告生成在 htmlcov/ 目录"\n\
' > /app/scripts/run-tests.sh && chmod +x /app/scripts/run-tests.sh

# 创建代码质量检查脚本
RUN echo '#!/bin/bash\n\
echo "=== 代码质量检查 ==="\n\
echo "1. 代码格式化..."\n\
uv run black --check .\n\
echo "2. 导入排序检查..."\n\
uv run isort --check-only .\n\
echo "3. 代码风格检查..."\n\
uv run flake8 .\n\
echo "4. 类型检查..."\n\
uv run mypy . || echo "类型检查完成（可能有警告）"\n\
echo "5. 安全检查..."\n\
uv run bandit -r . -f json -o security-report.json || echo "安全检查完成"\n\
echo ""\n\
echo "所有检查完成！"\n\
' > /app/scripts/quality-check.sh && chmod +x /app/scripts/quality-check.sh

# 创建数据库工具脚本
RUN echo '#!/bin/bash\n\
echo "=== 数据库工具 ==="\n\
echo "1. 等待数据库连接..."\n\
until pg_isready -h postgres_dev -p 5432 -U postgres; do\n\
  echo "等待 PostgreSQL 启动..."\n\
  sleep 2\n\
done\n\
echo "数据库连接测试..."\n\
psql -h postgres_dev -U postgres -d ai_chart -c "SELECT version();" || echo "数据库连接测试完成"\n\
echo ""\n\
echo "数据库准备完成！"\n\
' > /app/scripts/db-setup.sh && chmod +x /app/scripts/db-setup.sh

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 设置脚本权限
RUN chmod +x /app/scripts/migration-utils.sh

# 将脚本添加到 PATH
ENV PATH="/app/scripts:${PATH}"

# 默认命令启动应用
CMD ["python", "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
