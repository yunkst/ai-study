"""
数据库配置和连接管理
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

from .config import settings

# 同步数据库连接
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 异步数据库连接
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG
)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# ORM基类
Base = declarative_base()

def get_db():
    """获取同步数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    """初始化数据库表"""
    import asyncio
    import time
    import subprocess
    import os
    
    print("🔄 开始数据库初始化...")
    
    # 等待数据库服务就绪（Docker环境）
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 测试数据库连接
            async with async_engine.begin() as conn:
                # 使用 text 对象执行简单查询，兼容 SQLAlchemy 2.x
                await conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功")
            break
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                print(f"❌ 数据库连接失败，已重试 {max_retries} 次: {e}")
                return
            print(f"⏳ 等待数据库就绪... ({retry_count}/{max_retries})")
            await asyncio.sleep(2)
    
    # 通过独立的子进程运行迁移脚本，避免asyncio冲突
    try:
        script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "migrate.py")
        process = await asyncio.create_subprocess_exec(
            "python", script_path, "auto",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print("❌ 数据库迁移脚本执行失败:")
            print(stderr.decode())
            raise Exception("数据库迁移失败")
        else:
            print("✅ 数据库迁移脚本执行成功。")
            print(stdout.decode())

        print("✅ 数据库迁移完成")
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        # 如果迁移失败，回退到创建表的方式
        print("🔄 回退到直接建表模式...")
        try:
            from models import user, question, practice, podcast, analytics, ai_config
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ 数据库表初始化完成（回退模式）")
        except Exception as fallback_error:
            print(f"❌ 回退建表也失败: {fallback_error}")
            raise 