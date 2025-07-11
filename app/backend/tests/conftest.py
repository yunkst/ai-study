"""
Global pytest configuration and fixtures
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base, get_db
from models.user import User
from models.question import Question, QuestionType, DifficultyLevel
from models.knowledge import KnowledgeDomain, KnowledgePoint

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def db_engine():
    """Create an in-memory SQLite database engine for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    """Create a database session for testing"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency for FastAPI testing"""
    def _override_get_db():
        yield db_session
    return _override_get_db

@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        device_id="test_device_123",
        nickname="测试用户",
        total_questions=100,
        correct_answers=75,
        total_study_time=300
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_domain(db_session):
    """Create a test knowledge domain"""
    domain = KnowledgeDomain(
        name="测试领域",
        description="用于测试的知识领域",
        exam_weight=0.3
    )
    db_session.add(domain)
    db_session.commit()
    return domain

@pytest.fixture
def test_knowledge_points(db_session, test_domain):
    """Create test knowledge points"""
    kps = []
    for i in range(3):
        kp = KnowledgePoint(
            name=f"测试知识点{i+1}",
            description=f"测试知识点{i+1}的描述",
            content=f"测试知识点{i+1}的内容",
            difficulty_level=((i % 3) + 1),
            domain_id=test_domain.id,
            learning_objectives=[f"目标{i+1}"],
            keywords=[f"关键词{i+1}"]
        )
        kps.append(kp)
        db_session.add(kp)
    
    db_session.commit()
    return kps

@pytest.fixture
def test_questions(db_session, test_knowledge_points):
    """Create test questions"""
    questions = []
    for i in range(5):
        question = Question(
            question_type=QuestionType.CHOICE,
            content=f"测试题目{i+1}",
            options={
                "A": f"选项A{i+1}",
                "B": f"选项B{i+1}",
                "C": f"选项C{i+1}",
                "D": f"选项D{i+1}"
            },
            correct_answer="A",
            explanation=f"题目{i+1}的解析",
            difficulty=DifficultyLevel((i % 3) + 1),
            knowledge_points=[test_knowledge_points[i % len(test_knowledge_points)].name]
        )
        questions.append(question)
        db_session.add(question)
    
    db_session.commit()
    return questions

@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls"""
    with patch('openai.ChatCompletion.acreate') as mock:
        mock.return_value.choices = [
            Mock(message=Mock(content="Mocked AI response"))
        ]
        yield mock

@pytest.fixture
def mock_celery():
    """Mock Celery task execution"""
    with patch('celery.Celery.send_task') as mock:
        mock.return_value = Mock(task_id="test_task_123")
        yield mock

@pytest.fixture
def mock_file_operations():
    """Mock file system operations"""
    with patch('builtins.open', create=True) as mock_open, \
         patch('os.path.exists') as mock_exists, \
         patch('os.makedirs') as mock_makedirs:
        
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock file content"
        yield {
            'open': mock_open,
            'exists': mock_exists,
            'makedirs': mock_makedirs
        }

@pytest.fixture
def sample_performance_data():
    """Sample performance data for analytics testing"""
    return {
        "accuracy_rate": 0.75,
        "average_time": 45.5,
        "total_questions": 100,
        "correct_answers": 75,
        "weak_areas": ["算法设计", "系统架构"],
        "strong_areas": ["面向对象编程", "数据结构"],
        "improvement_trend": "increasing"
    }

@pytest.fixture
def sample_knowledge_content():
    """Sample knowledge content for RAG testing"""
    return {
        "documents": [
            {
                "title": "软件工程基础",
                "content": "软件工程是一门综合性学科，涉及软件开发的全生命周期。",
                "metadata": {"chapter": "第一章", "page": 1}
            },
            {
                "title": "面向对象编程",
                "content": "面向对象编程是一种编程范式，基于对象和类的概念。",
                "metadata": {"chapter": "第二章", "page": 15}
            }
        ],
        "embeddings": [[0.1, 0.2, 0.3] * 333 + [0.1]],  # Mock 1000-dim embeddings
        "similarity_threshold": 0.8
    }

# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )

# Async test utilities
@pytest.fixture
async def async_session():
    """Async database session for async tests"""
    # This would be implemented with async SQLAlchemy in a real async app
    pass

# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Timer utility for performance testing"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.end_time - self.start_time
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()

# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data(db_session):
    """Automatically cleanup test data after each test"""
    yield
    # Cleanup is handled by session.close() in db_session fixture 