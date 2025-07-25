
"""AI相关API端点

提供AI对话、学习记录等相关的API接口。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.db import models
from app.db.database import get_db
from app.schemas.ai import (
    AIMessage,
    AIStreamRequest,
    StudyRecord,
    StudyRecordCreate,
    StudyStats,
)
from app.services.ai_service import ai_service

router = APIRouter()

@router.post("/chat/stream")
async def stream_chat(
    request: AIStreamRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """流式AI聊天接口"""

    async def generate_response():
        full_response = ""
        try:
            # 如果有question_id，获取题目上下文
            context = request.context
            if request.question_id:
                question = db.query(models.Question).filter(
                    models.Question.id == request.question_id
                ).first()
                if question:
                    context = f"题目：{question.title}\n内容：{question.content}"
                    if request.conversation_type == "explanation":
                        # 获取用户的答案
                        user_answer = db.query(models.UserAnswer).filter(
                            models.UserAnswer.user_id == current_user.id,
                            models.UserAnswer.question_id == request.question_id
                        ).first()
                        if user_answer:
                            context += f"\n用户答案：{user_answer.user_answer}\n正确答案：{question.correct_answer}"

            # 构建完整的消息
            full_message = request.message
            if context:
                full_message = f"上下文：{context}\n\n用户问题：{request.message}"

            async for chunk in ai_service.stream_chat(
                message=full_message,
                user_id=str(current_user.id)
            ):
                full_response += chunk
                yield f"data: {chunk}\n\n"

            # 保存对话记录
            conversation = models.AIConversation(
                user_id=current_user.id,
                question_id=request.question_id,
                user_message=request.message,
                ai_response=full_response,
                conversation_type=request.conversation_type
            )
            db.add(conversation)
            db.commit()

            yield "data: [DONE]\n\n"

        except (ValueError, TypeError, HTTPException) as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@router.post("/explanation/{question_id}")
async def get_explanation(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """获取题目解析"""
    question = db.query(models.Question).filter(
        models.Question.id == question_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    user_answer = db.query(models.UserAnswer).filter(
        models.UserAnswer.user_id == current_user.id,
        models.UserAnswer.question_id == question_id
    ).first()

    if not user_answer:
        raise HTTPException(status_code=400, detail="Please answer the question first")

    explanation = await ai_service.get_explanation(
        question=f"{question.title}\n{question.content}",
        user_answer=user_answer.user_answer,
        correct_answer=question.correct_answer,
        user_id=str(current_user.id)
    )

    # 保存对话记录
    conversation = models.AIConversation(
        user_id=current_user.id,
        question_id=question_id,
        user_message="请解析这道题",
        ai_response=explanation,
        conversation_type="explanation"
    )
    db.add(conversation)
    db.commit()

    return {"explanation": explanation}

@router.post("/hint/{question_id}")
async def get_hint(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """获取题目提示"""
    question = db.query(models.Question).filter(
        models.Question.id == question_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    hint = await ai_service.get_hint(
        question=f"{question.title}\n{question.content}",
        user_id=str(current_user.id)
    )

    # 保存对话记录
    conversation = models.AIConversation(
        user_id=current_user.id,
        question_id=question_id,
        user_message="请给我一些提示",
        ai_response=hint,
        conversation_type="hint"
    )
    db.add(conversation)
    db.commit()

    return {"hint": hint}

@router.get("/conversations", response_model=list[AIMessage])
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """获取AI对话历史"""
    conversations = db.query(models.AIConversation).filter(
        models.AIConversation.user_id == current_user.id
    ).order_by(models.AIConversation.created_at.desc()).limit(50).all()

    return conversations

# 学习记录相关接口
@router.post("/study-records", response_model=StudyRecord)
async def create_study_record(
    record: StudyRecordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """创建学习记录"""
    db_record = models.StudyRecord(
        user_id=current_user.id,
        **record.dict()
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.get("/study-stats", response_model=StudyStats)
async def get_study_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """获取学习统计"""
    # 获取总答题数
    total_answers = db.query(models.UserAnswer).filter(
        models.UserAnswer.user_id == current_user.id
    ).count()

    # 获取正确答题数
    correct_answers = db.query(models.UserAnswer).filter(
        models.UserAnswer.user_id == current_user.id,
        models.UserAnswer.is_correct is True
    ).count()

    # 计算正确率
    accuracy_rate = (correct_answers / total_answers * 100) if total_answers > 0 else 0

    # 获取总学习时间
    total_study_time = db.query(models.StudyRecord).filter(
        models.StudyRecord.user_id == current_user.id
    ).with_entities(models.StudyRecord.study_time).all()
    total_time = sum([record[0] for record in total_study_time])

    # 获取学习过的学科
    subjects = db.query(models.Subject).join(
        models.Question
    ).join(
        models.UserAnswer
    ).filter(
        models.UserAnswer.user_id == current_user.id
    ).distinct().all()

    subject_names = [subject.name for subject in subjects]

    # 获取最近的学习记录
    recent_records = db.query(models.StudyRecord).filter(
        models.StudyRecord.user_id == current_user.id
    ).order_by(models.StudyRecord.study_date.desc()).limit(10).all()

    return StudyStats(
        total_questions=total_answers,
        correct_answers=correct_answers,
        accuracy_rate=round(accuracy_rate, 2),
        total_study_time=total_time,
        subjects_studied=subject_names,
        recent_records=recent_records
    )
