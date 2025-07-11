"""
Practice API 单元测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from main import app
from models.practice import PracticeSession as PracticeSessionModel, Answer as AnswerModel
from models.question import Question

client = TestClient(app)

# 测试数据
MOCK_QUESTIONS = [
    {
        "id": 1,
        "question_type": "choice",
        "content": "什么是软件架构？",
        "difficulty": 1,
        "knowledge_points": ["软件架构基础"],
        "options": {"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
        "correct_answer": "A",
        "explanation": "这是解释"
    },
    {
        "id": 2,
        "question_type": "choice",
        "content": "什么是设计模式？",
        "difficulty": 2,
        "knowledge_points": ["设计模式"],
        "options": {"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
        "correct_answer": "B",
        "explanation": "这是解释"
    }
]

MOCK_SESSION = {
    "id": 1,
    "question_ids": [1, 2],
    "start_time": "2024-01-01T10:00:00",
    "end_time": None,
    "score": None,
    "total_questions": 2,
    "answered_count": 0,
    "correct_count": 0
}

MOCK_SESSION_COMPLETED = {
    "id": 1,
    "question_ids": [1, 2],
    "start_time": "2024-01-01T10:00:00",
    "end_time": "2024-01-01T10:15:00",
    "score": 80.0,
    "total_questions": 2,
    "answered_count": 2,
    "correct_count": 1
}

class TestPracticeAPI:
    """Practice API 测试类"""
    
    @patch('api.practice.get_db')
    def test_create_practice_session_success(self, mock_get_db):
        """测试创建练习会话 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟数据库查询
        mock_question1 = MagicMock()
        mock_question1.id = 1
        mock_question2 = MagicMock()
        mock_question2.id = 2
        
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [
            mock_question1, mock_question2
        ]
        
        # 模拟会话创建
        mock_session = MagicMock()
        mock_session.id = 1
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        request_data = {
            "knowledge_points": ["软件架构基础"],
            "difficulty": "basic",
            "question_count": 2,
            "question_type": "choice"
        }
        
        with patch('api.practice.PracticeSessionModel') as mock_session_model:
            mock_session_model.return_value = mock_session
            
            response = client.post("/api/practice/sessions", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["id"] == 1
            assert len(data["question_ids"]) == 2
            assert data["total_questions"] == 2
    
    def test_create_practice_session_validation_error(self):
        """测试创建练习会话 - 验证错误"""
        request_data = {
            "question_count": 0  # 无效数量
        }
        
        response = client.post("/api/practice/sessions", json=request_data)
        
        assert response.status_code == 400
        assert "题目数量必须大于0" in response.json()["detail"]
    
    @patch('api.practice.get_db')
    def test_get_practice_session_success(self, mock_get_db):
        """测试获取练习会话 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟会话查询
        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.question_ids = [1, 2]
        mock_session.start_time = datetime(2024, 1, 1, 10, 0, 0)
        mock_session.end_time = None
        mock_session.score = None
        mock_session.total_questions = 2
        mock_session.correct_count = 0
        mock_session.duration_seconds = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        
        response = client.get("/api/practice/sessions/1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == 1
        assert data["question_ids"] == [1, 2]
        assert data["total_questions"] == 2
        assert data["end_time"] is None
    
    @patch('api.practice.get_db')
    def test_get_practice_session_not_found(self, mock_get_db):
        """测试获取练习会话 - 未找到"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/api/practice/sessions/999")
        
        assert response.status_code == 404
        assert "练习会话未找到" in response.json()["detail"]
    
    @patch('api.practice.get_db')
    def test_submit_answer_success(self, mock_get_db):
        """测试提交答案 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟会话查询
        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.end_time = None
        mock_session.question_ids = [1, 2]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        
        # 模拟题目查询
        mock_question = MagicMock()
        mock_question.id = 1
        mock_question.correct_answer = "A"
        mock_question.explanation = "这是解释"
        
        def mock_query(model):
            if model == PracticeSessionModel:
                return mock_db.query.return_value
            elif model == Question:
                query_mock = MagicMock()
                query_mock.filter.return_value.first.return_value = mock_question
                return query_mock
            elif model == AnswerModel:
                query_mock = MagicMock()
                query_mock.filter.return_value.first.return_value = None
                return query_mock
        
        mock_db.query.side_effect = mock_query
        
        request_data = {
            "question_id": 1,
            "answer": "A",
            "time_spent": 30
        }
        
        with patch('api.practice.AnswerModel') as mock_answer_model:
            mock_answer = MagicMock()
            mock_answer_model.return_value = mock_answer
            
            response = client.post("/api/practice/sessions/1/answer", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["is_correct"] is True
            assert data["correct_answer"] == "A"
            assert data["explanation"] == "这是解释"
    
    @patch('api.practice.get_db')
    def test_submit_answer_wrong(self, mock_get_db):
        """测试提交答案 - 错误答案"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 设置mock数据
        mock_session = MagicMock()
        mock_session.end_time = None
        mock_session.question_ids = [1, 2]
        
        mock_question = MagicMock()
        mock_question.correct_answer = "A"
        mock_question.explanation = "这是解释"
        
        def mock_query(model):
            if model == PracticeSessionModel:
                query_mock = MagicMock()
                query_mock.filter.return_value.first.return_value = mock_session
                return query_mock
            elif model == Question:
                query_mock = MagicMock()
                query_mock.filter.return_value.first.return_value = mock_question
                return query_mock
            elif model == AnswerModel:
                query_mock = MagicMock()
                query_mock.filter.return_value.first.return_value = None
                return query_mock
        
        mock_db.query.side_effect = mock_query
        
        request_data = {
            "question_id": 1,
            "answer": "B",  # 错误答案
            "time_spent": 45
        }
        
        response = client.post("/api/practice/sessions/1/answer", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_correct"] is False
        assert data["correct_answer"] == "A"
    
    def test_submit_answer_session_ended(self):
        """测试提交答案 - 会话已结束"""
        with patch('api.practice.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # 模拟已结束的会话
            mock_session = MagicMock()
            mock_session.end_time = datetime.now()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_session
            
            request_data = {
                "question_id": 1,
                "answer": "A",
                "time_spent": 30
            }
            
            response = client.post("/api/practice/sessions/1/answer", json=request_data)
            
            assert response.status_code == 400
            assert "练习会话已结束" in response.json()["detail"]
    
    @patch('api.practice.get_db')
    def test_finish_practice_session_success(self, mock_get_db):
        """测试结束练习会话 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟活跃会话
        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.end_time = None
        mock_session.start_time = datetime(2024, 1, 1, 10, 0, 0)
        mock_session.total_questions = 2
        
        # 模拟答案统计
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_db.query.return_value.filter.return_value.count.return_value = 1  # 正确答案数
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 2  # 总答案数
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 15, 0)
            
            response = client.post("/api/practice/sessions/1/finish")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["message"] == "练习会话已结束"
            assert "score" in data
            assert "duration_minutes" in data
            assert "summary" in data
    
    @patch('api.practice.get_db')
    def test_get_session_questions_success(self, mock_get_db):
        """测试获取会话题目 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟会话
        mock_session = MagicMock()
        mock_session.question_ids = [1, 2]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        
        # 模拟题目
        mock_questions = [
            MagicMock(id=1, question_type="choice", content="题目1", difficulty=1,
                     knowledge_points=["知识点1"], options={"A": "选项A"}, correct_answer="A"),
            MagicMock(id=2, question_type="choice", content="题目2", difficulty=2,
                     knowledge_points=["知识点2"], options={"A": "选项A"}, correct_answer="B")
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_questions
        
        response = client.get("/api/practice/sessions/1/questions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[1]["id"] == 2
        # 验证不包含正确答案
        assert "correct_answer" not in data[0]
        assert "correct_answer" not in data[1]
    
    @patch('api.practice.get_db')
    def test_get_session_statistics_success(self, mock_get_db):
        """测试获取会话统计 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟会话
        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.user_id = 1
        mock_session.total_questions = 10
        mock_session.correct_count = 8
        mock_session.score = 80.0
        mock_session.duration_seconds = 600
        mock_session.start_time = datetime(2024, 1, 1, 10, 0, 0)
        mock_session.end_time = datetime(2024, 1, 1, 10, 10, 0)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        
        # 模拟答案统计
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        
        response = client.get("/api/practice/sessions/1/statistics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == 1
        assert data["total_questions"] == 10
        assert data["correct_answers"] == 8
        assert data["accuracy_rate"] == 0.8
        assert data["total_time_minutes"] == 10
        assert data["average_time_per_question"] == 60
    
    @patch('api.practice.get_db')
    def test_get_user_sessions_success(self, mock_get_db):
        """测试获取用户会话列表 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟会话列表
        mock_sessions = [
            MagicMock(
                id=1,
                start_time=datetime(2024, 1, 1, 10, 0, 0),
                end_time=datetime(2024, 1, 1, 10, 15, 0),
                score=80.0,
                total_questions=10,
                correct_count=8
            ),
            MagicMock(
                id=2,
                start_time=datetime(2024, 1, 2, 10, 0, 0),
                end_time=None,
                score=None,
                total_questions=5,
                correct_count=0
            )
        ]
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_sessions
        
        response = client.get("/api/practice/sessions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["score"] == 80.0
        assert data[1]["id"] == 2
        assert data[1]["score"] is None
    
    def test_practice_api_error_handling(self):
        """测试Practice API错误处理"""
        with patch('api.practice.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.query.side_effect = Exception("数据库错误")
            
            response = client.get("/api/practice/sessions/1")
            
            assert response.status_code == 500
            assert "获取练习会话失败" in response.json()["detail"]


class TestPracticeIntegration:
    """Practice API 集成测试"""
    
    @patch('api.practice.get_db')
    def test_complete_practice_workflow(self, mock_get_db):
        """测试完整的练习流程"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 1. 创建练习会话
        mock_questions = [MagicMock(id=1), MagicMock(id=2)]
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = mock_questions
        
        mock_session = MagicMock()
        mock_session.id = 1
        
        with patch('api.practice.PracticeSessionModel') as mock_session_model:
            mock_session_model.return_value = mock_session
            
            create_response = client.post("/api/practice/sessions", json={
                "knowledge_points": ["软件架构基础"],
                "question_count": 2
            })
            
            assert create_response.status_code == 200
            session_id = create_response.json()["id"]
        
        # 2. 获取题目
        mock_session.question_ids = [1, 2]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        
        mock_question_objects = [
            MagicMock(id=1, content="题目1", question_type="choice", difficulty=1,
                     knowledge_points=["知识点1"], options={"A": "选项A"})
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_question_objects
        
        questions_response = client.get(f"/api/practice/sessions/{session_id}/questions")
        assert questions_response.status_code == 200
        
        # 3. 提交答案
        mock_session.end_time = None
        mock_question = MagicMock()
        mock_question.correct_answer = "A"
        mock_question.explanation = "解释"
        
        def mock_query(model):
            if model == PracticeSessionModel:
                query_mock = MagicMock()
                query_mock.filter.return_value.first.return_value = mock_session
                return query_mock
            elif model == Question:
                query_mock = MagicMock()
                query_mock.filter.return_value.first.return_value = mock_question
                return query_mock
            elif model == AnswerModel:
                query_mock = MagicMock()
                query_mock.filter.return_value.first.return_value = None
                return query_mock
        
        mock_db.query.side_effect = mock_query
        
        with patch('api.practice.AnswerModel'):
            answer_response = client.post(f"/api/practice/sessions/{session_id}/answer", json={
                "question_id": 1,
                "answer": "A",
                "time_spent": 30
            })
            
            assert answer_response.status_code == 200
            assert answer_response.json()["is_correct"] is True
        
        # 4. 结束会话
        mock_session.total_questions = 2
        mock_session.start_time = datetime(2024, 1, 1, 10, 0, 0)
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 1
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 15, 0)
            
            finish_response = client.post(f"/api/practice/sessions/{session_id}/finish")
            assert finish_response.status_code == 200


class TestPracticeValidation:
    """Practice API 验证测试"""
    
    def test_create_session_invalid_difficulty(self):
        """测试创建会话 - 无效难度"""
        response = client.post("/api/practice/sessions", json={
            "difficulty": "invalid_difficulty",
            "question_count": 5
        })
        
        assert response.status_code == 400
        assert "无效的难度级别" in response.json()["detail"]
    
    def test_create_session_invalid_question_type(self):
        """测试创建会话 - 无效题目类型"""
        response = client.post("/api/practice/sessions", json={
            "question_type": "invalid_type",
            "question_count": 5
        })
        
        assert response.status_code == 400
        assert "无效的题目类型" in response.json()["detail"]
    
    def test_submit_answer_invalid_question_id(self):
        """测试提交答案 - 无效题目ID"""
        with patch('api.practice.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # 模拟会话存在但题目不在会话中
            mock_session = MagicMock()
            mock_session.end_time = None
            mock_session.question_ids = [1, 2]
            mock_db.query.return_value.filter.return_value.first.return_value = mock_session
            
            response = client.post("/api/practice/sessions/1/answer", json={
                "question_id": 999,  # 不在会话中的题目
                "answer": "A",
                "time_spent": 30
            })
            
            assert response.status_code == 400
            assert "题目不属于当前练习会话" in response.json()["detail"]


@pytest.fixture
def mock_practice_models():
    """Practice相关模型的mock fixture"""
    with patch('api.practice.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 设置常用的mock返回值
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        yield mock_db 