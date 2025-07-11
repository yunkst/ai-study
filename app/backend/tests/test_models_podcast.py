"""
Comprehensive tests for Podcast model
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.podcast import Podcast, PodcastStatus, PodcastStyle
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

class TestPodcastStatus:
    """Test PodcastStatus enum"""
    
    def test_podcast_status_values(self):
        """Test enum values"""
        assert PodcastStatus.GENERATING.value == "generating"
        assert PodcastStatus.READY.value == "ready"
        assert PodcastStatus.ERROR.value == "error"

class TestPodcastStyle:
    """Test PodcastStyle enum"""
    
    def test_podcast_style_values(self):
        """Test enum values"""
        assert PodcastStyle.CONVERSATION.value == "conversation"
        assert PodcastStyle.LECTURE.value == "lecture"
        assert PodcastStyle.QA.value == "qa"

class TestPodcast:
    """Test Podcast model"""
    
    def test_create_basic_podcast(self, db_session):
        """Test creating a basic podcast"""
        topics = ["面向对象编程", "设计模式", "软件架构"]
        knowledge_points = ["封装", "继承", "多态", "单例模式", "工厂模式"]
        
        podcast = Podcast(
            title="软件工程基础知识播客",
            description="介绍软件工程的基本概念和设计模式",
            topics=topics,
            knowledge_points=knowledge_points,
            style=PodcastStyle.CONVERSATION
        )
        
        db_session.add(podcast)
        db_session.commit()
        
        assert podcast.id is not None
        assert podcast.title == "软件工程基础知识播客"
        assert podcast.topics == topics
        assert podcast.knowledge_points == knowledge_points
        assert podcast.style == PodcastStyle.CONVERSATION
        assert podcast.status == PodcastStatus.GENERATING  # default
        assert podcast.generation_progress == 0.0  # default
        assert podcast.listen_count == 0  # default

    def test_podcast_defaults(self, db_session):
        """Test default values for podcast"""
        podcast = Podcast(
            title="最简播客",
            topics=["基础概念"]
        )
        
        db_session.add(podcast)
        db_session.commit()
        
        assert podcast.style == PodcastStyle.CONVERSATION  # default
        assert podcast.status == PodcastStatus.GENERATING  # default
        assert podcast.generation_progress == 0.0
        assert podcast.listen_count == 0
        assert podcast.created_at is not None
        assert podcast.completed_at is None

    def test_podcast_repr(self, db_session):
        """Test string representation of podcast"""
        podcast = Podcast(
            title="测试播客",
            topics=["测试主题"]
        )
        db_session.add(podcast)
        db_session.commit()
        
        expected_repr = f"<Podcast(id={podcast.id}, title='测试播客', status=generating)>"
        assert repr(podcast) == expected_repr

    def test_podcast_with_script_and_audio(self, db_session):
        """Test podcast with script content and audio file"""
        script_content = """
        欢迎收听软件工程播客！今天我们来讨论面向对象编程的基本概念。
        
        主持人A：大家好，我是主持人A。
        主持人B：我是主持人B。今天我们要聊的是面向对象编程，这是软件开发中的重要概念。
        
        主持人A：对的，面向对象编程主要包括三个基本特性：封装、继承和多态。
        主持人B：让我们先从封装开始讲解...
        """
        
        podcast = Podcast(
            title="面向对象编程详解",
            description="深入讲解OOP概念",
            topics=["面向对象编程"],
            knowledge_points=["封装", "继承", "多态"],
            style=PodcastStyle.CONVERSATION,
            script_content=script_content,
            audio_file_path="/podcasts/oop_explanation.mp3",
            duration_seconds=1800,  # 30 minutes
            file_size_bytes=25600000,  # ~25MB
            status=PodcastStatus.READY
        )
        
        db_session.add(podcast)
        db_session.commit()
        
        assert podcast.script_content == script_content
        assert podcast.audio_file_path == "/podcasts/oop_explanation.mp3"
        assert podcast.duration_seconds == 1800
        assert podcast.file_size_bytes == 25600000
        assert podcast.status == PodcastStatus.READY

    def test_podcast_generation_progress_tracking(self, db_session):
        """Test tracking podcast generation progress"""
        podcast = Podcast(
            title="生成中的播客",
            topics=["算法"],
            task_id="task_123456"
        )
        
        db_session.add(podcast)
        db_session.commit()
        
        # Simulate progress updates
        progress_steps = [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        statuses = [
            PodcastStatus.GENERATING,
            PodcastStatus.GENERATING,
            PodcastStatus.GENERATING,
            PodcastStatus.GENERATING,
            PodcastStatus.GENERATING,
            PodcastStatus.READY
        ]
        
        for i, (progress, status) in enumerate(zip(progress_steps, statuses)):
            podcast.generation_progress = progress
            podcast.status = status
            
            if status == PodcastStatus.READY:
                podcast.completed_at = datetime.utcnow()
                podcast.audio_file_path = "/podcasts/generated_podcast.mp3"
                podcast.duration_seconds = 1200
            
            db_session.commit()
            
            # Verify progress
            assert podcast.generation_progress == progress
            assert podcast.status == status
            
        # Final verification
        assert podcast.status == PodcastStatus.READY
        assert podcast.generation_progress == 1.0
        assert podcast.completed_at is not None

    def test_podcast_error_handling(self, db_session):
        """Test podcast with generation error"""
        podcast = Podcast(
            title="失败的播客",
            topics=["复杂主题"],
            task_id="failed_task_789"
        )
        
        db_session.add(podcast)
        db_session.commit()
        
        # Simulate generation failure
        podcast.status = PodcastStatus.ERROR
        podcast.error_message = "生成失败：AI服务不可用"
        podcast.generation_progress = 0.4  # Failed at 40%
        
        db_session.commit()
        
        assert podcast.status == PodcastStatus.ERROR
        assert podcast.error_message == "生成失败：AI服务不可用"
        assert podcast.generation_progress == 0.4
        assert podcast.completed_at is None

    def test_podcast_different_styles(self, db_session):
        """Test podcasts with different styles"""
        styles_data = [
            {
                "title": "对话式播客",
                "style": PodcastStyle.CONVERSATION,
                "topics": ["软件测试"],
                "description": "两位专家对话讨论软件测试方法"
            },
            {
                "title": "讲座式播客", 
                "style": PodcastStyle.LECTURE,
                "topics": ["数据库设计"],
                "description": "专家独自讲解数据库设计原理"
            },
            {
                "title": "问答式播客",
                "style": PodcastStyle.QA,
                "topics": ["网络安全"],
                "description": "问答形式介绍网络安全知识"
            }
        ]
        
        podcasts = []
        for data in styles_data:
            podcast = Podcast(
                title=data["title"],
                description=data["description"],
                topics=data["topics"],
                style=data["style"]
            )
            podcasts.append(podcast)
            db_session.add(podcast)
        
        db_session.commit()
        
        # Verify different styles
        assert podcasts[0].style == PodcastStyle.CONVERSATION
        assert podcasts[1].style == PodcastStyle.LECTURE
        assert podcasts[2].style == PodcastStyle.QA

    def test_podcast_listen_count_tracking(self, db_session):
        """Test tracking podcast listen count"""
        podcast = Podcast(
            title="热门播客",
            topics=["人工智能"],
            status=PodcastStatus.READY,
            audio_file_path="/podcasts/ai_podcast.mp3"
        )
        
        db_session.add(podcast)
        db_session.commit()
        
        # Simulate multiple listens
        for i in range(1, 11):  # 10 listens
            podcast.listen_count = i
            db_session.commit()
            assert podcast.listen_count == i
        
        # Final verification
        assert podcast.listen_count == 10

    def test_complex_topics_and_knowledge_points(self, db_session):
        """Test podcast with complex topics and knowledge points structure"""
        complex_topics = [
            {
                "name": "微服务架构",
                "subtopics": ["服务拆分", "服务通信", "服务治理"],
                "difficulty": "advanced"
            },
            {
                "name": "容器化技术",
                "subtopics": ["Docker", "Kubernetes", "服务网格"],
                "difficulty": "intermediate"
            }
        ]
        
        detailed_knowledge_points = [
            {
                "point": "服务拆分原则",
                "category": "架构设计",
                "importance": "high"
            },
            {
                "point": "Docker容器",
                "category": "运维技术", 
                "importance": "medium"
            },
            {
                "point": "API网关",
                "category": "系统集成",
                "importance": "high"
            }
        ]
        
        podcast = Podcast(
            title="现代软件架构播客",
            description="深入探讨现代软件架构设计",
            topics=complex_topics,
            knowledge_points=detailed_knowledge_points,
            style=PodcastStyle.LECTURE
        )
        
        db_session.add(podcast)
        db_session.commit()
        
        assert podcast.topics == complex_topics
        assert podcast.knowledge_points == detailed_knowledge_points
        assert podcast.topics[0]["name"] == "微服务架构"
        assert podcast.knowledge_points[0]["importance"] == "high"

    def test_podcast_file_size_and_duration_calculations(self, db_session):
        """Test podcast file size and duration calculations"""
        podcasts_data = [
            {"title": "短播客", "duration": 300, "size": 5000000},      # 5 minutes, 5MB
            {"title": "中等播客", "duration": 1800, "size": 30000000},   # 30 minutes, 30MB
            {"title": "长播客", "duration": 3600, "size": 60000000},     # 60 minutes, 60MB
        ]
        
        podcasts = []
        for data in podcasts_data:
            podcast = Podcast(
                title=data["title"],
                topics=["测试主题"],
                duration_seconds=data["duration"],
                file_size_bytes=data["size"],
                status=PodcastStatus.READY,
                audio_file_path=f"/podcasts/{data['title'].lower().replace(' ', '_')}.mp3"
            )
            podcasts.append(podcast)
            db_session.add(podcast)
        
        db_session.commit()
        
        # Calculate metrics
        for i, podcast in enumerate(podcasts):
            duration_minutes = podcast.duration_seconds / 60
            size_mb = podcast.file_size_bytes / (1024 * 1024)
            bitrate_kbps = (podcast.file_size_bytes * 8) / (podcast.duration_seconds * 1000)
            
            if i == 0:  # Short podcast
                assert duration_minutes == 5
                assert abs(size_mb - 4.77) < 0.1  # ~5MB
                assert abs(bitrate_kbps - 133.33) < 1  # ~133 kbps
            elif i == 1:  # Medium podcast
                assert duration_minutes == 30
                assert abs(size_mb - 28.61) < 0.1  # ~30MB
            elif i == 2:  # Long podcast
                assert duration_minutes == 60
                assert abs(size_mb - 57.22) < 0.1  # ~60MB

    def test_podcast_search_and_filtering(self, db_session):
        """Test searching and filtering podcasts"""
        # Create podcasts with different characteristics
        podcasts_data = [
            {
                "title": "Java编程基础",
                "topics": ["Java", "编程基础"],
                "status": PodcastStatus.READY,
                "style": PodcastStyle.LECTURE,
                "listen_count": 50
            },
            {
                "title": "Java高级特性",
                "topics": ["Java", "高级编程"],
                "status": PodcastStatus.READY,
                "style": PodcastStyle.CONVERSATION,
                "listen_count": 30
            },
            {
                "title": "Python数据分析",
                "topics": ["Python", "数据分析"],
                "status": PodcastStatus.GENERATING,
                "style": PodcastStyle.LECTURE,
                "listen_count": 0
            },
            {
                "title": "前端开发入门",
                "topics": ["HTML", "CSS", "JavaScript"],
                "status": PodcastStatus.ERROR,
                "style": PodcastStyle.QA,
                "listen_count": 0
            }
        ]
        
        for data in podcasts_data:
            podcast = Podcast(
                title=data["title"],
                topics=data["topics"],
                status=data["status"],
                style=data["style"],
                listen_count=data["listen_count"]
            )
            db_session.add(podcast)
        
        db_session.commit()
        
        # Test filtering by status
        ready_podcasts = db_session.query(Podcast).filter_by(
            status=PodcastStatus.READY
        ).all()
        assert len(ready_podcasts) == 2
        
        # Test filtering by style
        lecture_podcasts = db_session.query(Podcast).filter_by(
            style=PodcastStyle.LECTURE
        ).all()
        assert len(lecture_podcasts) == 2
        
        # Test filtering by listen count (popular podcasts)
        popular_podcasts = db_session.query(Podcast).filter(
            Podcast.listen_count > 20
        ).all()
        assert len(popular_podcasts) == 2
        
        # Test searching by title
        java_podcasts = db_session.query(Podcast).filter(
            Podcast.title.contains("Java")
        ).all()
        assert len(java_podcasts) == 2

    def test_podcast_completion_time_tracking(self, db_session):
        """Test tracking podcast creation and completion times"""
        creation_time = datetime.utcnow()
        
        podcast = Podcast(
            title="时间跟踪测试播客",
            topics=["测试主题"]
        )
        
        db_session.add(podcast)
        db_session.commit()
        
        # Verify creation time
        assert podcast.created_at is not None
        assert podcast.created_at >= creation_time
        assert podcast.completed_at is None
        
        # Simulate completion
        completion_time = datetime.utcnow() + timedelta(minutes=5)
        podcast.status = PodcastStatus.READY
        podcast.completed_at = completion_time
        podcast.generation_progress = 1.0
        
        db_session.commit()
        
        # Calculate generation time
        generation_duration = podcast.completed_at - podcast.created_at
        assert generation_duration.total_seconds() >= 300  # At least 5 minutes
        assert podcast.status == PodcastStatus.READY

    def test_podcast_task_id_tracking(self, db_session):
        """Test tracking background task IDs"""
        podcast = Podcast(
            title="任务跟踪播客",
            topics=["后台任务"],
            task_id="bg_task_abc123"
        )
        
        db_session.add(podcast)
        db_session.commit()
        
        assert podcast.task_id == "bg_task_abc123"
        
        # Find podcast by task ID
        found_podcast = db_session.query(Podcast).filter_by(
            task_id="bg_task_abc123"
        ).first()
        
        assert found_podcast is not None
        assert found_podcast.id == podcast.id

if __name__ == "__main__":
    pytest.main([__file__]) 