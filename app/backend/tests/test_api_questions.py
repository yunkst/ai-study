"""
Questions API 单元测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from main import app
from models.question import Question, QuestionType, DifficultyLevel

client = TestClient(app)

# 测试数据
MOCK_QUESTION_DATA = {
    "id": 1,
    "question_type": "choice",
    "content": "什么是软件架构？",
    "difficulty": 1,
    "knowledge_points": ["软件架构基础", "系统设计"],
    "options": {
        "A": "软件的结构设计",
        "B": "硬件的配置",
        "C": "数据库设计",
        "D": "用户界面设计"
    },
    "correct_answer": "A",
    "explanation": "软件架构是系统的整体结构设计，包括组件、组件间的关系以及指导其设计与演化的原则。",
    "created_at": "2024-01-01T00:00:00",
    "total_attempts": 100,
    "correct_attempts": 75
}

MOCK_QUESTIONS_LIST = [
    {
        "id": 1,
        "question_type": "choice",
        "content": "什么是软件架构？",
        "difficulty": 1,
        "knowledge_points": ["软件架构基础"]
    },
    {
        "id": 2,
        "question_type": "case",
        "content": "请分析以下系统架构案例...",
        "difficulty": 2,
        "knowledge_points": ["系统设计", "架构模式"]
    },
    {
        "id": 3,
        "question_type": "essay",
        "content": "论述微服务架构的优缺点",
        "difficulty": 3,
        "knowledge_points": ["微服务", "分布式系统"]
    }
]

MOCK_SEARCH_RESULTS = [
    {
        "id": 1,
        "content": "什么是软件架构？",
        "knowledge_points": ["软件架构基础"],
        "difficulty": 1,
        "relevance_score": 0.95
    },
    {
        "id": 2,
        "content": "架构设计的基本原则",
        "knowledge_points": ["软件架构基础", "设计原则"],
        "difficulty": 2,
        "relevance_score": 0.87
    }
]

class TestQuestionsAPI:
    """Questions API 测试类"""
    
    @patch('api.questions.get_db')
    def test_get_questions_success(self, mock_get_db):
        """测试获取题目列表 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟题目查询
        mock_questions = [
            MagicMock(
                id=1,
                question_type=QuestionType.CHOICE,
                content="题目1",
                difficulty=DifficultyLevel.BASIC,
                knowledge_points=["知识点1"],
                options={"A": "选项A"},
                correct_answer="A",
                explanation="解释1",
                created_at=datetime(2024, 1, 1),
                updated_at=None
            ),
            MagicMock(
                id=2,
                question_type=QuestionType.CASE,
                content="题目2",
                difficulty=DifficultyLevel.INTERMEDIATE,
                knowledge_points=["知识点2"],
                options=None,
                correct_answer="答案2",
                explanation="解释2",
                created_at=datetime(2024, 1, 2),
                updated_at=None
            )
        ]
        
        # 模拟统计查询
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_questions
        mock_db.query.return_value.count.return_value = 2
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [10, 8]  # 总次数，正确次数
        
        response = client.get("/api/questions/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "questions" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        
        assert len(data["questions"]) == 2
        assert data["total"] == 2
        assert data["questions"][0]["id"] == 1
        assert data["questions"][0]["question_type"] == "choice"
    
    @patch('api.questions.get_db')
    def test_get_questions_with_filters(self, mock_get_db):
        """测试获取题目列表 - 带筛选条件"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_questions = [
            MagicMock(
                id=1,
                question_type=QuestionType.CHOICE,
                content="题目1",
                difficulty=DifficultyLevel.BASIC,
                knowledge_points=["软件架构基础"],
                options={"A": "选项A"},
                correct_answer="A",
                explanation="解释",
                created_at=datetime(2024, 1, 1),
                updated_at=None
            )
        ]
        
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_questions
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [5, 4]
        
        response = client.get("/api/questions/?difficulty=basic&question_type=choice&knowledge_point=软件架构基础")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["questions"]) == 1
        assert data["questions"][0]["difficulty"] == 1  # BASIC = 1
        assert data["questions"][0]["question_type"] == "choice"
    
    @patch('api.questions.get_db')
    def test_get_question_detail_success(self, mock_get_db):
        """测试获取题目详情 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟题目查询
        mock_question = MagicMock()
        mock_question.id = 1
        mock_question.question_type = QuestionType.CHOICE
        mock_question.content = "什么是软件架构？"
        mock_question.difficulty = DifficultyLevel.BASIC
        mock_question.knowledge_points = ["软件架构基础"]
        mock_question.options = {"A": "选项A", "B": "选项B"}
        mock_question.correct_answer = "A"
        mock_question.explanation = "这是解释"
        mock_question.created_at = datetime(2024, 1, 1)
        mock_question.updated_at = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_question
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [10, 8]  # 统计数据
        
        response = client.get("/api/questions/1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == 1
        assert data["content"] == "什么是软件架构？"
        assert data["question_type"] == "choice"
        assert data["difficulty"] == 1
        assert data["knowledge_points"] == ["软件架构基础"]
        assert data["total_attempts"] == 10
        assert data["correct_attempts"] == 8
    
    @patch('api.questions.get_db')
    def test_get_question_detail_not_found(self, mock_get_db):
        """测试获取题目详情 - 未找到"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/api/questions/999")
        
        assert response.status_code == 404
        assert "题目未找到" in response.json()["detail"]
    
    @patch('api.questions.get_db')
    def test_search_questions_success(self, mock_get_db):
        """测试搜索题目 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟搜索结果
        mock_questions = [
            MagicMock(
                id=1,
                content="什么是软件架构？",
                question_type=QuestionType.CHOICE,
                difficulty=DifficultyLevel.BASIC,
                knowledge_points=["软件架构基础"],
                options={"A": "选项A"},
                correct_answer="A",
                explanation="解释",
                created_at=datetime(2024, 1, 1),
                updated_at=None
            )
        ]
        
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = mock_questions
        
        response = client.get("/api/questions/search?query=软件架构")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total" in data
        assert "query" in data
        
        assert len(data["results"]) == 1
        assert data["query"] == "软件架构"
        assert "软件架构" in data["results"][0]["content"]
    
    def test_search_questions_empty_query(self):
        """测试搜索题目 - 空查询"""
        response = client.get("/api/questions/search?query=")
        
        assert response.status_code == 400
        assert "搜索关键词不能为空" in response.json()["detail"]
    
    @patch('api.questions.get_db')
    def test_create_question_success(self, mock_get_db):
        """测试创建题目 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_question = MagicMock()
        mock_question.id = 1
        
        request_data = {
            "question_type": "choice",
            "content": "新题目内容",
            "difficulty": 1,
            "knowledge_points": ["软件架构基础"],
            "options": {"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
            "correct_answer": "A",
            "explanation": "这是解释"
        }
        
        with patch('api.questions.Question') as mock_question_model:
            mock_question_model.return_value = mock_question
            
            response = client.post("/api/questions/", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["message"] == "题目创建成功"
            assert data["question_id"] == 1
    
    def test_create_question_validation_error(self):
        """测试创建题目 - 验证错误"""
        request_data = {
            "question_type": "invalid_type",  # 无效类型
            "content": "题目内容",
            "difficulty": 1,
            "knowledge_points": ["知识点"],
            "correct_answer": "A"
        }
        
        response = client.post("/api/questions/", json=request_data)
        
        assert response.status_code == 400
        assert "无效的题目类型" in response.json()["detail"]
    
    def test_create_choice_question_missing_options(self):
        """测试创建选择题 - 缺少选项"""
        request_data = {
            "question_type": "choice",
            "content": "选择题内容",
            "difficulty": 1,
            "knowledge_points": ["知识点"],
            "correct_answer": "A"
            # 缺少options字段
        }
        
        response = client.post("/api/questions/", json=request_data)
        
        assert response.status_code == 400
        assert "选择题必须提供选项" in response.json()["detail"]
    
    @patch('api.questions.get_db')
    def test_update_question_success(self, mock_get_db):
        """测试更新题目 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟现有题目
        mock_question = MagicMock()
        mock_question.id = 1
        mock_question.content = "原始内容"
        mock_question.difficulty = DifficultyLevel.BASIC
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_question
        
        request_data = {
            "content": "更新后的内容",
            "difficulty": 2,
            "explanation": "更新后的解释"
        }
        
        response = client.put("/api/questions/1", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "题目更新成功"
        
        # 验证题目属性被更新
        assert mock_question.content == "更新后的内容"
        assert mock_question.difficulty == DifficultyLevel.INTERMEDIATE
        assert mock_question.explanation == "更新后的解释"
    
    @patch('api.questions.get_db')
    def test_update_question_not_found(self, mock_get_db):
        """测试更新题目 - 未找到"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        request_data = {"content": "更新内容"}
        
        response = client.put("/api/questions/999", json=request_data)
        
        assert response.status_code == 404
        assert "题目未找到" in response.json()["detail"]
    
    @patch('api.questions.get_db')
    def test_delete_question_success(self, mock_get_db):
        """测试删除题目 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_question = MagicMock()
        mock_question.id = 1
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_question
        
        response = client.delete("/api/questions/1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "题目删除成功"
        
        # 验证删除操作被调用
        mock_db.delete.assert_called_once_with(mock_question)
        mock_db.commit.assert_called_once()
    
    @patch('api.questions.get_db')
    def test_delete_question_not_found(self, mock_get_db):
        """测试删除题目 - 未找到"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.delete("/api/questions/999")
        
        assert response.status_code == 404
        assert "题目未找到" in response.json()["detail"]
    
    @patch('api.questions.get_db')
    def test_get_random_questions_success(self, mock_get_db):
        """测试获取随机题目 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_questions = [
            MagicMock(
                id=1,
                question_type=QuestionType.CHOICE,
                content="随机题目1",
                difficulty=DifficultyLevel.BASIC,
                knowledge_points=["知识点1"],
                options={"A": "选项A"},
                correct_answer="A",
                explanation="解释1",
                created_at=datetime(2024, 1, 1),
                updated_at=None
            ),
            MagicMock(
                id=2,
                question_type=QuestionType.CHOICE,
                content="随机题目2",
                difficulty=DifficultyLevel.INTERMEDIATE,
                knowledge_points=["知识点2"],
                options={"A": "选项A"},
                correct_answer="A",
                explanation="解释2",
                created_at=datetime(2024, 1, 2),
                updated_at=None
            )
        ]
        
        with patch('random.sample') as mock_sample:
            mock_sample.return_value = mock_questions
            mock_db.query.return_value.all.return_value = mock_questions
            
            response = client.get("/api/questions/random?count=2")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 2
            assert data[0]["id"] == 1
            assert data[1]["id"] == 2
    
    def test_get_random_questions_invalid_count(self):
        """测试获取随机题目 - 无效数量"""
        response = client.get("/api/questions/random?count=0")
        
        assert response.status_code == 400
        assert "题目数量必须大于0" in response.json()["detail"]
        
        response = client.get("/api/questions/random?count=101")
        
        assert response.status_code == 400
        assert "题目数量不能超过100" in response.json()["detail"]
    
    @patch('api.questions.get_db')
    def test_get_knowledge_points_success(self, mock_get_db):
        """测试获取知识点列表 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟知识点查询
        mock_questions = [
            MagicMock(knowledge_points=["软件架构基础", "设计模式"]),
            MagicMock(knowledge_points=["系统设计", "软件架构基础"]),
            MagicMock(knowledge_points=["性能优化"])
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_questions
        
        response = client.get("/api/questions/knowledge-points")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "knowledge_points" in data
        assert "total_count" in data
        
        # 验证知识点去重和统计
        knowledge_points = data["knowledge_points"]
        assert any(kp["name"] == "软件架构基础" and kp["count"] == 2 for kp in knowledge_points)
        assert any(kp["name"] == "设计模式" and kp["count"] == 1 for kp in knowledge_points)
        assert any(kp["name"] == "系统设计" and kp["count"] == 1 for kp in knowledge_points)
        assert any(kp["name"] == "性能优化" and kp["count"] == 1 for kp in knowledge_points)
    
    @patch('api.questions.get_db')
    def test_get_questions_statistics_success(self, mock_get_db):
        """测试获取题目统计 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟统计查询
        mock_db.query.return_value.count.return_value = 100  # 总题目数
        mock_db.query.return_value.filter.return_value.count.side_effect = [30, 50, 20]  # 各难度题目数
        mock_db.query.return_value.filter.return_value.count.side_effect = [40, 35, 25]  # 各类型题目数
        
        response = client.get("/api/questions/statistics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_questions" in data
        assert "difficulty_distribution" in data
        assert "type_distribution" in data
        assert "knowledge_point_distribution" in data
        assert "creation_trends" in data
        
        assert data["total_questions"] == 100


class TestQuestionsIntegration:
    """Questions API 集成测试"""
    
    @patch('api.questions.get_db')
    def test_complete_question_management_workflow(self, mock_get_db):
        """测试完整的题目管理工作流"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 1. 创建题目
        mock_question = MagicMock()
        mock_question.id = 1
        
        with patch('api.questions.Question') as mock_question_model:
            mock_question_model.return_value = mock_question
            
            create_response = client.post("/api/questions/", json={
                "question_type": "choice",
                "content": "测试题目",
                "difficulty": 1,
                "knowledge_points": ["测试知识点"],
                "options": {"A": "选项A", "B": "选项B"},
                "correct_answer": "A",
                "explanation": "测试解释"
            })
            
            assert create_response.status_code == 200
            question_id = create_response.json()["question_id"]
        
        # 2. 获取题目详情
        mock_question.question_type = QuestionType.CHOICE
        mock_question.content = "测试题目"
        mock_question.difficulty = DifficultyLevel.BASIC
        mock_question.knowledge_points = ["测试知识点"]
        mock_question.options = {"A": "选项A", "B": "选项B"}
        mock_question.correct_answer = "A"
        mock_question.explanation = "测试解释"
        mock_question.created_at = datetime(2024, 1, 1)
        mock_question.updated_at = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_question
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [0, 0]
        
        detail_response = client.get(f"/api/questions/{question_id}")
        assert detail_response.status_code == 200
        
        # 3. 更新题目
        update_response = client.put(f"/api/questions/{question_id}", json={
            "content": "更新后的题目",
            "explanation": "更新后的解释"
        })
        assert update_response.status_code == 200
        
        # 4. 搜索题目
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_question]
        
        search_response = client.get("/api/questions/search?query=测试")
        assert search_response.status_code == 200
        
        # 5. 删除题目
        delete_response = client.delete(f"/api/questions/{question_id}")
        assert delete_response.status_code == 200
    
    @patch('api.questions.get_db')
    def test_question_filtering_and_pagination(self, mock_get_db):
        """测试题目筛选和分页"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟大量题目数据
        mock_questions = [
            MagicMock(
                id=i,
                question_type=QuestionType.CHOICE,
                content=f"题目{i}",
                difficulty=DifficultyLevel.BASIC if i % 3 == 0 else DifficultyLevel.INTERMEDIATE,
                knowledge_points=[f"知识点{i % 5}"],
                options={"A": "选项A"},
                correct_answer="A",
                explanation=f"解释{i}",
                created_at=datetime(2024, 1, i % 30 + 1),
                updated_at=None
            ) for i in range(1, 11)
        ]
        
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_questions[:5]
        mock_db.query.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        
        # 测试分页
        response = client.get("/api/questions/?page=1&size=5")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["questions"]) == 5
        assert data["total"] == 10
        assert data["page"] == 1
        assert data["size"] == 5


class TestQuestionsValidation:
    """Questions API 验证测试"""
    
    def test_create_question_content_validation(self):
        """测试题目内容验证"""
        # 空内容
        response = client.post("/api/questions/", json={
            "question_type": "choice",
            "content": "",
            "difficulty": 1,
            "knowledge_points": ["知识点"],
            "options": {"A": "选项A"},
            "correct_answer": "A"
        })
        
        assert response.status_code == 400
        assert "题目内容不能为空" in response.json()["detail"]
    
    def test_create_question_knowledge_points_validation(self):
        """测试知识点验证"""
        # 空知识点列表
        response = client.post("/api/questions/", json={
            "question_type": "choice",
            "content": "题目内容",
            "difficulty": 1,
            "knowledge_points": [],
            "options": {"A": "选项A"},
            "correct_answer": "A"
        })
        
        assert response.status_code == 400
        assert "至少需要指定一个知识点" in response.json()["detail"]
    
    def test_create_question_difficulty_validation(self):
        """测试难度验证"""
        # 无效难度
        response = client.post("/api/questions/", json={
            "question_type": "choice",
            "content": "题目内容",
            "difficulty": 0,  # 无效难度
            "knowledge_points": ["知识点"],
            "options": {"A": "选项A"},
            "correct_answer": "A"
        })
        
        assert response.status_code == 400
        assert "无效的难度级别" in response.json()["detail"]


@pytest.fixture
def mock_questions_db():
    """Questions相关数据库的mock fixture"""
    with patch('api.questions.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 设置常用的mock返回值
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.count.return_value = 0
        
        yield mock_db


class TestQuestionsPerformance:
    """Questions API 性能测试"""
    
    @patch('api.questions.get_db')
    def test_large_questions_list_performance(self, mock_get_db):
        """测试大量题目列表的性能"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟大量题目
        mock_questions = [
            MagicMock(
                id=i,
                question_type=QuestionType.CHOICE,
                content=f"题目{i}",
                difficulty=DifficultyLevel.BASIC,
                knowledge_points=[f"知识点{i % 10}"],
                options={"A": "选项A"},
                correct_answer="A",
                explanation=f"解释{i}",
                created_at=datetime(2024, 1, 1),
                updated_at=None
            ) for i in range(1, 1001)  # 1000个题目
        ]
        
        # 分页返回
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_questions[:50]
        mock_db.query.return_value.count.return_value = 1000
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        
        import time
        start_time = time.time()
        
        response = client.get("/api/questions/?page=1&size=50")
        
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 2.0  # 应该在2秒内完成
        
        data = response.json()
        assert len(data["questions"]) == 50
        assert data["total"] == 1000 