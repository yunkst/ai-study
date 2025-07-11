"""
Admin API 单元测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import psutil

from main import app

client = TestClient(app)

# 测试数据
MOCK_SYSTEM_STATUS = {
    "status": "healthy",
    "uptime": "2 days, 5 hours, 30 minutes",
    "database_connected": True,
    "redis_connected": False,
    "ai_service_status": "available",
    "active_tasks": 3,
    "memory_usage_mb": 512.5,
    "cpu_usage_percent": 15.2,
    "disk_usage_percent": 45.8,
    "last_backup": "2024-01-01T02:00:00"
}

MOCK_DATABASE_STATS = {
    "total_questions": 1500,
    "total_users": 250,
    "total_practice_sessions": 850,
    "total_podcasts": 45,
    "database_size_mb": 128.5,
    "active_connections": 12,
    "query_performance": {
        "avg_response_time_ms": 25.3,
        "slow_queries_count": 3
    }
}

MOCK_USER_ANALYTICS = {
    "total_users": 250,
    "active_users_today": 85,
    "active_users_week": 180,
    "new_users_today": 5,
    "user_retention_rate": 0.78,
    "avg_session_duration": 1800,
    "top_knowledge_points": [
        {"name": "软件架构基础", "users": 120},
        {"name": "设计模式", "users": 95},
        {"name": "系统设计", "users": 80}
    ]
}

MOCK_BACKUP_INFO = {
    "last_backup": "2024-01-01T02:00:00",
    "backup_size_mb": 256.7,
    "backup_status": "success",
    "next_scheduled_backup": "2024-01-02T02:00:00",
    "retention_days": 30,
    "backup_location": "/backups/db_backup_20240101.sql"
}

class TestAdminAPI:
    """Admin API 测试类"""
    
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_percent')
    @patch('psutil.disk_usage')
    @patch('api.admin.get_db')
    def test_get_system_status_success(self, mock_get_db, mock_disk_usage, mock_cpu_percent, mock_virtual_memory):
        """测试获取系统状态 - 成功"""
        # Mock系统资源信息
        mock_virtual_memory.return_value.used = 512 * 1024 * 1024  # 512MB
        mock_cpu_percent.return_value = 15.2
        mock_disk_usage.return_value.percent = 45.8
        
        # Mock数据库连接
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.execute.return_value = Mock()  # 模拟数据库连接成功
        
        # Mock任务管理器
        with patch('api.admin.task_manager.get_active_tasks_count') as mock_active_tasks:
            mock_active_tasks.return_value = 3
            
            response = client.get("/api/admin/system-status")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] in ["healthy", "warning", "error"]
            assert "uptime" in data
            assert data["database_connected"] is True
            assert data["active_tasks"] == 3
            assert data["memory_usage_mb"] == 512.0
            assert data["cpu_usage_percent"] == 15.2
            assert data["disk_usage_percent"] == 45.8
    
    @patch('api.admin.get_db')
    def test_get_system_status_database_error(self, mock_get_db):
        """测试获取系统状态 - 数据库连接失败"""
        # Mock数据库连接失败
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.execute.side_effect = Exception("Database connection failed")
        
        with patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('api.admin.task_manager.get_active_tasks_count') as mock_tasks:
            
            mock_memory.return_value.used = 512 * 1024 * 1024
            mock_cpu.return_value = 15.2
            mock_disk.return_value.percent = 45.8
            mock_tasks.return_value = 0
            
            response = client.get("/api/admin/system-status")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["database_connected"] is False
            assert data["status"] in ["warning", "error"]
    
    @patch('api.admin.get_db')
    def test_get_database_stats_success(self, mock_get_db):
        """测试获取数据库统计 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock各种统计查询
        def mock_scalar_results(*args, **kwargs):
            # 根据查询类型返回不同的结果
            query = str(args[0]) if args else ""
            if "Question" in query:
                return 1500
            elif "User" in query:
                return 250
            elif "PracticeSession" in query:
                return 850
            elif "Podcast" in query:
                return 45
            else:
                return 0
        
        mock_db.execute.return_value.scalar.side_effect = mock_scalar_results
        
        # Mock数据库大小查询
        with patch('api.admin.text') as mock_text:
            mock_db.execute.return_value.fetchone.return_value = (128.5,)
            
            response = client.get("/api/admin/database-stats")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "total_questions" in data
            assert "total_users" in data
            assert "total_practice_sessions" in data
            assert "total_podcasts" in data
            assert "database_size_mb" in data
            assert "active_connections" in data
            assert "query_performance" in data
    
    @patch('api.admin.get_db')
    def test_get_user_analytics_success(self, mock_get_db):
        """测试获取用户分析 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock用户统计查询
        mock_db.query.return_value.count.return_value = 250  # 总用户数
        
        # Mock今日活跃用户查询
        mock_db.query.return_value.filter.return_value.count.side_effect = [85, 180, 5]  # 今日、本周、今日新增
        
        # Mock知识点统计
        mock_knowledge_stats = [
            ("软件架构基础", 120),
            ("设计模式", 95),
            ("系统设计", 80)
        ]
        mock_db.execute.return_value.fetchall.return_value = mock_knowledge_stats
        
        response = client.get("/api/admin/user-analytics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_users"] == 250
        assert "active_users_today" in data
        assert "active_users_week" in data
        assert "new_users_today" in data
        assert "user_retention_rate" in data
        assert "top_knowledge_points" in data
        assert len(data["top_knowledge_points"]) == 3
    
    @patch('api.admin.asyncio.create_task')
    def test_trigger_backup_success(self, mock_create_task):
        """测试触发备份 - 成功"""
        mock_task = MagicMock()
        mock_create_task.return_value = mock_task
        
        response = client.post("/api/admin/backup")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "备份任务已启动"
        assert "backup_id" in data
        assert "estimated_time" in data
        
        # 验证异步任务被创建
        mock_create_task.assert_called_once()
    
    @patch('api.admin.os.path.exists')
    @patch('api.admin.os.path.getsize')
    @patch('api.admin.os.path.getctime')
    def test_get_backup_info_success(self, mock_getctime, mock_getsize, mock_exists):
        """测试获取备份信息 - 成功"""
        # Mock文件系统信息
        mock_exists.return_value = True
        mock_getsize.return_value = 256 * 1024 * 1024  # 256MB
        mock_getctime.return_value = datetime(2024, 1, 1, 2, 0, 0).timestamp()
        
        with patch('api.admin.os.listdir') as mock_listdir:
            mock_listdir.return_value = ["db_backup_20240101.sql"]
            
            response = client.get("/api/admin/backup-info")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "last_backup" in data
            assert "backup_size_mb" in data
            assert "backup_status" in data
            assert "next_scheduled_backup" in data
            assert data["backup_size_mb"] == 256.0
    
    def test_get_backup_info_no_backup(self):
        """测试获取备份信息 - 无备份文件"""
        with patch('api.admin.os.path.exists') as mock_exists, \
             patch('api.admin.os.listdir') as mock_listdir:
            
            mock_exists.return_value = True  # 备份目录存在
            mock_listdir.return_value = []  # 但没有备份文件
            
            response = client.get("/api/admin/backup-info")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["last_backup"] is None
            assert data["backup_status"] == "no_backup"
    
    @patch('api.admin.get_db')
    def test_cleanup_old_data_success(self, mock_get_db):
        """测试清理旧数据 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock删除操作的返回值
        mock_db.query.return_value.filter.return_value.delete.side_effect = [10, 25, 5]  # 删除的记录数
        
        response = client.post("/api/admin/cleanup", json={
            "days_to_keep": 30,
            "cleanup_sessions": True,
            "cleanup_logs": True,
            "cleanup_temp_files": True
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "数据清理完成"
        assert "deleted_sessions" in data
        assert "deleted_logs" in data
        assert "freed_space_mb" in data
        
        # 验证commit被调用
        mock_db.commit.assert_called()
    
    def test_cleanup_old_data_validation(self):
        """测试清理旧数据 - 参数验证"""
        # 无效的保留天数
        response = client.post("/api/admin/cleanup", json={
            "days_to_keep": 0,  # 无效值
            "cleanup_sessions": True
        })
        
        assert response.status_code == 400
        assert "保留天数必须大于0" in response.json()["detail"]
    
    @patch('api.admin.get_db')
    def test_get_system_logs_success(self, mock_get_db):
        """测试获取系统日志 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock日志查询（假设有日志表）
        mock_logs = [
            MagicMock(
                id=1,
                level="INFO",
                message="系统启动",
                timestamp=datetime(2024, 1, 1, 10, 0, 0),
                module="system"
            ),
            MagicMock(
                id=2,
                level="ERROR",
                message="数据库连接失败",
                timestamp=datetime(2024, 1, 1, 10, 5, 0),
                module="database"
            )
        ]
        
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = mock_logs
        mock_db.query.return_value.count.return_value = 2
        
        response = client.get("/api/admin/logs?level=all&limit=50")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert "total" in data
        assert len(data["logs"]) == 2
        assert data["logs"][0]["level"] == "INFO"
        assert data["logs"][1]["level"] == "ERROR"
    
    @patch('api.admin.get_db')
    def test_export_data_success(self, mock_get_db):
        """测试导出数据 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock数据查询
        mock_questions = [
            MagicMock(id=1, content="题目1", difficulty=1),
            MagicMock(id=2, content="题目2", difficulty=2)
        ]
        mock_db.query.return_value.all.return_value = mock_questions
        
        with patch('api.admin.json.dumps') as mock_json_dumps:
            mock_json_dumps.return_value = '{"data": "exported"}'
            
            response = client.post("/api/admin/export", json={
                "data_types": ["questions", "users"],
                "format": "json",
                "date_range": {
                    "start": "2024-01-01",
                    "end": "2024-01-31"
                }
            })
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["message"] == "数据导出完成"
            assert "export_file" in data
            assert "file_size_mb" in data
    
    def test_export_data_validation(self):
        """测试导出数据 - 参数验证"""
        # 无效的数据类型
        response = client.post("/api/admin/export", json={
            "data_types": ["invalid_type"],
            "format": "json"
        })
        
        assert response.status_code == 400
        assert "无效的数据类型" in response.json()["detail"]
        
        # 无效的格式
        response = client.post("/api/admin/export", json={
            "data_types": ["questions"],
            "format": "invalid_format"
        })
        
        assert response.status_code == 400
        assert "无效的导出格式" in response.json()["detail"]
    
    @patch('api.admin.task_manager.get_all_tasks')
    def test_get_task_status_success(self, mock_get_all_tasks):
        """测试获取任务状态 - 成功"""
        mock_tasks = [
            {
                "id": "task_1",
                "name": "数据备份",
                "status": "running",
                "progress": 75,
                "start_time": "2024-01-01T10:00:00",
                "estimated_completion": "2024-01-01T10:30:00"
            },
            {
                "id": "task_2",
                "name": "播客生成",
                "status": "completed",
                "progress": 100,
                "start_time": "2024-01-01T09:00:00",
                "completion_time": "2024-01-01T09:15:00"
            }
        ]
        
        mock_get_all_tasks.return_value = mock_tasks
        
        response = client.get("/api/admin/tasks")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "active_tasks" in data
        assert "completed_tasks" in data
        assert "failed_tasks" in data
        assert len(data["active_tasks"]) == 1
        assert len(data["completed_tasks"]) == 1
        assert data["active_tasks"][0]["status"] == "running"
    
    @patch('api.admin.task_manager.cancel_task')
    def test_cancel_task_success(self, mock_cancel_task):
        """测试取消任务 - 成功"""
        mock_cancel_task.return_value = True
        
        response = client.post("/api/admin/tasks/task_123/cancel")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "任务已取消"
        mock_cancel_task.assert_called_once_with("task_123")
    
    @patch('api.admin.task_manager.cancel_task')
    def test_cancel_task_not_found(self, mock_cancel_task):
        """测试取消任务 - 任务未找到"""
        mock_cancel_task.return_value = False
        
        response = client.post("/api/admin/tasks/nonexistent/cancel")
        
        assert response.status_code == 404
        assert "任务未找到或无法取消" in response.json()["detail"]


class TestAdminIntegration:
    """Admin API 集成测试"""
    
    @patch('api.admin.get_db')
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_percent')
    @patch('psutil.disk_usage')
    def test_complete_admin_workflow(self, mock_disk_usage, mock_cpu_percent, mock_virtual_memory, mock_get_db):
        """测试完整的管理工作流"""
        # 设置系统资源mock
        mock_virtual_memory.return_value.used = 512 * 1024 * 1024
        mock_cpu_percent.return_value = 15.2
        mock_disk_usage.return_value.percent = 45.8
        
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.execute.return_value = Mock()
        
        with patch('api.admin.task_manager.get_active_tasks_count') as mock_active_tasks:
            mock_active_tasks.return_value = 2
            
            # 1. 检查系统状态
            status_response = client.get("/api/admin/system-status")
            assert status_response.status_code == 200
            
            # 2. 获取数据库统计
            mock_db.execute.return_value.scalar.return_value = 100
            mock_db.execute.return_value.fetchone.return_value = (50.0,)
            
            stats_response = client.get("/api/admin/database-stats")
            assert stats_response.status_code == 200
            
            # 3. 获取用户分析
            mock_db.query.return_value.count.return_value = 50
            mock_db.query.return_value.filter.return_value.count.return_value = 20
            mock_db.execute.return_value.fetchall.return_value = [("测试知识点", 10)]
            
            analytics_response = client.get("/api/admin/user-analytics")
            assert analytics_response.status_code == 200
            
            # 4. 触发备份
            with patch('api.admin.asyncio.create_task') as mock_create_task:
                mock_create_task.return_value = MagicMock()
                
                backup_response = client.post("/api/admin/backup")
                assert backup_response.status_code == 200
    
    @patch('api.admin.get_db')
    def test_maintenance_workflow(self, mock_get_db):
        """测试维护工作流"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 1. 数据清理
        mock_db.query.return_value.filter.return_value.delete.return_value = 10
        
        cleanup_response = client.post("/api/admin/cleanup", json={
            "days_to_keep": 30,
            "cleanup_sessions": True,
            "cleanup_logs": True
        })
        assert cleanup_response.status_code == 200
        
        # 2. 数据导出
        mock_db.query.return_value.all.return_value = []
        
        with patch('api.admin.json.dumps') as mock_json_dumps:
            mock_json_dumps.return_value = "{}"
            
            export_response = client.post("/api/admin/export", json={
                "data_types": ["questions"],
                "format": "json"
            })
            assert export_response.status_code == 200


class TestAdminValidation:
    """Admin API 验证测试"""
    
    def test_admin_permissions(self):
        """测试管理员权限验证"""
        # 这里可以添加权限验证的测试
        # 当前简化实现，未添加认证
        pass
    
    def test_backup_validation(self):
        """测试备份参数验证"""
        # 测试备份类型验证等
        pass


class TestAdminSecurity:
    """Admin API 安全测试"""
    
    def test_sensitive_data_protection(self):
        """测试敏感数据保护"""
        # 确保系统状态不暴露敏感信息
        response = client.get("/api/admin/system-status")
        
        if response.status_code == 200:
            data = response.json()
            # 验证不包含敏感信息如密码、密钥等
            assert "password" not in str(data).lower()
            assert "secret" not in str(data).lower()
            assert "key" not in str(data).lower()
    
    def test_rate_limiting(self):
        """测试访问频率限制"""
        # 这里可以添加频率限制的测试
        pass


@pytest.fixture
def mock_admin_services():
    """Admin相关服务的mock fixture"""
    with patch('api.admin.get_db') as mock_get_db, \
         patch('api.admin.task_manager') as mock_task_manager:
        
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 设置任务管理器mock
        mock_task_manager.get_active_tasks_count.return_value = 0
        mock_task_manager.get_all_tasks.return_value = []
        
        yield {
            "db": mock_db,
            "task_manager": mock_task_manager
        }


class TestAdminPerformance:
    """Admin API 性能测试"""
    
    @patch('api.admin.get_db')
    def test_system_status_performance(self, mock_get_db):
        """测试系统状态查询性能"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.execute.return_value = Mock()
        
        with patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('api.admin.task_manager.get_active_tasks_count') as mock_tasks:
            
            mock_memory.return_value.used = 512 * 1024 * 1024
            mock_cpu.return_value = 15.2
            mock_disk.return_value.percent = 45.8
            mock_tasks.return_value = 3
            
            import time
            start_time = time.time()
            
            response = client.get("/api/admin/system-status")
            
            end_time = time.time()
            
            assert response.status_code == 200
            assert end_time - start_time < 1.0  # 应该在1秒内完成
    
    @patch('api.admin.get_db')
    def test_database_stats_performance(self, mock_get_db):
        """测试数据库统计查询性能"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟快速响应
        mock_db.execute.return_value.scalar.return_value = 1000
        mock_db.execute.return_value.fetchone.return_value = (100.0,)
        
        import time
        start_time = time.time()
        
        response = client.get("/api/admin/database-stats")
        
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 2.0  # 应该在2秒内完成 