#!/usr/bin/env python3
"""
Docker 环境数据库迁移脚本
适用于容器启动时的自动迁移
"""

import sys
import os
import asyncio
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alembic.config import Config
from alembic import command
from core.config import settings
from sqlalchemy import create_engine, text

# 使用同步引擎检测数据库就绪，避免事件循环嵌套
sync_engine = create_engine(settings.DATABASE_URL)


def get_alembic_config():
    """获取 Alembic 配置"""
    config = Config(os.path.join(project_root, "alembic.ini"))
    # 动态设置数据库URL，使用异步驱动以兼容 Alembic env.py
    async_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    config.set_main_option("sqlalchemy.url", async_url)
    return config


def wait_for_database():
    """同步等待数据库服务就绪"""
    print("⏳ 等待数据库服务就绪...")
    max_retries = 60
    retry_count = 0

    while retry_count < max_retries:
        try:
            with sync_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                print(f"❌ 数据库连接失败，已重试 {max_retries} 次: {e}")
                return False
            print(f"⏳ 等待数据库... ({retry_count}/{max_retries})")
            time.sleep(2)


def check_migration_table():
    """检查是否存在迁移版本表"""
    try:
        config = get_alembic_config()
        command.current(config)
        return True
    except Exception:
        return False


def create_initial_migration():
    """创建初始迁移"""
    try:
        print("📋 生成初始迁移文件...")
        config = get_alembic_config()
        command.revision(config, autogenerate=True, message="初始化数据库")
        print("✅ 初始迁移文件生成成功")
        return True
    except Exception as e:
        print(f"❌ 生成初始迁移失败: {e}")
        return False


def apply_migrations():
    """应用迁移"""
    try:
        print("📋 应用数据库迁移...")
        config = get_alembic_config()
        command.upgrade(config, "head")
        print("✅ 数据库迁移应用成功")
        return True
    except Exception as e:
        print(f"❌ 应用迁移失败: {e}")
        return False


def show_current_version():
    """显示当前数据库版本"""
    try:
        config = get_alembic_config()
        print("📊 当前数据库版本:")
        command.current(config)
    except Exception as e:
        print(f"⚠️ 无法显示当前版本: {e}")


def run_auto_migration():
    """同步自动迁移流程（适用于容器启动）"""
    print("🚀 开始自动数据库迁移流程...")

    if not wait_for_database():
        print("❌ 数据库连接失败，退出")
        return False

    if not check_migration_table():
        print("ℹ️ 未发现迁移历史，创建初始迁移...")
        if not create_initial_migration():
            print("❌ 初始迁移创建失败，退出")
            return False
    else:
        print("ℹ️ 发现现有迁移历史")

    if not apply_migrations():
        print("❌ 迁移应用失败，退出")
        return False

    show_current_version()
    print("✅ 自动迁移流程完成")
    return True


def create_migration(message):
    """手动创建迁移"""
    print(f"📋 创建新迁移: {message}")
    try:
        config = get_alembic_config()
        command.revision(config, autogenerate=True, message=message)
        print("✅ 迁移创建成功")
        return True
    except Exception as e:
        print(f"❌ 创建迁移失败: {e}")
        return False


def show_help():
    """显示帮助"""
    print("""
🐳 Docker 环境数据库迁移工具

用法:
  python scripts/migrate.py <命令> [参数]

命令:
  auto                    自动迁移（容器启动时使用）
  create <描述>           手动创建迁移
  upgrade                 应用迁移到最新版本
  current                 显示当前版本
  history                 显示迁移历史
  help                    显示帮助

示例:
  # 容器启动自动迁移
  python scripts/migrate.py auto
  
  # 手动创建迁移
  python scripts/migrate.py create "添加新字段"
  
  # 升级数据库
  python scripts/migrate.py upgrade
""")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command_name = sys.argv[1].lower()
    
    if command_name == "auto":
        # 自动迁移（异步）
        result = run_auto_migration()
        sys.exit(0 if result else 1)
        
    elif command_name == "create":
        if len(sys.argv) < 3:
            print("❌ 请提供迁移描述")
            return
        create_migration(sys.argv[2])
        
    elif command_name == "upgrade":
        apply_migrations()
        
    elif command_name == "current":
        show_current_version()
        
    elif command_name == "history":
        try:
            config = get_alembic_config()
            command.history(config)
        except Exception as e:
            print(f"❌ 显示历史失败: {e}")
            
    elif command_name == "help":
        show_help()
        
    else:
        print(f"❌ 未知命令: {command_name}")
        show_help()


if __name__ == "__main__":
    main() 