"""题库相关API端点

提供题库管理、上传等相关的API接口。
"""
import logging

from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.db.database import get_db
from app.db import models
from app.schemas.question_bank import (
    QuestionBank,
    QuestionBankImportResponse,
    QuestionBankUpdate,
)
from app.services.question_bank_service import QuestionBankService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[QuestionBank])
async def get_question_banks(
    skip: int = 0,
    limit: int = 100,
    subject_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """获取题库列表"""
    service = QuestionBankService(db)
    return service.get_question_banks(skip=skip, limit=limit, subject_id=subject_id)


@router.get("/{question_bank_id}", response_model=QuestionBank)
async def get_question_bank(
    question_bank_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """获取单个题库详情"""
    service = QuestionBankService(db)
    question_bank = service.get_question_bank(question_bank_id)
    if not question_bank:
        raise HTTPException(status_code=404, detail="题库不存在")
    return question_bank


@router.post("/upload", response_model=QuestionBankImportResponse)
async def upload_question_bank(
    name: str = Form(..., description="题库名称"),
    description: str = Form(None, description="题库描述"),
    subject_id: int = Form(..., description="学科ID（必填）"),
    file: UploadFile = File(..., description="题库JSON文件"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """上传题库文件"""
    # 验证文件类型
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="只支持JSON格式的文件")
    
    # 验证文件大小（限制为50MB）
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过50MB")
    
    try:
        # 读取文件内容
        content = await file.read()
        file_content = content.decode('utf-8')
        
        service = QuestionBankService(db)
        
        # 创建题库记录
        question_bank = service.create_question_bank(
            name=name,
            description=description,
            file_name=file.filename,
            subject_id=subject_id
        )
        
        # 解析文件
        questions = service.parse_question_bank_file(file_content)
        
        # 导入题目
        import_result = service.import_questions(question_bank.id, questions)
        
        return QuestionBankImportResponse(
            question_bank_id=question_bank.id,
            message=f"题库上传成功！共导入 {import_result['imported_count']} 道题目",
            total_questions=len(questions)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("题库上传失败: %s", e)
        raise HTTPException(status_code=500, detail="题库上传失败，请稍后重试") from e


@router.put("/{question_bank_id}", response_model=QuestionBank)
async def update_question_bank(
    question_bank_id: int,
    question_bank_update: QuestionBankUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """更新题库信息"""
    service = QuestionBankService(db)
    question_bank = service.get_question_bank(question_bank_id)
    
    if not question_bank:
        raise HTTPException(status_code=404, detail="题库不存在")
    
    # 更新字段
    update_data = question_bank_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question_bank, field, value)
    
    db.commit()
    db.refresh(question_bank)
    return question_bank


@router.delete("/{question_bank_id}")
async def delete_question_bank(
    question_bank_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """删除题库"""
    service = QuestionBankService(db)
    success = service.delete_question_bank(question_bank_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="题库不存在")
    
    return {"message": "题库删除成功"}


@router.post("/{question_bank_id}/reimport")
async def reimport_question_bank(
    question_bank_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """重新导入题库（如果之前导入失败）"""
    service = QuestionBankService(db)
    question_bank = service.get_question_bank(question_bank_id)
    
    if not question_bank:
        raise HTTPException(status_code=404, detail="题库不存在")
    
    if question_bank.status == "completed":
        raise HTTPException(status_code=400, detail="题库已经导入完成，无需重新导入")
    
    # TODO: 实现重新导入逻辑
    # 这里需要重新读取原始文件并导入
    raise HTTPException(status_code=501, detail="重新导入功能暂未实现")