"""
知识体系管理API
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
import json
import asyncio
import os
import shutil
import logging
from pathlib import Path
import tempfile
import zipfile
from datetime import datetime

from core.database import get_db
from models.knowledge import KnowledgeDomain, KnowledgePoint, SkillPoint, UserKnowledgeProgress
from models.learning_path import LearningPath
from services.knowledge_extractor import KnowledgeExtractor
from services.learning_path_service import LearningPathService
from services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic模型
class KnowledgeDomainResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    exam_weight: float
    sort_order: int
    knowledge_points_count: int
    
    class Config:
        from_attributes = True

class KnowledgePointResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    difficulty_level: int
    exam_weight: float
    estimated_study_hours: float
    domain_name: str
    prerequisites_count: int
    mastery_level: float = 0.0  # 用户掌握程度
    
    class Config:
        from_attributes = True

class ImportProgress(BaseModel):
    status: str  # "running", "completed", "error"
    message: str
    progress: float  # 0.0 - 1.0
    details: Optional[Dict] = None

class ImportRequest(BaseModel):
    directory: str = "/app/resources/System_Architect"
    force_reimport: bool = False
    include_case_studies: bool = True

class RAGProcessRequest(BaseModel):
    mode: str = "full"  # full, incremental
    embedding_model: str = "bge-m3"
    chunk_size: int = 1024

class KnowledgeStatistics(BaseModel):
    total_domains: int
    total_knowledge_points: int
    total_skill_points: int
    total_study_hours: float
    days_2h_per_day: int
    days_4h_per_day: int
    weeks_20h_per_week: int

# 全局导入状态
import_status = {
    "status": "idle",  # idle, running, completed, error
    "progress": 0.0,
    "message": "",
    "details": None,
    "start_time": None,
    "error": None
}

@router.get("/domains")
async def get_knowledge_domains(db: Session = Depends(get_db)):
    """获取所有知识域"""
    try:
        domains = db.query(KnowledgeDomain).options(
            joinedload(KnowledgeDomain.knowledge_points)
        ).all()
        
        result = []
        for domain in domains:
            result.append({
                "id": domain.id,
                "name": domain.name,
                "description": domain.description,
                "exam_weight": domain.exam_weight,
                "knowledge_points_count": len(domain.knowledge_points)
            })
        
        return result
    except Exception as e:
        logger.error(f"获取知识域失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/points")
async def get_knowledge_points(
    domain_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取知识点列表"""
    try:
        query = db.query(KnowledgePoint).options(
            joinedload(KnowledgePoint.domain),
            joinedload(KnowledgePoint.prerequisites),
            joinedload(KnowledgePoint.skill_points)
        )
        
        if domain_id:
            query = query.filter(KnowledgePoint.domain_id == domain_id)
        
        points = query.all()
        
        result = []
        for point in points:
            result.append({
                "id": point.id,
                "name": point.name,
                "description": point.description,
                "domain_name": point.domain.name if point.domain else "",
                "difficulty_level": point.difficulty_level,
                "exam_weight": point.exam_weight,
                "estimated_study_hours": point.estimated_study_hours,
                "prerequisites_count": len(point.prerequisites),
                "skill_points_count": len(point.skill_points)
            })
        
        return result
    except Exception as e:
        logger.error(f"获取知识点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/points/{point_id}/details")
async def get_knowledge_point_details(point_id: str, db: Session = Depends(get_db)):
    """获取知识点详细信息"""
    try:
        point = db.query(KnowledgePoint).options(
            joinedload(KnowledgePoint.domain),
            joinedload(KnowledgePoint.prerequisites),
            joinedload(KnowledgePoint.skill_points)
        ).filter(KnowledgePoint.id == point_id).first()
        
        if not point:
            raise HTTPException(status_code=404, detail="知识点不存在")
        
        # 解析学习目标JSON
        learning_objectives = []
        if point.learning_objectives:
            try:
                learning_objectives = json.loads(point.learning_objectives)
            except:
                learning_objectives = [point.learning_objectives]
        
        result = {
            "id": point.id,
            "name": point.name,
            "description": point.description,
            "domain": {
                "id": point.domain.id,
                "name": point.domain.name
            } if point.domain else None,
            "difficulty_level": point.difficulty_level,
            "exam_weight": point.exam_weight,
            "estimated_study_hours": point.estimated_study_hours,
            "learning_objectives": learning_objectives,
            "prerequisites": [
                {"id": prereq.id, "name": prereq.name}
                for prereq in point.prerequisites
            ],
            "skill_points": [
                {
                    "id": skill.id,
                    "name": skill.name,
                    "description": skill.description,
                    "skill_type": skill.skill_type
                }
                for skill in point.skill_points
            ]
        }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识点详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_knowledge_statistics(db: Session = Depends(get_db)):
    """获取知识库统计信息"""
    try:
        # 基础统计
        total_domains = db.query(KnowledgeDomain).count()
        total_knowledge_points = db.query(KnowledgePoint).count()
        total_skill_points = db.query(SkillPoint).count()
        
        # 计算总学时
        result = db.query(db.func.sum(KnowledgePoint.estimated_study_hours)).scalar()
        total_study_hours = float(result) if result else 0.0
        
        # 难度分布
        difficulty_stats = db.query(
            KnowledgePoint.difficulty_level,
            db.func.count(KnowledgePoint.id).label('count')
        ).group_by(KnowledgePoint.difficulty_level).all()
        
        difficulty_distribution = {
            f"难度{level}": count for level, count in difficulty_stats
        }
        
        # 权重分布（按知识域）
        weight_stats = db.query(
            KnowledgeDomain.name,
            db.func.sum(KnowledgePoint.exam_weight).label('total_weight')
        ).join(KnowledgePoint).group_by(KnowledgeDomain.name).all()
        
        weight_distribution = {
            name: float(weight) for name, weight in weight_stats
        }
        
        basic_statistics = {
            "total_domains": total_domains,
            "total_knowledge_points": total_knowledge_points,
            "total_skill_points": total_skill_points,
            "total_study_hours": total_study_hours,
            "days_2h_per_day": int(total_study_hours / 2) if total_study_hours > 0 else 0,
            "days_4h_per_day": int(total_study_hours / 4) if total_study_hours > 0 else 0,
            "weeks_20h_per_week": int(total_study_hours / 20) if total_study_hours > 0 else 0
        }
        
        return {
            "basic_statistics": basic_statistics,
            "difficulty_distribution": difficulty_distribution,
            "weight_distribution": weight_distribution
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph")
async def get_knowledge_graph(db: Session = Depends(get_db)):
    """获取知识图谱数据"""
    try:
        domains = db.query(KnowledgeDomain).options(
            joinedload(KnowledgeDomain.knowledge_points)
        ).all()
        
        nodes = []
        edges = []
        
        # 添加知识域节点
        for domain in domains:
            nodes.append({
                "id": f"domain_{domain.id}",
                "name": domain.name,
                "type": "domain",
                "size": len(domain.knowledge_points) * 2 + 10,
                "color": "#67C23A"
            })
            
            # 添加知识点节点
            for point in domain.knowledge_points:
                nodes.append({
                    "id": f"point_{point.id}",
                    "name": point.name,
                    "type": "knowledge_point",
                    "size": point.difficulty_level * 3 + 5,
                    "color": "#409EFF"
                })
                
                # 知识域到知识点的边
                edges.append({
                    "source": f"domain_{domain.id}",
                    "target": f"point_{point.id}",
                    "type": "contains"
                })
        
        # 添加知识点依赖关系
        points = db.query(KnowledgePoint).options(
            joinedload(KnowledgePoint.prerequisites)
        ).all()
        
        for point in points:
            for prereq in point.prerequisites:
                edges.append({
                    "source": f"point_{prereq.id}",
                    "target": f"point_{point.id}",
                    "type": "prerequisite"
                })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    except Exception as e:
        logger.error(f"获取知识图谱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/import/status")
async def get_import_status():
    """获取导入任务状态"""
    return import_status

@router.post("/import/start")
async def start_import(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """启动知识库导入任务"""
    global import_status
    
    if import_status["status"] == "running":
        raise HTTPException(status_code=400, detail="导入任务正在进行中")
    
    try:
        # 重置状态
        import_status.update({
            "status": "running",
            "progress": 0.0,
            "message": "正在初始化导入任务...",
            "details": {"domains_created": 0, "knowledge_points_created": 0, "skill_points_created": 0, "dependencies_created": 0},
            "start_time": datetime.now(),
            "error": None
        })
        
        # 启动后台任务
        background_tasks.add_task(
            run_knowledge_import,
            request.directory,
            request.force_reimport,
            request.include_case_studies,
            db
        )
        
        return JSONResponse({"message": "导入任务已启动"})
        
    except Exception as e:
        import_status.update({
            "status": "error",
            "message": f"启动导入失败: {str(e)}"
        })
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rag/process")
async def start_rag_processing(
    request: RAGProcessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """启动RAG文档处理"""
    try:
        rag_service = RAGService()
        
        # 启动后台任务
        background_tasks.add_task(
            rag_service.process_documents,
            request.mode,
            request.embedding_model,
            request.chunk_size
        )
        
        return JSONResponse({"message": "RAG处理任务已启动"})
        
    except Exception as e:
        logger.error(f"启动RAG处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 背景任务函数
async def run_knowledge_import(
    directory: str, 
    force_reimport: bool, 
    include_case_studies: bool,
    db: Session
):
    """运行知识库导入的后台任务"""
    global import_status
    
    try:
        # 检查目录是否存在
        if not os.path.exists(directory):
            # 尝试Docker容器内的替代路径
            alternative_paths = [
                "/app/data/System_Architect",
                "/app/resources",
                "/data/System_Architect"
            ]
            
            found_path = None
            for path in alternative_paths:
                if os.path.exists(path):
                    found_path = path
                    break
            
            if not found_path:
                raise FileNotFoundError(f"找不到学习资料目录: {directory}")
            
            directory = found_path
            
        import_status["message"] = f"正在扫描目录: {directory}"
        import_status["progress"] = 0.1
        
        # 创建知识提取器
        extractor = KnowledgeExtractor(db)
        
        # 设置进度回调
        def progress_callback(step: str, progress: float, details: dict = None):
            import_status.update({
                "message": step,
                "progress": progress,
                "details": details or import_status["details"]
            })
        
        # 执行导入
        await asyncio.to_thread(
            extractor.extract_from_directory,
            directory,
            force_reimport=force_reimport,
            include_case_studies=include_case_studies,
            progress_callback=progress_callback
        )
        
        import_status.update({
            "status": "completed",
            "progress": 1.0,
            "message": "知识库导入完成！"
        })
        
    except Exception as e:
        logger.error(f"导入失败: {e}")
        import_status.update({
            "status": "error",
            "message": f"导入失败: {str(e)}",
            "error": str(e)
        })

async def process_uploaded_files(
    file_paths: List[str],
    temp_dir: Path,
    db: Session
):
    """处理上传文件的后台任务"""
    try:
        # 解压缩文件（如果是压缩包）
        extracted_dir = temp_dir / "extracted"
        extracted_dir.mkdir(exist_ok=True)
        
        for file_path in file_paths:
            if file_path.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extracted_dir)
            else:
                # 复制文件到提取目录
                shutil.copy2(file_path, extracted_dir)
        
        # 使用知识提取器处理文件
        extractor = KnowledgeExtractor(db)
        await asyncio.to_thread(
            extractor.extract_from_directory,
            str(extracted_dir)
        )
        
    except Exception as e:
        logger.error(f"处理上传文件失败: {e}")
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)

@router.delete("/clear")
async def clear_knowledge_base(db: Session = Depends(get_db)):
    """清空知识库"""
    try:
        # 删除所有数据（注意依赖关系顺序）
        db.query(SkillPoint).delete()
        db.query(KnowledgePoint).delete()
        db.query(KnowledgeDomain).delete()
        db.commit()
        
        return JSONResponse({"message": "知识库已清空"})
        
    except Exception as e:
        db.rollback()
        logger.error(f"清空知识库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "import_status": import_status["status"]
    } 