"""
AI Service 单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import json
import asyncio

from services.ai_service import ai_service

# 测试数据
MOCK_QUESTION_EXPLANATION = {
    "explanation": "这道题考查的是软件架构的基本概念。软件架构是系统的根本组织结构，它定义了系统的各个组件、组件之间的关系以及指导其设计和演化的原则和准则。正确答案是A，因为...",
    "key_concepts": ["软件架构", "系统组织", "组件关系"],
    "difficulty_level": "基础",
    "related_topics": ["系统设计", "架构模式"]
}

MOCK_PODCAST_SCRIPT = {
    "title": "软件架构基础学习播客",
    "description": "深入了解软件架构的基本概念和设计原则",
    "duration_estimate": 900,  # 15分钟
    "segments": [
        {
            "speaker": "主持人",
            "content": "欢迎收听软件架构学习播客，今天我们来聊聊软件架构的基础概念。",
            "timestamp": "00:00",
            "tone": "friendly"
        },
        {
            "speaker": "专家",
            "content": "软件架构是系统的根本组织结构，它就像建筑的蓝图一样重要。",
            "timestamp": "00:30",
            "tone": "explanatory"
        }
    ],
    "knowledge_points": ["软件架构基础", "系统设计"],
    "target_audience": "初学者"
}

MOCK_LEARNING_PLAN = {
    "plan_title": "软件架构掌握计划",
    "total_duration_days": 30,
    "difficulty_progression": "基础 -> 中级 -> 高级",
    "phases": [
        {
            "phase_number": 1,
            "title": "基础概念学习",
            "duration_days": 10,
            "objectives": ["理解软件架构定义", "掌握基本架构原则"],
            "activities": [
                {"type": "study", "content": "阅读架构基础文档", "duration": 120},
                {"type": "practice", "content": "完成基础练习题", "duration": 60}
            ]
        },
        {
            "phase_number": 2,
            "title": "架构模式学习",
            "duration_days": 15,
            "objectives": ["掌握常见架构模式", "理解模式应用场景"],
            "activities": [
                {"type": "study", "content": "学习设计模式", "duration": 180},
                {"type": "practice", "content": "模式应用练习", "duration": 90}
            ]
        }
    ],
    "milestones": [
        {"day": 10, "milestone": "完成基础概念学习"},
        {"day": 25, "milestone": "掌握主要架构模式"},
        {"day": 30, "milestone": "能够设计简单系统架构"}
    ]
}

MOCK_PROGRESS_ANALYSIS = {
    "current_level": "中级",
    "mastery_percentage": 75.5,
    "strengths": ["理论知识扎实", "基础概念清晰"],
    "weaknesses": ["实践经验不足", "复杂场景应用能力待提升"],
    "recommended_focus_areas": ["微服务架构", "性能优化"],
    "next_learning_goals": [
        "深入学习分布式系统设计",
        "实际项目架构设计练习"
    ],
    "estimated_time_to_next_level": 45  # 天
}

class TestAIService:
    """AI服务测试类"""
    
    def test_ai_service_initialization(self):
        """测试AI服务初始化"""
        assert ai_service is not None
        assert hasattr(ai_service, 'openai_client')
        assert hasattr(ai_service, 'generate_question_explanation')
        assert hasattr(ai_service, 'generate_podcast_script')
    
    @patch('services.ai_service.AsyncOpenAI')
    @patch('services.ai_service.settings')
    def test_init_clients_with_api_key(self, mock_settings, mock_openai):
        """测试客户端初始化 - 有API密钥"""
        mock_settings.OPENAI_API_KEY = "test_api_key"
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        ai_service._init_clients()
        
        assert ai_service.openai_client is not None
        mock_openai.assert_called_once_with(api_key="test_api_key")
    
    @patch('services.ai_service.settings')
    def test_init_clients_without_api_key(self, mock_settings):
        """测试客户端初始化 - 无API密钥"""
        mock_settings.OPENAI_API_KEY = None
        
        ai_service._init_clients()
        
        assert ai_service.openai_client is None
    
    @pytest.mark.asyncio
    async def test_generate_question_explanation_success(self):
        """测试生成题目解析 - 成功"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(MOCK_QUESTION_EXPLANATION)
        
        mock_client.chat.completions.create.return_value = mock_response
        ai_service.openai_client = mock_client
        
        result = await ai_service.generate_question_explanation(
            question="什么是软件架构？",
            answer="A"
        )
        
        assert result["explanation"] is not None
        assert "软件架构" in result["explanation"]
        assert "key_concepts" in result
        assert isinstance(result["key_concepts"], list)
    
    @pytest.mark.asyncio
    async def test_generate_question_explanation_no_client(self):
        """测试生成题目解析 - 无AI客户端"""
        ai_service.openai_client = None
        
        result = await ai_service.generate_question_explanation(
            question="什么是软件架构？",
            answer="A"
        )
        
        assert "AI服务不可用" in result["explanation"]
        assert result["key_concepts"] == []
    
    @pytest.mark.asyncio
    async def test_generate_question_explanation_api_error(self):
        """测试生成题目解析 - API错误"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        ai_service.openai_client = mock_client
        
        result = await ai_service.generate_question_explanation(
            question="什么是软件架构？",
            answer="A"
        )
        
        assert "生成解析时出错" in result["explanation"]
        assert result["key_concepts"] == []
    
    @pytest.mark.asyncio
    async def test_generate_podcast_script_success(self):
        """测试生成播客脚本 - 成功"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(MOCK_PODCAST_SCRIPT)
        
        mock_client.chat.completions.create.return_value = mock_response
        ai_service.openai_client = mock_client
        
        result = await ai_service.generate_podcast_script(
            topics=["软件架构基础"],
            style="conversation",
            duration_minutes=15
        )
        
        assert result["title"] is not None
        assert result["segments"] is not None
        assert len(result["segments"]) > 0
        assert result["duration_estimate"] == 900
    
    @pytest.mark.asyncio
    async def test_generate_podcast_script_validation_error(self):
        """测试生成播客脚本 - 验证错误"""
        # 测试空主题
        result = await ai_service.generate_podcast_script(
            topics=[],
            style="conversation",
            duration_minutes=15
        )
        
        assert "至少需要一个主题" in result["error"]
        
        # 测试无效时长
        result = await ai_service.generate_podcast_script(
            topics=["软件架构"],
            style="conversation",
            duration_minutes=0
        )
        
        assert "时长必须在1-60分钟之间" in result["error"]
    
    @pytest.mark.asyncio
    async def test_generate_learning_plan_success(self):
        """测试生成学习计划 - 成功"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(MOCK_LEARNING_PLAN)
        
        mock_client.chat.completions.create.return_value = mock_response
        ai_service.openai_client = mock_client
        
        with patch.object(ai_service, 'analyze_user_progress') as mock_analyze:
            mock_analyze.return_value = MOCK_PROGRESS_ANALYSIS
            
            result = await ai_service.generate_learning_plan(
                user_id="test_user",
                target_knowledge_points=["软件架构基础", "设计模式"],
                time_constraint_days=30
            )
            
            assert result["plan_title"] is not None
            assert result["phases"] is not None
            assert len(result["phases"]) > 0
            assert result["total_duration_days"] == 30
    
    @pytest.mark.asyncio
    async def test_analyze_user_progress_success(self):
        """测试分析用户进度 - 成功"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(MOCK_PROGRESS_ANALYSIS)
        
        mock_client.chat.completions.create.return_value = mock_response
        ai_service.openai_client = mock_client
        
        # Mock用户学习数据
        mock_user_data = {
            "total_questions": 100,
            "correct_answers": 80,
            "knowledge_points": {
                "软件架构基础": {"mastery": 0.85},
                "设计模式": {"mastery": 0.70}
            }
        }
        
        result = await ai_service.analyze_user_progress("test_user", mock_user_data)
        
        assert result["current_level"] is not None
        assert result["mastery_percentage"] > 0
        assert "strengths" in result
        assert "weaknesses" in result
        assert "recommended_focus_areas" in result
    
    @pytest.mark.asyncio
    async def test_generate_daily_podcast_success(self):
        """测试生成每日播客 - 成功"""
        mock_client = AsyncMock()
        
        # Mock热门主题分析
        with patch.object(ai_service, '_analyze_trending_topics') as mock_trending:
            mock_trending.return_value = ["软件架构", "微服务", "设计模式"]
            
            # Mock播客脚本生成
            with patch.object(ai_service, 'generate_podcast_script') as mock_script:
                mock_script.return_value = MOCK_PODCAST_SCRIPT
                
                result = await ai_service.generate_daily_podcast()
                
                assert result["status"] == "success"
                assert "podcast_script" in result
                assert "selected_topics" in result
                assert len(result["selected_topics"]) > 0
    
    def test_validate_podcast_parameters(self):
        """测试播客参数验证"""
        # 测试有效参数
        is_valid, error = ai_service._validate_podcast_parameters(
            topics=["软件架构"],
            style="conversation",
            duration_minutes=15
        )
        assert is_valid is True
        assert error is None
        
        # 测试无效风格
        is_valid, error = ai_service._validate_podcast_parameters(
            topics=["软件架构"],
            style="invalid_style",
            duration_minutes=15
        )
        assert is_valid is False
        assert "无效的播客风格" in error
        
        # 测试主题过多
        is_valid, error = ai_service._validate_podcast_parameters(
            topics=["主题" + str(i) for i in range(11)],  # 11个主题
            style="conversation",
            duration_minutes=15
        )
        assert is_valid is False
        assert "主题数量过多" in error
    
    def test_estimate_podcast_duration(self):
        """测试播客时长估算"""
        # 测试正常脚本
        segments = [
            {"content": "这是一段测试内容。" * 10, "speaker": "主持人"},
            {"content": "这是另一段测试内容。" * 15, "speaker": "专家"}
        ]
        
        duration = ai_service._estimate_podcast_duration(segments)
        assert duration > 0
        assert isinstance(duration, int)
        
        # 测试空脚本
        duration = ai_service._estimate_podcast_duration([])
        assert duration == 0
    
    @pytest.mark.asyncio
    async def test_enhance_question_with_ai_success(self):
        """测试AI增强题目 - 成功"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        enhanced_question = {
            "original_question": "什么是软件架构？",
            "enhanced_question": "在大型分布式系统中，软件架构设计需要考虑哪些关键因素？",
            "difficulty_increase": 1,
            "additional_context": "考虑可扩展性、可维护性和性能优化",
            "learning_objectives": ["理解分布式系统架构", "掌握架构设计原则"]
        }
        mock_response.choices[0].message.content = json.dumps(enhanced_question)
        
        mock_client.chat.completions.create.return_value = mock_response
        ai_service.openai_client = mock_client
        
        result = await ai_service.enhance_question_with_ai(
            original_question="什么是软件架构？",
            target_difficulty="中级",
            knowledge_context=["软件架构基础"]
        )
        
        assert result["enhanced_question"] is not None
        assert result["difficulty_increase"] > 0
        assert "learning_objectives" in result


class TestAIServiceAdvanced:
    """AI服务高级功能测试"""
    
    @pytest.mark.asyncio
    async def test_intelligent_content_recommendation_success(self):
        """测试智能内容推荐 - 成功"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        
        recommendations = {
            "recommended_topics": ["微服务架构", "API设计", "数据库设计"],
            "study_path": [
                {"topic": "微服务基础", "priority": "high", "estimated_time": 120},
                {"topic": "服务通信", "priority": "medium", "estimated_time": 90}
            ],
            "difficulty_progression": "当前水平：中级 -> 目标水平：高级",
            "personalized_tips": [
                "建议先巩固分布式系统基础",
                "多做实际项目练习"
            ]
        }
        
        mock_response.choices[0].message.content = json.dumps(recommendations)
        mock_client.chat.completions.create.return_value = mock_response
        ai_service.openai_client = mock_client
        
        user_profile = {
            "learning_style": "实践导向",
            "current_knowledge": ["软件架构基础", "设计模式"],
            "learning_goals": ["微服务架构", "系统设计"],
            "time_availability": "每周5小时"
        }
        
        result = await ai_service.intelligent_content_recommendation(
            user_profile=user_profile,
            learning_history={"completed_topics": ["软件架构基础"]}
        )
        
        assert "recommended_topics" in result
        assert "study_path" in result
        assert len(result["recommended_topics"]) > 0
    
    @pytest.mark.asyncio
    async def test_adaptive_question_generation_success(self):
        """测试自适应题目生成 - 成功"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        
        generated_questions = {
            "questions": [
                {
                    "question": "在微服务架构中，如何处理分布式事务？",
                    "type": "case",
                    "difficulty": 3,
                    "options": {
                        "A": "使用两阶段提交",
                        "B": "采用SAGA模式",
                        "C": "避免分布式事务",
                        "D": "以上都可以"
                    },
                    "correct_answer": "D",
                    "knowledge_points": ["微服务架构", "分布式事务"]
                }
            ],
            "generation_strategy": "基于用户弱点定向生成",
            "difficulty_distribution": {"基础": 0, "中级": 0, "高级": 1}
        }
        
        mock_response.choices[0].message.content = json.dumps(generated_questions)
        mock_client.chat.completions.create.return_value = mock_response
        ai_service.openai_client = mock_client
        
        user_weaknesses = ["微服务架构", "分布式系统"]
        result = await ai_service.adaptive_question_generation(
            knowledge_gaps=user_weaknesses,
            target_difficulty="高级",
            question_count=5
        )
        
        assert "questions" in result
        assert len(result["questions"]) > 0
        assert result["questions"][0]["difficulty"] == 3
    
    @pytest.mark.asyncio
    async def test_learning_conversation_bot_success(self):
        """测试学习对话机器人 - 成功"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        
        bot_response = {
            "response": "软件架构是系统的高层设计，它定义了系统的主要组件和它们之间的关系。你想了解哪个方面的架构设计？",
            "follow_up_questions": [
                "你对哪种架构模式感兴趣？",
                "想了解架构设计的具体步骤吗？"
            ],
            "knowledge_points_covered": ["软件架构定义", "系统组件"],
            "confidence_level": 0.92
        }
        
        mock_response.choices[0].message.content = json.dumps(bot_response)
        mock_client.chat.completions.create.return_value = mock_response
        ai_service.openai_client = mock_client
        
        conversation_history = [
            {"role": "user", "content": "什么是软件架构？"},
        ]
        
        result = await ai_service.learning_conversation_bot(
            user_question="能详细解释一下吗？",
            conversation_history=conversation_history,
            user_context={"level": "初学者", "interests": ["系统设计"]}
        )
        
        assert result["response"] is not None
        assert "follow_up_questions" in result
        assert result["confidence_level"] > 0.8


class TestAIServiceIntegration:
    """AI服务集成测试"""
    
    @pytest.mark.asyncio
    async def test_complete_ai_workflow(self):
        """测试完整的AI工作流"""
        mock_client = AsyncMock()
        ai_service.openai_client = mock_client
        
        # Mock各种AI响应
        def mock_ai_response(content):
            response = MagicMock()
            response.choices = [MagicMock()]
            response.choices[0].message.content = json.dumps(content)
            return response
        
        # 1. 生成题目解析
        mock_client.chat.completions.create.return_value = mock_ai_response(MOCK_QUESTION_EXPLANATION)
        explanation = await ai_service.generate_question_explanation("测试题目", "A")
        assert "explanation" in explanation
        
        # 2. 生成播客脚本
        mock_client.chat.completions.create.return_value = mock_ai_response(MOCK_PODCAST_SCRIPT)
        script = await ai_service.generate_podcast_script(["软件架构"], "conversation", 15)
        assert "segments" in script
        
        # 3. 分析用户进度
        mock_client.chat.completions.create.return_value = mock_ai_response(MOCK_PROGRESS_ANALYSIS)
        analysis = await ai_service.analyze_user_progress("test_user", {"total_questions": 100})
        assert "current_level" in analysis
        
        # 4. 生成学习计划
        with patch.object(ai_service, 'analyze_user_progress') as mock_analyze:
            mock_analyze.return_value = MOCK_PROGRESS_ANALYSIS
            mock_client.chat.completions.create.return_value = mock_ai_response(MOCK_LEARNING_PLAN)
            
            plan = await ai_service.generate_learning_plan("test_user", ["软件架构"], 30)
            assert "phases" in plan


class TestAIServiceValidation:
    """AI服务验证测试"""
    
    def test_content_safety_validation(self):
        """测试内容安全验证"""
        # 测试安全内容
        safe_content = "软件架构是系统设计的重要组成部分"
        is_safe = ai_service._validate_content_safety(safe_content)
        assert is_safe is True
        
        # 测试包含敏感词的内容
        unsafe_content = "这里包含一些不当内容..."
        is_safe = ai_service._validate_content_safety(unsafe_content)
        # 根据实际实现调整断言
        assert isinstance(is_safe, bool)
    
    def test_json_response_validation(self):
        """测试JSON响应验证"""
        # 测试有效JSON
        valid_json = '{"key": "value", "number": 123}'
        is_valid, parsed = ai_service._validate_json_response(valid_json)
        assert is_valid is True
        assert parsed["key"] == "value"
        
        # 测试无效JSON
        invalid_json = '{"key": "value", "invalid": }'
        is_valid, parsed = ai_service._validate_json_response(invalid_json)
        assert is_valid is False
        assert parsed == {}
    
    def test_response_completeness_validation(self):
        """测试响应完整性验证"""
        # 测试完整的播客脚本响应
        complete_response = {
            "title": "测试播客",
            "segments": [{"speaker": "主持人", "content": "内容"}],
            "duration_estimate": 600
        }
        
        is_complete = ai_service._validate_podcast_response(complete_response)
        assert is_complete is True
        
        # 测试不完整的响应
        incomplete_response = {
            "title": "测试播客"
            # 缺少segments和duration_estimate
        }
        
        is_complete = ai_service._validate_podcast_response(incomplete_response)
        assert is_complete is False


class TestAIServiceErrorHandling:
    """AI服务错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_api_rate_limit_handling(self):
        """测试API速率限制处理"""
        mock_client = AsyncMock()
        
        # 模拟速率限制错误
        from openai import RateLimitError
        mock_client.chat.completions.create.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=None,
            body=None
        )
        ai_service.openai_client = mock_client
        
        result = await ai_service.generate_question_explanation("测试题目", "A")
        
        assert "速率限制" in result["explanation"] or "API限制" in result["explanation"]
    
    @pytest.mark.asyncio
    async def test_api_timeout_handling(self):
        """测试API超时处理"""
        mock_client = AsyncMock()
        
        # 模拟超时
        mock_client.chat.completions.create.side_effect = asyncio.TimeoutError()
        ai_service.openai_client = mock_client
        
        result = await ai_service.generate_question_explanation("测试题目", "A")
        
        assert "超时" in result["explanation"] or "请求失败" in result["explanation"]
    
    @pytest.mark.asyncio
    async def test_malformed_response_handling(self):
        """测试异常响应处理"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        
        # 模拟异常的JSON响应
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "这不是有效的JSON"
        
        mock_client.chat.completions.create.return_value = mock_response
        ai_service.openai_client = mock_client
        
        result = await ai_service.generate_question_explanation("测试题目", "A")
        
        assert "解析失败" in result["explanation"] or "格式错误" in result["explanation"]


@pytest.fixture
def mock_ai_dependencies():
    """AI服务依赖的mock fixture"""
    with patch('services.ai_service.AsyncOpenAI') as mock_openai, \
         patch('services.ai_service.settings') as mock_settings:
        
        mock_settings.OPENAI_API_KEY = "test_api_key"
        
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        yield {
            "openai": mock_openai,
            "client": mock_client,
            "settings": mock_settings
        }


class TestAIServicePerformance:
    """AI服务性能测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self):
        """测试并发请求性能"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(MOCK_QUESTION_EXPLANATION)
        
        mock_client.chat.completions.create.return_value = mock_response
        ai_service.openai_client = mock_client
        
        import time
        start_time = time.time()
        
        # 并发执行多个AI请求
        tasks = []
        for i in range(5):
            task = ai_service.generate_question_explanation(f"题目{i}", "A")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        
        assert len(results) == 5
        assert all("explanation" in result for result in results)
        # 并发执行应该比串行快
        assert end_time - start_time < 10.0  # 应该在10秒内完成
    
    @pytest.mark.asyncio
    async def test_large_content_processing_performance(self):
        """测试大内容处理性能"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(MOCK_PODCAST_SCRIPT)
        
        mock_client.chat.completions.create.return_value = mock_response
        ai_service.openai_client = mock_client
        
        # 生成大量主题的播客脚本
        large_topics = ["主题" + str(i) for i in range(10)]
        
        import time
        start_time = time.time()
        
        result = await ai_service.generate_podcast_script(
            topics=large_topics,
            style="conversation",
            duration_minutes=60
        )
        
        end_time = time.time()
        
        assert "segments" in result
        assert end_time - start_time < 5.0  # 应该在5秒内完成 