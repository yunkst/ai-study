"""
Comprehensive tests for Learning Path models
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.learning_path import (
    LearningPath, UserLearningPlan, DailyLearningPlan, LearningRecommendation,
    LearningGoal, PathStatus
)
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

@pytest.fixture
def sample_user(db_session):
    """Create a sample user"""
    user = User(device_id="learning_path_device", nickname="路径测试用户")
    db_session.add(user)
    db_session.commit()
    return user

class TestLearningGoal:
    """Test LearningGoal enum"""
    
    def test_learning_goal_values(self):
        """Test enum values"""
        assert LearningGoal.BASIC_PASS.value == "basic_pass"
        assert LearningGoal.HIGH_SCORE.value == "high_score"
        assert LearningGoal.COMPREHENSIVE.value == "comprehensive"
        assert LearningGoal.QUICK_REVIEW.value == "quick_review"

class TestPathStatus:
    """Test PathStatus enum"""
    
    def test_path_status_values(self):
        """Test enum values"""
        assert PathStatus.NOT_STARTED.value == "not_started"
        assert PathStatus.IN_PROGRESS.value == "in_progress"
        assert PathStatus.COMPLETED.value == "completed"
        assert PathStatus.PAUSED.value == "paused"

class TestLearningPath:
    """Test LearningPath model"""
    
    def test_create_basic_learning_path(self, db_session, sample_user):
        """Test creating a basic learning path"""
        knowledge_point_sequence = [
            {"kp_id": 1, "order": 1, "weight": 0.2},
            {"kp_id": 2, "order": 2, "weight": 0.3},
            {"kp_id": 3, "order": 3, "weight": 0.5}
        ]
        
        path = LearningPath(
            name="Java基础学习路径",
            description="Java编程基础知识学习路径",
            learning_goal=LearningGoal.BASIC_PASS,
            estimated_days=30,
            difficulty_level=2,
            knowledge_point_sequence=knowledge_point_sequence,
            created_by=sample_user.id
        )
        
        db_session.add(path)
        db_session.commit()
        
        assert path.id is not None
        assert path.name == "Java基础学习路径"
        assert path.learning_goal == LearningGoal.BASIC_PASS
        assert path.estimated_days == 30
        assert path.difficulty_level == 2
        assert path.knowledge_point_sequence == knowledge_point_sequence
        assert path.is_default is False
        assert path.is_active is True

    def test_learning_path_defaults(self, db_session):
        """Test default values for learning path"""
        path = LearningPath(
            name="默认路径",
            learning_goal=LearningGoal.BASIC_PASS,
            knowledge_point_sequence=[{"kp_id": 1, "order": 1, "weight": 1.0}]
        )
        
        db_session.add(path)
        db_session.commit()
        
        assert path.estimated_days == 30
        assert path.difficulty_level == 1
        assert path.is_default is False
        assert path.is_active is True

    def test_learning_path_repr(self, db_session):
        """Test string representation of learning path"""
        path = LearningPath(
            name="测试路径",
            learning_goal=LearningGoal.HIGH_SCORE,
            knowledge_point_sequence=[{"kp_id": 1, "order": 1, "weight": 1.0}]
        )
        db_session.add(path)
        db_session.commit()
        
        expected_repr = f"<LearningPath(id={path.id}, name='测试路径', goal=high_score)>"
        assert repr(path) == expected_repr

    def test_complex_learning_stages(self, db_session):
        """Test learning path with detailed learning stages"""
        learning_stages = [
            {
                "name": "基础阶段",
                "kp_ids": [1, 2, 3],
                "target_days": 10,
                "description": "掌握Java语法基础",
                "objectives": ["变量声明", "控制结构", "方法定义"]
            },
            {
                "name": "面向对象阶段",
                "kp_ids": [4, 5, 6],
                "target_days": 15,
                "description": "理解面向对象编程",
                "objectives": ["类和对象", "继承", "多态"]
            },
            {
                "name": "高级特性阶段",
                "kp_ids": [7, 8, 9],
                "target_days": 12,
                "description": "掌握Java高级特性",
                "objectives": ["泛型", "集合框架", "异常处理"]
            }
        ]
        
        knowledge_sequence = []
        for stage in learning_stages:
            for i, kp_id in enumerate(stage["kp_ids"]):
                knowledge_sequence.append({
                    "kp_id": kp_id,
                    "order": len(knowledge_sequence) + 1,
                    "weight": 1.0 / len(stage["kp_ids"]),
                    "stage": stage["name"]
                })
        
        path = LearningPath(
            name="Java完整学习路径",
            description="从零基础到熟练掌握Java编程",
            learning_goal=LearningGoal.COMPREHENSIVE,
            estimated_days=37,
            difficulty_level=3,
            knowledge_point_sequence=knowledge_sequence,
            learning_stages=learning_stages
        )
        
        db_session.add(path)
        db_session.commit()
        
        assert path.learning_stages == learning_stages
        assert len(path.learning_stages) == 3
        assert path.learning_stages[0]["target_days"] == 10
        assert len(path.knowledge_point_sequence) == 9

    def test_default_learning_path(self, db_session):
        """Test creating a default learning path"""
        path = LearningPath(
            name="系统默认路径",
            learning_goal=LearningGoal.BASIC_PASS,
            knowledge_point_sequence=[{"kp_id": 1, "order": 1, "weight": 1.0}],
            is_default=True
        )
        
        db_session.add(path)
        db_session.commit()
        
        assert path.is_default is True
        
        # Query for default path
        default_path = db_session.query(LearningPath).filter_by(is_default=True).first()
        assert default_path is not None
        assert default_path.name == "系统默认路径"

class TestUserLearningPlan:
    """Test UserLearningPlan model"""
    
    def test_create_user_learning_plan(self, db_session, sample_user):
        """Test creating a user learning plan"""
        # Create learning path first
        path = LearningPath(
            name="用户学习路径",
            learning_goal=LearningGoal.HIGH_SCORE,
            knowledge_point_sequence=[{"kp_id": 1, "order": 1, "weight": 1.0}]
        )
        db_session.add(path)
        db_session.commit()
        
        target_date = datetime.utcnow() + timedelta(days=45)
        
        plan = UserLearningPlan(
            user_id=sample_user.id,
            learning_path_id=path.id,
            plan_name="我的Java学习计划",
            target_exam_date=target_date,
            daily_study_hours=2.5,
            preferred_difficulty=3
        )
        
        db_session.add(plan)
        db_session.commit()
        
        assert plan.id is not None
        assert plan.user_id == sample_user.id
        assert plan.learning_path_id == path.id
        assert plan.plan_name == "我的Java学习计划"
        assert plan.daily_study_hours == 2.5
        assert plan.preferred_difficulty == 3
        assert plan.status == PathStatus.NOT_STARTED
        assert plan.overall_progress == 0.0

    def test_user_learning_plan_defaults(self, db_session, sample_user):
        """Test default values for user learning plan"""
        path = LearningPath(
            name="默认路径",
            learning_goal=LearningGoal.BASIC_PASS,
            knowledge_point_sequence=[{"kp_id": 1, "order": 1, "weight": 1.0}]
        )
        db_session.add(path)
        db_session.commit()
        
        plan = UserLearningPlan(
            user_id=sample_user.id,
            learning_path_id=path.id,
            plan_name="默认计划"
        )
        
        db_session.add(plan)
        db_session.commit()
        
        assert plan.status == PathStatus.NOT_STARTED
        assert plan.current_stage == 0
        assert plan.overall_progress == 0.0
        assert plan.daily_study_hours == 2.0
        assert plan.preferred_difficulty == 2

    def test_user_learning_plan_repr(self, db_session, sample_user):
        """Test string representation of user learning plan"""
        path = LearningPath(
            name="测试路径",
            learning_goal=LearningGoal.BASIC_PASS,
            knowledge_point_sequence=[{"kp_id": 1, "order": 1, "weight": 1.0}]
        )
        db_session.add(path)
        db_session.commit()
        
        plan = UserLearningPlan(
            user_id=sample_user.id,
            learning_path_id=path.id,
            plan_name="测试计划",
            status=PathStatus.IN_PROGRESS
        )
        db_session.add(plan)
        db_session.commit()
        
        expected_repr = f"<UserLearningPlan(id={plan.id}, user_id={sample_user.id}, status=in_progress)>"
        assert repr(plan) == expected_repr

    def test_user_learning_plan_relationships(self, db_session, sample_user):
        """Test relationships between user learning plan, user, and learning path"""
        path = LearningPath(
            name="关系测试路径",
            learning_goal=LearningGoal.BASIC_PASS,
            knowledge_point_sequence=[{"kp_id": 1, "order": 1, "weight": 1.0}],
            created_by=sample_user.id
        )
        db_session.add(path)
        db_session.commit()
        
        plan = UserLearningPlan(
            user_id=sample_user.id,
            learning_path_id=path.id,
            plan_name="关系测试计划"
        )
        db_session.add(plan)
        db_session.commit()
        
        # Test relationships
        assert plan.user == sample_user
        assert plan.learning_path == path
        assert plan.learning_path.creator == sample_user

    def test_custom_knowledge_sequence(self, db_session, sample_user):
        """Test user learning plan with custom knowledge point sequence"""
        # Original path sequence
        original_sequence = [
            {"kp_id": 1, "order": 1, "weight": 0.3},
            {"kp_id": 2, "order": 2, "weight": 0.4},
            {"kp_id": 3, "order": 3, "weight": 0.3}
        ]
        
        path = LearningPath(
            name="原始路径",
            learning_goal=LearningGoal.BASIC_PASS,
            knowledge_point_sequence=original_sequence
        )
        db_session.add(path)
        db_session.commit()
        
        # User's customized sequence
        custom_sequence = [
            {"kp_id": 3, "order": 1, "weight": 0.5, "reason": "用户已有基础"},
            {"kp_id": 1, "order": 2, "weight": 0.3, "reason": "用户需要加强"},
            {"kp_id": 2, "order": 3, "weight": 0.2, "reason": "用户较为熟悉"}
        ]
        
        plan = UserLearningPlan(
            user_id=sample_user.id,
            learning_path_id=path.id,
            plan_name="个性化学习计划",
            custom_sequence=custom_sequence
        )
        
        db_session.add(plan)
        db_session.commit()
        
        assert plan.custom_sequence == custom_sequence
        assert plan.custom_sequence[0]["kp_id"] == 3  # Starts with kp_id 3
        assert plan.custom_sequence[0]["reason"] == "用户已有基础"

    def test_learning_plan_progress_tracking(self, db_session, sample_user):
        """Test tracking learning plan progress over time"""
        path = LearningPath(
            name="进度跟踪路径",
            learning_goal=LearningGoal.HIGH_SCORE,
            knowledge_point_sequence=[
                {"kp_id": i, "order": i, "weight": 0.25} for i in range(1, 5)
            ]
        )
        db_session.add(path)
        db_session.commit()
        
        plan = UserLearningPlan(
            user_id=sample_user.id,
            learning_path_id=path.id,
            plan_name="进度跟踪计划",
            start_date=datetime.utcnow()
        )
        db_session.add(plan)
        db_session.commit()
        
        # Simulate progress updates
        progress_updates = [
            {"stage": 0, "progress": 0.25, "status": PathStatus.IN_PROGRESS},
            {"stage": 1, "progress": 0.5, "status": PathStatus.IN_PROGRESS},
            {"stage": 2, "progress": 0.75, "status": PathStatus.IN_PROGRESS},
            {"stage": 3, "progress": 1.0, "status": PathStatus.COMPLETED}
        ]
        
        for update in progress_updates:
            plan.current_stage = update["stage"]
            plan.overall_progress = update["progress"]
            plan.status = update["status"]
            
            if update["status"] == PathStatus.COMPLETED:
                plan.actual_completion_date = datetime.utcnow()
            
            db_session.commit()
            
            assert plan.current_stage == update["stage"]
            assert plan.overall_progress == update["progress"]
            assert plan.status == update["status"]
        
        # Final verification
        assert plan.status == PathStatus.COMPLETED
        assert plan.overall_progress == 1.0
        assert plan.actual_completion_date is not None

class TestDailyLearningPlan:
    """Test DailyLearningPlan model"""
    
    def test_create_daily_learning_plan(self, db_session, sample_user):
        """Test creating a daily learning plan"""
        # Create user learning plan first
        path = LearningPath(
            name="每日计划路径",
            learning_goal=LearningGoal.BASIC_PASS,
            knowledge_point_sequence=[{"kp_id": 1, "order": 1, "weight": 1.0}]
        )
        user_plan = UserLearningPlan(
            user_id=sample_user.id,
            learning_path_id=path.id,
            plan_name="每日学习计划"
        )
        db_session.add_all([path, user_plan])
        db_session.commit()
        
        planned_kps = [
            {"kp_id": 1, "target_mastery": 0.8, "estimated_time": 60},
            {"kp_id": 2, "target_mastery": 0.7, "estimated_time": 45}
        ]
        
        daily_plan = DailyLearningPlan(
            user_plan_id=user_plan.id,
            plan_date=datetime.utcnow(),
            planned_knowledge_points=planned_kps,
            planned_study_minutes=120
        )
        
        db_session.add(daily_plan)
        db_session.commit()
        
        assert daily_plan.id is not None
        assert daily_plan.user_plan_id == user_plan.id
        assert daily_plan.planned_knowledge_points == planned_kps
        assert daily_plan.planned_study_minutes == 120
        assert daily_plan.actual_study_minutes == 0
        assert daily_plan.is_completed is False

    def test_daily_plan_defaults(self, db_session, sample_user):
        """Test default values for daily learning plan"""
        path = LearningPath(
            name="默认路径",
            learning_goal=LearningGoal.BASIC_PASS,
            knowledge_point_sequence=[{"kp_id": 1, "order": 1, "weight": 1.0}]
        )
        user_plan = UserLearningPlan(
            user_id=sample_user.id,
            learning_path_id=path.id,
            plan_name="默认计划"
        )
        db_session.add_all([path, user_plan])
        db_session.commit()
        
        daily_plan = DailyLearningPlan(
            user_plan_id=user_plan.id,
            plan_date=datetime.utcnow(),
            planned_knowledge_points=[{"kp_id": 1}]
        )
        
        db_session.add(daily_plan)
        db_session.commit()
        
        assert daily_plan.planned_study_minutes == 120
        assert daily_plan.actual_study_minutes == 0
        assert daily_plan.is_completed is False
        assert daily_plan.completion_rate == 0.0

    def test_daily_plan_repr(self, db_session, sample_user):
        """Test string representation of daily learning plan"""
        path = LearningPath(
            name="测试路径",
            learning_goal=LearningGoal.BASIC_PASS,
            knowledge_point_sequence=[{"kp_id": 1, "order": 1, "weight": 1.0}]
        )
        user_plan = UserLearningPlan(
            user_id=sample_user.id,
            learning_path_id=path.id,
            plan_name="测试计划"
        )
        db_session.add_all([path, user_plan])
        db_session.commit()
        
        plan_date = datetime.utcnow()
        daily_plan = DailyLearningPlan(
            user_plan_id=user_plan.id,
            plan_date=plan_date,
            planned_knowledge_points=[{"kp_id": 1}],
            is_completed=True
        )
        db_session.add(daily_plan)
        db_session.commit()
        
        expected_repr = f"<DailyLearningPlan(id={daily_plan.id}, date={plan_date}, completed=True)>"
        assert repr(daily_plan) == expected_repr

    def test_daily_plan_completion_tracking(self, db_session, sample_user):
        """Test tracking daily plan completion"""
        path = LearningPath(
            name="完成度跟踪路径",
            learning_goal=LearningGoal.BASIC_PASS,
            knowledge_point_sequence=[{"kp_id": i, "order": i, "weight": 0.5} for i in range(1, 3)]
        )
        user_plan = UserLearningPlan(
            user_id=sample_user.id,
            learning_path_id=path.id,
            plan_name="完成度跟踪计划"
        )
        db_session.add_all([path, user_plan])
        db_session.commit()
        
        planned_kps = [
            {"kp_id": 1, "target_mastery": 0.8},
            {"kp_id": 2, "target_mastery": 0.7}
        ]
        
        daily_plan = DailyLearningPlan(
            user_plan_id=user_plan.id,
            plan_date=datetime.utcnow(),
            planned_knowledge_points=planned_kps,
            planned_study_minutes=90
        )
        db_session.add(daily_plan)
        db_session.commit()
        
        # Simulate completion
        completed_kps = [
            {"kp_id": 1, "achieved_mastery": 0.85, "time_spent": 50},
            {"kp_id": 2, "achieved_mastery": 0.65, "time_spent": 40}
        ]
        
        daily_plan.completed_knowledge_points = completed_kps
        daily_plan.actual_study_minutes = 90
        daily_plan.is_completed = True
        daily_plan.completion_rate = 1.0
        daily_plan.difficulty_feedback = 3  # Medium difficulty
        daily_plan.notes = "今天学习效果很好，掌握了核心概念"
        
        db_session.commit()
        
        assert daily_plan.completed_knowledge_points == completed_kps
        assert daily_plan.actual_study_minutes == 90
        assert daily_plan.is_completed is True
        assert daily_plan.completion_rate == 1.0
        assert daily_plan.difficulty_feedback == 3

    def test_multiple_daily_plans(self, db_session, sample_user):
        """Test creating multiple daily plans for a user learning plan"""
        path = LearningPath(
            name="多日计划路径",
            learning_goal=LearningGoal.COMPREHENSIVE,
            knowledge_point_sequence=[{"kp_id": i, "order": i, "weight": 0.2} for i in range(1, 6)]
        )
        user_plan = UserLearningPlan(
            user_id=sample_user.id,
            learning_path_id=path.id,
            plan_name="多日学习计划"
        )
        db_session.add_all([path, user_plan])
        db_session.commit()
        
        # Create daily plans for a week
        daily_plans = []
        base_date = datetime.utcnow().date()
        
        for day in range(7):
            plan_date = base_date + timedelta(days=day)
            kp_for_day = [(day % 5) + 1]  # Cycle through knowledge points
            
            daily_plan = DailyLearningPlan(
                user_plan_id=user_plan.id,
                plan_date=plan_date,
                planned_knowledge_points=[{"kp_id": kp} for kp in kp_for_day],
                planned_study_minutes=60 + (day * 10)  # Increasing study time
            )
            daily_plans.append(daily_plan)
            db_session.add(daily_plan)
        
        db_session.commit()
        
        # Verify all daily plans created
        assert len(daily_plans) == 7
        
        # Check study time progression
        study_times = [plan.planned_study_minutes for plan in daily_plans]
        assert study_times == [60, 70, 80, 90, 100, 110, 120]
        
        # Query by user plan
        user_daily_plans = db_session.query(DailyLearningPlan).filter_by(
            user_plan_id=user_plan.id
        ).all()
        assert len(user_daily_plans) == 7

class TestLearningRecommendation:
    """Test LearningRecommendation model"""
    
    def test_create_learning_recommendation(self, db_session, sample_user):
        """Test creating a learning recommendation"""
        recommended_kps = [
            {"kp_id": 1, "reason": "weak_area", "priority": 0.9},
            {"kp_id": 3, "reason": "prerequisite", "priority": 0.7}
        ]
        
        reasoning = {
            "algorithm": "collaborative_filtering",
            "confidence": 0.85,
            "factors": ["user_performance", "peer_comparison", "difficulty_analysis"],
            "explanation": "基于用户表现和同级对比分析推荐"
        }
        
        recommendation = LearningRecommendation(
            user_id=sample_user.id,
            recommendation_type="next_topic",
            recommended_knowledge_points=recommended_kps,
            algorithm_version="v2.0",
            reasoning=reasoning,
            recommendation_score=0.85,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        db_session.add(recommendation)
        db_session.commit()
        
        assert recommendation.id is not None
        assert recommendation.user_id == sample_user.id
        assert recommendation.recommendation_type == "next_topic"
        assert recommendation.recommended_knowledge_points == recommended_kps
        assert recommendation.reasoning == reasoning
        assert recommendation.recommendation_score == 0.85

    def test_recommendation_defaults(self, db_session, sample_user):
        """Test default values for learning recommendation"""
        recommendation = LearningRecommendation(
            user_id=sample_user.id,
            recommendation_type="review",
            recommended_knowledge_points=[{"kp_id": 1}]
        )
        
        db_session.add(recommendation)
        db_session.commit()
        
        assert recommendation.algorithm_version == "v1.0"
        assert recommendation.recommendation_score == 0.5

    def test_recommendation_repr(self, db_session, sample_user):
        """Test string representation of learning recommendation"""
        recommendation = LearningRecommendation(
            user_id=sample_user.id,
            recommendation_type="practice",
            recommended_knowledge_points=[{"kp_id": 1}]
        )
        db_session.add(recommendation)
        db_session.commit()
        
        expected_repr = f"<LearningRecommendation(id={recommendation.id}, user_id={sample_user.id}, type=practice)>"
        assert repr(recommendation) == expected_repr

    def test_recommendation_user_feedback(self, db_session, sample_user):
        """Test user feedback on recommendations"""
        recommendation = LearningRecommendation(
            user_id=sample_user.id,
            recommendation_type="strengthen",
            recommended_knowledge_points=[{"kp_id": 2, "reason": "low_score"}]
        )
        db_session.add(recommendation)
        db_session.commit()
        
        # Simulate user feedback
        user_feedback = {
            "usefulness": 4,  # 1-5 scale
            "followed": True,
            "time_to_follow": 2,  # hours
            "result_improvement": 0.15,  # 15% improvement
            "comments": "推荐很有用，确实帮助提高了理解"
        }
        
        recommendation.user_feedback = user_feedback
        db_session.commit()
        
        assert recommendation.user_feedback == user_feedback
        assert recommendation.user_feedback["usefulness"] == 4
        assert recommendation.user_feedback["followed"] is True

    def test_different_recommendation_types(self, db_session, sample_user):
        """Test different types of learning recommendations"""
        recommendation_types = [
            {
                "type": "next_topic",
                "kps": [{"kp_id": 1, "readiness": 0.9}],
                "description": "推荐下一个学习主题"
            },
            {
                "type": "review",
                "kps": [{"kp_id": 2, "forgetting_curve": 0.3}],
                "description": "推荐复习内容"
            },
            {
                "type": "practice", 
                "kps": [{"kp_id": 3, "practice_needed": 0.8}],
                "description": "推荐练习内容"
            },
            {
                "type": "strengthen",
                "kps": [{"kp_id": 4, "weakness_level": 0.7}],
                "description": "推荐加强薄弱环节"
            }
        ]
        
        recommendations = []
        for rec_data in recommendation_types:
            rec = LearningRecommendation(
                user_id=sample_user.id,
                recommendation_type=rec_data["type"],
                recommended_knowledge_points=rec_data["kps"],
                algorithm_version="v2.1"
            )
            recommendations.append(rec)
            db_session.add(rec)
        
        db_session.commit()
        
        # Verify all recommendations created
        assert len(recommendations) == 4
        
        # Check specific recommendation types
        types = [rec.recommendation_type for rec in recommendations]
        assert "next_topic" in types
        assert "review" in types
        assert "practice" in types
        assert "strengthen" in types

    def test_recommendation_expiration(self, db_session, sample_user):
        """Test recommendation expiration handling"""
        now = datetime.utcnow()
        
        # Active recommendation
        active_rec = LearningRecommendation(
            user_id=sample_user.id,
            recommendation_type="next_topic",
            recommended_knowledge_points=[{"kp_id": 1}],
            expires_at=now + timedelta(days=3)
        )
        
        # Expired recommendation
        expired_rec = LearningRecommendation(
            user_id=sample_user.id,
            recommendation_type="review",
            recommended_knowledge_points=[{"kp_id": 2}],
            expires_at=now - timedelta(days=1)
        )
        
        db_session.add_all([active_rec, expired_rec])
        db_session.commit()
        
        # Query active recommendations
        active_recommendations = db_session.query(LearningRecommendation).filter(
            LearningRecommendation.user_id == sample_user.id,
            LearningRecommendation.expires_at > now
        ).all()
        
        assert len(active_recommendations) == 1
        assert active_recommendations[0].recommendation_type == "next_topic"
        
        # Query expired recommendations
        expired_recommendations = db_session.query(LearningRecommendation).filter(
            LearningRecommendation.user_id == sample_user.id,
            LearningRecommendation.expires_at <= now
        ).all()
        
        assert len(expired_recommendations) == 1
        assert expired_recommendations[0].recommendation_type == "review"

if __name__ == "__main__":
    pytest.main([__file__]) 