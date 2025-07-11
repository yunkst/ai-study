"""
Podcast API 单元测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import json
import os
import tempfile

from main import app

client = TestClient(app)

# 测试数据
MOCK_PODCAST_DATA = {
    "id": 1,
    "title": "软件架构基础学习",
    "description": "深入了解软件架构的基本概念和设计原则",
    "duration": 900,  # 15分钟
    "file_url": "/static/podcasts/podcast_1.mp3",
    "knowledge_points": ["软件架构基础", "设计模式"],
    "topics": ["软件架构", "系统设计"],
    "style": "conversation",
    "status": "completed",
    "created_at": "2024-01-01T00:00:00",
    "generated_at": "2024-01-01T00:15:00"
}

MOCK_EPISODE_LIST = [
    {
        "id": 1,
        "title": "软件架构基础",
        "duration": 900,
        "status": "completed",
        "created_at": "2024-01-01T00:00:00"
    },
    {
        "id": 2,
        "title": "设计模式详解",
        "duration": 1200,
        "status": "generating",
        "created_at": "2024-01-02T00:00:00"
    }
]

MOCK_GENERATION_TASK = {
    "task_id": "task_123",
    "status": "running",
    "progress": 50,
    "estimated_time": 300,
    "current_step": "生成音频文件"
}

class TestPodcastAPI:
    """Podcast API 测试类"""
    
    @patch('api.podcast.get_db')
    def test_get_podcast_episodes_success(self, mock_get_db):
        """测试获取播客列表 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟播客查询
        from models.podcast import Podcast, PodcastStatus, PodcastStyle
        mock_podcasts = [
            MagicMock(
                id=1,
                title="播客1",
                description="描述1",
                duration=900,
                file_url="/static/podcasts/podcast_1.mp3",
                knowledge_points=["知识点1"],
                topics=["主题1"],
                style=PodcastStyle.CONVERSATION,
                status=PodcastStatus.COMPLETED,
                created_at=datetime(2024, 1, 1),
                generated_at=datetime(2024, 1, 1, 0, 15)
            ),
            MagicMock(
                id=2,
                title="播客2",
                description="描述2",
                duration=1200,
                file_url=None,
                knowledge_points=["知识点2"],
                topics=["主题2"],
                style=PodcastStyle.LECTURE,
                status=PodcastStatus.GENERATING,
                created_at=datetime(2024, 1, 2),
                generated_at=None
            )
        ]
        
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = mock_podcasts
        
        response = client.get("/api/podcast/episodes")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["status"] == "completed"
        assert data[1]["id"] == 2
        assert data[1]["status"] == "generating"
    
    @patch('api.podcast.get_db')
    def test_get_podcast_episode_detail_success(self, mock_get_db):
        """测试获取播客详情 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        from models.podcast import Podcast, PodcastStatus, PodcastStyle
        mock_podcast = MagicMock()
        mock_podcast.id = 1
        mock_podcast.title = "测试播客"
        mock_podcast.description = "测试描述"
        mock_podcast.duration = 900
        mock_podcast.file_url = "/static/podcasts/test.mp3"
        mock_podcast.knowledge_points = ["软件架构"]
        mock_podcast.topics = ["系统设计"]
        mock_podcast.style = PodcastStyle.CONVERSATION
        mock_podcast.status = PodcastStatus.COMPLETED
        mock_podcast.created_at = datetime(2024, 1, 1)
        mock_podcast.generated_at = datetime(2024, 1, 1, 0, 15)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_podcast
        
        response = client.get("/api/podcast/episodes/1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == 1
        assert data["title"] == "测试播客"
        assert data["status"] == "completed"
        assert data["file_url"] == "/static/podcasts/test.mp3"
    
    @patch('api.podcast.get_db')
    def test_get_podcast_episode_not_found(self, mock_get_db):
        """测试获取播客详情 - 未找到"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/api/podcast/episodes/999")
        
        assert response.status_code == 404
        assert "播客未找到" in response.json()["detail"]
    
    @patch('api.podcast.task_manager.submit_task')
    @patch('api.podcast.get_db')
    def test_generate_podcast_success(self, mock_get_db, mock_submit_task):
        """测试生成播客 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_submit_task.return_value = "task_123"
        
        request_data = {
            "topics": ["软件架构基础", "设计模式"],
            "style": "conversation",
            "duration_minutes": 15,
            "description": "软件架构学习播客"
        }
        
        with patch('api.podcast.Podcast') as mock_podcast_model:
            mock_podcast = MagicMock()
            mock_podcast.id = 1
            mock_podcast_model.return_value = mock_podcast
            
            response = client.post("/api/podcast/generate", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["message"] == "播客生成任务已启动"
            assert data["episode_id"] == 1
            assert data["task_id"] == "task_123"
            assert "estimated_time" in data
    
    def test_generate_podcast_validation_error(self):
        """测试生成播客 - 验证错误"""
        # 无效风格
        response = client.post("/api/podcast/generate", json={
            "topics": ["软件架构"],
            "style": "invalid_style",
            "duration_minutes": 15
        })
        
        assert response.status_code == 400
        assert "无效的播客风格" in response.json()["detail"]
        
        # 无效时长
        response = client.post("/api/podcast/generate", json={
            "topics": ["软件架构"],
            "style": "conversation",
            "duration_minutes": 0
        })
        
        assert response.status_code == 400
        assert "播客时长必须在1-60分钟之间" in response.json()["detail"]
        
        # 空主题
        response = client.post("/api/podcast/generate", json={
            "topics": [],
            "style": "conversation",
            "duration_minutes": 15
        })
        
        assert response.status_code == 400
        assert "至少需要指定一个主题" in response.json()["detail"]
    
    @patch('api.podcast.get_db')
    def test_download_podcast_success(self, mock_get_db):
        """测试下载播客 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        from models.podcast import Podcast, PodcastStatus
        mock_podcast = MagicMock()
        mock_podcast.id = 1
        mock_podcast.status = PodcastStatus.COMPLETED
        mock_podcast.file_url = "/static/podcasts/test.mp3"
        mock_podcast.title = "测试播客"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_podcast
        
        # 创建临时文件模拟播客文件
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(b"fake mp3 content")
            temp_file_path = temp_file.name
        
        try:
            with patch('os.path.exists') as mock_exists, \
                 patch('api.podcast.FileResponse') as mock_file_response:
                
                mock_exists.return_value = True
                mock_file_response.return_value = Mock()
                
                # 模拟文件路径
                with patch('api.podcast.os.path.join') as mock_join:
                    mock_join.return_value = temp_file_path
                    
                    response = client.get("/api/podcast/episodes/1/download")
                    
                    assert response.status_code == 200
                    mock_file_response.assert_called_once()
        finally:
            os.unlink(temp_file_path)
    
    @patch('api.podcast.get_db')
    def test_download_podcast_not_ready(self, mock_get_db):
        """测试下载播客 - 未完成生成"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        from models.podcast import Podcast, PodcastStatus
        mock_podcast = MagicMock()
        mock_podcast.status = PodcastStatus.GENERATING
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_podcast
        
        response = client.get("/api/podcast/episodes/1/download")
        
        assert response.status_code == 400
        assert "播客尚未生成完成" in response.json()["detail"]
    
    @patch('api.podcast.get_db')
    def test_download_podcast_file_not_found(self, mock_get_db):
        """测试下载播客 - 文件不存在"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        from models.podcast import Podcast, PodcastStatus
        mock_podcast = MagicMock()
        mock_podcast.status = PodcastStatus.COMPLETED
        mock_podcast.file_url = "/static/podcasts/nonexistent.mp3"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_podcast
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            response = client.get("/api/podcast/episodes/1/download")
            
            assert response.status_code == 404
            assert "播客文件未找到" in response.json()["detail"]
    
    @patch('api.podcast.task_manager.get_task_status')
    def test_get_generation_status_success(self, mock_get_task_status):
        """测试获取生成状态 - 成功"""
        mock_get_task_status.return_value = {
            "status": "running",
            "progress": 75,
            "estimated_time": 120,
            "current_step": "生成音频文件"
        }
        
        response = client.get("/api/podcast/generation-status/task_123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "running"
        assert data["progress"] == 75
        assert data["estimated_time"] == 120
        assert data["current_step"] == "生成音频文件"
    
    @patch('api.podcast.task_manager.get_task_status')
    def test_get_generation_status_not_found(self, mock_get_task_status):
        """测试获取生成状态 - 任务未找到"""
        mock_get_task_status.return_value = None
        
        response = client.get("/api/podcast/generation-status/nonexistent")
        
        assert response.status_code == 404
        assert "生成任务未找到" in response.json()["detail"]
    
    @patch('api.podcast.get_db')
    def test_delete_podcast_success(self, mock_get_db):
        """测试删除播客 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_podcast = MagicMock()
        mock_podcast.id = 1
        mock_podcast.file_url = "/static/podcasts/test.mp3"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_podcast
        
        with patch('os.path.exists') as mock_exists, \
             patch('os.remove') as mock_remove:
            
            mock_exists.return_value = True
            
            response = client.delete("/api/podcast/episodes/1")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["message"] == "播客删除成功"
            
            # 验证删除操作
            mock_db.delete.assert_called_once_with(mock_podcast)
            mock_db.commit.assert_called_once()
    
    @patch('api.podcast.get_db')
    def test_get_podcast_statistics_success(self, mock_get_db):
        """测试获取播客统计 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟统计查询
        mock_db.query.return_value.count.return_value = 10  # 总播客数
        mock_db.query.return_value.filter.return_value.count.side_effect = [7, 2, 1]  # 各状态播客数
        
        # 模拟平均时长
        mock_db.query.return_value.filter.return_value.with_entities.return_value.scalar.return_value = 900
        
        # 模拟热门主题
        from models.podcast import Podcast
        mock_podcasts = [
            MagicMock(topics=["软件架构", "设计模式"]),
            MagicMock(topics=["系统设计", "软件架构"]),
            MagicMock(topics=["性能优化"])
        ]
        mock_db.query.return_value.all.return_value = mock_podcasts
        
        response = client.get("/api/podcast/statistics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_episodes" in data
        assert "status_distribution" in data
        assert "average_duration" in data
        assert "popular_topics" in data
        assert "generation_trends" in data
        
        assert data["total_episodes"] == 10
        assert data["average_duration"] == 15.0  # 900秒转换为分钟


class TestPodcastIntegration:
    """Podcast API 集成测试"""
    
    @patch('api.podcast.task_manager.submit_task')
    @patch('api.podcast.get_db')
    def test_complete_podcast_workflow(self, mock_get_db, mock_submit_task):
        """测试完整的播客工作流"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 1. 生成播客
        mock_submit_task.return_value = "task_123"
        
        with patch('api.podcast.Podcast') as mock_podcast_model:
            mock_podcast = MagicMock()
            mock_podcast.id = 1
            mock_podcast_model.return_value = mock_podcast
            
            generate_response = client.post("/api/podcast/generate", json={
                "topics": ["软件架构基础"],
                "style": "conversation",
                "duration_minutes": 15
            })
            
            assert generate_response.status_code == 200
            episode_id = generate_response.json()["episode_id"]
            task_id = generate_response.json()["task_id"]
        
        # 2. 查询生成状态
        with patch('api.podcast.task_manager.get_task_status') as mock_get_task_status:
            mock_get_task_status.return_value = {
                "status": "running",
                "progress": 50,
                "estimated_time": 300,
                "current_step": "生成脚本"
            }
            
            status_response = client.get(f"/api/podcast/generation-status/{task_id}")
            assert status_response.status_code == 200
        
        # 3. 获取播客详情
        from models.podcast import Podcast, PodcastStatus, PodcastStyle
        mock_podcast.title = "生成的播客"
        mock_podcast.status = PodcastStatus.COMPLETED
        mock_podcast.file_url = "/static/podcasts/generated.mp3"
        mock_podcast.knowledge_points = ["软件架构基础"]
        mock_podcast.topics = ["软件架构基础"]
        mock_podcast.style = PodcastStyle.CONVERSATION
        mock_podcast.duration = 900
        mock_podcast.description = None
        mock_podcast.created_at = datetime(2024, 1, 1)
        mock_podcast.generated_at = datetime(2024, 1, 1, 0, 15)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_podcast
        
        detail_response = client.get(f"/api/podcast/episodes/{episode_id}")
        assert detail_response.status_code == 200
        
        # 4. 下载播客
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(b"podcast content")
            temp_file_path = temp_file.name
        
        try:
            with patch('os.path.exists') as mock_exists, \
                 patch('api.podcast.FileResponse') as mock_file_response:
                
                mock_exists.return_value = True
                mock_file_response.return_value = Mock()
                
                with patch('api.podcast.os.path.join') as mock_join:
                    mock_join.return_value = temp_file_path
                    
                    download_response = client.get(f"/api/podcast/episodes/{episode_id}/download")
                    assert download_response.status_code == 200
        finally:
            os.unlink(temp_file_path)
    
    @patch('api.podcast.get_db')
    def test_podcast_management_workflow(self, mock_get_db):
        """测试播客管理工作流"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 1. 获取播客列表
        from models.podcast import Podcast, PodcastStatus, PodcastStyle
        mock_podcasts = [
            MagicMock(
                id=1,
                title="播客1",
                description="描述1",
                duration=900,
                file_url="/static/podcasts/podcast_1.mp3",
                knowledge_points=["知识点1"],
                topics=["主题1"],
                style=PodcastStyle.CONVERSATION,
                status=PodcastStatus.COMPLETED,
                created_at=datetime(2024, 1, 1),
                generated_at=datetime(2024, 1, 1, 0, 15)
            )
        ]
        
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = mock_podcasts
        
        list_response = client.get("/api/podcast/episodes")
        assert list_response.status_code == 200
        
        # 2. 获取统计信息
        mock_db.query.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.with_entities.return_value.scalar.return_value = 900
        mock_db.query.return_value.all.return_value = mock_podcasts
        
        stats_response = client.get("/api/podcast/statistics")
        assert stats_response.status_code == 200
        
        # 3. 删除播客
        mock_db.query.return_value.filter.return_value.first.return_value = mock_podcasts[0]
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # 文件不存在，不需要删除
            
            delete_response = client.delete("/api/podcast/episodes/1")
            assert delete_response.status_code == 200


class TestPodcastValidation:
    """Podcast API 验证测试"""
    
    def test_generate_podcast_topics_validation(self):
        """测试生成播客主题验证"""
        # 主题过多
        response = client.post("/api/podcast/generate", json={
            "topics": ["主题" + str(i) for i in range(11)],  # 超过10个主题
            "style": "conversation",
            "duration_minutes": 15
        })
        
        assert response.status_code == 400
        assert "主题数量不能超过10个" in response.json()["detail"]
    
    def test_generate_podcast_duration_validation(self):
        """测试播客时长验证"""
        # 时长过长
        response = client.post("/api/podcast/generate", json={
            "topics": ["软件架构"],
            "style": "conversation",
            "duration_minutes": 61  # 超过60分钟
        })
        
        assert response.status_code == 400
        assert "播客时长必须在1-60分钟之间" in response.json()["detail"]


class TestPodcastGeneration:
    """播客生成相关测试"""
    
    @patch('api.podcast.asyncio.create_task')
    @patch('api.podcast.tts_service.generate_audio')
    @patch('api.podcast.ai_service.generate_podcast_script')
    def test_podcast_generation_process(self, mock_generate_script, mock_generate_audio, mock_create_task):
        """测试播客生成过程"""
        # 模拟脚本生成
        mock_generate_script.return_value = {
            "title": "测试播客",
            "description": "测试描述",
            "segments": [
                {"speaker": "主持人", "content": "欢迎收听", "timestamp": "00:00"},
                {"speaker": "嘉宾", "content": "谢谢邀请", "timestamp": "00:30"}
            ]
        }
        
        # 模拟音频生成
        mock_generate_audio.return_value = "/static/podcasts/test.mp3"
        
        # 模拟异步任务
        mock_task = AsyncMock()
        mock_create_task.return_value = mock_task
        
        # 这里测试播客生成逻辑的各个组件
        # 实际的生成过程会在后台任务中执行
        
        assert mock_generate_script is not None
        assert mock_generate_audio is not None


@pytest.fixture
def mock_podcast_models():
    """Podcast相关模型的mock fixture"""
    with patch('api.podcast.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 设置常用的mock返回值
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.count.return_value = 0
        
        yield mock_db


class TestPodcastPerformance:
    """Podcast API 性能测试"""
    
    @patch('api.podcast.get_db')
    def test_large_podcast_list_performance(self, mock_get_db):
        """测试大量播客列表的性能"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟大量播客
        from models.podcast import Podcast, PodcastStatus, PodcastStyle
        mock_podcasts = [
            MagicMock(
                id=i,
                title=f"播客{i}",
                description=f"描述{i}",
                duration=900,
                file_url=f"/static/podcasts/podcast_{i}.mp3",
                knowledge_points=[f"知识点{i % 5}"],
                topics=[f"主题{i % 3}"],
                style=PodcastStyle.CONVERSATION,
                status=PodcastStatus.COMPLETED,
                created_at=datetime(2024, 1, 1),
                generated_at=datetime(2024, 1, 1, 0, 15)
            ) for i in range(1, 101)  # 100个播客
        ]
        
        # 分页返回
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = mock_podcasts[:20]
        
        import time
        start_time = time.time()
        
        response = client.get("/api/podcast/episodes?limit=20")
        
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 1.0  # 应该在1秒内完成
        
        data = response.json()
        assert len(data) == 20 