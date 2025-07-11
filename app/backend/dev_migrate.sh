#!/bin/bash

# 开发环境数据库迁移便捷脚本
# 在 Docker 容器中运行迁移命令

SERVICE_NAME="ai-tutor-backend-1"  # Docker compose 服务名称

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐳 Docker 环境数据库迁移工具${NC}"

# 检查参数
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}用法:${NC}"
    echo "  ./dev_migrate.sh <命令> [参数]"
    echo ""
    echo -e "${YELLOW}命令:${NC}"
    echo "  create <描述>    创建新迁移"
    echo "  upgrade          升级到最新版本"
    echo "  current          显示当前版本"
    echo "  history          显示迁移历史"
    echo "  auto             运行自动迁移"
    echo "  shell            进入容器shell"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo "  ./dev_migrate.sh create \"添加用户表\""
    echo "  ./dev_migrate.sh upgrade"
    echo "  ./dev_migrate.sh current"
    exit 1
fi

COMMAND=$1

# 检查 Docker 容器是否运行
if ! docker ps | grep -q $SERVICE_NAME; then
    echo -e "${RED}❌ 后端容器未运行，请先启动：${NC}"
    echo "  docker compose up backend"
    exit 1
fi

case $COMMAND in
    "create")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ 请提供迁移描述${NC}"
            exit 1
        fi
        echo -e "${YELLOW}📋 创建迁移: $2${NC}"
        docker exec -it $SERVICE_NAME python scripts/migrate.py create "$2"
        ;;
    
    "upgrade")
        echo -e "${YELLOW}📋 升级数据库到最新版本${NC}"
        docker exec -it $SERVICE_NAME python scripts/migrate.py upgrade
        ;;
    
    "current")
        echo -e "${YELLOW}📊 显示当前数据库版本${NC}"
        docker exec -it $SERVICE_NAME python scripts/migrate.py current
        ;;
    
    "history")
        echo -e "${YELLOW}📚 显示迁移历史${NC}"
        docker exec -it $SERVICE_NAME python scripts/migrate.py history
        ;;
    
    "auto")
        echo -e "${YELLOW}🔄 运行自动迁移${NC}"
        docker exec -it $SERVICE_NAME python scripts/migrate.py auto
        ;;
    
    "shell")
        echo -e "${YELLOW}🔧 进入容器 shell${NC}"
        docker exec -it $SERVICE_NAME bash
        ;;
    
    *)
        echo -e "${RED}❌ 未知命令: $COMMAND${NC}"
        exit 1
        ;;
esac 