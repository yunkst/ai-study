"""
Comprehensive tests for Question model
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.question import Question, QuestionType, DifficultyLevel
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

class TestQuestionType:
    """Test QuestionType enum"""
    
    def test_question_type_values(self):
        """Test enum values"""
        assert QuestionType.CHOICE.value == "choice"
        assert QuestionType.CASE.value == "case"
        assert QuestionType.ESSAY.value == "essay"

class TestDifficultyLevel:
    """Test DifficultyLevel enum"""
    
    def test_difficulty_level_values(self):
        """Test enum values"""
        assert DifficultyLevel.BASIC.value == 1
        assert DifficultyLevel.INTERMEDIATE.value == 2
        assert DifficultyLevel.ADVANCED.value == 3

class TestQuestion:
    """Test Question model"""
    
    def test_create_choice_question(self, db_session):
        """Test creating a choice question"""
        options = {
            "A": "选项A内容",
            "B": "选项B内容", 
            "C": "选项C内容",
            "D": "选项D内容"
        }
        
        question = Question(
            question_type=QuestionType.CHOICE,
            content="这是一道选择题的题目内容",
            options=options,
            correct_answer="A",
            explanation="选择A是正确的，因为...",
            difficulty=DifficultyLevel.BASIC,
            knowledge_points=["面向对象编程", "封装"]
        )
        
        db_session.add(question)
        db_session.commit()
        
        assert question.id is not None
        assert question.question_type == QuestionType.CHOICE
        assert question.options == options
        assert question.correct_answer == "A"
        assert question.difficulty == DifficultyLevel.BASIC
        assert question.knowledge_points == ["面向对象编程", "封装"]

    def test_create_case_question(self, db_session):
        """Test creating a case analysis question"""
        question = Question(
            question_type=QuestionType.CASE,
            content="案例背景：某公司需要设计一个电商系统...\n请分析系统架构设计",
            correct_answer="从分层架构角度分析，应包含表现层、业务层、数据层...",
            explanation="案例分析要点包括...",
            difficulty=DifficultyLevel.ADVANCED,
            knowledge_points=["系统设计", "架构模式"]
        )
        
        db_session.add(question)
        db_session.commit()
        
        assert question.question_type == QuestionType.CASE
        assert question.options is None  # Case questions don't have options
        assert question.difficulty == DifficultyLevel.ADVANCED

    def test_create_essay_question(self, db_session):
        """Test creating an essay question"""
        question = Question(
            question_type=QuestionType.ESSAY,
            content="请论述软件工程中敏捷开发方法的优缺点",
            correct_answer="敏捷开发方法的优点包括：1. 快速响应变化...\n缺点包括：1. 文档不足...",
            explanation="评分标准：论述完整性、逻辑性、实例支撑等",
            difficulty=DifficultyLevel.INTERMEDIATE,
            knowledge_points=["软件工程", "敏捷开发"]
        )
        
        db_session.add(question)
        db_session.commit()
        
        assert question.question_type == QuestionType.ESSAY
        assert question.difficulty == DifficultyLevel.INTERMEDIATE

    def test_question_defaults(self, db_session):
        """Test default values for question"""
        question = Question(
            question_type=QuestionType.CHOICE,
            content="最简单的题目",
            correct_answer="A"
        )
        
        db_session.add(question)
        db_session.commit()
        
        assert question.difficulty == DifficultyLevel.BASIC  # default
        assert question.total_attempts == 0  # default
        assert question.correct_attempts == 0  # default
        assert question.created_at is not None
        assert question.updated_at is None  # Only set on update

    def test_question_repr(self, db_session):
        """Test string representation of question"""
        question = Question(
            question_type=QuestionType.CHOICE,
            content="测试题目",
            correct_answer="A"
        )
        db_session.add(question)
        db_session.commit()
        
        expected_repr = f"<Question(id={question.id}, type=choice)>"
        assert repr(question) == expected_repr

    def test_accuracy_rate_property(self, db_session):
        """Test accuracy_rate property calculation"""
        # Question with attempts
        question_with_stats = Question(
            question_type=QuestionType.CHOICE,
            content="有统计数据的题目",
            correct_answer="A",
            total_attempts=100,
            correct_attempts=75
        )
        db_session.add(question_with_stats)
        
        # Question with no attempts
        question_no_stats = Question(
            question_type=QuestionType.CHOICE,
            content="无统计数据的题目",
            correct_answer="B"
        )
        db_session.add(question_no_stats)
        
        db_session.commit()
        
        # Test accuracy calculation
        assert question_with_stats.accuracy_rate == 0.75
        assert question_no_stats.accuracy_rate == 0.0

    def test_update_question_statistics(self, db_session):
        """Test updating question statistics"""
        question = Question(
            question_type=QuestionType.CHOICE,
            content="统计测试题目",
            correct_answer="C"
        )
        db_session.add(question)
        db_session.commit()
        
        # Simulate answer attempts
        question.total_attempts = 10
        question.correct_attempts = 6
        db_session.commit()
        
        assert question.accuracy_rate == 0.6
        
        # Add more attempts
        question.total_attempts = 20
        question.correct_attempts = 16
        db_session.commit()
        
        assert question.accuracy_rate == 0.8

    def test_complex_options_structure(self, db_session):
        """Test complex options structure for choice questions"""
        complex_options = {
            "A": {
                "text": "选项A的详细描述",
                "explanation": "为什么选择A"
            },
            "B": {
                "text": "选项B的详细描述", 
                "explanation": "为什么选择B"
            },
            "C": {
                "text": "选项C的详细描述",
                "explanation": "为什么选择C"
            }
        }
        
        question = Question(
            question_type=QuestionType.CHOICE,
            content="复杂选项结构的题目",
            options=complex_options,
            correct_answer="B"
        )
        
        db_session.add(question)
        db_session.commit()
        
        assert question.options == complex_options
        assert question.options["B"]["explanation"] == "为什么选择B"

    def test_knowledge_points_array(self, db_session):
        """Test knowledge points array handling"""
        knowledge_points = [
            "数据结构",
            "算法设计",
            "时间复杂度分析",
            "空间复杂度分析"
        ]
        
        question = Question(
            question_type=QuestionType.CHOICE,
            content="算法相关题目",
            correct_answer="A",
            knowledge_points=knowledge_points
        )
        
        db_session.add(question)
        db_session.commit()
        
        assert question.knowledge_points == knowledge_points
        assert len(question.knowledge_points) == 4
        assert "数据结构" in question.knowledge_points

    def test_questions_by_difficulty(self, db_session):
        """Test querying questions by difficulty level"""
        # Create questions with different difficulties
        basic_q = Question(
            question_type=QuestionType.CHOICE,
            content="基础题目",
            correct_answer="A",
            difficulty=DifficultyLevel.BASIC
        )
        
        intermediate_q = Question(
            question_type=QuestionType.CASE,
            content="中级案例题",
            correct_answer="分析...",
            difficulty=DifficultyLevel.INTERMEDIATE
        )
        
        advanced_q = Question(
            question_type=QuestionType.ESSAY,
            content="高级论述题",
            correct_answer="论述...",
            difficulty=DifficultyLevel.ADVANCED
        )
        
        db_session.add_all([basic_q, intermediate_q, advanced_q])
        db_session.commit()
        
        # Query by difficulty
        basic_questions = db_session.query(Question).filter_by(
            difficulty=DifficultyLevel.BASIC
        ).all()
        assert len(basic_questions) == 1
        
        advanced_questions = db_session.query(Question).filter_by(
            difficulty=DifficultyLevel.ADVANCED
        ).all()
        assert len(advanced_questions) == 1

    def test_questions_by_type(self, db_session):
        """Test querying questions by type"""
        # Create questions of different types
        choice_q1 = Question(
            question_type=QuestionType.CHOICE,
            content="选择题1",
            correct_answer="A"
        )
        
        choice_q2 = Question(
            question_type=QuestionType.CHOICE,
            content="选择题2",
            correct_answer="B"
        )
        
        case_q = Question(
            question_type=QuestionType.CASE,
            content="案例题",
            correct_answer="案例分析"
        )
        
        db_session.add_all([choice_q1, choice_q2, case_q])
        db_session.commit()
        
        # Query choice questions
        choice_questions = db_session.query(Question).filter_by(
            question_type=QuestionType.CHOICE
        ).all()
        assert len(choice_questions) == 2
        
        # Query case questions
        case_questions = db_session.query(Question).filter_by(
            question_type=QuestionType.CASE
        ).all()
        assert len(case_questions) == 1

    def test_question_statistics_analysis(self, db_session):
        """Test statistical analysis across questions"""
        # Create questions with various statistics
        questions_data = [
            {"content": "题目1", "total_attempts": 100, "correct_attempts": 90},
            {"content": "题目2", "total_attempts": 80, "correct_attempts": 40},
            {"content": "题目3", "total_attempts": 60, "correct_attempts": 45},
            {"content": "题目4", "total_attempts": 40, "correct_attempts": 30},
        ]
        
        questions = []
        for data in questions_data:
            q = Question(
                question_type=QuestionType.CHOICE,
                content=data["content"],
                correct_answer="A",
                total_attempts=data["total_attempts"],
                correct_attempts=data["correct_attempts"]
            )
            questions.append(q)
            db_session.add(q)
        
        db_session.commit()
        
        # Calculate average accuracy
        total_accuracy = sum(q.accuracy_rate for q in questions)
        avg_accuracy = total_accuracy / len(questions)
        assert abs(avg_accuracy - 0.7125) < 0.001  # Expected: (0.9 + 0.5 + 0.75 + 0.75) / 4
        
        # Find hardest question (lowest accuracy)
        hardest_q = min(questions, key=lambda q: q.accuracy_rate)
        assert hardest_q.content == "题目2"
        assert hardest_q.accuracy_rate == 0.5
        
        # Find easiest question (highest accuracy)
        easiest_q = max(questions, key=lambda q: q.accuracy_rate)
        assert easiest_q.content == "题目1"
        assert easiest_q.accuracy_rate == 0.9

    def test_empty_and_null_fields(self, db_session):
        """Test handling of empty and null fields"""
        question = Question(
            question_type=QuestionType.CHOICE,
            content="简单题目",
            correct_answer="A",
            explanation=None,  # Null explanation
            options=None,      # Null options
            knowledge_points=None  # Null knowledge points
        )
        
        db_session.add(question)
        db_session.commit()
        
        assert question.explanation is None
        assert question.options is None
        assert question.knowledge_points is None

    def test_long_content_and_explanation(self, db_session):
        """Test questions with long content and explanations"""
        long_content = "这是一个很长的题目内容。" * 50  # Repeat to make it long
        long_explanation = "这是一个很长的解析说明。" * 100  # Very long explanation
        
        question = Question(
            question_type=QuestionType.ESSAY,
            content=long_content,
            correct_answer="详细答案",
            explanation=long_explanation
        )
        
        db_session.add(question)
        db_session.commit()
        
        assert len(question.content) > 500
        assert len(question.explanation) > 1000
        assert question.content == long_content
        assert question.explanation == long_explanation

if __name__ == "__main__":
    pytest.main([__file__]) 