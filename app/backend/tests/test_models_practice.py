"""
Comprehensive tests for Practice models (PracticeSession and Answer)
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.practice import PracticeSession, Answer
from models.user import User
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

@pytest.fixture
def sample_user(db_session):
    """Create a sample user"""
    user = User(device_id="test_device", nickname="测试用户")
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_questions(db_session):
    """Create sample questions"""
    questions = []
    for i in range(5):
        question = Question(
            question_type=QuestionType.CHOICE,
            content=f"这是第{i+1}道题目",
            correct_answer="A",
            options={"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}
        )
        questions.append(question)
        db_session.add(question)
    
    db_session.commit()
    return questions

class TestPracticeSession:
    """Test PracticeSession model"""
    
    def test_create_practice_session(self, db_session, sample_user, sample_questions):
        """Test creating a practice session"""
        question_ids = [q.id for q in sample_questions]
        
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=question_ids,
            total_questions=len(question_ids)
        )
        
        db_session.add(session)
        db_session.commit()
        
        assert session.id is not None
        assert session.user_id == sample_user.id
        assert session.question_ids == question_ids
        assert session.total_questions == 5
        assert session.start_time is not None
        assert session.end_time is None  # Not finished yet
        assert session.score is None
        assert session.correct_count == 0  # default

    def test_practice_session_repr(self, db_session, sample_user):
        """Test string representation of practice session"""
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=[1, 2, 3],
            total_questions=3
        )
        db_session.add(session)
        db_session.commit()
        
        expected_repr = f"<PracticeSession(id={session.id}, user_id={sample_user.id})>"
        assert repr(session) == expected_repr

    def test_practice_session_relationship_with_user(self, db_session, sample_user):
        """Test relationship between practice session and user"""
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=[1, 2],
            total_questions=2
        )
        db_session.add(session)
        db_session.commit()
        
        # Test relationship
        assert session.user == sample_user
        assert session.user.nickname == "测试用户"

    def test_practice_session_completion(self, db_session, sample_user):
        """Test completing a practice session"""
        start_time = datetime.utcnow()
        
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=[1, 2, 3],
            total_questions=3
        )
        db_session.add(session)
        db_session.commit()
        
        # Simulate session completion
        end_time = start_time + timedelta(minutes=15)
        session.end_time = end_time
        session.duration_seconds = int((end_time - session.start_time).total_seconds())
        session.score = 85.5
        session.correct_count = 2
        
        db_session.commit()
        
        assert session.end_time is not None
        assert session.duration_seconds == 900  # 15 minutes
        assert session.score == 85.5
        assert session.correct_count == 2

    def test_practice_session_with_complex_question_ids(self, db_session, sample_user):
        """Test practice session with complex question IDs structure"""
        # Simulate question IDs with additional metadata
        complex_question_ids = [
            {"id": 1, "difficulty": "basic"},
            {"id": 2, "difficulty": "intermediate"},
            {"id": 3, "difficulty": "advanced"}
        ]
        
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=complex_question_ids,
            total_questions=3
        )
        
        db_session.add(session)
        db_session.commit()
        
        assert session.question_ids == complex_question_ids
        assert session.question_ids[1]["difficulty"] == "intermediate"

class TestAnswer:
    """Test Answer model"""
    
    def test_create_answer(self, db_session, sample_user, sample_questions):
        """Test creating an answer"""
        # Create practice session first
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=[sample_questions[0].id],
            total_questions=1
        )
        db_session.add(session)
        db_session.commit()
        
        # Create answer
        answer = Answer(
            session_id=session.id,
            question_id=sample_questions[0].id,
            user_answer="A",
            is_correct=True,
            time_spent_seconds=30
        )
        
        db_session.add(answer)
        db_session.commit()
        
        assert answer.id is not None
        assert answer.session_id == session.id
        assert answer.question_id == sample_questions[0].id
        assert answer.user_answer == "A"
        assert answer.is_correct is True
        assert answer.time_spent_seconds == 30
        assert answer.answered_at is not None

    def test_answer_repr(self, db_session, sample_user, sample_questions):
        """Test string representation of answer"""
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=[sample_questions[0].id],
            total_questions=1
        )
        db_session.add(session)
        db_session.commit()
        
        answer = Answer(
            session_id=session.id,
            question_id=sample_questions[0].id,
            user_answer="B",
            is_correct=False,
            time_spent_seconds=45
        )
        db_session.add(answer)
        db_session.commit()
        
        expected_repr = f"<Answer(id={answer.id}, question_id={sample_questions[0].id}, correct=False)>"
        assert repr(answer) == expected_repr

    def test_answer_relationships(self, db_session, sample_user, sample_questions):
        """Test relationships between answer, session, and question"""
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=[sample_questions[0].id],
            total_questions=1
        )
        db_session.add(session)
        db_session.commit()
        
        answer = Answer(
            session_id=session.id,
            question_id=sample_questions[0].id,
            user_answer="A",
            is_correct=True,
            time_spent_seconds=25
        )
        db_session.add(answer)
        db_session.commit()
        
        # Test relationships
        assert answer.session == session
        assert answer.question == sample_questions[0]
        assert answer.session.user == sample_user

    def test_multiple_answers_in_session(self, db_session, sample_user, sample_questions):
        """Test multiple answers within a practice session"""
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=[q.id for q in sample_questions[:3]],
            total_questions=3
        )
        db_session.add(session)
        db_session.commit()
        
        # Create answers for each question
        answers_data = [
            {"question": sample_questions[0], "user_answer": "A", "is_correct": True, "time": 30},
            {"question": sample_questions[1], "user_answer": "B", "is_correct": False, "time": 45},
            {"question": sample_questions[2], "user_answer": "A", "is_correct": True, "time": 20}
        ]
        
        answers = []
        for data in answers_data:
            answer = Answer(
                session_id=session.id,
                question_id=data["question"].id,
                user_answer=data["user_answer"],
                is_correct=data["is_correct"],
                time_spent_seconds=data["time"]
            )
            answers.append(answer)
            db_session.add(answer)
        
        db_session.commit()
        
        # Verify all answers are created
        assert len(answers) == 3
        
        # Calculate session statistics
        correct_count = sum(1 for a in answers if a.is_correct)
        total_time = sum(a.time_spent_seconds for a in answers)
        accuracy = correct_count / len(answers)
        
        assert correct_count == 2
        assert total_time == 95  # 30 + 45 + 20
        assert accuracy == 2/3

    def test_answer_timing_analysis(self, db_session, sample_user, sample_questions):
        """Test answer timing analysis"""
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=[q.id for q in sample_questions],
            total_questions=5
        )
        db_session.add(session)
        db_session.commit()
        
        # Create answers with different timing patterns
        timing_data = [
            {"time": 15, "correct": True},   # Quick and correct
            {"time": 60, "correct": True},   # Slow but correct
            {"time": 10, "correct": False},  # Quick but wrong
            {"time": 90, "correct": False},  # Slow and wrong
            {"time": 30, "correct": True}    # Average time, correct
        ]
        
        answers = []
        for i, data in enumerate(timing_data):
            answer = Answer(
                session_id=session.id,
                question_id=sample_questions[i].id,
                user_answer="A",
                is_correct=data["correct"],
                time_spent_seconds=data["time"]
            )
            answers.append(answer)
            db_session.add(answer)
        
        db_session.commit()
        
        # Analyze timing patterns
        correct_answers = [a for a in answers if a.is_correct]
        incorrect_answers = [a for a in answers if not a.is_correct]
        
        avg_time_correct = sum(a.time_spent_seconds for a in correct_answers) / len(correct_answers)
        avg_time_incorrect = sum(a.time_spent_seconds for a in incorrect_answers) / len(incorrect_answers)
        
        assert len(correct_answers) == 3
        assert len(incorrect_answers) == 2
        assert avg_time_correct == (15 + 60 + 30) / 3  # 35 seconds
        assert avg_time_incorrect == (10 + 90) / 2      # 50 seconds

    def test_long_text_answers(self, db_session, sample_user):
        """Test answers with long text content"""
        # Create an essay question
        essay_question = Question(
            question_type=QuestionType.ESSAY,
            content="请论述软件工程的重要性",
            correct_answer="软件工程是..."
        )
        db_session.add(essay_question)
        db_session.commit()
        
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=[essay_question.id],
            total_questions=1
        )
        db_session.add(session)
        db_session.commit()
        
        # Create answer with long text
        long_answer = """软件工程是一门研究和应用如何以系统性的、规范化的、可度量的方法去开发、运营和维护软件的学科。
        它涉及软件生命周期的各个阶段，包括需求分析、系统设计、编程实现、测试验证、部署运维等。
        软件工程的重要性体现在以下几个方面：
        1. 提高软件质量和可靠性
        2. 降低开发成本和风险
        3. 提升开发效率和团队协作
        4. 确保软件的可维护性和可扩展性
        """ * 3  # Make it longer
        
        answer = Answer(
            session_id=session.id,
            question_id=essay_question.id,
            user_answer=long_answer,
            is_correct=True,
            time_spent_seconds=600  # 10 minutes for essay
        )
        
        db_session.add(answer)
        db_session.commit()
        
        assert len(answer.user_answer) > 500
        assert answer.time_spent_seconds == 600

    def test_practice_session_scoring_calculation(self, db_session, sample_user, sample_questions):
        """Test practice session scoring calculation"""
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=[q.id for q in sample_questions],
            total_questions=5
        )
        db_session.add(session)
        db_session.commit()
        
        # Create answers with varying correctness
        correct_answers = 3
        for i in range(5):
            answer = Answer(
                session_id=session.id,
                question_id=sample_questions[i].id,
                user_answer="A",
                is_correct=(i < correct_answers),  # First 3 are correct
                time_spent_seconds=30
            )
            db_session.add(answer)
        
        db_session.commit()
        
        # Calculate and update session score
        session.correct_count = correct_answers
        session.score = (correct_answers / session.total_questions) * 100
        db_session.commit()
        
        assert session.correct_count == 3
        assert session.score == 60.0  # 3/5 * 100 = 60%

    def test_practice_session_performance_metrics(self, db_session, sample_user, sample_questions):
        """Test various performance metrics calculation"""
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=[q.id for q in sample_questions],
            total_questions=5
        )
        db_session.add(session)
        db_session.commit()
        
        # Create answers with specific timing and correctness patterns
        answers_data = [
            {"correct": True, "time": 20},   # Fast correct
            {"correct": True, "time": 40},   # Normal correct
            {"correct": False, "time": 80},  # Slow incorrect
            {"correct": True, "time": 25},   # Fast correct
            {"correct": False, "time": 15}   # Very fast incorrect (guess)
        ]
        
        total_time = 0
        correct_count = 0
        
        for i, data in enumerate(answers_data):
            answer = Answer(
                session_id=session.id,
                question_id=sample_questions[i].id,
                user_answer="A",
                is_correct=data["correct"],
                time_spent_seconds=data["time"]
            )
            db_session.add(answer)
            
            total_time += data["time"]
            if data["correct"]:
                correct_count += 1
        
        db_session.commit()
        
        # Update session with calculated metrics
        session.duration_seconds = total_time
        session.correct_count = correct_count
        session.score = (correct_count / session.total_questions) * 100
        db_session.commit()
        
        # Performance metrics
        accuracy_rate = session.score / 100
        avg_time_per_question = session.duration_seconds / session.total_questions
        questions_per_minute = 60 / avg_time_per_question
        
        assert session.correct_count == 3
        assert session.score == 60.0
        assert session.duration_seconds == 180  # Total time
        assert avg_time_per_question == 36      # 180/5
        assert abs(questions_per_minute - 1.67) < 0.01  # 60/36

if __name__ == "__main__":
    pytest.main([__file__]) 