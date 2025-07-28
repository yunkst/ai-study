
"""题目相关API端点

提供题目查询、答题、统计等相关的API接口。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.db import models
from app.db.database import get_db
from app.schemas.question import (
    AnswerResult,
    PaginatedResponse,
    Question,
    QuestionCreate,
    QuestionForApp,
    QuestionUpdate,
    Subject,
    SubjectCreate,
    UserAnswer,
    UserAnswerCreate,
)

router = APIRouter()

# 学科相关接口
@router.get("/subjects", response_model=list[Subject])
async def get_subjects(db: Session = Depends(get_db)):
    """获取所有学科"""
    subjects = db.query(models.Subject).all()
    return subjects

@router.post("/subjects", response_model=Subject)
async def create_subject(
    subject: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """创建学科（管理员功能）"""
    db_subject = models.Subject(**subject.dict())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

@router.get("/subjects/{subject_id}", response_model=Subject)
async def get_subject(
    subject_id: int,
    db: Session = Depends(get_db)
):
    """获取单个学科详情"""
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="学科不存在")
    return subject

@router.delete("/subjects/{subject_id}")
async def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """删除学科（管理员功能）"""
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="学科不存在")
    
    # 检查是否有关联的题目
    question_count = db.query(models.Question).filter(models.Question.subject_id == subject_id).count()
    if question_count > 0:
        raise HTTPException(status_code=400, detail=f"无法删除学科，该学科下还有 {question_count} 道题目")
    
    db.delete(subject)
    db.commit()
    return {"message": "学科删除成功"}

# 题目相关接口
@router.get("/", response_model=PaginatedResponse[Question])
async def get_questions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    question_bank_id: int | None = Query(None, description="题库ID筛选"),
    subject_id: str | None = Query(None),
    question_type: str | None = Query(None),
    difficulty: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """获取题目列表（管理员查看，包含答案）"""
    query = db.query(models.Question)

    # 处理subject_id参数，将空字符串转换为None
    if subject_id and subject_id.strip():
        try:
            subject_id_int = int(subject_id)
            query = query.filter(models.Question.subject_id == subject_id_int)
        except ValueError:
            pass  # 忽略无效的subject_id
    
    if question_bank_id:
        query = query.filter(models.Question.question_bank_id == question_bank_id)
    
    if question_type and question_type.strip():
        query = query.filter(models.Question.question_type == question_type)
    if difficulty:
        query = query.filter(models.Question.difficulty == difficulty)

    # 获取总数
    total = query.count()
    
    # 计算分页参数
    skip = (page - 1) * size
    questions = query.offset(skip).limit(size).all()
    
    # 返回分页响应
    return PaginatedResponse.create(questions, total, page, size)

@router.get("/questions/for-app", response_model=list[QuestionForApp])
async def get_questions_for_app(
    subject_id: int | None = Query(None),
    difficulty: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """获取题目列表（APP使用，不包含答案）"""
    query = db.query(models.Question)

    if subject_id:
        query = query.filter(models.Question.subject_id == subject_id)
    if difficulty:
        query = query.filter(models.Question.difficulty == difficulty)

    questions = query.offset(skip).limit(limit).all()

    # 转换为APP格式（移除正确答案和解析）
    app_questions = []
    for q in questions:
        app_question = QuestionForApp(
            id=q.id,
            subject_id=q.subject_id,
            title=q.title,
            content=q.content,
            question_type=q.question_type,
            options=q.options,
            difficulty=q.difficulty,
            tags=q.tags,
            subject=q.subject
        )
        app_questions.append(app_question)

    return app_questions

@router.post("/questions", response_model=Question)
async def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """创建题目（管理员功能）"""
    # 验证学科是否存在
    subject = db.query(models.Subject).filter(
        models.Subject.id == question.subject_id
    ).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    db_question = models.Question(**question.dict())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

@router.get("/questions/{question_id}", response_model=Question)
async def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """获取单个题目详情"""
    question = db.query(models.Question).filter(
        models.Question.id == question_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.put("/questions/{question_id}", response_model=Question)
async def update_question(
    question_id: int,
    question_update: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """更新题目（管理员功能）"""
    question = db.query(models.Question).filter(
        models.Question.id == question_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    update_data = question_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)
    return question

# 答题相关接口
@router.post("/questions/{question_id}/answer", response_model=AnswerResult)
async def submit_answer(
    question_id: int,
    answer_data: UserAnswerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """提交答案"""
    # 验证题目是否存在
    question = db.query(models.Question).filter(
        models.Question.id == question_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # 检查是否已经答过这道题
    existing_answer = db.query(models.UserAnswer).filter(
        and_(
            models.UserAnswer.user_id == current_user.id,
            models.UserAnswer.question_id == question_id
        )
    ).first()

    # 判断答案是否正确
    is_correct = answer_data.user_answer.strip().lower() == question.correct_answer.strip().lower()

    if existing_answer:
        # 更新已有答案
        existing_answer.user_answer = answer_data.user_answer
        existing_answer.is_correct = is_correct
        existing_answer.time_spent = answer_data.time_spent
        db.commit()
    else:
        # 创建新答案记录
        db_answer = models.UserAnswer(
            user_id=current_user.id,
            question_id=question_id,
            user_answer=answer_data.user_answer,
            is_correct=is_correct,
            time_spent=answer_data.time_spent
        )
        db.add(db_answer)
        db.commit()

    return AnswerResult(
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        user_answer=answer_data.user_answer
    )

@router.get("/my-answers", response_model=list[UserAnswer])
async def get_my_answers(
    subject_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """获取我的答题记录"""
    query = db.query(models.UserAnswer).filter(
        models.UserAnswer.user_id == current_user.id
    )

    if subject_id:
        query = query.join(models.Question).filter(
            models.Question.subject_id == subject_id
        )

    answers = query.order_by(models.UserAnswer.created_at.desc()).offset(skip).limit(limit).all()
    return answers
