"""
Comprehensive tests for Analytics models (LearningAnalysis and StudyPlan)
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.analytics import LearningAnalysis, StudyPlan
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
    user = User(device_id="analytics_test_device", nickname="分析测试用户")
    db_session.add(user)
    db_session.commit()
    return user

class TestLearningAnalysis:
    """Test LearningAnalysis model"""
    
    def test_create_basic_learning_analysis(self, db_session, sample_user):
        """Test creating a basic learning analysis"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        analysis = LearningAnalysis(
            user_id=sample_user.id,
            period_start=start_date,
            period_end=end_date,
            total_questions=100,
            correct_answers=75,
            accuracy_rate=0.75,
            average_time_per_question=45.5,
            study_sessions=12,
            total_study_time=360  # 6 hours in minutes
        )
        
        db_session.add(analysis)
        db_session.commit()
        
        assert analysis.id is not None
        assert analysis.user_id == sample_user.id
        assert analysis.total_questions == 100
        assert analysis.correct_answers == 75
        assert analysis.accuracy_rate == 0.75
        assert analysis.average_time_per_question == 45.5
        assert analysis.study_sessions == 12
        assert analysis.total_study_time == 360
        assert analysis.analysis_date is not None

    def test_learning_analysis_defaults(self, db_session, sample_user):
        """Test default values for learning analysis"""
        analysis = LearningAnalysis(
            user_id=sample_user.id,
            period_start=datetime.utcnow() - timedelta(days=1),
            period_end=datetime.utcnow()
        )
        
        db_session.add(analysis)
        db_session.commit()
        
        assert analysis.total_questions == 0
        assert analysis.correct_answers == 0
        assert analysis.accuracy_rate == 0.0
        assert analysis.average_time_per_question == 0.0
        assert analysis.study_sessions == 0
        assert analysis.total_study_time == 0

    def test_learning_analysis_repr(self, db_session, sample_user):
        """Test string representation of learning analysis"""
        analysis = LearningAnalysis(
            user_id=sample_user.id,
            period_start=datetime.utcnow() - timedelta(days=1),
            period_end=datetime.utcnow()
        )
        db_session.add(analysis)
        db_session.commit()
        
        expected_repr = f"<LearningAnalysis(id={analysis.id}, user_id={sample_user.id}, date={analysis.analysis_date})>"
        assert repr(analysis) == expected_repr

    def test_learning_analysis_relationship_with_user(self, db_session, sample_user):
        """Test relationship between learning analysis and user"""
        analysis = LearningAnalysis(
            user_id=sample_user.id,
            period_start=datetime.utcnow() - timedelta(days=1),
            period_end=datetime.utcnow()
        )
        db_session.add(analysis)
        db_session.commit()
        
        # Test relationship
        assert analysis.user == sample_user
        assert analysis.user.nickname == "分析测试用户"

    def test_complex_knowledge_points_analysis(self, db_session, sample_user):
        """Test learning analysis with detailed knowledge points analysis"""
        knowledge_points_analysis = {
            "面向对象编程": {
                "attempted": 20,
                "correct": 16,
                "accuracy": 0.8,
                "average_time": 35.2,
                "difficulty_rating": 2.5,
                "improvement_trend": "increasing"
            },
            "数据结构": {
                "attempted": 15,
                "correct": 9,
                "accuracy": 0.6,
                "average_time": 58.7,
                "difficulty_rating": 3.8,
                "improvement_trend": "stable"
            },
            "算法设计": {
                "attempted": 25,
                "correct": 12,
                "accuracy": 0.48,
                "average_time": 78.3,
                "difficulty_rating": 4.2,
                "improvement_trend": "decreasing"
            }
        }
        
        analysis = LearningAnalysis(
            user_id=sample_user.id,
            period_start=datetime.utcnow() - timedelta(days=7),
            period_end=datetime.utcnow(),
            total_questions=60,
            correct_answers=37,
            accuracy_rate=0.617,
            knowledge_points_analysis=knowledge_points_analysis
        )
        
        db_session.add(analysis)
        db_session.commit()
        
        assert analysis.knowledge_points_analysis == knowledge_points_analysis
        assert analysis.knowledge_points_analysis["面向对象编程"]["accuracy"] == 0.8
        assert analysis.knowledge_points_analysis["算法设计"]["improvement_trend"] == "decreasing"

    def test_difficulty_analysis(self, db_session, sample_user):
        """Test learning analysis with difficulty-based analysis"""
        difficulty_analysis = {
            "basic": {
                "questions": 30,
                "correct": 27,
                "accuracy": 0.9,
                "average_time": 25.4
            },
            "intermediate": {
                "questions": 40,
                "correct": 28,
                "accuracy": 0.7,
                "average_time": 45.8
            },
            "advanced": {
                "questions": 30,
                "correct": 15,
                "accuracy": 0.5,
                "average_time": 75.2
            }
        }
        
        analysis = LearningAnalysis(
            user_id=sample_user.id,
            period_start=datetime.utcnow() - timedelta(days=14),
            period_end=datetime.utcnow(),
            total_questions=100,
            correct_answers=70,
            accuracy_rate=0.7,
            difficulty_analysis=difficulty_analysis
        )
        
        db_session.add(analysis)
        db_session.commit()
        
        assert analysis.difficulty_analysis == difficulty_analysis
        assert analysis.difficulty_analysis["basic"]["accuracy"] == 0.9
        assert analysis.difficulty_analysis["advanced"]["accuracy"] == 0.5

    def test_ai_recommendations(self, db_session, sample_user):
        """Test learning analysis with AI-generated recommendations"""
        ai_recommendations = """
        基于你的学习表现分析，以下是个性化建议：
        
        1. 强化算法设计练习
           - 当前准确率仅48%，需要重点关注
           - 建议每天增加30分钟算法练习时间
           - 推荐从基础排序算法开始复习
        
        2. 保持面向对象编程优势
           - 当前准确率80%，表现优秀
           - 可以尝试更复杂的设计模式练习
        
        3. 改善学习节奏
           - 建议将长时间学习分成多个短时间段
           - 每学习25分钟休息5分钟，提高效率
        
        4. 增加复习频率
           - 错题需要在24小时内重做一遍
           - 一周后再次复习加深记忆
        """
        
        weak_points = [
            {
                "topic": "算法设计",
                "accuracy": 0.48,
                "reason": "逻辑思维需要加强",
                "suggestions": ["多做递归练习", "掌握动态规划基础"]
            },
            {
                "topic": "时间复杂度分析",
                "accuracy": 0.52,
                "reason": "数学基础薄弱",
                "suggestions": ["复习对数运算", "理解循环嵌套复杂度"]
            }
        ]
        
        analysis = LearningAnalysis(
            user_id=sample_user.id,
            period_start=datetime.utcnow() - timedelta(days=7),
            period_end=datetime.utcnow(),
            total_questions=80,
            correct_answers=56,
            accuracy_rate=0.7,
            ai_recommendations=ai_recommendations,
            weak_points=weak_points
        )
        
        db_session.add(analysis)
        db_session.commit()
        
        assert analysis.ai_recommendations == ai_recommendations
        assert analysis.weak_points == weak_points
        assert len(analysis.weak_points) == 2
        assert analysis.weak_points[0]["topic"] == "算法设计"

    def test_multiple_analysis_periods(self, db_session, sample_user):
        """Test creating multiple learning analyses for different periods"""
        # Create weekly analyses for the past month
        analyses_data = []
        for week in range(4):
            start_date = datetime.utcnow() - timedelta(days=(week+1)*7)
            end_date = datetime.utcnow() - timedelta(days=week*7)
            
            # Simulate improving performance over time
            base_questions = 50
            improvement_factor = (4 - week) * 0.1  # 0.1, 0.2, 0.3, 0.4
            accuracy = 0.5 + improvement_factor
            
            analysis = LearningAnalysis(
                user_id=sample_user.id,
                period_start=start_date,
                period_end=end_date,
                total_questions=base_questions,
                correct_answers=int(base_questions * accuracy),
                accuracy_rate=accuracy,
                average_time_per_question=60 - (week * 5),  # Getting faster
                study_sessions=10 + week,  # Studying more frequently
                total_study_time=180 + (week * 30)  # Studying longer
            )
            analyses_data.append(analysis)
            db_session.add(analysis)
        
        db_session.commit()
        
        # Verify progression
        assert len(analyses_data) == 4
        
        # Check improvement trend (most recent first)
        accuracies = [a.accuracy_rate for a in analyses_data]
        assert accuracies == [0.9, 0.8, 0.7, 0.6]  # Improving over time
        
        # Check study time increase
        study_times = [a.total_study_time for a in analyses_data]
        assert study_times == [270, 240, 210, 180]  # Increasing study time

class TestStudyPlan:
    """Test StudyPlan model"""
    
    def test_create_basic_study_plan(self, db_session, sample_user):
        """Test creating a basic study plan"""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        plan = StudyPlan(
            user_id=sample_user.id,
            plan_title="软件工程冲刺计划",
            start_date=start_date,
            end_date=end_date,
            daily_questions_target=15,
            daily_study_time_target=60,  # 1 hour
            accuracy_target=0.85
        )
        
        db_session.add(plan)
        db_session.commit()
        
        assert plan.id is not None
        assert plan.user_id == sample_user.id
        assert plan.plan_title == "软件工程冲刺计划"
        assert plan.daily_questions_target == 15
        assert plan.daily_study_time_target == 60
        assert plan.accuracy_target == 0.85
        assert plan.is_active == 1  # True (SQLite compatible)
        assert plan.completion_rate == 0.0

    def test_study_plan_defaults(self, db_session, sample_user):
        """Test default values for study plan"""
        plan = StudyPlan(
            user_id=sample_user.id,
            plan_title="默认计划",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7)
        )
        
        db_session.add(plan)
        db_session.commit()
        
        assert plan.daily_questions_target == 10
        assert plan.daily_study_time_target == 45
        assert plan.accuracy_target == 0.8
        assert plan.is_active == 1
        assert plan.completion_rate == 0.0

    def test_study_plan_repr(self, db_session, sample_user):
        """Test string representation of study plan"""
        plan = StudyPlan(
            user_id=sample_user.id,
            plan_title="测试计划",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7)
        )
        db_session.add(plan)
        db_session.commit()
        
        expected_repr = f"<StudyPlan(id={plan.id}, title='测试计划', active={bool(plan.is_active)})>"
        assert repr(plan) == expected_repr

    def test_study_plan_relationship_with_user(self, db_session, sample_user):
        """Test relationship between study plan and user"""
        plan = StudyPlan(
            user_id=sample_user.id,
            plan_title="关系测试计划",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7)
        )
        db_session.add(plan)
        db_session.commit()
        
        # Test relationship
        assert plan.user == sample_user
        assert plan.user.nickname == "分析测试用户"

    def test_complex_focus_topics(self, db_session, sample_user):
        """Test study plan with complex focus topics structure"""
        focus_topics = [
            {
                "topic": "数据结构",
                "priority": "high",
                "target_accuracy": 0.9,
                "estimated_hours": 20,
                "subtopics": ["数组", "链表", "栈", "队列", "树"]
            },
            {
                "topic": "算法设计",
                "priority": "medium",
                "target_accuracy": 0.8,
                "estimated_hours": 30,
                "subtopics": ["排序", "搜索", "动态规划", "贪心算法"]
            },
            {
                "topic": "系统设计",
                "priority": "low",
                "target_accuracy": 0.75,
                "estimated_hours": 15,
                "subtopics": ["架构模式", "负载均衡", "数据库设计"]
            }
        ]
        
        plan = StudyPlan(
            user_id=sample_user.id,
            plan_title="重点突破计划",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=45),
            focus_topics=focus_topics,
            daily_questions_target=20,
            daily_study_time_target=90
        )
        
        db_session.add(plan)
        db_session.commit()
        
        assert plan.focus_topics == focus_topics
        assert len(plan.focus_topics) == 3
        assert plan.focus_topics[0]["priority"] == "high"
        assert plan.focus_topics[1]["estimated_hours"] == 30

    def test_detailed_plan_structure(self, db_session, sample_user):
        """Test study plan with detailed daily planning"""
        plan_details = {
            "weekly_schedule": {
                "monday": {
                    "topics": ["数据结构"],
                    "target_questions": 15,
                    "target_time": 60,
                    "focus_areas": ["数组操作", "链表实现"]
                },
                "tuesday": {
                    "topics": ["算法设计"],
                    "target_questions": 12,
                    "target_time": 75,
                    "focus_areas": ["排序算法", "时间复杂度分析"]
                },
                "wednesday": {
                    "topics": ["数据结构", "算法设计"],
                    "target_questions": 18,
                    "target_time": 90,
                    "focus_areas": ["综合练习"]
                },
                "thursday": {
                    "topics": ["系统设计"],
                    "target_questions": 10,
                    "target_time": 60,
                    "focus_areas": ["架构模式", "设计原则"]
                },
                "friday": {
                    "topics": ["复习"],
                    "target_questions": 20,
                    "target_time": 45,
                    "focus_areas": ["错题重做", "薄弱点强化"]
                },
                "saturday": {
                    "topics": ["模拟考试"],
                    "target_questions": 50,
                    "target_time": 120,
                    "focus_areas": ["综合测试"]
                },
                "sunday": {
                    "topics": ["休息"],
                    "target_questions": 0,
                    "target_time": 0,
                    "focus_areas": ["总结回顾"]
                }
            },
            "milestones": [
                {"week": 1, "target": "掌握基础数据结构", "accuracy_target": 0.7},
                {"week": 2, "target": "理解常用算法", "accuracy_target": 0.75},
                {"week": 4, "target": "系统设计入门", "accuracy_target": 0.8},
                {"week": 6, "target": "综合应用", "accuracy_target": 0.85}
            ],
            "reward_system": {
                "daily_target_met": "15分钟休息时间",
                "weekly_target_met": "看一部电影",
                "monthly_target_met": "购买喜欢的书籍"
            }
        }
        
        plan = StudyPlan(
            user_id=sample_user.id,
            plan_title="详细学习计划",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=42),  # 6 weeks
            plan_details=plan_details,
            daily_questions_target=20,
            daily_study_time_target=75
        )
        
        db_session.add(plan)
        db_session.commit()
        
        assert plan.plan_details == plan_details
        assert plan.plan_details["weekly_schedule"]["monday"]["target_questions"] == 15
        assert len(plan.plan_details["milestones"]) == 4
        assert plan.plan_details["reward_system"]["daily_target_met"] == "15分钟休息时间"

    def test_study_plan_completion_tracking(self, db_session, sample_user):
        """Test tracking study plan completion progress"""
        plan = StudyPlan(
            user_id=sample_user.id,
            plan_title="进度跟踪计划",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=20)
        )
        
        db_session.add(plan)
        db_session.commit()
        
        # Simulate progress over time
        progress_updates = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        
        for progress in progress_updates:
            plan.completion_rate = progress
            
            if progress >= 1.0:
                plan.is_active = 0  # Mark as completed
            
            db_session.commit()
            assert plan.completion_rate == progress
        
        # Final verification
        assert plan.completion_rate == 1.0
        assert plan.is_active == 0  # Completed

    def test_multiple_study_plans_per_user(self, db_session, sample_user):
        """Test creating multiple study plans for one user"""
        plans_data = [
            {
                "title": "短期冲刺计划",
                "duration": 7,
                "daily_questions": 25,
                "daily_time": 90,
                "active": True
            },
            {
                "title": "长期系统学习",
                "duration": 60,
                "daily_questions": 15,
                "daily_time": 60,
                "active": False
            },
            {
                "title": "考前复习计划",
                "duration": 14,
                "daily_questions": 30,
                "daily_time": 120,
                "active": False
            }
        ]
        
        plans = []
        for i, data in enumerate(plans_data):
            plan = StudyPlan(
                user_id=sample_user.id,
                plan_title=data["title"],
                start_date=datetime.utcnow() + timedelta(days=i*30),
                end_date=datetime.utcnow() + timedelta(days=i*30 + data["duration"]),
                daily_questions_target=data["daily_questions"],
                daily_study_time_target=data["daily_time"],
                is_active=1 if data["active"] else 0
            )
            plans.append(plan)
            db_session.add(plan)
        
        db_session.commit()
        
        # Verify all plans created
        assert len(plans) == 3
        
        # Check active plan
        active_plans = [p for p in plans if p.is_active == 1]
        assert len(active_plans) == 1
        assert active_plans[0].plan_title == "短期冲刺计划"
        
        # Query user's plans
        user_plans = db_session.query(StudyPlan).filter_by(user_id=sample_user.id).all()
        assert len(user_plans) == 3

    def test_study_plan_date_validation(self, db_session, sample_user):
        """Test study plan with various date configurations"""
        now = datetime.utcnow()
        
        # Past plan (completed)
        past_plan = StudyPlan(
            user_id=sample_user.id,
            plan_title="已完成计划",
            start_date=now - timedelta(days=30),
            end_date=now - timedelta(days=1),
            completion_rate=1.0,
            is_active=0
        )
        
        # Current plan (ongoing)
        current_plan = StudyPlan(
            user_id=sample_user.id,
            plan_title="当前计划",
            start_date=now - timedelta(days=5),
            end_date=now + timedelta(days=10),
            completion_rate=0.4,
            is_active=1
        )
        
        # Future plan (scheduled)
        future_plan = StudyPlan(
            user_id=sample_user.id,
            plan_title="未来计划",
            start_date=now + timedelta(days=20),
            end_date=now + timedelta(days=50),
            completion_rate=0.0,
            is_active=0
        )
        
        db_session.add_all([past_plan, current_plan, future_plan])
        db_session.commit()
        
        # Verify plan states
        assert past_plan.completion_rate == 1.0
        assert past_plan.is_active == 0
        
        assert current_plan.is_active == 1
        assert 0 < current_plan.completion_rate < 1
        
        assert future_plan.completion_rate == 0.0
        assert future_plan.start_date > now

if __name__ == "__main__":
    pytest.main([__file__]) 