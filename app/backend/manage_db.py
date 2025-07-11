#!/usr/bin/env python3
"""
数据库管理脚本
提供常用的 Alembic 迁移命令
"""

import sys
import os
from alembic.config import Config
from alembic import command

def get_alembic_config():
    """获取 Alembic 配置"""
    return Config("alembic.ini")

def init_db():
    """初始化数据库（首次创建迁移）"""
    print("📋 生成初始迁移文件...")
    try:
        config = get_alembic_config()
        command.revision(config, autogenerate=True, message="初始化数据库")
        print("✅ 初始迁移文件生成成功")
        
        print("📋 应用迁移到数据库...")
        command.upgrade(config, "head")
        print("✅ 数据库初始化完成")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")

def create_migration(message=None):
    """创建新的迁移文件"""
    if not message:
        message = input("输入迁移描述: ")
    
    print(f"📋 生成迁移文件: {message}")
    try:
        config = get_alembic_config()
        command.revision(config, autogenerate=True, message=message)
        print("✅ 迁移文件生成成功")
    except Exception as e:
        print(f"❌ 生成迁移失败: {e}")

def upgrade_db(revision="head"):
    """升级数据库到指定版本"""
    print(f"📋 升级数据库到版本: {revision}")
    try:
        config = get_alembic_config()
        command.upgrade(config, revision)
        print("✅ 数据库升级完成")
    except Exception as e:
        print(f"❌ 升级失败: {e}")

def downgrade_db(revision):
    """降级数据库到指定版本"""
    print(f"📋 降级数据库到版本: {revision}")
    try:
        config = get_alembic_config()
        command.downgrade(config, revision)
        print("✅ 数据库降级完成")
    except Exception as e:
        print(f"❌ 降级失败: {e}")

def show_history():
    """显示迁移历史"""
    print("📋 迁移历史:")
    try:
        config = get_alembic_config()
        command.history(config)
    except Exception as e:
        print(f"❌ 显示历史失败: {e}")

def show_current():
    """显示当前数据库版本"""
    print("📋 当前数据库版本:")
    try:
        config = get_alembic_config()
        command.current(config)
    except Exception as e:
        print(f"❌ 显示当前版本失败: {e}")

def show_help():
    """显示帮助信息"""
    print("""
🗃️  数据库管理脚本

用法: python manage_db.py <命令> [参数]

命令:
  init                    初始化数据库（首次使用）
  migrate <描述>          创建新的迁移文件
  upgrade [版本]          升级数据库（默认升级到最新）
  downgrade <版本>        降级数据库到指定版本
  history                 显示迁移历史
  current                 显示当前数据库版本
  help                    显示此帮助信息

示例:
  python manage_db.py init
  python manage_db.py migrate "添加用户表"
  python manage_db.py upgrade
  python manage_db.py downgrade -1
  python manage_db.py history
  python manage_db.py current
""")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command_name = sys.argv[1].lower()
    
    if command_name == "init":
        init_db()
    elif command_name == "migrate":
        message = sys.argv[2] if len(sys.argv) > 2 else None
        create_migration(message)
    elif command_name == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        upgrade_db(revision)
    elif command_name == "downgrade":
        if len(sys.argv) < 3:
            print("❌ 请指定降级版本")
            return
        downgrade_db(sys.argv[2])
    elif command_name == "history":
        show_history()
    elif command_name == "current":
        show_current()
    elif command_name == "help":
        show_help()
    else:
        print(f"❌ 未知命令: {command_name}")
        show_help()

if __name__ == "__main__":
    main() 