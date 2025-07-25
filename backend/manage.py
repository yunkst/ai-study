#!/usr/bin/env python3
"""数据库管理CLI工具"""

import logging

import click

from app.db import models
from app.db.database import engine
from app.services.migration_service import migration_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """AI Study Platform 数据库管理工具"""
    pass

@cli.command()
def init_db():
    """初始化数据库"""
    click.echo("Initializing database...")
    try:
        # 创建所有表
        models.Base.metadata.create_all(bind=engine)
        click.echo("Database initialized successfully!")
    except Exception as e:
        click.echo(f"Failed to initialize database: {e}")
        raise click.Abort() from e

@cli.command()
@click.option('--message', '-m', default='Auto migration', help='Migration message')
def migrate(message):
    """生成迁移脚本"""
    click.echo(f"Generating migration: {message}")
    try:
        if migration_service.generate_migration(message):
            click.echo("Migration generated successfully!")
        else:
            click.echo("Failed to generate migration")
            raise click.Abort()
    except Exception as e:
        click.echo(f"Migration generation failed: {e}")
        raise click.Abort() from e

@cli.command()
def upgrade():
    """执行数据库迁移"""
    click.echo("Running database migrations...")
    try:
        if migration_service.run_migrations():
            click.echo("Migrations applied successfully!")
        else:
            click.echo("Failed to apply migrations")
            raise click.Abort()
    except Exception as e:
        click.echo(f"Migration failed: {e}")
        raise click.Abort() from e

@cli.command()
def check():
    """检查数据库状态"""
    click.echo("Checking database status...")
    try:
        # 检查数据库连接
        if migration_service.check_database_exists():
            click.echo("✓ Database connection: OK")
        else:
            click.echo("✗ Database connection: FAILED")
            return

        # 检查Alembic表
        if migration_service.check_alembic_table_exists():
            click.echo("✓ Alembic initialized: YES")

            # 检查当前版本
            current = migration_service.get_current_revision()
            head = migration_service.get_head_revision()

            click.echo(f"Current revision: {current or 'None'}")
            click.echo(f"Head revision: {head or 'None'}")

            # 检查待执行的迁移
            if migration_service.has_pending_migrations():
                click.echo("⚠ Pending migrations: YES")
            else:
                click.echo("✓ Pending migrations: NO")

            # 检查模型变更
            if migration_service.check_model_changes():
                click.echo("⚠ Model changes detected: YES")
            else:
                click.echo("✓ Model changes detected: NO")
        else:
            click.echo("✗ Alembic initialized: NO")

    except Exception as e:
        click.echo(f"Status check failed: {e}")
        raise click.Abort() from e

@cli.command()
def auto_migrate():
    """自动执行完整的迁移检查和更新"""
    click.echo("Starting automatic migration process...")
    try:
        if migration_service.startup_migration_check():
            click.echo("✓ Automatic migration completed successfully!")
        else:
            click.echo("✗ Automatic migration failed")
            raise click.Abort()
    except Exception as e:
        click.echo(f"Automatic migration failed: {e}")
        raise click.Abort() from e

if __name__ == '__main__':
    cli()
