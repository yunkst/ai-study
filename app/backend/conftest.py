"""
测试配置和全局fixture
"""

import os
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import event
from sqlalchemy.pool import StaticPool

from main import app
from core.database import get_db, Base
from core.config import settings

# 设置测试环境变量
os.environ["TESTING"] = "true"

# 测试数据库配置
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# 创建测试数据库引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# 创建测试session maker
TestingSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=AsyncSession
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建测试事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_database():
    """设置测试数据库"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # 清理数据库
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def override_get_db(db_session: AsyncSession):
    """覆盖数据库依赖"""
    async def _get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture
async def client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def auth_headers() -> dict:
    """认证头部"""
    return {"X-Access-Key": "test-key"}

@pytest.fixture
async def authenticated_client(client: AsyncClient, auth_headers: dict) -> AsyncClient:
    """已认证的测试客户端"""
    client.headers.update(auth_headers)
    return client

# 测试数据工厂
class TestDataFactory:
    """测试数据工厂"""
    
    @staticmethod
    def user_data(email: str = "test@example.com"):
        """创建用户测试数据"""
        return {
            "email": email,
            "is_active": True,
            "created_at": "2023-01-01T00:00:00",
            "last_login": "2023-01-01T00:00:00"
        }
    
    @staticmethod
    def question_data(title: str = "测试题目"):
        """创建题目测试数据"""
        return {
            "title": title,
            "content": "这是一道测试题目",
            "options": ["选项A", "选项B", "选项C", "选项D"],
            "correct_answer": 0,
            "explanation": "这是解析",
            "difficulty": "medium",
            "tags": ["测试", "示例"],
            "question_type": "single_choice"
        }

@pytest.fixture
def test_data_factory():
    """测试数据工厂fixture"""
    return TestDataFactory 