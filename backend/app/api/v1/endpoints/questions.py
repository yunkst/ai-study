
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

# 题目相关接口
@router.get("/questions", response_model=list[Question])
async def get_questions(
    subject_id: int | None = Query(None),
    difficulty: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """获取题目列表（管理员查看，包含答案）"""
    query = db.query(models.Question)

    if subject_id:
        query = query.filter(models.Question.subject_id == subject_id)
    if difficulty:
        query = query.filter(models.Question.difficulty == difficulty)

    questions = query.offset(skip).limit(limit).all()
    return questions

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
