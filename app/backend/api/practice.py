"""
练习相关API路由
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from core.database import get_db
from models.practice import PracticeSession as PracticeSessionModel, Answer as AnswerModel
from models.question import Question, QuestionType, DifficultyLevel
from models.user import User
import random
import json
from services.ai_service import ai_service

router = APIRouter()

# ====== 新增：单题生成请求模型 ======


class QuestionGenerateRequest(BaseModel):
    topic: str
    difficulty: Optional[int] = 3


# ====== 新增：生成单题接口 ======


@router.post("/generate")
async def generate_single_question(
    request_data: QuestionGenerateRequest,
):
    """根据主题生成一道练习题，供前端即时练习使用"""
    try:
        result = await ai_service.generate_question(request_data.topic, request_data.difficulty or 3)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"题目生成失败: {e}")

class PracticeSessionCreate(BaseModel):
    knowledge_points: Optional[List[str]] = None
    difficulty: Optional[str] = "basic"
    question_count: int = 10
    question_type: Optional[str] = None

class PracticeSession(BaseModel):
    id: int
    question_ids: List[int]
    start_time: str
    end_time: Optional[str] = None
    score: Optional[float] = None
    total_questions: int
    status: str = "active"

class Answer(BaseModel):
    question_id: int
    answer: str
    time_spent: int  # 秒

class AnswerResponse(BaseModel):
    question_id: int
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    time_spent: int

class SessionResults(BaseModel):
    session_id: int
    total_questions: int
    correct_answers: int
    score: float
    time_spent: int
    accuracy_rate: float
    answers: List[AnswerResponse]

class PracticeHistory(BaseModel):
    sessions: List[Dict[str, Any]]
    total_sessions: int
    average_score: float
    total_questions: int
    total_correct: int

async def get_user_id(request: Request) -> int:
    """从请求中获取用户ID，这里简化为默认用户"""
    return 1

def get_questions_by_criteria(
    db: Session, 
    knowledge_points: Optional[List[str]] = None,
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None,
    limit: int = 10
) -> List[Question]:
    """根据条件筛选题目"""
    query = db.query(Question)
    
    if knowledge_points:
        # 过滤包含指定知识点的题目
        for point in knowledge_points:
            query = query.filter(Question.knowledge_points.contains([point]))
    
    if difficulty:
        difficulty_map = {
            "basic": DifficultyLevel.BASIC,
            "intermediate": DifficultyLevel.INTERMEDIATE, 
            "advanced": DifficultyLevel.ADVANCED
        }
        if difficulty in difficulty_map:
            query = query.filter(Question.difficulty == difficulty_map[difficulty])
    
    if question_type:
        type_map = {
            "choice": QuestionType.CHOICE,
            "case": QuestionType.CASE,
            "essay": QuestionType.ESSAY
        }
        if question_type in type_map:
            query = query.filter(Question.question_type == type_map[question_type])
    
    questions = query.limit(limit * 2).all()  # 获取更多题目用于随机选择
    
    # 随机选择指定数量的题目
    if len(questions) > limit:
        questions = random.sample(questions, limit)
    
    return questions

@router.post("/sessions", response_model=PracticeSession)
async def start_practice_session(
    session_data: PracticeSessionCreate,
    request: Request,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """开始练习会话"""
    try:
        # 获取符合条件的题目
        questions = get_questions_by_criteria(
            db,
            knowledge_points=session_data.knowledge_points,
            difficulty=session_data.difficulty,
            question_type=session_data.question_type,
            limit=session_data.question_count
        )
        
        if not questions:
            raise HTTPException(status_code=404, detail="未找到符合条件的题目")
        
        # 创建练习会话
        question_ids = [q.id for q in questions]
        practice_session = PracticeSessionModel(
            user_id=user_id,
            question_ids=question_ids,
            total_questions=len(question_ids)
        )
        
        db.add(practice_session)
        db.commit()
        db.refresh(practice_session)
        
        return PracticeSession(
            id=practice_session.id,
            question_ids=question_ids,
            start_time=practice_session.start_time.isoformat(),
            total_questions=practice_session.total_questions,
            status="active"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建练习会话失败: {str(e)}")

@router.get("/sessions/{session_id}/questions")
async def get_session_questions(
    session_id: int,
    request: Request,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取练习会话的题目"""
    try:
        # 验证会话
        session = db.query(PracticeSessionModel).filter(
            PracticeSessionModel.id == session_id,
            PracticeSessionModel.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="练习会话未找到")
        
        # 获取题目详情
        questions = db.query(Question).filter(
            Question.id.in_(session.question_ids)
        ).all()
        
        # 构建响应，隐藏正确答案
        question_data = []
        for q in questions:
            question_dict = {
                "id": q.id,
                "type": q.question_type.value,
                "content": q.content,
                "difficulty": q.difficulty.value,
                "knowledge_points": q.knowledge_points or []
            }
            
            # 选择题包含选项
            if q.question_type == QuestionType.CHOICE and q.options:
                question_dict["options"] = q.options
            
            question_data.append(question_dict)
        
        return {
            "session_id": session_id,
            "questions": question_data,
            "total_questions": len(question_data),
            "start_time": session.start_time.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取题目失败: {str(e)}")

@router.post("/sessions/{session_id}/answers")
async def submit_answer(
    session_id: int, 
    answer: Answer, 
    request: Request,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """提交答案"""
    try:
        # 验证会话
        session = db.query(PracticeSessionModel).filter(
            PracticeSessionModel.id == session_id,
            PracticeSessionModel.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="练习会话未找到")
        
        # 获取题目
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="题目未找到")
        
        # 检查是否已经回答过
        existing_answer = db.query(AnswerModel).filter(
            AnswerModel.session_id == session_id,
            AnswerModel.question_id == answer.question_id
        ).first()
        
        if existing_answer:
            raise HTTPException(status_code=400, detail="该题目已经回答过")
        
        # 评估答案正确性
        is_correct = _evaluate_answer(question, answer.answer)
        
        # 保存答案
        answer_record = AnswerModel(
            session_id=session_id,
            question_id=answer.question_id,
            user_answer=answer.answer,
            is_correct=is_correct,
            time_spent_seconds=answer.time_spent
        )
        
        db.add(answer_record)
        
        # 更新题目统计
        question.total_attempts += 1
        if is_correct:
            question.correct_attempts += 1
        
        db.commit()
        db.refresh(answer_record)
        
        return AnswerResponse(
            question_id=answer.question_id,
            is_correct=is_correct,
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            time_spent=answer.time_spent
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"提交答案失败: {str(e)}")

def _evaluate_answer(question: Question, user_answer: str) -> bool:
    """评估答案正确性"""
    if question.question_type == QuestionType.CHOICE:
        # 选择题直接比较
        return user_answer.strip().lower() == question.correct_answer.strip().lower()
    
    elif question.question_type == QuestionType.CASE:
        # 案例分析题可以进行关键词匹配
        correct_keywords = question.correct_answer.lower().split()
        user_keywords = user_answer.lower().split()
        
        # 简单的关键词匹配逻辑
        matches = sum(1 for keyword in correct_keywords if keyword in user_keywords)
        return matches >= len(correct_keywords) * 0.6  # 60%关键词匹配
    
    elif question.question_type == QuestionType.ESSAY:
        # 论文题暂时简单处理，可以后续集成AI评分
        return len(user_answer.strip()) >= 100  # 至少100字符
    
    return False

@router.get("/sessions/{session_id}/results", response_model=SessionResults)
async def get_session_results(
    session_id: int, 
    request: Request,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取练习结果"""
    try:
        # 获取会话
        session = db.query(PracticeSessionModel).filter(
            PracticeSessionModel.id == session_id,
            PracticeSessionModel.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="练习会话未找到")
        
        # 获取所有答案
        answers = db.query(AnswerModel).filter(
            AnswerModel.session_id == session_id
        ).all()
        
        # 计算统计信息
        total_questions = session.total_questions
        correct_answers = sum(1 for answer in answers if answer.is_correct)
        accuracy_rate = correct_answers / total_questions if total_questions > 0 else 0
        score = accuracy_rate * 100
        total_time = sum(answer.time_spent_seconds for answer in answers)
        
        # 更新会话结果
        if not session.end_time:
            session.end_time = datetime.now()
            session.duration_seconds = total_time
            session.score = score
            session.correct_count = correct_answers
            db.commit()
        
        # 构建答案响应
        answer_responses = []
        for answer in answers:
            question = db.query(Question).filter(Question.id == answer.question_id).first()
            answer_responses.append(AnswerResponse(
                question_id=answer.question_id,
                is_correct=answer.is_correct,
                correct_answer=question.correct_answer if question else "",
                explanation=question.explanation if question else None,
                time_spent=answer.time_spent_seconds
            ))
        
        return SessionResults(
            session_id=session_id,
            total_questions=total_questions,
            correct_answers=correct_answers,
            score=score,
            time_spent=total_time,
            accuracy_rate=accuracy_rate,
            answers=answer_responses
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取练习结果失败: {str(e)}")

@router.get("/history", response_model=PracticeHistory)
async def get_practice_history(
    request: Request,
    limit: int = 20,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取练习历史"""
    try:
        # 获取用户的练习会话
        sessions = db.query(PracticeSessionModel).filter(
            PracticeSessionModel.user_id == user_id
        ).order_by(PracticeSessionModel.start_time.desc()).limit(limit).all()
        
        # 构建会话数据
        session_data = []
        total_questions = 0
        total_correct = 0
        total_score = 0
        
        for session in sessions:
            session_info = {
                "id": session.id,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "total_questions": session.total_questions,
                "correct_count": session.correct_count or 0,
                "score": session.score or 0,
                "duration_seconds": session.duration_seconds or 0,
                "status": "completed" if session.end_time else "active"
            }
            session_data.append(session_info)
            
            if session.end_time:  # 只计算完成的会话
                total_questions += session.total_questions
                total_correct += session.correct_count or 0
                total_score += session.score or 0
        
        # 计算平均分
        completed_sessions = [s for s in sessions if s.end_time]
        average_score = total_score / len(completed_sessions) if completed_sessions else 0
        
        return PracticeHistory(
            sessions=session_data,
            total_sessions=len(sessions),
            average_score=average_score,
            total_questions=total_questions,
            total_correct=total_correct
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取练习历史失败: {str(e)}")

@router.delete("/sessions/{session_id}")
async def cancel_session(
    session_id: int,
    request: Request,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """取消练习会话"""
    try:
        session = db.query(PracticeSessionModel).filter(
            PracticeSessionModel.id == session_id,
            PracticeSessionModel.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="练习会话未找到")
        
        if session.end_time:
            raise HTTPException(status_code=400, detail="会话已结束，无法取消")
        
        # 标记会话结束
        session.end_time = datetime.now()
        db.commit()
        
        return {"message": "练习会话已取消"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"取消会话失败: {str(e)}") 