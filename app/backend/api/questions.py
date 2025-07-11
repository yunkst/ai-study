"""
题库相关API路由
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from core.database import get_db
from models.question import Question, QuestionType, DifficultyLevel
from models.practice import Answer as AnswerModel
import json

router = APIRouter()

class QuestionBase(BaseModel):
    question_type: str  # choice, case, essay
    content: str
    difficulty: int
    knowledge_points: List[str]
    options: Optional[Dict[str, str]] = None
    correct_answer: str
    explanation: Optional[str] = None

class QuestionCreate(QuestionBase):
    pass

class QuestionResponse(QuestionBase):
    id: int
    created_at: str
    updated_at: Optional[str] = None
    total_attempts: int = 0
    correct_attempts: int = 0
    accuracy_rate: float = 0.0

class QuestionListResponse(BaseModel):
    id: int
    question_type: str
    content: str
    difficulty: int
    knowledge_points: List[str]
    total_attempts: int
    accuracy_rate: float
    created_at: str

class SearchQuery(BaseModel):
    query: str
    question_type: Optional[str] = None
    difficulty: Optional[int] = None
    knowledge_points: Optional[List[str]] = None
    limit: int = 20

class SearchResults(BaseModel):
    results: List[QuestionListResponse]
    total: int
    query: str
    filters: Dict[str, Any]

class QuestionStats(BaseModel):
    total_questions: int
    by_type: Dict[str, int]
    by_difficulty: Dict[str, int]
    by_knowledge_point: Dict[str, int]
    average_accuracy: float

async def get_user_id(request: Request) -> int:
    """从请求中获取用户ID"""
    return 1

def _convert_question_to_response(question: Question) -> QuestionListResponse:
    """转换题目模型为响应格式"""
    return QuestionListResponse(
        id=question.id,
        question_type=question.question_type.value,
        content=question.content,
        difficulty=question.difficulty.value,
        knowledge_points=question.knowledge_points or [],
        total_attempts=question.total_attempts,
        accuracy_rate=question.accuracy_rate,
        created_at=question.created_at.isoformat()
    )

def _convert_question_to_full_response(question: Question) -> QuestionResponse:
    """转换题目模型为完整响应格式"""
    return QuestionResponse(
        id=question.id,
        question_type=question.question_type.value,
        content=question.content,
        difficulty=question.difficulty.value,
        knowledge_points=question.knowledge_points or [],
        options=question.options,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        created_at=question.created_at.isoformat(),
        updated_at=question.updated_at.isoformat() if question.updated_at else None,
        total_attempts=question.total_attempts,
        correct_attempts=question.correct_attempts,
        accuracy_rate=question.accuracy_rate
    )

@router.get("/", response_model=List[QuestionListResponse])
async def get_questions(
    request: Request,
    question_type: Optional[str] = Query(None, description="题目类型: choice, case, essay"),
    difficulty: Optional[int] = Query(None, description="难度等级: 1-基础, 2-中级, 3-高级"),
    knowledge_point: Optional[str] = Query(None, description="知识点筛选"),
    limit: int = Query(20, description="返回数量限制"),
    offset: int = Query(0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """获取题目列表"""
    try:
        query = db.query(Question)
        
        # 按类型筛选
        if question_type:
            try:
                type_enum = QuestionType(question_type)
                query = query.filter(Question.question_type == type_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的题目类型: {question_type}")
        
        # 按难度筛选
        if difficulty:
            try:
                difficulty_enum = DifficultyLevel(difficulty)
                query = query.filter(Question.difficulty == difficulty_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的难度等级: {difficulty}")
        
        # 按知识点筛选
        if knowledge_point:
            query = query.filter(Question.knowledge_points.contains([knowledge_point]))
        
        # 分页
        questions = query.order_by(Question.created_at.desc()).offset(offset).limit(limit).all()
        
        return [_convert_question_to_response(q) for q in questions]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取题目列表失败: {str(e)}")

@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int, 
    request: Request,
    include_answer: bool = Query(False, description="是否包含答案信息"),
    db: Session = Depends(get_db)
):
    """获取单个题目详情"""
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        
        if not question:
            raise HTTPException(status_code=404, detail="题目未找到")
        
        response = _convert_question_to_full_response(question)
        
        # 如果不包含答案，隐藏正确答案
        if not include_answer:
            response.correct_answer = ""
            response.explanation = None
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取题目详情失败: {str(e)}")

@router.post("/search", response_model=SearchResults)
async def search_questions(
    search_query: SearchQuery,
    request: Request,
    db: Session = Depends(get_db)
):
    """智能搜索题目"""
    try:
        query = db.query(Question)
        
        # 文本搜索 - 在题目内容中搜索
        if search_query.query:
            search_term = f"%{search_query.query}%"
            query = query.filter(
                or_(
                    Question.content.ilike(search_term),
                    Question.explanation.ilike(search_term)
                )
            )
        
        # 类型筛选
        if search_query.question_type:
            try:
                type_enum = QuestionType(search_query.question_type)
                query = query.filter(Question.question_type == type_enum)
            except ValueError:
                pass
        
        # 难度筛选
        if search_query.difficulty:
            try:
                difficulty_enum = DifficultyLevel(search_query.difficulty)
                query = query.filter(Question.difficulty == difficulty_enum)
            except ValueError:
                pass
        
        # 知识点筛选
        if search_query.knowledge_points:
            for point in search_query.knowledge_points:
                query = query.filter(Question.knowledge_points.contains([point]))
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        questions = query.order_by(Question.created_at.desc()).limit(search_query.limit).all()
        
        results = [_convert_question_to_response(q) for q in questions]
        
        return SearchResults(
            results=results,
            total=total,
            query=search_query.query,
            filters={
                "question_type": search_query.question_type,
                "difficulty": search_query.difficulty,
                "knowledge_points": search_query.knowledge_points
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索题目失败: {str(e)}")

@router.post("/", response_model=QuestionResponse)
async def create_question(
    question_data: QuestionCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """创建新题目"""
    try:
        # 验证题目类型
        try:
            question_type = QuestionType(question_data.question_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的题目类型: {question_data.question_type}")
        
        # 验证难度等级
        try:
            difficulty = DifficultyLevel(question_data.difficulty)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的难度等级: {question_data.difficulty}")
        
        # 创建题目
        question = Question(
            question_type=question_type,
            content=question_data.content,
            options=question_data.options,
            correct_answer=question_data.correct_answer,
            explanation=question_data.explanation,
            difficulty=difficulty,
            knowledge_points=question_data.knowledge_points
        )
        
        db.add(question)
        db.commit()
        db.refresh(question)
        
        return _convert_question_to_full_response(question)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建题目失败: {str(e)}")

@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    question_data: QuestionCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """更新题目"""
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        
        if not question:
            raise HTTPException(status_code=404, detail="题目未找到")
        
        # 验证题目类型
        try:
            question_type = QuestionType(question_data.question_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的题目类型: {question_data.question_type}")
        
        # 验证难度等级
        try:
            difficulty = DifficultyLevel(question_data.difficulty)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的难度等级: {question_data.difficulty}")
        
        # 更新字段
        question.question_type = question_type
        question.content = question_data.content
        question.options = question_data.options
        question.correct_answer = question_data.correct_answer
        question.explanation = question_data.explanation
        question.difficulty = difficulty
        question.knowledge_points = question_data.knowledge_points
        
        db.commit()
        db.refresh(question)
        
        return _convert_question_to_full_response(question)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新题目失败: {str(e)}")

@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """删除题目"""
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        
        if not question:
            raise HTTPException(status_code=404, detail="题目未找到")
        
        # 检查是否有相关的答案记录
        answer_count = db.query(AnswerModel).filter(AnswerModel.question_id == question_id).count()
        
        if answer_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"无法删除题目，存在 {answer_count} 个相关的答案记录"
            )
        
        db.delete(question)
        db.commit()
        
        return {"message": "题目删除成功"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除题目失败: {str(e)}")

@router.get("/stats/overview", response_model=QuestionStats)
async def get_question_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取题库统计信息"""
    try:
        # 总题目数
        total_questions = db.query(Question).count()
        
        # 按类型统计
        type_stats = {}
        for question_type in QuestionType:
            count = db.query(Question).filter(Question.question_type == question_type).count()
            type_stats[question_type.value] = count
        
        # 按难度统计
        difficulty_stats = {}
        for difficulty in DifficultyLevel:
            count = db.query(Question).filter(Question.difficulty == difficulty).count()
            difficulty_stats[str(difficulty.value)] = count
        
        # 按知识点统计 (取前10个最常见的知识点)
        knowledge_point_stats = {}
        questions_with_points = db.query(Question).filter(Question.knowledge_points.isnot(None)).all()
        
        point_counts = {}
        for question in questions_with_points:
            if question.knowledge_points:
                for point in question.knowledge_points:
                    point_counts[point] = point_counts.get(point, 0) + 1
        
        # 取前10个最常见的知识点
        sorted_points = sorted(point_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        knowledge_point_stats = dict(sorted_points)
        
        # 计算平均正确率
        questions_with_attempts = db.query(Question).filter(Question.total_attempts > 0).all()
        if questions_with_attempts:
            total_accuracy = sum(q.accuracy_rate for q in questions_with_attempts)
            average_accuracy = total_accuracy / len(questions_with_attempts)
        else:
            average_accuracy = 0.0
        
        return QuestionStats(
            total_questions=total_questions,
            by_type=type_stats,
            by_difficulty=difficulty_stats,
            by_knowledge_point=knowledge_point_stats,
            average_accuracy=average_accuracy
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/knowledge-points/list")
async def get_knowledge_points(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取所有知识点列表"""
    try:
        questions = db.query(Question).filter(Question.knowledge_points.isnot(None)).all()
        
        all_points = set()
        for question in questions:
            if question.knowledge_points:
                all_points.update(question.knowledge_points)
        
        return {
            "knowledge_points": sorted(list(all_points)),
            "total_count": len(all_points)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识点列表失败: {str(e)}")

@router.get("/random")
async def get_random_questions(
    request: Request,
    count: int = Query(5, description="随机题目数量"),
    difficulty: Optional[int] = Query(None, description="指定难度"),
    knowledge_point: Optional[str] = Query(None, description="指定知识点"),
    db: Session = Depends(get_db)
):
    """获取随机题目"""
    try:
        query = db.query(Question)
        
        # 难度筛选
        if difficulty:
            try:
                difficulty_enum = DifficultyLevel(difficulty)
                query = query.filter(Question.difficulty == difficulty_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的难度等级: {difficulty}")
        
        # 知识点筛选
        if knowledge_point:
            query = query.filter(Question.knowledge_points.contains([knowledge_point]))
        
        # 随机排序并限制数量
        questions = query.order_by(func.random()).limit(count).all()
        
        return {
            "questions": [_convert_question_to_response(q) for q in questions],
            "count": len(questions),
            "filters": {
                "difficulty": difficulty,
                "knowledge_point": knowledge_point
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取随机题目失败: {str(e)}") 