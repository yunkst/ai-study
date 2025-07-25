"""数据库迁移服务模块

提供数据库迁移相关的功能，包括检查数据库状态、执行迁移等。
"""
import logging
import subprocess
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import SessionLocal, engine

logger = logging.getLogger(__name__)

class MigrationService:
    """数据库迁移服务"""

    def __init__(self):
        self.alembic_dir = Path(__file__).parent.parent.parent / "alembic"
        self.versions_dir = self.alembic_dir / "versions"

    def check_database_exists(self) -> bool:
        """检查数据库是否存在"""
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error("Database connection failed: %s", e)
            return False

    def check_alembic_table_exists(self) -> bool:
        """检查alembic_version表是否存在"""
        try:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            return "alembic_version" in tables
        except SQLAlchemyError as e:
            logger.error("Failed to check alembic table: %s", e)
            return False

    def get_current_revision(self) -> str | None:
        """获取当前数据库版本"""
        try:
            with SessionLocal() as db:
                result = db.execute(text("SELECT version_num FROM alembic_version"))
                row = result.fetchone()
                return row[0] if row else None
        except SQLAlchemyError as e:
            logger.error("Failed to get current revision: %s", e)
            return None

    def get_head_revision(self) -> str | None:
        """获取最新的迁移版本"""
        try:
            result = subprocess.run(
                ["alembic", "heads"],
                cwd=Path(__file__).parent.parent.parent,
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout.strip()
            if output:
                # 提取版本号（通常是第一个单词）
                return output.split()[0]
            return None
        except subprocess.CalledProcessError as e:
            logger.error("Failed to get head revision: %s", e)
            return None

    def has_pending_migrations(self) -> bool:
        """检查是否有待执行的迁移"""
        current = self.get_current_revision()
        head = self.get_head_revision()

        if current is None and head is not None:
            return True

        if current != head:
            return True

        return False

    def run_migrations(self) -> bool:
        """执行数据库迁移"""
        try:
            logger.info("Running database migrations...")
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                cwd=Path(__file__).parent.parent.parent,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Migration output: %s", result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Migration failed: %s", e.stderr)
            return False

    def init_alembic(self) -> bool:
        """初始化Alembic（如果还没有初始化）"""
        try:
            if not self.alembic_dir.exists():
                logger.info("Initializing Alembic...")
                subprocess.run(
                    ["alembic", "init", "alembic"],
                    cwd=Path(__file__).parent.parent.parent,
                    check=True
                )
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to initialize Alembic: %s", e)
            return False

    def generate_migration(self, message: str = "Auto-generated migration") -> bool:
        """生成新的迁移脚本"""
        try:
            logger.info("Generating migration: %s", message)
            result = subprocess.run(
                ["alembic", "revision", "--autogenerate", "-m", message],
                cwd=Path(__file__).parent.parent.parent,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Migration generation output: %s", result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to generate migration: %s", e.stderr)
            return False

    def check_model_changes(self) -> bool:
        """检查模型是否有变更（通过比较当前状态和数据库状态）"""
        try:
            # 使用alembic check命令来检查是否有未应用的变更
            result = subprocess.run(
                ["alembic", "check"],
                cwd=Path(__file__).parent.parent.parent,
                capture_output=True,
                text=True,
                check=False
            )

            # 如果返回码不为0，说明有变更
            if result.returncode != 0:
                logger.info("Model changes detected: %s", result.stdout)
                return True
            return False
        except subprocess.CalledProcessError as e:
            # 如果alembic check不支持，使用备用方法
            logger.warning("alembic check failed, using alternative method: %s", e)
            return self._check_model_changes_alternative()

    def _check_model_changes_alternative(self) -> bool:
        """备用的模型变更检查方法"""
        try:
            # 尝试生成一个临时迁移文件来检查变更
            import os
            import tempfile

            with tempfile.TemporaryDirectory():

                result = subprocess.run(
                    ["alembic", "revision", "--autogenerate", "-m", "temp_check"],
                    cwd=Path(__file__).parent.parent.parent,
                    capture_output=True,
                    text=True,
                    check=False
                )

                if result.returncode == 0:
                    # 检查生成的最新迁移文件
                    versions_dir = Path(__file__).parent.parent.parent / "alembic" / "versions"
                    if versions_dir.exists():
                        migration_files = list(versions_dir.glob("*.py"))
                        if migration_files:
                            latest_file = max(migration_files, key=os.path.getctime)
                            with open(latest_file, encoding='utf-8') as f:
                                content = f.read()
                                # 检查是否包含实际的迁移操作
                                if "def upgrade():" in content:
                                    upgrade_section = content.split("def upgrade():")[1].split("def downgrade()")[0]
                                    if "pass" not in upgrade_section.strip():
                                        # 删除临时生成的迁移文件
                                        os.remove(latest_file)
                                        return True
                            # 删除临时生成的迁移文件（如果只包含pass）
                            os.remove(latest_file)

                return False
        except (subprocess.CalledProcessError, OSError, ValueError) as e:
            logger.error("Alternative model change check failed: %s", e)
            return False

    def startup_migration_check(self) -> bool:
        """启动时的迁移检查和执行"""
        logger.info("Starting migration check...")

        # 1. 检查数据库连接
        if not self.check_database_exists():
            logger.error("Database connection failed")
            return False

        # 2. 检查是否已初始化Alembic
        if not self.check_alembic_table_exists():
            logger.info("Alembic not initialized, running initial migration...")
            # 创建初始迁移
            if not self.generate_migration("Initial migration"):
                return False
            # 执行迁移
            if not self.run_migrations():
                return False
        else:
            # 3. 检查是否有待执行的迁移
            if self.has_pending_migrations():
                logger.info("Found pending migrations, applying...")
                if not self.run_migrations():
                    return False

        # 4. 检查模型是否有新的变更
        if self.check_model_changes():
            logger.info("Detected model changes, generating new migration...")
            if not self.generate_migration("Auto-generated model changes"):
                return False
            # 执行新生成的迁移
            if not self.run_migrations():
                return False

        logger.info("Migration check completed successfully")
        return True

migration_service = MigrationService()
