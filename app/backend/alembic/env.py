"""
Alembic 环境配置
"""

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 导入所有模型以确保元数据完整
from models import user, question, practice, podcast, analytics, ai_config
from core.database import Base
from core.config import settings

# 这是 Alembic Config 对象，它提供对 .ini 文件中使用的值的访问
config = context.config

# 使用 asyncpg 驱动以兼容 async 引擎
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))

# 解释 config 文件中的日志记录
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加你的模型的 MetaData 对象在这里
# 对于 'autogenerate' 支持
target_metadata = Base.metadata

# 其他由 env.py 使用的值，在运行时由 alembic.ini 文件定义，
# 由 env.py 提供访问，可在这里配置。


def run_migrations_offline() -> None:
    """以'离线'模式运行迁移。

    这将 URL 配置为只是一个 URL，而不是一个引擎，
    但是一个引擎的 API 仍然可以通过起始事务上下文的方式使用，
    在任何试图实际连接到数据库之前。

    调用 context.execute() 和其他方法将会向脚本输出发出给定的字符串。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """运行迁移函数"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步模式下运行迁移"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """以'在线'模式运行迁移。

    在这种情况下，我们需要创建一个引擎并将连接与上下文关联。
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 