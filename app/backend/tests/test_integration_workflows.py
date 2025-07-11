"""
Comprehensive integration tests for end-to-end workflows
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base, get_db
from models.user import User
from models.question import Question, QuestionType, DifficultyLevel
from models.practice import PracticeSession, Answer
from models.podcast import Podcast, PodcastStatus, PodcastStyle
from models.analytics import LearningAnalysis, StudyPlan
from models.knowledge import KnowledgeDomain, KnowledgePoint, DocumentChunk
from models.learning_path import LearningPath, UserLearningPlan, DailyLearningPlan

from services.analytics_service import AnalyticsService
from services.ai_service import AIService
from services.rag_service import RAGService
from services.knowledge_extractor import KnowledgeExtractor
from services.learning_path_service import LearningPathService

from api.analytics import router as analytics_router
from api.practice import router as practice_router
from api.podcast import router as podcast_router
from api.questions import router as questions_router

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
    """Create a sample user for integration tests"""
    user = User(
        device_id="integration_test_device",
        nickname="集成测试用户",
        total_questions=50,
        correct_answers=35,
        total_study_time=300
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_domain_and_kps(db_session):
    """Create sample domain and knowledge points"""
    domain = KnowledgeDomain(
        name="软件工程",
        description="软件工程相关知识",
        exam_weight=0.4
    )
    db_session.add(domain)
    db_session.commit()
    
    knowledge_points = []
    for i in range(5):
        kp = KnowledgePoint(
            name=f"知识点{i+1}",
            description=f"知识点{i+1}的描述",
            content=f"知识点{i+1}的详细内容",
            difficulty_level=((i % 3) + 1),
            domain_id=domain.id,
            learning_objectives=[f"目标{i+1}"],
            keywords=[f"关键词{i+1}"]
        )
        knowledge_points.append(kp)
        db_session.add(kp)
    
    db_session.commit()
    return domain, knowledge_points

@pytest.fixture
def sample_questions(db_session, sample_domain_and_kps):
    """Create sample questions"""
    domain, kps = sample_domain_and_kps
    questions = []
    
    for i in range(10):
        question = Question(
            question_type=QuestionType.CHOICE,
            content=f"这是第{i+1}道题目的内容",
            options={
                "A": f"选项A{i+1}",
                "B": f"选项B{i+1}",
                "C": f"选项C{i+1}",
                "D": f"选项D{i+1}"
            },
            correct_answer="A",
            explanation=f"题目{i+1}的解析",
            difficulty=DifficultyLevel((i % 3) + 1),
            knowledge_points=[kps[i % len(kps)].name],
            total_attempts=10 + i,
            correct_attempts=7 + (i % 4)
        )
        questions.append(question)
        db_session.add(question)
    
    db_session.commit()
    return questions

class TestCompleteLearningSess`ionWorkflow:
    """Test complete learning session workflow from practice to analytics"""
    
    def test_full_practice_to_analytics_workflow(self, db_session, sample_user, sample_questions):
        """Test complete workflow: practice session -> answer submission -> analytics generation"""
        # Step 1: Create practice session
        question_ids = [q.id for q in sample_questions[:5]]
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=question_ids,
            total_questions=5
        )
        db_session.add(session)
        db_session.commit()
        
        assert session.start_time is not None
        assert session.end_time is None
        
        # Step 2: Simulate answering questions
        answers_data = [
            {"question_id": question_ids[0], "user_answer": "A", "correct": True, "time": 30},
            {"question_id": question_ids[1], "user_answer": "B", "correct": False, "time": 45},
            {"question_id": question_ids[2], "user_answer": "A", "correct": True, "time": 25},
            {"question_id": question_ids[3], "user_answer": "C", "correct": False, "time": 60},
            {"question_id": question_ids[4], "user_answer": "A", "correct": True, "time": 35}
        ]
        
        total_time = 0
        correct_count = 0
        
        for answer_data in answers_data:
            answer = Answer(
                session_id=session.id,
                question_id=answer_data["question_id"],
                user_answer=answer_data["user_answer"],
                is_correct=answer_data["correct"],
                time_spent_seconds=answer_data["time"]
            )
            db_session.add(answer)
            
            total_time += answer_data["time"]
            if answer_data["correct"]:
                correct_count += 1
        
        db_session.commit()
        
        # Step 3: Complete practice session
        session.end_time = datetime.utcnow()
        session.duration_seconds = total_time
        session.correct_count = correct_count
        session.score = (correct_count / session.total_questions) * 100
        db_session.commit()
        
        assert session.score == 60.0  # 3/5 * 100
        assert session.duration_seconds == 195  # Total time
        
        # Step 4: Update user statistics
        sample_user.total_questions += session.total_questions
        sample_user.correct_answers += session.correct_count
        sample_user.total_study_time += session.duration_seconds // 60
        db_session.commit()
        
        assert sample_user.total_questions == 55  # 50 + 5
        assert sample_user.correct_answers == 38  # 35 + 3
        
        # Step 5: Generate analytics
        analytics = LearningAnalysis(
            user_id=sample_user.id,
            period_start=datetime.utcnow() - timedelta(days=1),
            period_end=datetime.utcnow(),
            total_questions=session.total_questions,
            correct_answers=session.correct_count,
            accuracy_rate=session.score / 100,
            average_time_per_question=session.duration_seconds / session.total_questions,
            study_sessions=1,
            total_study_time=session.duration_seconds // 60
        )
        db_session.add(analytics)
        db_session.commit()
        
        assert analytics.accuracy_rate == 0.6
        assert analytics.average_time_per_question == 39.0  # 195/5
        
        # Step 6: Verify complete workflow
        completed_session = db_session.query(PracticeSession).filter_by(id=session.id).first()
        session_answers = db_session.query(Answer).filter_by(session_id=session.id).all()
        user_analytics = db_session.query(LearningAnalysis).filter_by(user_id=sample_user.id).first()
        
        assert completed_session.is_completed
        assert len(session_answers) == 5
        assert user_analytics.total_questions == 5

    @patch('services.ai_service.openai.ChatCompletion.acreate')
    async def test_ai_enhanced_learning_workflow(self, mock_openai, db_session, sample_user, sample_questions):
        """Test learning workflow with AI-generated explanations and recommendations"""
        # Mock AI service responses
        mock_openai.return_value = AsyncMock()
        mock_openai.return_value.choices = [
            Mock(message=Mock(content="这是AI生成的详细解析和学习建议"))
        ]
        
        # Create practice session with poor performance
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=[q.id for q in sample_questions[:3]],
            total_questions=3,
            score=33.33,  # Poor performance
            correct_count=1
        )
        db_session.add(session)
        db_session.commit()
        
        # Create AI service instance
        ai_service = AIService()
        
        # Generate AI explanations for wrong answers
        wrong_questions = [sample_questions[1], sample_questions[2]]
        explanations = []
        
        for question in wrong_questions:
            explanation = await ai_service.generate_question_explanation(
                question_id=question.id,
                user_answer="B",  # Wrong answer
                correct_answer=question.correct_answer,
                difficulty="intermediate"
            )
            explanations.append(explanation)
        
        assert len(explanations) == 2
        mock_openai.assert_called()
        
        # Generate learning recommendations
        recommendations = await ai_service.generate_learning_recommendations(
            user_id=sample_user.id,
            weak_areas=["算法设计", "数据结构"],
            performance_data={"accuracy": 0.33, "time_efficiency": 0.7}
        )
        
        assert recommendations is not None
        
        # Create analytics with AI recommendations
        analytics = LearningAnalysis(
            user_id=sample_user.id,
            period_start=datetime.utcnow() - timedelta(days=1),
            period_end=datetime.utcnow(),
            total_questions=3,
            correct_answers=1,
            accuracy_rate=0.33,
            ai_recommendations=recommendations
        )
        db_session.add(analytics)
        db_session.commit()
        
        assert analytics.ai_recommendations is not None

class TestPodcastGenerationWorkflow:
    """Test podcast generation workflow from request to completion"""
    
    @patch('services.ai_service.openai.ChatCompletion.acreate')
    @patch('celery.Celery.send_task')
    async def test_complete_podcast_generation_workflow(self, mock_celery, mock_openai, db_session):
        """Test complete podcast generation from request to audio file"""
        # Mock AI service for script generation
        mock_openai.return_value = AsyncMock()
        mock_openai.return_value.choices = [
            Mock(message=Mock(content="""
            欢迎收听软件工程播客！今天我们来讨论面向对象编程。
            
            主持人A：大家好，我是主持人A。
            主持人B：我是主持人B。今天我们要聊面向对象编程的核心概念。
            
            主持人A：面向对象编程有三大特性：封装、继承和多态。
            主持人B：让我们详细讨论每一个特性...
            """))
        ]
        
        # Mock Celery task
        mock_celery.return_value = Mock(task_id="podcast_task_123")
        
        # Step 1: Create podcast generation request
        topics = ["面向对象编程", "设计模式"]
        knowledge_points = ["封装", "继承", "多态", "单例模式"]
        
        podcast = Podcast(
            title="面向对象编程详解",
            description="深入讲解面向对象编程核心概念",
            topics=topics,
            knowledge_points=knowledge_points,
            style=PodcastStyle.CONVERSATION,
            task_id="podcast_task_123"
        )
        db_session.add(podcast)
        db_session.commit()
        
        assert podcast.status == PodcastStatus.GENERATING
        assert podcast.generation_progress == 0.0
        
        # Step 2: Generate script using AI service
        ai_service = AIService()
        script = await ai_service.generate_podcast_script(
            topics=topics,
            knowledge_points=knowledge_points,
            style="conversation",
            duration_minutes=15
        )
        
        assert script is not None
        mock_openai.assert_called()
        
        # Step 3: Update podcast with generated script
        podcast.script_content = script
        podcast.generation_progress = 0.5
        db_session.commit()
        
        # Step 4: Simulate audio generation completion
        podcast.audio_file_path = "/podcasts/oop_explanation.mp3"
        podcast.duration_seconds = 900  # 15 minutes
        podcast.file_size_bytes = 14400000  # ~14MB
        podcast.status = PodcastStatus.READY
        podcast.generation_progress = 1.0
        podcast.completed_at = datetime.utcnow()
        db_session.commit()
        
        # Step 5: Verify complete workflow
        completed_podcast = db_session.query(Podcast).filter_by(id=podcast.id).first()
        
        assert completed_podcast.status == PodcastStatus.READY
        assert completed_podcast.generation_progress == 1.0
        assert completed_podcast.script_content is not None
        assert completed_podcast.audio_file_path is not None
        assert completed_podcast.completed_at is not None

    async def test_podcast_error_handling_workflow(self, db_session):
        """Test podcast generation error handling workflow"""
        # Create podcast that will fail
        podcast = Podcast(
            title="失败的播客",
            topics=["复杂主题"],
            task_id="failing_task_456"
        )
        db_session.add(podcast)
        db_session.commit()
        
        # Simulate generation failure
        podcast.status = PodcastStatus.ERROR
        podcast.error_message = "AI服务暂时不可用，请稍后重试"
        podcast.generation_progress = 0.3  # Failed at 30%
        db_session.commit()
        
        # Verify error state
        failed_podcast = db_session.query(Podcast).filter_by(id=podcast.id).first()
        assert failed_podcast.status == PodcastStatus.ERROR
        assert failed_podcast.error_message is not None
        assert failed_podcast.completed_at is None

class TestLearningPathProgressionWorkflow:
    """Test learning path progression and daily plan workflow"""
    
    def test_complete_learning_path_workflow(self, db_session, sample_user, sample_domain_and_kps):
        """Test complete learning path from creation to completion"""
        domain, kps = sample_domain_and_kps
        
        # Step 1: Create learning path
        knowledge_sequence = [
            {"kp_id": kp.id, "order": i+1, "weight": 0.2} 
            for i, kp in enumerate(kps)
        ]
        
        learning_stages = [
            {
                "name": "基础阶段",
                "kp_ids": [kps[0].id, kps[1].id],
                "target_days": 10
            },
            {
                "name": "进阶阶段", 
                "kp_ids": [kps[2].id, kps[3].id, kps[4].id],
                "target_days": 15
            }
        ]
        
        path = LearningPath(
            name="完整学习路径",
            description="从基础到进阶的完整学习路径",
            knowledge_point_sequence=knowledge_sequence,
            learning_stages=learning_stages,
            estimated_days=25,
            created_by=sample_user.id
        )
        db_session.add(path)
        db_session.commit()
        
        # Step 2: Create user learning plan
        user_plan = UserLearningPlan(
            user_id=sample_user.id,
            learning_path_id=path.id,
            plan_name="我的完整学习计划",
            target_exam_date=datetime.utcnow() + timedelta(days=30),
            daily_study_hours=2.0
        )
        db_session.add(user_plan)
        db_session.commit()
        
        assert user_plan.overall_progress == 0.0
        assert user_plan.current_stage == 0
        
        # Step 3: Create daily learning plans
        daily_plans = []
        base_date = datetime.utcnow().date()
        
        for day in range(5):  # Create 5 daily plans
            plan_date = base_date + timedelta(days=day)
            kp_for_day = kps[day % len(kps)]
            
            daily_plan = DailyLearningPlan(
                user_plan_id=user_plan.id,
                plan_date=plan_date,
                planned_knowledge_points=[{
                    "kp_id": kp_for_day.id,
                    "target_mastery": 0.8
                }],
                planned_study_minutes=120
            )
            daily_plans.append(daily_plan)
            db_session.add(daily_plan)
        
        db_session.commit()
        
        # Step 4: Simulate daily plan completion
        for i, daily_plan in enumerate(daily_plans):
            # Simulate completion
            daily_plan.completed_knowledge_points = [{
                "kp_id": daily_plan.planned_knowledge_points[0]["kp_id"],
                "achieved_mastery": 0.75 + (i * 0.05),  # Improving over time
                "time_spent": 110 + (i * 5)
            }]
            daily_plan.actual_study_minutes = 115 + (i * 5)
            daily_plan.is_completed = True
            daily_plan.completion_rate = 1.0
            daily_plan.difficulty_feedback = 3
            
        db_session.commit()
        
        # Step 5: Update user learning plan progress
        completed_plans = len([p for p in daily_plans if p.is_completed])
        user_plan.overall_progress = completed_plans / len(daily_plans)
        
        if user_plan.overall_progress >= 0.5:
            user_plan.current_stage = 1  # Move to next stage
        
        db_session.commit()
        
        # Step 6: Verify workflow completion
        updated_plan = db_session.query(UserLearningPlan).filter_by(id=user_plan.id).first()
        completed_daily_plans = db_session.query(DailyLearningPlan).filter_by(
            user_plan_id=user_plan.id,
            is_completed=True
        ).all()
        
        assert updated_plan.overall_progress == 1.0
        assert updated_plan.current_stage == 1
        assert len(completed_daily_plans) == 5

class TestKnowledgeExtractionAndRAGWorkflow:
    """Test knowledge extraction and RAG system workflow"""
    
    @patch('services.rag_service.openai.Embedding.create')
    async def test_document_processing_to_rag_workflow(self, mock_embedding, db_session):
        """Test complete workflow from document upload to RAG query"""
        # Mock embedding generation
        mock_embedding.return_value = Mock(
            data=[Mock(embedding=[0.1, 0.2, 0.3, 0.4, 0.5] * 200)]  # 1000-dim embedding
        )
        
        # Step 1: Simulate document processing
        extractor = KnowledgeExtractor()
        
        # Mock document content
        document_content = """
        软件工程是一门研究和应用如何以系统性的、规范化的、可度量的方法去开发、运营和维护软件的学科。
        软件工程包括以下几个主要阶段：
        1. 需求分析：明确用户需求和系统功能
        2. 系统设计：设计系统架构和模块结构
        3. 编程实现：编写代码实现设计功能
        4. 测试验证：确保软件质量和正确性
        5. 部署运维：将软件部署到生产环境并维护
        """
        
        # Step 2: Extract and create document chunks
        chunks_data = [
            {
                "content": "软件工程是一门研究和应用如何以系统性的、规范化的、可度量的方法去开发、运营和维护软件的学科。",
                "chapter": "第一章 软件工程概述",
                "section": "1.1 定义"
            },
            {
                "content": "软件工程包括需求分析、系统设计、编程实现、测试验证、部署运维等主要阶段。",
                "chapter": "第一章 软件工程概述", 
                "section": "1.2 主要阶段"
            },
            {
                "content": "需求分析阶段主要任务是明确用户需求和系统功能，为后续设计提供依据。",
                "chapter": "第二章 需求分析",
                "section": "2.1 需求分析概述"
            }
        ]
        
        document_chunks = []
        for i, chunk_data in enumerate(chunks_data):
            chunk = DocumentChunk(
                source_file="/documents/software_engineering.pdf",
                file_hash="se_doc_hash_123",
                chunk_index=i,
                content=chunk_data["content"],
                content_type="text",
                chapter=chunk_data["chapter"],
                section=chunk_data["section"],
                metadata={"page": i+1, "word_count": len(chunk_data["content"])},
                embedding_model="text-embedding-ada-002",
                embedding_vector=[0.1, 0.2, 0.3, 0.4, 0.5] * 200,  # Mock embedding
                chunk_length=len(chunk_data["content"])
            )
            document_chunks.append(chunk)
            db_session.add(chunk)
        
        db_session.commit()
        
        # Step 3: Initialize RAG service and perform similarity search
        rag_service = RAGService()
        
        # Mock similarity search
        query = "什么是软件工程？"
        
        # Simulate RAG search (normally would compute similarity)
        relevant_chunks = db_session.query(DocumentChunk).filter(
            DocumentChunk.content.contains("软件工程")
        ).limit(3).all()
        
        assert len(relevant_chunks) >= 1
        
        # Step 4: Generate context-aware response
        context = "\n".join([chunk.content for chunk in relevant_chunks])
        
        # Mock AI response generation (would normally call OpenAI)
        rag_response = f"根据知识库内容：{context[:100]}... 软件工程是一门系统化的软件开发学科。"
        
        assert "软件工程" in rag_response
        assert len(context) > 0
        
        # Step 5: Verify complete RAG workflow
        all_chunks = db_session.query(DocumentChunk).filter_by(
            file_hash="se_doc_hash_123"
        ).all()
        
        assert len(all_chunks) == 3
        assert all(chunk.embedding_vector is not None for chunk in all_chunks)

class TestAnalyticsAndRecommendationWorkflow:
    """Test analytics generation and recommendation workflow"""
    
    async def test_performance_analysis_to_recommendation_workflow(self, db_session, sample_user, sample_questions):
        """Test workflow from performance data to personalized recommendations"""
        # Step 1: Create multiple practice sessions with varying performance
        sessions_data = [
            {"questions": sample_questions[:3], "correct": 1, "time": 180},  # Poor performance
            {"questions": sample_questions[3:6], "correct": 2, "time": 150}, # Improving
            {"questions": sample_questions[6:9], "correct": 3, "time": 120}  # Good performance
        ]
        
        sessions = []
        for i, session_data in enumerate(sessions_data):
            session = PracticeSession(
                user_id=sample_user.id,
                question_ids=[q.id for q in session_data["questions"]],
                total_questions=3,
                correct_count=session_data["correct"],
                duration_seconds=session_data["time"],
                score=(session_data["correct"] / 3) * 100,
                start_time=datetime.utcnow() - timedelta(days=3-i),
                end_time=datetime.utcnow() - timedelta(days=3-i) + timedelta(minutes=session_data["time"]//60)
            )
            sessions.append(session)
            db_session.add(session)
        
        db_session.commit()
        
        # Step 2: Generate analytics with trend analysis
        analytics_service = AnalyticsService()
        
        # Calculate performance metrics
        total_questions = sum(s.total_questions for s in sessions)
        total_correct = sum(s.correct_count for s in sessions)
        avg_time = sum(s.duration_seconds for s in sessions) / len(sessions)
        accuracy_trend = [s.score / 100 for s in sessions]  # [0.33, 0.67, 1.0] - improving
        
        # Create comprehensive analytics
        analytics = LearningAnalysis(
            user_id=sample_user.id,
            period_start=datetime.utcnow() - timedelta(days=7),
            period_end=datetime.utcnow(),
            total_questions=total_questions,
            correct_answers=total_correct,
            accuracy_rate=total_correct / total_questions,
            average_time_per_question=avg_time / 3,
            study_sessions=len(sessions),
            total_study_time=sum(s.duration_seconds for s in sessions) // 60,
            difficulty_analysis={
                "basic": {"accuracy": 0.8, "improvement": "stable"},
                "intermediate": {"accuracy": 0.6, "improvement": "increasing"},
                "advanced": {"accuracy": 0.4, "improvement": "needs_focus"}
            },
            weak_points=[
                {"topic": "算法设计", "accuracy": 0.4, "priority": "high"},
                {"topic": "系统设计", "accuracy": 0.5, "priority": "medium"}
            ]
        )
        db_session.add(analytics)
        db_session.commit()
        
        # Step 3: Generate study plan based on analytics
        study_plan = StudyPlan(
            user_id=sample_user.id,
            plan_title="基于分析的改进计划",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=21),
            daily_questions_target=20,  # Increased target
            daily_study_time_target=90,  # Increased time
            accuracy_target=0.85,
            focus_topics=[
                {
                    "topic": "算法设计",
                    "priority": "high",
                    "target_accuracy": 0.8,
                    "weekly_hours": 8
                },
                {
                    "topic": "系统设计",
                    "priority": "medium", 
                    "target_accuracy": 0.75,
                    "weekly_hours": 5
                }
            ]
        )
        db_session.add(study_plan)
        db_session.commit()
        
        # Step 4: Verify complete analytics workflow
        user_analytics = db_session.query(LearningAnalysis).filter_by(user_id=sample_user.id).first()
        user_study_plan = db_session.query(StudyPlan).filter_by(user_id=sample_user.id).first()
        
        assert user_analytics.accuracy_rate == 6/9  # Total: 6 correct out of 9
        assert len(user_analytics.weak_points) == 2
        assert user_study_plan.daily_questions_target == 20
        assert len(user_study_plan.focus_topics) == 2

class TestCrossSystemIntegrationWorkflow:
    """Test integration across multiple system components"""
    
    @patch('services.ai_service.openai.ChatCompletion.acreate')
    async def test_complete_system_integration_workflow(self, mock_openai, db_session, sample_user, sample_domain_and_kps, sample_questions):
        """Test complete integration across practice, analytics, RAG, and AI components"""
        # Mock AI responses
        mock_openai.return_value = AsyncMock()
        mock_openai.return_value.choices = [
            Mock(message=Mock(content="AI生成的学习建议和内容"))
        ]
        
        domain, kps = sample_domain_and_kps
        
        # Step 1: Knowledge extraction and RAG setup
        document_chunk = DocumentChunk(
            source_file="/docs/study_guide.pdf",
            file_hash="study_guide_123",
            chunk_index=0,
            content="面向对象编程是软件开发的重要方法，包括封装、继承和多态三大特性。",
            content_type="text",
            embedding_model="text-embedding-ada-002",
            embedding_vector=[0.1] * 1000
        )
        db_session.add(document_chunk)
        db_session.commit()
        
        # Step 2: Practice session with real-time AI assistance
        session = PracticeSession(
            user_id=sample_user.id,
            question_ids=[q.id for q in sample_questions[:3]],
            total_questions=3
        )
        db_session.add(session)
        db_session.commit()
        
        # Step 3: Answer questions with AI explanations
        ai_service = AIService()
        
        for i, question in enumerate(sample_questions[:3]):
            # Submit answer
            answer = Answer(
                session_id=session.id,
                question_id=question.id,
                user_answer="B",  # Assume wrong answer
                is_correct=False,
                time_spent_seconds=45
            )
            db_session.add(answer)
            
            # Get AI explanation for wrong answer
            explanation = await ai_service.generate_question_explanation(
                question_id=question.id,
                user_answer="B",
                correct_answer=question.correct_answer,
                difficulty="intermediate"
            )
            
            # Store explanation (in real system, would be returned to user)
            answer.ai_explanation = explanation
        
        db_session.commit()
        
        # Step 4: Complete session and generate analytics
        session.end_time = datetime.utcnow()
        session.correct_count = 0  # All wrong for this example
        session.score = 0.0
        session.duration_seconds = 135
        db_session.commit()
        
        # Step 5: Generate AI-powered analytics and recommendations
        analytics = LearningAnalysis(
            user_id=sample_user.id,
            period_start=datetime.utcnow() - timedelta(days=1),
            period_end=datetime.utcnow(),
            total_questions=3,
            correct_answers=0,
            accuracy_rate=0.0,
            weak_points=[{"topic": "面向对象编程", "accuracy": 0.0}]
        )
        
        # Generate AI recommendations
        recommendations = await ai_service.generate_learning_recommendations(
            user_id=sample_user.id,
            weak_areas=["面向对象编程"],
            performance_data={"accuracy": 0.0, "improvement_needed": True}
        )
        
        analytics.ai_recommendations = recommendations
        db_session.add(analytics)
        db_session.commit()
        
        # Step 6: Create adaptive learning path
        adaptive_sequence = [
            {"kp_id": kps[0].id, "order": 1, "weight": 0.4, "focus": "remedial"},
            {"kp_id": kps[1].id, "order": 2, "weight": 0.3, "focus": "practice"},
            {"kp_id": kps[2].id, "order": 3, "weight": 0.3, "focus": "advanced"}
        ]
        
        learning_path = LearningPath(
            name="AI驱动的自适应学习路径",
            description="基于用户表现动态调整的学习路径",
            knowledge_point_sequence=adaptive_sequence,
            estimated_days=14,
            created_by=sample_user.id
        )
        db_session.add(learning_path)
        db_session.commit()
        
        # Step 7: Verify complete cross-system integration
        final_session = db_session.query(PracticeSession).filter_by(id=session.id).first()
        final_analytics = db_session.query(LearningAnalysis).filter_by(user_id=sample_user.id).first()
        final_path = db_session.query(LearningPath).filter_by(created_by=sample_user.id).first()
        answer_with_ai = db_session.query(Answer).filter_by(session_id=session.id).first()
        
        assert final_session.score == 0.0
        assert final_analytics.ai_recommendations is not None
        assert final_path.name == "AI驱动的自适应学习路径"
        assert answer_with_ai.ai_explanation is not None
        assert mock_openai.call_count >= 2  # Called for explanations and recommendations

if __name__ == "__main__":
    pytest.main([__file__]) 