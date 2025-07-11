"""
Analytics API 单元测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

from main import app
from services.analytics_service import analytics_service

client = TestClient(app)

# 测试数据
MOCK_PERFORMANCE_DATA = {
    "user_id": "test_user",
    "analysis_date": "2024-01-01T00:00:00",
    "total_questions": 100,
    "correct_answers": 80,
    "accuracy_rate": 0.8,
    "average_time_per_question": 45,
    "study_sessions": 10,
    "total_study_time": 600,
    "knowledge_points": {
        "软件架构基础": {"mastery": 0.85, "questions": 30},
        "设计模式": {"mastery": 0.92, "questions": 25},
        "系统架构": {"mastery": 0.65, "questions": 40}
    },
    "difficulty_analysis": {
        "基础": {"accuracy": 0.95, "count": 40},
        "中级": {"accuracy": 0.78, "count": 45},
        "高级": {"accuracy": 0.45, "count": 15}
    }
}

MOCK_WEAK_POINTS = [
    {
        "topic": "系统架构",
        "mastery": 0.65,
        "questions_count": 40,
        "priority": "中",
        "recommendation": "需要加强：加强系统设计和架构模式的理解"
    }
]

MOCK_PROGRESS_DATA = {
    "user_id": "test_user",
    "tracking_period": "7天",
    "daily_stats": [
        {
            "date": "2024-01-01",
            "questions_answered": 10,
            "accuracy": 0.8,
            "study_time": 45,
            "sessions": 1
        }
    ],
    "trends": {
        "accuracy_trend": "上升",
        "speed_trend": "稳定",
        "consistency": 0.85
    },
    "achievements": [
        {"date": "2024-01-01", "type": "连续练习7天"}
    ]
}

class TestAnalyticsAPI:
    """Analytics API 测试类"""
    
    @patch.object(analytics_service, 'analyze_user_performance')
    @patch.object(analytics_service, 'identify_weak_points')
    def test_get_learning_stats_success(self, mock_weak_points, mock_performance):
        """测试获取学习统计数据 - 成功"""
        # 设置mock返回值
        mock_performance.return_value = MOCK_PERFORMANCE_DATA
        mock_weak_points.return_value = MOCK_WEAK_POINTS
        
        response = client.get("/api/analytics/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应结构
        assert "total_questions" in data
        assert "correct_rate" in data
        assert "weak_points" in data
        assert "strong_points" in data
        assert "study_time_hours" in data
        assert "difficulty_breakdown" in data
        
        # 验证具体数值
        assert data["total_questions"] == 100
        assert data["correct_rate"] == 0.8
        assert "系统架构" in data["weak_points"]
        assert "设计模式" in data["strong_points"]  # mastery > 0.8
        assert data["study_time_hours"] == 10.0  # 600分钟转换为小时
        
        # 验证调用
        mock_performance.assert_called_once_with("default")
        mock_weak_points.assert_called_once_with("default")
    
    @patch.object(analytics_service, 'analyze_user_performance')
    def test_get_learning_stats_no_data(self, mock_performance):
        """测试获取学习统计数据 - 无数据"""
        mock_performance.return_value = {}
        
        response = client.get("/api/analytics/stats")
        
        assert response.status_code == 404
        assert "用户学习数据未找到" in response.json()["detail"]
    
    @patch.object(analytics_service, 'track_learning_progress')
    @patch.object(analytics_service, 'analyze_user_performance')
    @patch.object(analytics_service, 'generate_study_plan')
    def test_get_progress_report_success(self, mock_study_plan, mock_performance, mock_progress):
        """测试获取进度报告 - 成功"""
        mock_progress.return_value = MOCK_PROGRESS_DATA
        mock_performance.return_value = MOCK_PERFORMANCE_DATA
        mock_study_plan.return_value = {
            "recommendations": ["建议1", "建议2"]
        }
        
        response = client.get("/api/analytics/progress?period=weekly")
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应结构
        assert data["period"] == "weekly"
        assert "knowledge_points" in data
        assert "difficulty_progress" in data
        assert "recommendations" in data
        assert "trends" in data
        assert "daily_stats" in data
        
        # 验证数据内容
        assert "软件架构基础" in data["knowledge_points"]
        assert data["knowledge_points"]["软件架构基础"] == 0.85
        assert len(data["recommendations"]) == 2
        
        # 验证调用参数
        mock_progress.assert_called_once_with("default", 7)  # weekly = 7 days
    
    def test_get_progress_report_invalid_period(self):
        """测试进度报告 - 无效周期参数"""
        with patch.object(analytics_service, 'track_learning_progress') as mock_progress:
            mock_progress.return_value = MOCK_PROGRESS_DATA
            
            response = client.get("/api/analytics/progress?period=invalid")
            
            # 应该使用默认值
            assert response.status_code == 200
            mock_progress.assert_called_once_with("default", 7)  # 默认weekly
    
    @patch.object(analytics_service, 'identify_weak_points')
    def test_get_weak_points_success(self, mock_weak_points):
        """测试获取薄弱点 - 成功"""
        mock_weak_points.return_value = MOCK_WEAK_POINTS
        
        response = client.get("/api/analytics/weak-points")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        weak_point = data[0]
        assert weak_point["topic"] == "系统架构"
        assert weak_point["mastery"] == 0.65
        assert weak_point["priority"] == "中"
        assert "recommendation" in weak_point
    
    @patch.object(analytics_service, 'generate_study_plan')
    @patch.object(analytics_service, 'identify_weak_points')
    def test_get_study_recommendations_success(self, mock_weak_points, mock_study_plan):
        """测试获取学习建议 - 成功"""
        mock_weak_points.return_value = MOCK_WEAK_POINTS
        mock_study_plan.return_value = {
            "current_level": "良好",
            "daily_goals": {
                "study_time_minutes": 45,
                "questions_count": 10,
                "focus_topics": ["系统架构"]
            },
            "recommendations": ["建议1", "建议2"]
        }
        
        response = client.get("/api/analytics/recommendations")
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应结构
        assert "next_topics" in data
        assert "suggested_difficulty" in data
        assert "estimated_study_time" in data
        assert "current_level" in data
        assert "daily_questions_target" in data
        assert "recommendations" in data
        
        # 验证数据内容
        assert "系统架构" in data["next_topics"]
        assert data["suggested_difficulty"] == "中级"  # 良好对应中级
        assert data["estimated_study_time"] == 45
        assert data["current_level"] == "良好"
    
    @patch('services.task_manager.task_manager.submit_task')
    def test_trigger_analysis_success(self, mock_submit_task):
        """测试触发分析 - 成功"""
        mock_submit_task.return_value = "task_123"
        
        response = client.post("/api/analytics/analyze")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "分析任务已启动"
        assert data["task_id"] == "task_123"
        assert "estimated_time" in data
        assert "status_endpoint" in data
        
        mock_submit_task.assert_called_once()
    
    @patch.object(analytics_service, 'analyze_user_performance')
    @patch.object(analytics_service, 'track_learning_progress')
    def test_get_learning_summary_success(self, mock_progress, mock_performance):
        """测试获取学习总结 - 成功"""
        mock_performance.return_value = MOCK_PERFORMANCE_DATA
        mock_progress.return_value = MOCK_PROGRESS_DATA
        
        response = client.get("/api/analytics/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应结构
        assert "user_id" in data
        assert "summary_date" in data
        assert "overall_progress" in data
        assert "recent_trends" in data
        assert "achievements" in data
        assert "consistency_score" in data
        assert "next_milestone" in data
        
        # 验证数据内容
        overall_progress = data["overall_progress"]
        assert overall_progress["accuracy_rate"] == 0.8
        assert overall_progress["total_questions"] == 100
        assert overall_progress["study_sessions"] == 10
    
    def test_analytics_error_handling(self):
        """测试分析服务错误处理"""
        with patch.object(analytics_service, 'analyze_user_performance') as mock_performance:
            mock_performance.side_effect = Exception("数据库连接失败")
            
            response = client.get("/api/analytics/stats")
            
            assert response.status_code == 500
            assert "获取学习统计失败" in response.json()["detail"]
    
    def test_analytics_endpoints_authentication(self):
        """测试分析接口的认证（如果需要）"""
        # 这里可以测试需要认证的端点
        # 目前使用简化的用户ID获取方式
        pass


class TestAnalyticsIntegration:
    """Analytics API 集成测试"""
    
    def test_analytics_workflow(self):
        """测试完整的分析工作流"""
        with patch.object(analytics_service, 'analyze_user_performance') as mock_performance, \
             patch.object(analytics_service, 'identify_weak_points') as mock_weak_points, \
             patch.object(analytics_service, 'generate_study_plan') as mock_study_plan:
            
            # 设置mock数据
            mock_performance.return_value = MOCK_PERFORMANCE_DATA
            mock_weak_points.return_value = MOCK_WEAK_POINTS
            mock_study_plan.return_value = {
                "recommendations": ["建议1"],
                "current_level": "良好"
            }
            
            # 1. 获取学习统计
            stats_response = client.get("/api/analytics/stats")
            assert stats_response.status_code == 200
            
            # 2. 获取薄弱点
            weak_points_response = client.get("/api/analytics/weak-points")
            assert weak_points_response.status_code == 200
            
            # 3. 获取学习建议
            recommendations_response = client.get("/api/analytics/recommendations")
            assert recommendations_response.status_code == 200
            
            # 验证数据一致性
            stats_data = stats_response.json()
            weak_points_data = weak_points_response.json()
            recommendations_data = recommendations_response.json()
            
            # 薄弱点应该在统计和建议中体现
            assert "系统架构" in stats_data["weak_points"]
            assert weak_points_data[0]["topic"] == "系统架构"
            assert "系统架构" in recommendations_data["next_topics"]


@pytest.fixture
def mock_analytics_service():
    """Analytics服务的mock fixture"""
    with patch('api.analytics.analytics_service') as mock:
        mock.analyze_user_performance.return_value = MOCK_PERFORMANCE_DATA
        mock.identify_weak_points.return_value = MOCK_WEAK_POINTS
        mock.track_learning_progress.return_value = MOCK_PROGRESS_DATA
        mock.generate_study_plan.return_value = {
            "recommendations": ["建议1", "建议2"],
            "current_level": "良好"
        }
        yield mock


class TestAnalyticsPerformance:
    """Analytics API 性能测试"""
    
    def test_concurrent_requests(self, mock_analytics_service):
        """测试并发请求处理"""
        import concurrent.futures
        import time
        
        def make_request():
            return client.get("/api/analytics/stats")
        
        start_time = time.time()
        
        # 并发发送10个请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        end_time = time.time()
        
        # 验证所有请求都成功
        for response in responses:
            assert response.status_code == 200
        
        # 验证响应时间合理（应该小于5秒）
        assert end_time - start_time < 5.0
    
    def test_large_data_handling(self):
        """测试大数据量处理"""
        # 模拟大量数据
        large_performance_data = MOCK_PERFORMANCE_DATA.copy()
        large_performance_data["knowledge_points"] = {
            f"知识点{i}": {"mastery": 0.5 + (i % 50) / 100, "questions": 10 + (i % 20)}
            for i in range(100)  # 100个知识点
        }
        
        with patch.object(analytics_service, 'analyze_user_performance') as mock_performance:
            mock_performance.return_value = large_performance_data
            
            response = client.get("/api/analytics/stats")
            
            assert response.status_code == 200
            data = response.json()
            
            # 验证能正确处理大量数据
            assert len(data["difficulty_breakdown"]) > 0
            assert data["total_questions"] == 100 