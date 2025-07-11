"""
Analytics Service 单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import json

from services.analytics_service import analytics_service

# 测试数据
MOCK_USER_PERFORMANCE = {
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
        "基础": {"accuracy": 0.95, "time_avg": 30},
        "中级": {"accuracy": 0.75, "time_avg": 50},
        "高级": {"accuracy": 0.60, "time_avg": 70}
    }
}

MOCK_LEARNING_TRENDS = {
    "period": "weekly",
    "data_points": [
        {"date": "2024-01-01", "accuracy": 0.75, "questions": 20, "study_time": 60},
        {"date": "2024-01-02", "accuracy": 0.80, "questions": 25, "study_time": 70},
        {"date": "2024-01-03", "accuracy": 0.85, "questions": 30, "study_time": 80}
    ],
    "trends": {
        "accuracy_trend": "improving",
        "study_time_trend": "increasing",
        "question_count_trend": "stable"
    }
}

MOCK_KNOWLEDGE_GAPS = [
    {
        "knowledge_point": "微服务架构",
        "accuracy": 0.45,
        "question_count": 20,
        "difficulty": "中级",
        "recommended_actions": ["加强基础概念学习", "增加实践练习"]
    },
    {
        "knowledge_point": "性能优化",
        "accuracy": 0.52,
        "question_count": 15,
        "difficulty": "高级",
        "recommended_actions": ["深入学习算法复杂度", "实际案例分析"]
    }
]

MOCK_STUDY_RECOMMENDATIONS = [
    {
        "type": "knowledge_gap",
        "priority": "high",
        "title": "加强微服务架构学习",
        "description": "您在微服务架构方面的掌握度较低（45%），建议重点学习",
        "action_items": [
            "阅读微服务架构基础文档",
            "完成微服务相关练习题",
            "观看微服务设计模式视频"
        ],
        "estimated_time": 120  # 分钟
    },
    {
        "type": "difficulty_challenge",
        "priority": "medium",
        "title": "提升高难度题目解答能力",
        "description": "高难度题目正确率为60%，有提升空间",
        "action_items": [
            "系统复习相关理论知识",
            "增加高难度题目练习时间",
            "寻求专家指导"
        ],
        "estimated_time": 90
    }
]

class TestAnalyticsService:
    """Analytics服务测试类"""
    
    def test_analytics_service_initialization(self):
        """测试Analytics服务初始化"""
        assert analytics_service is not None
        assert hasattr(analytics_service, 'analyze_user_performance')
        assert hasattr(analytics_service, 'get_learning_trends')
        assert hasattr(analytics_service, 'identify_knowledge_gaps')
    
    @patch('services.analytics_service.get_db')
    def test_analyze_user_performance_success(self, mock_get_db):
        """测试分析用户表现 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock练习会话数据
        from models.practice import PracticeSession as PracticeSessionModel, Answer as AnswerModel
        from models.question import Question
        
        mock_sessions = [
            MagicMock(
                id=1,
                start_time=datetime(2024, 1, 1, 10, 0),
                end_time=datetime(2024, 1, 1, 10, 30),
                total_questions=10,
                correct_count=8,
                score=80.0
            ),
            MagicMock(
                id=2,
                start_time=datetime(2024, 1, 2, 14, 0),
                end_time=datetime(2024, 1, 2, 14, 45),
                total_questions=15,
                correct_count=12,
                score=80.0
            )
        ]
        
        # Mock答案数据
        mock_answers = [
            MagicMock(
                question_id=1,
                is_correct=True,
                time_spent=30,
                question=MagicMock(
                    knowledge_points=["软件架构基础"],
                    difficulty=1
                )
            ),
            MagicMock(
                question_id=2,
                is_correct=False,
                time_spent=60,
                question=MagicMock(
                    knowledge_points=["设计模式"],
                    difficulty=2
                )
            )
        ]
        
        # 设置数据库查询mock
        mock_db.query.return_value.filter.return_value.all.return_value = mock_sessions
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = mock_answers
        
        result = analytics_service.analyze_user_performance("test_user")
        
        assert result["user_id"] == "test_user"
        assert "analysis_date" in result
        assert "total_questions" in result
        assert "accuracy_rate" in result
        assert "knowledge_points" in result
        assert "difficulty_analysis" in result
        assert result["total_questions"] > 0
        assert 0 <= result["accuracy_rate"] <= 1
    
    @patch('services.analytics_service.get_db')
    def test_analyze_user_performance_no_data(self, mock_get_db):
        """测试分析用户表现 - 无数据"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock空数据
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = analytics_service.analyze_user_performance("new_user")
        
        assert result["user_id"] == "new_user"
        assert result["total_questions"] == 0
        assert result["accuracy_rate"] == 0.0
        assert result["knowledge_points"] == {}
    
    @patch('services.analytics_service.get_db')
    def test_get_learning_trends_success(self, mock_get_db):
        """测试获取学习趋势 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock每日学习数据
        mock_daily_data = [
            MagicMock(
                date=datetime(2024, 1, 1).date(),
                total_questions=20,
                correct_answers=15,
                study_time=60
            ),
            MagicMock(
                date=datetime(2024, 1, 2).date(),
                total_questions=25,
                correct_answers=22,
                study_time=75
            ),
            MagicMock(
                date=datetime(2024, 1, 3).date(),
                total_questions=30,
                correct_answers=26,
                study_time=90
            )
        ]
        
        # Mock SQL查询结果
        mock_db.execute.return_value.fetchall.return_value = [
            (datetime(2024, 1, 1).date(), 20, 15, 60),
            (datetime(2024, 1, 2).date(), 25, 22, 75),
            (datetime(2024, 1, 3).date(), 30, 26, 90)
        ]
        
        result = analytics_service.get_learning_trends(
            user_id="test_user",
            period="weekly"
        )
        
        assert result["period"] == "weekly"
        assert "data_points" in result
        assert "trends" in result
        assert len(result["data_points"]) == 3
        
        # 验证趋势分析
        assert result["trends"]["accuracy_trend"] in ["improving", "stable", "declining"]
        assert result["trends"]["study_time_trend"] in ["increasing", "stable", "decreasing"]
    
    @patch('services.analytics_service.get_db')
    def test_identify_knowledge_gaps_success(self, mock_get_db):
        """测试识别知识盲点 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock知识点统计数据
        mock_knowledge_stats = [
            ("微服务架构", 20, 9, 2.0),   # 知识点、总题数、正确数、平均难度
            ("性能优化", 15, 8, 2.5),
            ("软件架构基础", 30, 28, 1.0)
        ]
        
        mock_db.execute.return_value.fetchall.return_value = mock_knowledge_stats
        
        result = analytics_service.identify_knowledge_gaps("test_user")
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # 验证知识盲点数据结构
        gap = result[0]
        assert "knowledge_point" in gap
        assert "accuracy" in gap
        assert "question_count" in gap
        assert "difficulty" in gap
        assert "recommended_actions" in gap
        
        # 验证按正确率排序（较低的在前）
        accuracies = [gap["accuracy"] for gap in result]
        assert accuracies == sorted(accuracies)
    
    @patch('services.analytics_service.get_db')
    def test_generate_study_recommendations_success(self, mock_get_db):
        """测试生成学习建议 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        with patch.object(analytics_service, 'analyze_user_performance') as mock_analyze, \
             patch.object(analytics_service, 'identify_knowledge_gaps') as mock_gaps:
            
            # Mock分析结果
            mock_analyze.return_value = MOCK_USER_PERFORMANCE
            mock_gaps.return_value = MOCK_KNOWLEDGE_GAPS
            
            result = analytics_service.generate_study_recommendations("test_user")
            
            assert isinstance(result, list)
            assert len(result) > 0
            
            # 验证建议数据结构
            recommendation = result[0]
            assert "type" in recommendation
            assert "priority" in recommendation
            assert "title" in recommendation
            assert "description" in recommendation
            assert "action_items" in recommendation
            assert "estimated_time" in recommendation
            
            # 验证优先级
            assert recommendation["priority"] in ["low", "medium", "high"]
    
    def test_calculate_knowledge_mastery(self):
        """测试计算知识点掌握度"""
        # 测试正常情况
        correct_count = 8
        total_count = 10
        avg_time = 45
        expected_time = 60
        
        mastery = analytics_service._calculate_knowledge_mastery(
            correct_count, total_count, avg_time, expected_time
        )
        
        assert 0 <= mastery <= 1
        assert mastery > 0.5  # 正确率80%应该有较高掌握度
    
    def test_calculate_knowledge_mastery_edge_cases(self):
        """测试知识点掌握度计算边界情况"""
        # 测试完全正确且时间优秀
        mastery = analytics_service._calculate_knowledge_mastery(10, 10, 30, 60)
        assert mastery > 0.9
        
        # 测试完全错误
        mastery = analytics_service._calculate_knowledge_mastery(0, 10, 60, 60)
        assert mastery < 0.3
        
        # 测试零除法保护
        mastery = analytics_service._calculate_knowledge_mastery(0, 0, 60, 60)
        assert mastery == 0.0
    
    def test_determine_trend_direction(self):
        """测试趋势方向判断"""
        # 测试上升趋势
        values = [0.6, 0.7, 0.8, 0.85, 0.9]
        trend = analytics_service._determine_trend_direction(values)
        assert trend == "improving"
        
        # 测试下降趋势
        values = [0.9, 0.85, 0.8, 0.7, 0.6]
        trend = analytics_service._determine_trend_direction(values)
        assert trend == "declining"
        
        # 测试稳定趋势
        values = [0.8, 0.82, 0.79, 0.81, 0.8]
        trend = analytics_service._determine_trend_direction(values)
        assert trend == "stable"
        
        # 测试空数据
        trend = analytics_service._determine_trend_direction([])
        assert trend == "stable"
    
    @patch('services.analytics_service.get_db')
    def test_get_comparative_analysis_success(self, mock_get_db):
        """测试获取对比分析 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock用户群体统计数据
        mock_db.execute.return_value.fetchone.side_effect = [
            (0.75, 50.0, 45.0),  # 平均正确率、平均学习时间、平均答题时间
            (0.80, 60.0, 40.0)   # 目标用户数据
        ]
        
        with patch.object(analytics_service, 'analyze_user_performance') as mock_analyze:
            mock_analyze.return_value = MOCK_USER_PERFORMANCE
            
            result = analytics_service.get_comparative_analysis("test_user")
            
            assert "user_performance" in result
            assert "peer_comparison" in result
            assert "ranking" in result
            
            # 验证对比数据
            comparison = result["peer_comparison"]
            assert "accuracy_vs_average" in comparison
            assert "study_time_vs_average" in comparison
            assert "question_speed_vs_average" in comparison
    
    @patch('services.analytics_service.get_db')
    def test_generate_progress_report_success(self, mock_get_db):
        """测试生成进度报告 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        with patch.object(analytics_service, 'analyze_user_performance') as mock_analyze, \
             patch.object(analytics_service, 'get_learning_trends') as mock_trends, \
             patch.object(analytics_service, 'identify_knowledge_gaps') as mock_gaps:
            
            mock_analyze.return_value = MOCK_USER_PERFORMANCE
            mock_trends.return_value = MOCK_LEARNING_TRENDS
            mock_gaps.return_value = MOCK_KNOWLEDGE_GAPS
            
            result = analytics_service.generate_progress_report(
                user_id="test_user",
                period="monthly"
            )
            
            assert "report_period" in result
            assert "performance_summary" in result
            assert "learning_trends" in result
            assert "knowledge_gaps" in result
            assert "achievements" in result
            assert "recommendations" in result
            
            # 验证报告完整性
            assert result["report_period"] == "monthly"
            assert len(result["achievements"]) > 0
            assert len(result["recommendations"]) > 0


class TestAnalyticsServiceAdvanced:
    """Analytics服务高级功能测试"""
    
    @patch('services.analytics_service.get_db')
    def test_predict_learning_outcomes_success(self, mock_get_db):
        """测试预测学习成果 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock历史学习数据
        historical_data = [
            {"date": "2024-01-01", "accuracy": 0.7, "study_time": 60},
            {"date": "2024-01-02", "accuracy": 0.75, "study_time": 70},
            {"date": "2024-01-03", "accuracy": 0.8, "study_time": 80}
        ]
        
        with patch.object(analytics_service, 'get_learning_trends') as mock_trends:
            mock_trends.return_value = {
                "data_points": historical_data,
                "trends": {"accuracy_trend": "improving"}
            }
            
            result = analytics_service.predict_learning_outcomes(
                user_id="test_user",
                prediction_days=7
            )
            
            assert "predicted_accuracy" in result
            assert "predicted_mastery_improvements" in result
            assert "estimated_completion_times" in result
            assert "confidence_interval" in result
            
            # 验证预测合理性
            assert 0 <= result["predicted_accuracy"] <= 1
            assert result["confidence_interval"] > 0
    
    @patch('services.analytics_service.get_db')
    def test_analyze_study_patterns_success(self, mock_get_db):
        """测试分析学习模式 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock学习时间数据
        mock_study_times = [
            (datetime(2024, 1, 1, 9, 0), 60),   # 上午9点，60分钟
            (datetime(2024, 1, 1, 14, 0), 45),  # 下午2点，45分钟
            (datetime(2024, 1, 2, 10, 0), 90),  # 上午10点，90分钟
            (datetime(2024, 1, 3, 15, 0), 30),  # 下午3点，30分钟
        ]
        
        mock_db.execute.return_value.fetchall.return_value = mock_study_times
        
        result = analytics_service.analyze_study_patterns("test_user")
        
        assert "optimal_study_times" in result
        assert "study_duration_patterns" in result
        assert "weekly_patterns" in result
        assert "productivity_analysis" in result
        
        # 验证时间模式分析
        optimal_times = result["optimal_study_times"]
        assert len(optimal_times) > 0
        assert all("hour" in time_slot for time_slot in optimal_times)
        assert all("performance_score" in time_slot for time_slot in optimal_times)
    
    @patch('services.analytics_service.get_db')
    def test_calculate_learning_efficiency_success(self, mock_get_db):
        """测试计算学习效率 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock效率计算数据
        mock_db.execute.return_value.fetchone.return_value = (
            100,  # 总题目数
            80,   # 正确题目数
            3600, # 总学习时间（秒）
            10    # 学习会话数
        )
        
        result = analytics_service.calculate_learning_efficiency("test_user")
        
        assert "questions_per_hour" in result
        assert "accuracy_per_minute" in result
        assert "efficiency_score" in result
        assert "improvement_suggestions" in result
        
        # 验证效率指标合理性
        assert result["questions_per_hour"] > 0
        assert result["efficiency_score"] > 0
        assert isinstance(result["improvement_suggestions"], list)
    
    def test_adaptive_difficulty_recommendation(self):
        """测试自适应难度推荐"""
        # 高正确率用户
        high_performer = {
            "accuracy_rate": 0.95,
            "average_time_per_question": 30,
            "difficulty_analysis": {
                "基础": {"accuracy": 0.98},
                "中级": {"accuracy": 0.95},
                "高级": {"accuracy": 0.90}
            }
        }
        
        recommendation = analytics_service._recommend_adaptive_difficulty(high_performer)
        assert recommendation["recommended_difficulty"] == "高级"
        assert recommendation["confidence"] > 0.8
        
        # 低正确率用户
        low_performer = {
            "accuracy_rate": 0.45,
            "average_time_per_question": 90,
            "difficulty_analysis": {
                "基础": {"accuracy": 0.60},
                "中级": {"accuracy": 0.40},
                "高级": {"accuracy": 0.30}
            }
        }
        
        recommendation = analytics_service._recommend_adaptive_difficulty(low_performer)
        assert recommendation["recommended_difficulty"] == "基础"
        assert "建议" in recommendation["suggestion"]


class TestAnalyticsServiceIntegration:
    """Analytics服务集成测试"""
    
    @patch('services.analytics_service.get_db')
    def test_complete_analytics_workflow(self, mock_get_db):
        """测试完整的分析工作流"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 设置综合mock数据
        mock_sessions = [MagicMock(total_questions=10, correct_count=8)]
        mock_answers = [MagicMock(is_correct=True, time_spent=30)]
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_sessions
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = mock_answers
        mock_db.execute.return_value.fetchall.return_value = [
            (datetime(2024, 1, 1).date(), 10, 8, 60)
        ]
        mock_db.execute.return_value.fetchone.return_value = (10, 8, 600, 1)
        
        # 1. 分析用户表现
        performance = analytics_service.analyze_user_performance("test_user")
        assert performance["accuracy_rate"] > 0
        
        # 2. 获取学习趋势
        trends = analytics_service.get_learning_trends("test_user", "weekly")
        assert "data_points" in trends
        
        # 3. 识别知识盲点
        gaps = analytics_service.identify_knowledge_gaps("test_user")
        assert isinstance(gaps, list)
        
        # 4. 生成学习建议
        recommendations = analytics_service.generate_study_recommendations("test_user")
        assert isinstance(recommendations, list)
        
        # 5. 生成完整报告
        report = analytics_service.generate_progress_report("test_user", "monthly")
        assert "performance_summary" in report
        assert "recommendations" in report


class TestAnalyticsServiceValidation:
    """Analytics服务验证测试"""
    
    def test_date_range_validation(self):
        """测试日期范围验证"""
        # 测试有效日期范围
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        is_valid = analytics_service._validate_date_range(start_date, end_date)
        assert is_valid is True
        
        # 测试无效日期范围（结束日期早于开始日期）
        start_date = datetime(2024, 1, 31)
        end_date = datetime(2024, 1, 1)
        
        is_valid = analytics_service._validate_date_range(start_date, end_date)
        assert is_valid is False
        
        # 测试过长的日期范围
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2025, 1, 1)  # 超过1年
        
        is_valid = analytics_service._validate_date_range(start_date, end_date, max_days=365)
        assert is_valid is False
    
    def test_user_data_validation(self):
        """测试用户数据验证"""
        # 测试有效用户数据
        valid_data = {
            "total_questions": 100,
            "correct_answers": 80,
            "study_time": 3600
        }
        
        is_valid = analytics_service._validate_user_data(valid_data)
        assert is_valid is True
        
        # 测试无效用户数据
        invalid_data = {
            "total_questions": -10,  # 负数
            "correct_answers": 150,  # 超过总题数
            "study_time": -100       # 负数
        }
        
        is_valid = analytics_service._validate_user_data(invalid_data)
        assert is_valid is False
    
    def test_performance_metrics_bounds(self):
        """测试性能指标边界"""
        # 测试正确率边界
        assert analytics_service._normalize_accuracy_rate(1.5) == 1.0
        assert analytics_service._normalize_accuracy_rate(-0.1) == 0.0
        assert analytics_service._normalize_accuracy_rate(0.75) == 0.75
        
        # 测试时间指标边界
        assert analytics_service._normalize_time_metric(0) == 0
        assert analytics_service._normalize_time_metric(-100) == 0
        assert analytics_service._normalize_time_metric(3600) == 3600


class TestAnalyticsServicePerformance:
    """Analytics服务性能测试"""
    
    @patch('services.analytics_service.get_db')
    def test_large_dataset_analysis_performance(self, mock_get_db):
        """测试大数据集分析性能"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟大量数据
        large_sessions = [MagicMock(total_questions=10, correct_count=8) for _ in range(1000)]
        large_answers = [MagicMock(is_correct=True, time_spent=30) for _ in range(10000)]
        
        mock_db.query.return_value.filter.return_value.all.return_value = large_sessions
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = large_answers
        
        import time
        start_time = time.time()
        
        result = analytics_service.analyze_user_performance("test_user")
        
        end_time = time.time()
        
        assert result["accuracy_rate"] > 0
        assert end_time - start_time < 3.0  # 应该在3秒内完成
    
    @patch('services.analytics_service.get_db')
    def test_concurrent_analysis_performance(self, mock_get_db):
        """测试并发分析性能"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_sessions = [MagicMock(total_questions=10, correct_count=8)]
        mock_answers = [MagicMock(is_correct=True, time_spent=30)]
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_sessions
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = mock_answers
        
        import concurrent.futures
        import time
        
        def analyze_user(user_id):
            return analytics_service.analyze_user_performance(f"user_{user_id}")
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(analyze_user, i) for i in range(10)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        
        assert len(results) == 10
        assert all(result["accuracy_rate"] >= 0 for result in results)
        assert end_time - start_time < 5.0  # 并发执行应该比串行快


@pytest.fixture
def mock_analytics_dependencies():
    """Analytics服务依赖的mock fixture"""
    with patch('services.analytics_service.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 设置常用的mock返回值
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.execute.return_value.fetchall.return_value = []
        mock_db.execute.return_value.fetchone.return_value = (0, 0, 0, 0)
        
        yield mock_db


class TestAnalyticsServiceEdgeCases:
    """Analytics服务边界情况测试"""
    
    @patch('services.analytics_service.get_db')
    def test_user_with_no_practice_history(self, mock_get_db):
        """测试无练习历史的用户"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock无数据
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = analytics_service.analyze_user_performance("new_user")
        
        assert result["total_questions"] == 0
        assert result["accuracy_rate"] == 0.0
        assert result["knowledge_points"] == {}
        assert result["study_sessions"] == 0
    
    @patch('services.analytics_service.get_db')
    def test_user_with_extreme_performance(self, mock_get_db):
        """测试极端表现的用户"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock完美表现数据
        perfect_sessions = [MagicMock(total_questions=10, correct_count=10, score=100.0)]
        perfect_answers = [MagicMock(is_correct=True, time_spent=10) for _ in range(10)]
        
        mock_db.query.return_value.filter.return_value.all.return_value = perfect_sessions
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = perfect_answers
        
        result = analytics_service.analyze_user_performance("perfect_user")
        
        assert result["accuracy_rate"] == 1.0
        assert result["average_time_per_question"] <= 10
    
    def test_malformed_data_handling(self):
        """测试异常数据处理"""
        # 测试除零保护
        result = analytics_service._calculate_knowledge_mastery(0, 0, 0, 0)
        assert result == 0.0
        
        # 测试负数处理
        result = analytics_service._normalize_accuracy_rate(-0.5)
        assert result == 0.0
        
        # 测试超出范围数据
        result = analytics_service._normalize_accuracy_rate(1.5)
        assert result == 1.0 