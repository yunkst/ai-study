#!/bin/bash
# 数据库迁移工具脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查并生成迁移
check_and_generate_migration() {
    log_info "检查数据库模型变化..."
    
    # 检查 alembic 是否初始化
    if [ ! -d "alembic/versions" ]; then
        log_error "Alembic 未初始化，请先运行 'alembic init alembic'"
        return 1
    fi
    
    # 检查是否有未应用的模型变化
    if uv run alembic check 2>/dev/null; then
        log_success "数据库模型与迁移文件同步"
        return 0
    else
        log_warning "检测到模型变化，生成新的迁移文件..."
        
        # 生成迁移文件
        local migration_message="${1:-Auto-generated migration at $(date '+%Y-%m-%d %H:%M:%S')}"
        
        # 尝试生成迁移
        if uv run alembic revision --autogenerate -m "$migration_message"; then
            log_success "迁移文件生成完成"
            
            # 显示生成的迁移文件
            local latest_migration=$(ls -t alembic/versions/*.py | head -1)
            if [ -f "$latest_migration" ]; then
                log_info "新生成的迁移文件: $(basename "$latest_migration")"
                
                # 显示迁移内容摘要
                log_info "迁移内容摘要:"
                grep -E "^def (upgrade|downgrade)" "$latest_migration" | head -2
            fi
            
            return 0
        else
            log_error "迁移文件生成失败"
            return 1
        fi
    fi
}

# 应用迁移
apply_migrations() {
    log_info "应用数据库迁移..."
    
    if uv run alembic upgrade head; then
        log_success "数据库迁移完成"
        
        # 显示当前迁移状态
        log_info "当前迁移状态:"
        uv run alembic current
        
        return 0
    else
        log_error "数据库迁移失败"
        return 1
    fi
}

# 显示迁移历史
show_migration_history() {
    log_info "迁移历史:"
    uv run alembic history --verbose
}

# 回滚迁移
rollback_migration() {
    local steps=${1:-1}
    log_warning "回滚 $steps 个迁移..."
    
    if uv run alembic downgrade -$steps; then
        log_success "迁移回滚完成"
        uv run alembic current
    else
        log_error "迁移回滚失败"
        return 1
    fi
}

# 主函数
main() {
    case "${1:-check}" in
        "check")
            check_and_generate_migration "$2"
            ;;
        "apply")
            apply_migrations
            ;;
        "auto")
            check_and_generate_migration "$2" && apply_migrations
            ;;
        "history")
            show_migration_history
            ;;
        "rollback")
            rollback_migration "$2"
            ;;
        *)
            echo "用法: $0 {check|apply|auto|history|rollback} [参数]"
            echo "  check [message]    - 检查并生成迁移文件"
            echo "  apply             - 应用迁移"
            echo "  auto [message]    - 自动检查、生成并应用迁移"
            echo "  history           - 显示迁移历史"
            echo "  rollback [steps]  - 回滚迁移（默认1步）"
            exit 1
            ;;
    esac
}

# 如果直接运行脚本
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi 