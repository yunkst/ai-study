"""
播客相关API路由
"""

from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pydantic import root_validator
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import os
import asyncio
import uuid

from core.database import get_db
from models.podcast import Podcast, PodcastStatus, PodcastStyle
from services.tts_service import tts_service
from services.ai_service import ai_service
from services.task_manager import task_manager

router = APIRouter()

class PodcastEpisode(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    duration: Optional[int] = None  # 秒
    file_url: Optional[str] = None
    knowledge_points: List[str]
    topics: List[str]
    style: str
    status: str  # generating, ready, error
    created_at: str
    completed_at: Optional[str] = None
    listen_count: int = 0
    generation_progress: float = 0.0
    error_message: Optional[str] = None

class PodcastRequest(BaseModel):
    # 兼容前端只传递单个 topic 的场景
    topic: Optional[str] = None
    topics: Optional[List[str]] = None
    duration_minutes: int = 15
    style: str = "conversation"  # conversation, lecture, qa
    title: Optional[str] = None
    description: Optional[str] = None

    @root_validator(pre=True)
    def _normalize_topics(cls, values):
        """确保 topics 字段存在。若仅提供 topic，则转换为列表"""
        single_topic = values.get("topic")
        topics = values.get("topics")
        if not topics and single_topic:
            values["topics"] = [single_topic]
        return values

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: float
    message: Optional[str] = None
    podcast_id: Optional[int] = None

async def get_user_id(request: Request) -> int:
    """从请求中获取用户ID"""
    return 1

def _convert_podcast_to_response(podcast: Podcast, base_url: str = "") -> PodcastEpisode:
    """转换播客模型为响应格式"""
    file_url = None
    if podcast.audio_file_path and podcast.status == PodcastStatus.READY:
        file_url = f"{base_url}/api/podcast/files/{podcast.id}"
    
    return PodcastEpisode(
        id=podcast.id,
        title=podcast.title,
        description=podcast.description,
        duration=podcast.duration_seconds,
        file_url=file_url,
        knowledge_points=podcast.knowledge_points or [],
        topics=podcast.topics or [],
        style=podcast.style.value,
        status=podcast.status.value,
        created_at=podcast.created_at.isoformat(),
        completed_at=podcast.completed_at.isoformat() if podcast.completed_at else None,
        listen_count=podcast.listen_count,
        generation_progress=podcast.generation_progress,
        error_message=podcast.error_message
    )

@router.get("/episodes", response_model=List[PodcastEpisode])
async def get_episodes(
    request: Request,
    limit: int = Query(20, description="返回数量限制"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(get_db)
):
    """获取播客列表"""
    try:
        query = db.query(Podcast)
        
        # 状态筛选
        if status:
            try:
                status_enum = PodcastStatus(status)
                query = query.filter(Podcast.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的状态: {status}")
        
        podcasts = query.order_by(Podcast.created_at.desc()).limit(limit).all()
        
        # 构建基础URL
        base_url = str(request.base_url).rstrip('/')
        
        return [_convert_podcast_to_response(podcast, base_url) for podcast in podcasts]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取播客列表失败: {str(e)}")

@router.get("/episodes/{episode_id}", response_model=PodcastEpisode)
async def get_episode(
    episode_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """获取单个播客详情"""
    try:
        podcast = db.query(Podcast).filter(Podcast.id == episode_id).first()
        
        if not podcast:
            raise HTTPException(status_code=404, detail="播客未找到")
        
        # 增加监听计数
        podcast.listen_count += 1
        db.commit()
        
        base_url = str(request.base_url).rstrip('/')
        return _convert_podcast_to_response(podcast, base_url)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取播客详情失败: {str(e)}")

async def _generate_podcast_background(
    podcast_id: int,
    topics: List[str],
    duration_minutes: int,
    style: str,
    db_session_factory
):
    """后台播客生成任务"""
    db = db_session_factory()
    
    try:
        # 获取播客记录
        podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
        if not podcast:
            return
        
        # 更新状态为生成中
        podcast.status = PodcastStatus.GENERATING
        podcast.generation_progress = 0.1
        db.commit()
        
        # 生成脚本
        print(f"🎙️ 开始生成播客脚本: {topics}")
        script = await ai_service.generate_podcast_script(
            topics=topics,
            duration_minutes=duration_minutes,
            style=style
        )
        
        if not script:
            raise Exception("脚本生成失败")
        
        podcast.script_content = str(script)
        podcast.generation_progress = 0.5
        db.commit()
        
        # 生成音频
        print(f"🔊 开始生成播客音频")
        audio_file = await tts_service.synthesize_podcast(script, f"podcast_{podcast_id}.mp3")
        
        if not audio_file:
            raise Exception("音频生成失败")
        
        # 获取文件信息
        if os.path.exists(audio_file):
            file_size = os.path.getsize(audio_file)
            # 估算音频时长（假设128kbps MP3）
            duration_seconds = int(file_size * 8 / (128 * 1000))
        else:
            raise Exception("音频文件生成失败")
        
        # 更新播客信息
        podcast.audio_file_path = audio_file
        podcast.file_size_bytes = file_size
        podcast.duration_seconds = duration_seconds
        podcast.status = PodcastStatus.READY
        podcast.generation_progress = 1.0
        podcast.completed_at = datetime.now()
        podcast.error_message = None
        
        db.commit()
        
        print(f"✅ 播客生成完成: {podcast.title}")
        
    except Exception as e:
        print(f"❌ 播客生成失败: {e}")
        
        # 更新错误状态
        if podcast:
            podcast.status = PodcastStatus.ERROR
            podcast.error_message = str(e)
            db.commit()
    
    finally:
        db.close()

@router.post("/generate")
async def generate_podcast(
    request: Request,
    podcast_request: PodcastRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """生成个性化播客"""
    try:
        # 验证输入
        if not podcast_request.topics:
            raise HTTPException(status_code=400, detail="主题列表不能为空")
        
        if podcast_request.duration_minutes < 1 or podcast_request.duration_minutes > 60:
            raise HTTPException(status_code=400, detail="时长必须在1-60分钟之间")
        
        # 验证风格
        try:
            style_enum = PodcastStyle(podcast_request.style)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的播客风格: {podcast_request.style}")
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 生成标题
        title = podcast_request.title
        if not title:
            title = f"{', '.join(podcast_request.topics[:2])} - 播客"
            if len(podcast_request.topics) > 2:
                title += f"等{len(podcast_request.topics)}个主题"
        
        # 创建播客记录
        podcast = Podcast(
            title=title,
            description=podcast_request.description,
            topics=podcast_request.topics,
            style=style_enum,
            task_id=task_id,
            status=PodcastStatus.GENERATING,
            generation_progress=0.0
        )
        
        db.add(podcast)
        db.commit()
        db.refresh(podcast)
        
        # 提交后台任务
        background_tasks.add_task(
            _generate_podcast_background,
            podcast.id,
            podcast_request.topics,
            podcast_request.duration_minutes,
            podcast_request.style,
            lambda: db.__class__(bind=db.bind)
        )
        
        return {
            "message": "播客生成任务已启动",
            "task_id": task_id,
            "podcast_id": podcast.id,
            "estimated_time": f"{podcast_request.duration_minutes * 2}-{podcast_request.duration_minutes * 3}分钟",
            "status_endpoint": f"/api/podcast/tasks/{task_id}"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"启动播客生成失败: {str(e)}")

@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_generation_status(
    task_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """获取生成任务状态"""
    try:
        podcast = db.query(Podcast).filter(Podcast.task_id == task_id).first()
        
        if not podcast:
            raise HTTPException(status_code=404, detail="任务未找到")
        
        # 映射状态
        status_map = {
            PodcastStatus.GENERATING: "processing",
            PodcastStatus.READY: "completed",
            PodcastStatus.ERROR: "failed"
        }
        
        status = status_map.get(podcast.status, "unknown")
        message = None
        
        if podcast.status == PodcastStatus.ERROR:
            message = podcast.error_message
        elif podcast.status == PodcastStatus.GENERATING:
            if podcast.generation_progress < 0.5:
                message = "正在生成脚本..."
            else:
                message = "正在合成音频..."
        elif podcast.status == PodcastStatus.READY:
            message = "播客生成完成"
        
        return TaskStatus(
            task_id=task_id,
            status=status,
            progress=podcast.generation_progress,
            message=message,
            podcast_id=podcast.id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")

@router.get("/files/{episode_id}")
async def download_podcast(
    episode_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """下载播客文件"""
    try:
        podcast = db.query(Podcast).filter(Podcast.id == episode_id).first()
        
        if not podcast:
            raise HTTPException(status_code=404, detail="播客未找到")
        
        if podcast.status != PodcastStatus.READY or not podcast.audio_file_path:
            raise HTTPException(status_code=400, detail="播客文件不可用")
        
        if not os.path.exists(podcast.audio_file_path):
            raise HTTPException(status_code=404, detail="播客文件不存在")
        
        # 增加下载计数
        podcast.listen_count += 1
        db.commit()
        
        # 生成安全的文件名
        safe_title = "".join(c for c in podcast.title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_title}.mp3"
        
        return FileResponse(
            path=podcast.audio_file_path,
            filename=filename,
            media_type="audio/mpeg"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载播客失败: {str(e)}")

@router.delete("/episodes/{episode_id}")
async def delete_episode(
    episode_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """删除播客"""
    try:
        podcast = db.query(Podcast).filter(Podcast.id == episode_id).first()
        
        if not podcast:
            raise HTTPException(status_code=404, detail="播客未找到")
        
        # 删除音频文件
        if podcast.audio_file_path and os.path.exists(podcast.audio_file_path):
            try:
                os.remove(podcast.audio_file_path)
            except:
                pass  # 文件删除失败不影响数据库删除
        
        db.delete(podcast)
        db.commit()
        
        return {"message": "播客删除成功"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除播客失败: {str(e)}")

@router.get("/stats/overview")
async def get_podcast_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取播客统计信息"""
    try:
        # 总播客数
        total_podcasts = db.query(Podcast).count()
        
        # 按状态统计
        ready_count = db.query(Podcast).filter(Podcast.status == PodcastStatus.READY).count()
        generating_count = db.query(Podcast).filter(Podcast.status == PodcastStatus.GENERATING).count()
        error_count = db.query(Podcast).filter(Podcast.status == PodcastStatus.ERROR).count()
        
        # 总监听次数
        total_listens = db.query(Podcast).with_entities(
            db.func.sum(Podcast.listen_count)
        ).scalar() or 0
        
        # 总时长（秒）
        total_duration = db.query(Podcast).filter(
            Podcast.duration_seconds.isnot(None)
        ).with_entities(
            db.func.sum(Podcast.duration_seconds)
        ).scalar() or 0
        
        # 热门主题
        all_podcasts = db.query(Podcast).filter(Podcast.topics.isnot(None)).all()
        topic_counts = {}
        for podcast in all_podcasts:
            if podcast.topics:
                for topic in podcast.topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # 取前10个最热门的主题
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_podcasts": total_podcasts,
            "status_breakdown": {
                "ready": ready_count,
                "generating": generating_count,
                "error": error_count
            },
            "total_listens": total_listens,
            "total_duration_minutes": total_duration // 60,
            "top_topics": dict(top_topics),
            "average_listens": total_listens / total_podcasts if total_podcasts > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}") 