"""
Comprehensive tests for knowledge-related models
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import uuid
import json

from models.knowledge import (
    Base, KnowledgeDomain, KnowledgePoint, SkillPoint, 
    UserKnowledgeProgress, LearningPath, UserLearningPlan,
    DailyLearningPlan, LearningRecommendation, DocumentChunk,
    ImportTask, SystemConfig, knowledge_dependencies,
    learning_path_knowledge_points
)

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
def sample_domain(db_session):
    """Create a sample knowledge domain"""
    domain = KnowledgeDomain(
        name="软件工程",
        description="软件开发相关知识域",
        exam_weight=0.3,
        sort_order=1,
        color="#409EFF"
    )
    db_session.add(domain)
    db_session.commit()
    return domain

@pytest.fixture
def sample_knowledge_point(db_session, sample_domain):
    """Create a sample knowledge point"""
    kp = KnowledgePoint(
        name="面向对象编程",
        description="OOP基础概念",
        content="封装、继承、多态等概念的详细说明",
        difficulty_level=2,
        exam_weight=0.1,
        estimated_study_hours=4.0,
        learning_objectives=["理解OOP概念", "掌握设计模式"],
        keywords=["封装", "继承", "多态"],
        references=["设计模式书籍", "在线教程"],
        examples="代码示例...",
        exercises=[{"type": "coding", "description": "实现一个类"}],
        domain_id=sample_domain.id
    )
    db_session.add(kp)
    db_session.commit()
    return kp

class TestKnowledgeDomain:
    """Test KnowledgeDomain model"""
    
    def test_create_domain(self, db_session):
        """Test creating a knowledge domain"""
        domain = KnowledgeDomain(
            name="数据结构",
            description="数据结构与算法"
        )
        db_session.add(domain)
        db_session.commit()
        
        assert domain.id is not None
        assert domain.name == "数据结构"
        assert domain.exam_weight == 0.0  # default value
        assert domain.is_active is True
        assert domain.created_at is not None
        assert domain.updated_at is not None

    def test_domain_unique_name(self, db_session):
        """Test that domain names must be unique"""
        domain1 = KnowledgeDomain(name="重复名称")
        domain2 = KnowledgeDomain(name="重复名称")
        
        db_session.add(domain1)
        db_session.commit()
        
        db_session.add(domain2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_domain_knowledge_points_relationship(self, db_session, sample_domain):
        """Test relationship between domain and knowledge points"""
        kp1 = KnowledgePoint(name="知识点1", domain_id=sample_domain.id)
        kp2 = KnowledgePoint(name="知识点2", domain_id=sample_domain.id)
        
        db_session.add_all([kp1, kp2])
        db_session.commit()
        
        # Test forward relationship
        assert len(sample_domain.knowledge_points) == 2
        assert kp1 in sample_domain.knowledge_points
        assert kp2 in sample_domain.knowledge_points
        
        # Test backward relationship
        assert kp1.domain == sample_domain
        assert kp2.domain == sample_domain

    def test_domain_cascade_delete(self, db_session, sample_domain):
        """Test that deleting domain cascades to knowledge points"""
        kp = KnowledgePoint(name="测试知识点", domain_id=sample_domain.id)
        db_session.add(kp)
        db_session.commit()
        
        domain_id = sample_domain.id
        kp_id = kp.id
        
        db_session.delete(sample_domain)
        db_session.commit()
        
        # Knowledge point should be deleted too
        assert db_session.query(KnowledgeDomain).filter_by(id=domain_id).first() is None
        assert db_session.query(KnowledgePoint).filter_by(id=kp_id).first() is None

class TestKnowledgePoint:
    """Test KnowledgePoint model"""
    
    def test_create_knowledge_point(self, db_session, sample_domain):
        """Test creating a knowledge point with all fields"""
        learning_objectives = ["目标1", "目标2"]
        keywords = ["关键词1", "关键词2"]
        references = ["参考1", "参考2"]
        exercises = [{"type": "choice", "question": "题目1"}]
        
        kp = KnowledgePoint(
            name="测试知识点",
            description="测试描述",
            content="详细内容",
            difficulty_level=3,
            exam_weight=0.15,
            estimated_study_hours=6.0,
            learning_objectives=learning_objectives,
            keywords=keywords,
            references=references,
            examples="示例内容",
            exercises=exercises,
            sort_order=5,
            domain_id=sample_domain.id
        )
        
        db_session.add(kp)
        db_session.commit()
        
        assert kp.id is not None
        assert kp.name == "测试知识点"
        assert kp.difficulty_level == 3
        assert kp.learning_objectives == learning_objectives
        assert kp.keywords == keywords
        assert kp.references == references
        assert kp.exercises == exercises
        assert kp.domain_id == sample_domain.id

    def test_knowledge_point_defaults(self, db_session, sample_domain):
        """Test default values for knowledge point"""
        kp = KnowledgePoint(name="最小知识点", domain_id=sample_domain.id)
        db_session.add(kp)
        db_session.commit()
        
        assert kp.difficulty_level == 1
        assert kp.exam_weight == 0.0
        assert kp.estimated_study_hours == 1.0
        assert kp.sort_order == 0
        assert kp.is_active is True

    def test_knowledge_point_dependencies(self, db_session, sample_domain):
        """Test self-referencing many-to-many relationship for dependencies"""
        kp1 = KnowledgePoint(name="基础知识点", domain_id=sample_domain.id)
        kp2 = KnowledgePoint(name="进阶知识点", domain_id=sample_domain.id)
        kp3 = KnowledgePoint(name="高级知识点", domain_id=sample_domain.id)
        
        db_session.add_all([kp1, kp2, kp3])
        db_session.commit()
        
        # Set up dependencies: kp3 depends on kp2, kp2 depends on kp1
        kp2.prerequisites.append(kp1)
        kp3.prerequisites.append(kp2)
        db_session.commit()
        
        # Test prerequisites
        assert len(kp1.prerequisites) == 0
        assert len(kp2.prerequisites) == 1
        assert kp1 in kp2.prerequisites
        assert len(kp3.prerequisites) == 1
        assert kp2 in kp3.prerequisites
        
        # Test dependents
        assert len(kp1.dependents) == 1
        assert kp2 in kp1.dependents
        assert len(kp2.dependents) == 1
        assert kp3 in kp2.dependents
        assert len(kp3.dependents) == 0

    def test_knowledge_point_skill_points_relationship(self, db_session, sample_knowledge_point):
        """Test relationship with skill points"""
        sp1 = SkillPoint(
            name="技能点1",
            skill_type="concept",
            knowledge_point_id=sample_knowledge_point.id
        )
        sp2 = SkillPoint(
            name="技能点2",
            skill_type="technique",
            knowledge_point_id=sample_knowledge_point.id
        )
        
        db_session.add_all([sp1, sp2])
        db_session.commit()
        
        assert len(sample_knowledge_point.skill_points) == 2
        assert sp1 in sample_knowledge_point.skill_points
        assert sp2 in sample_knowledge_point.skill_points
        assert sp1.knowledge_point == sample_knowledge_point
        assert sp2.knowledge_point == sample_knowledge_point

class TestSkillPoint:
    """Test SkillPoint model"""
    
    def test_create_skill_point(self, db_session, sample_knowledge_point):
        """Test creating a skill point"""
        practice_methods = ["方法1", "方法2"]
        assessment_questions = ["问题1", "问题2"]
        
        sp = SkillPoint(
            name="编程技能",
            description="编程实现能力",
            skill_type="application",
            mastery_criteria="能够独立编写代码",
            practice_methods=practice_methods,
            assessment_questions=assessment_questions,
            difficulty_level=2,
            estimated_practice_hours=3.0,
            knowledge_point_id=sample_knowledge_point.id
        )
        
        db_session.add(sp)
        db_session.commit()
        
        assert sp.id is not None
        assert sp.name == "编程技能"
        assert sp.skill_type == "application"
        assert sp.practice_methods == practice_methods
        assert sp.assessment_questions == assessment_questions
        assert sp.difficulty_level == 2

    def test_skill_point_defaults(self, db_session, sample_knowledge_point):
        """Test default values for skill point"""
        sp = SkillPoint(name="最小技能点", knowledge_point_id=sample_knowledge_point.id)
        db_session.add(sp)
        db_session.commit()
        
        assert sp.difficulty_level == 1
        assert sp.estimated_practice_hours == 0.5
        assert sp.is_active is True

class TestUserKnowledgeProgress:
    """Test UserKnowledgeProgress model"""
    
    def test_create_user_progress(self, db_session, sample_knowledge_point):
        """Test creating user knowledge progress"""
        progress = UserKnowledgeProgress(
            user_id="user123",
            knowledge_point_id=sample_knowledge_point.id,
            mastery_level=0.7,
            study_time_minutes=120,
            last_reviewed_at=datetime.utcnow(),
            review_count=3,
            correct_answers=15,
            total_answers=20,
            notes="学习笔记内容",
            is_bookmarked=True
        )
        
        db_session.add(progress)
        db_session.commit()
        
        assert progress.id is not None
        assert progress.user_id == "user123"
        assert progress.mastery_level == 0.7
        assert progress.study_time_minutes == 120
        assert progress.review_count == 3
        assert progress.is_bookmarked is True

    def test_user_progress_defaults(self, db_session, sample_knowledge_point):
        """Test default values for user progress"""
        progress = UserKnowledgeProgress(
            user_id="user456",
            knowledge_point_id=sample_knowledge_point.id
        )
        
        db_session.add(progress)
        db_session.commit()
        
        assert progress.mastery_level == 0.0
        assert progress.study_time_minutes == 0
        assert progress.review_count == 0
        assert progress.correct_answers == 0
        assert progress.total_answers == 0
        assert progress.is_bookmarked is False

class TestLearningPath:
    """Test LearningPath model"""
    
    def test_create_learning_path(self, db_session):
        """Test creating a learning path"""
        learning_objectives = ["目标1", "目标2"]
        
        path = LearningPath(
            name="Java学习路径",
            description="Java全栈开发学习路径",
            target_exam="Java认证考试",
            difficulty_level=3,
            estimated_total_hours=100.0,
            prerequisites_description="需要基础编程概念",
            learning_objectives=learning_objectives,
            is_public=True,
            created_by="admin"
        )
        
        db_session.add(path)
        db_session.commit()
        
        assert path.id is not None
        assert path.name == "Java学习路径"
        assert path.difficulty_level == 3
        assert path.learning_objectives == learning_objectives
        assert path.is_public is True

    def test_learning_path_knowledge_points_relationship(self, db_session, sample_knowledge_point):
        """Test many-to-many relationship with knowledge points"""
        path = LearningPath(name="测试路径")
        db_session.add(path)
        db_session.commit()
        
        # Add knowledge point to learning path
        path.knowledge_points.append(sample_knowledge_point)
        db_session.commit()
        
        assert len(path.knowledge_points) == 1
        assert sample_knowledge_point in path.knowledge_points
        assert len(sample_knowledge_point.learning_paths) == 1
        assert path in sample_knowledge_point.learning_paths

class TestUserLearningPlan:
    """Test UserLearningPlan model"""
    
    def test_create_user_learning_plan(self, db_session, sample_knowledge_point):
        """Test creating user learning plan"""
        path = LearningPath(name="测试路径")
        db_session.add(path)
        db_session.commit()
        
        settings = {"reminder_enabled": True, "difficulty_preference": "adaptive"}
        
        plan = UserLearningPlan(
            user_id="user789",
            learning_path_id=path.id,
            plan_name="我的学习计划",
            start_date=datetime.utcnow(),
            target_completion_date=datetime.utcnow() + timedelta(days=30),
            daily_study_hours=3.0,
            current_knowledge_point_id=sample_knowledge_point.id,
            completion_percentage=0.25,
            settings=settings
        )
        
        db_session.add(plan)
        db_session.commit()
        
        assert plan.id is not None
        assert plan.user_id == "user789"
        assert plan.daily_study_hours == 3.0
        assert plan.completion_percentage == 0.25
        assert plan.settings == settings

class TestDailyLearningPlan:
    """Test DailyLearningPlan model"""
    
    def test_create_daily_plan(self, db_session):
        """Test creating daily learning plan"""
        # Create user learning plan first
        path = LearningPath(name="测试路径")
        db_session.add(path)
        db_session.commit()
        
        user_plan = UserLearningPlan(
            user_id="user123",
            learning_path_id=path.id,
            plan_name="测试计划"
        )
        db_session.add(user_plan)
        db_session.commit()
        
        planned_kps = [{"kp_id": "kp1", "estimated_hours": 2.0}]
        completed_kps = [{"kp_id": "kp1", "actual_hours": 1.5, "mastery": 0.8}]
        
        daily_plan = DailyLearningPlan(
            user_plan_id=user_plan.id,
            plan_date=datetime.utcnow().date(),
            planned_knowledge_points=planned_kps,
            planned_study_hours=2.0,
            actual_study_hours=1.5,
            completed_knowledge_points=completed_kps,
            mood_rating=4,
            difficulty_rating=3,
            is_completed=True,
            notes="今天学习效果不错"
        )
        
        db_session.add(daily_plan)
        db_session.commit()
        
        assert daily_plan.id is not None
        assert daily_plan.planned_knowledge_points == planned_kps
        assert daily_plan.completed_knowledge_points == completed_kps
        assert daily_plan.mood_rating == 4
        assert daily_plan.is_completed is True

class TestLearningRecommendation:
    """Test LearningRecommendation model"""
    
    def test_create_recommendation(self, db_session, sample_knowledge_point):
        """Test creating learning recommendation"""
        rec = LearningRecommendation(
            user_id="user123",
            knowledge_point_id=sample_knowledge_point.id,
            recommendation_type="review",
            priority_score=0.8,
            reason="需要复习加强记忆",
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        db_session.add(rec)
        db_session.commit()
        
        assert rec.id is not None
        assert rec.recommendation_type == "review"
        assert rec.priority_score == 0.8
        assert rec.is_active is True

class TestDocumentChunk:
    """Test DocumentChunk model"""
    
    def test_create_document_chunk(self, db_session):
        """Test creating document chunk"""
        metadata = {"title": "第一章", "page": 1}
        embedding_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        chunk = DocumentChunk(
            source_file="/path/to/document.pdf",
            file_hash="abc123def456",
            chunk_index=1,
            content="这是文档的第一个分块内容",
            content_type="text",
            chapter="第一章 基础概念",
            section="1.1 介绍",
            metadata=metadata,
            embedding_model="text-embedding-ada-002",
            embedding_vector=embedding_vector,
            chunk_length=50
        )
        
        db_session.add(chunk)
        db_session.commit()
        
        assert chunk.id is not None
        assert chunk.source_file == "/path/to/document.pdf"
        assert chunk.chunk_index == 1
        assert chunk.metadata == metadata
        assert chunk.embedding_vector == embedding_vector
        assert chunk.is_active is True

class TestImportTask:
    """Test ImportTask model"""
    
    def test_create_import_task(self, db_session):
        """Test creating import task"""
        parameters = {"scan_depth": 3, "file_types": ["pdf", "docx"]}
        result_summary = {"files_processed": 10, "chunks_created": 150}
        
        task = ImportTask(
            task_name="扫描学习资料",
            task_type="scan",
            source_path="/data/learning_materials",
            parameters=parameters,
            status="completed",
            progress=1.0,
            message="扫描完成",
            result_summary=result_summary,
            started_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow(),
            created_by="admin"
        )
        
        db_session.add(task)
        db_session.commit()
        
        assert task.id is not None
        assert task.task_type == "scan"
        assert task.status == "completed"
        assert task.parameters == parameters
        assert task.result_summary == result_summary

    def test_import_task_defaults(self, db_session):
        """Test default values for import task"""
        task = ImportTask(
            task_name="最小任务",
            task_type="upload"
        )
        
        db_session.add(task)
        db_session.commit()
        
        assert task.status == "pending"
        assert task.progress == 0.0

class TestSystemConfig:
    """Test SystemConfig model"""
    
    def test_create_system_config(self, db_session):
        """Test creating system configuration"""
        config_value = {
            "max_concurrent_tasks": 5,
            "default_embedding_model": "text-embedding-ada-002",
            "rag_chunk_size": 1000
        }
        
        config = SystemConfig(
            config_key="rag_settings",
            config_value=config_value,
            description="RAG系统相关配置"
        )
        
        db_session.add(config)
        db_session.commit()
        
        assert config.id is not None
        assert config.config_key == "rag_settings"
        assert config.config_value == config_value
        assert config.is_active is True

    def test_system_config_unique_key(self, db_session):
        """Test that config keys must be unique"""
        config1 = SystemConfig(config_key="unique_key", config_value={"value": 1})
        config2 = SystemConfig(config_key="unique_key", config_value={"value": 2})
        
        db_session.add(config1)
        db_session.commit()
        
        db_session.add(config2)
        with pytest.raises(IntegrityError):
            db_session.commit()

class TestComplexRelationships:
    """Test complex relationships and scenarios"""
    
    def test_learning_path_with_knowledge_points_and_sequence(self, db_session, sample_domain):
        """Test complete learning path setup with proper sequencing"""
        # Create multiple knowledge points
        kp1 = KnowledgePoint(name="基础概念", domain_id=sample_domain.id, sort_order=1)
        kp2 = KnowledgePoint(name="中级技能", domain_id=sample_domain.id, sort_order=2)
        kp3 = KnowledgePoint(name="高级应用", domain_id=sample_domain.id, sort_order=3)
        
        db_session.add_all([kp1, kp2, kp3])
        db_session.commit()
        
        # Set up dependencies
        kp2.prerequisites.append(kp1)
        kp3.prerequisites.append(kp2)
        
        # Create learning path
        path = LearningPath(
            name="完整学习路径",
            description="从基础到高级的完整路径"
        )
        db_session.add(path)
        db_session.commit()
        
        # Add knowledge points to path
        path.knowledge_points.extend([kp1, kp2, kp3])
        db_session.commit()
        
        # Create user learning plan
        user_plan = UserLearningPlan(
            user_id="test_user",
            learning_path_id=path.id,
            plan_name="我的完整学习计划"
        )
        db_session.add(user_plan)
        db_session.commit()
        
        # Create daily plans
        today = datetime.utcnow().date()
        daily_plan = DailyLearningPlan(
            user_plan_id=user_plan.id,
            plan_date=today,
            planned_knowledge_points=[{"kp_id": kp1.id, "target_time": 60}]
        )
        db_session.add(daily_plan)
        db_session.commit()
        
        # Verify all relationships
        assert len(path.knowledge_points) == 3
        assert len(user_plan.learning_path.knowledge_points) == 3
        assert len(user_plan.daily_plans) == 1
        assert daily_plan.user_plan == user_plan

    def test_user_progress_tracking_across_knowledge_points(self, db_session, sample_domain):
        """Test tracking user progress across multiple knowledge points"""
        # Create knowledge points
        kps = []
        for i in range(3):
            kp = KnowledgePoint(name=f"知识点{i+1}", domain_id=sample_domain.id)
            kps.append(kp)
        
        db_session.add_all(kps)
        db_session.commit()
        
        # Create progress records for user
        user_id = "progress_user"
        for i, kp in enumerate(kps):
            progress = UserKnowledgeProgress(
                user_id=user_id,
                knowledge_point_id=kp.id,
                mastery_level=0.2 * (i + 1),  # Increasing mastery
                study_time_minutes=30 * (i + 1),
                correct_answers=5 * (i + 1),
                total_answers=10 * (i + 1)
            )
            db_session.add(progress)
        
        db_session.commit()
        
        # Verify progress tracking
        user_progress = db_session.query(UserKnowledgeProgress).filter_by(user_id=user_id).all()
        assert len(user_progress) == 3
        
        # Check mastery progression
        mastery_levels = [p.mastery_level for p in user_progress]
        assert mastery_levels == [0.2, 0.4, 0.6]

    def test_document_chunk_for_rag_system(self, db_session):
        """Test document chunking for RAG system"""
        # Create multiple chunks from the same document
        source_file = "/documents/machine_learning.pdf"
        file_hash = "ml_doc_hash_123"
        
        chunks = []
        for i in range(5):
            chunk = DocumentChunk(
                source_file=source_file,
                file_hash=file_hash,
                chunk_index=i,
                content=f"这是第{i+1}个文档分块的内容...",
                content_type="text",
                chapter=f"第{(i//2)+1}章",
                section=f"{(i//2)+1}.{(i%2)+1}",
                metadata={"page": i+1, "word_count": 100},
                embedding_model="text-embedding-ada-002",
                embedding_vector=[0.1 * j for j in range(10)],  # Mock embedding
                chunk_length=100
            )
            chunks.append(chunk)
        
        db_session.add_all(chunks)
        db_session.commit()
        
        # Verify document chunking
        doc_chunks = db_session.query(DocumentChunk).filter_by(file_hash=file_hash).all()
        assert len(doc_chunks) == 5
        
        # Check chunk ordering
        chunk_indices = [c.chunk_index for c in doc_chunks]
        assert sorted(chunk_indices) == list(range(5))

if __name__ == "__main__":
    pytest.main([__file__]) 