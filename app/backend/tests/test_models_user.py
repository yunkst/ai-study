"""
Comprehensive tests for User model
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from models.user import User
from core.database import Base

@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

class TestUser:
    """Test User model"""
    
    def test_create_user_with_all_fields(self, db_session):
        """Test creating a user with all fields specified"""
        user = User(
            device_id="device_12345",
            nickname="学霸小明",
            total_questions=100,
            correct_answers=80,
            total_study_time=300
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.device_id == "device_12345"
        assert user.nickname == "学霸小明"
        assert user.total_questions == 100
        assert user.correct_answers == 80
        assert user.total_study_time == 300
        assert user.created_at is not None
        assert user.last_active_at is not None

    def test_create_user_with_defaults(self, db_session):
        """Test creating a user with default values"""
        user = User(device_id="device_67890")
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.device_id == "device_67890"
        assert user.nickname == "学习者"  # default value
        assert user.total_questions == 0  # default value
        assert user.correct_answers == 0  # default value
        assert user.total_study_time == 0  # default value

    def test_device_id_unique_constraint(self, db_session):
        """Test that device_id must be unique"""
        user1 = User(device_id="unique_device")
        user2 = User(device_id="unique_device")
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_repr(self, db_session):
        """Test string representation of user"""
        user = User(
            device_id="test_device",
            nickname="测试用户"
        )
        db_session.add(user)
        db_session.commit()
        
        expected_repr = f"<User(id={user.id}, nickname='测试用户')>"
        assert repr(user) == expected_repr

    def test_accuracy_calculation(self, db_session):
        """Test accuracy calculation based on statistics"""
        user = User(
            device_id="stats_device",
            total_questions=50,
            correct_answers=40
        )
        db_session.add(user)
        db_session.commit()
        
        # Calculate accuracy rate manually
        accuracy = user.correct_answers / user.total_questions if user.total_questions > 0 else 0
        assert accuracy == 0.8

    def test_user_with_zero_questions(self, db_session):
        """Test user with no questions answered yet"""
        user = User(
            device_id="new_user_device",
            total_questions=0,
            correct_answers=0
        )
        db_session.add(user)
        db_session.commit()
        
        # Ensure no division by zero issues
        accuracy = user.correct_answers / user.total_questions if user.total_questions > 0 else 0
        assert accuracy == 0

    def test_user_nickname_length(self, db_session):
        """Test user nickname with various lengths"""
        # Test normal length nickname
        user1 = User(device_id="device1", nickname="正常长度昵称")
        db_session.add(user1)
        db_session.commit()
        assert user1.nickname == "正常长度昵称"
        
        # Test long nickname (up to 100 characters)
        long_nickname = "很长的昵称" * 15  # Should be around 75 characters
        user2 = User(device_id="device2", nickname=long_nickname)
        db_session.add(user2)
        db_session.commit()
        assert user2.nickname == long_nickname

    def test_study_time_tracking(self, db_session):
        """Test study time tracking functionality"""
        user = User(
            device_id="study_device",
            total_study_time=150  # 150 minutes
        )
        db_session.add(user)
        db_session.commit()
        
        # Convert to hours for verification
        study_hours = user.total_study_time / 60
        assert study_hours == 2.5

    def test_performance_metrics(self, db_session):
        """Test various performance calculation scenarios"""
        # High performer
        high_performer = User(
            device_id="high_performer",
            total_questions=200,
            correct_answers=180,
            total_study_time=600
        )
        db_session.add(high_performer)
        
        # Average performer  
        avg_performer = User(
            device_id="avg_performer", 
            total_questions=100,
            correct_answers=65,
            total_study_time=300
        )
        db_session.add(avg_performer)
        
        # Low performer
        low_performer = User(
            device_id="low_performer",
            total_questions=50,
            correct_answers=20,
            total_study_time=400
        )
        db_session.add(low_performer)
        
        db_session.commit()
        
        # Verify performance calculations
        high_acc = high_performer.correct_answers / high_performer.total_questions
        avg_acc = avg_performer.correct_answers / avg_performer.total_questions  
        low_acc = low_performer.correct_answers / low_performer.total_questions
        
        assert high_acc == 0.9
        assert avg_acc == 0.65
        assert low_acc == 0.4
        
        # Check study efficiency (questions per minute)
        high_efficiency = high_performer.total_questions / high_performer.total_study_time
        low_efficiency = low_performer.total_questions / low_performer.total_study_time
        
        assert high_efficiency > low_efficiency

    def test_update_user_stats(self, db_session):
        """Test updating user statistics"""
        user = User(device_id="update_device")
        db_session.add(user)
        db_session.commit()
        
        original_created = user.created_at
        
        # Update statistics
        user.total_questions = 25
        user.correct_answers = 20
        user.total_study_time = 120
        user.nickname = "更新后的昵称"
        
        db_session.commit()
        
        # Verify updates
        assert user.total_questions == 25
        assert user.correct_answers == 20
        assert user.total_study_time == 120
        assert user.nickname == "更新后的昵称"
        assert user.created_at == original_created  # Should not change

    def test_user_query_operations(self, db_session):
        """Test various query operations on user data"""
        # Create multiple users
        users_data = [
            {"device_id": "user1", "nickname": "张三", "correct_answers": 80, "total_questions": 100},
            {"device_id": "user2", "nickname": "李四", "correct_answers": 60, "total_questions": 100},
            {"device_id": "user3", "nickname": "王五", "correct_answers": 90, "total_questions": 100},
        ]
        
        for user_data in users_data:
            user = User(**user_data)
            db_session.add(user)
        
        db_session.commit()
        
        # Query by nickname
        zhang_san = db_session.query(User).filter_by(nickname="张三").first()
        assert zhang_san is not None
        assert zhang_san.device_id == "user1"
        
        # Query high performers (>= 85% accuracy)
        high_performers = db_session.query(User).filter(
            User.correct_answers >= User.total_questions * 0.85
        ).all()
        assert len(high_performers) == 2  # 张三 and 王五
        
        # Count total users
        total_users = db_session.query(User).count()
        assert total_users == 3

if __name__ == "__main__":
    pytest.main([__file__]) 