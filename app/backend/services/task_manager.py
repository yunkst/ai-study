"""
任务管理系统 - 后台任务执行、进度追踪和错误处理
"""

import asyncio
import threading
import time
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, PriorityQueue
import traceback

from sqlalchemy.orm import Session
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    warnings: List[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

@dataclass
class TaskProgress:
    """任务进度信息"""
    current_step: int = 0
    total_steps: int = 100
    percentage: float = 0.0
    message: str = ""
    details: Dict[str, Any] = None
    
    def update(self, current: int = None, total: int = None, message: str = None, **details):
        """更新进度"""
        if current is not None:
            self.current_step = current
        if total is not None:
            self.total_steps = total
        if message is not None:
            self.message = message
        if details:
            if self.details is None:
                self.details = {}
            self.details.update(details)
        
        if self.total_steps > 0:
            self.percentage = min(100.0, (self.current_step / self.total_steps) * 100)

@dataclass
class Task:
    """任务定义"""
    id: str
    name: str
    task_type: str
    function: Callable
    parameters: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    progress: TaskProgress = None
    result: Optional[TaskResult] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: Optional[int] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.progress is None:
            self.progress = TaskProgress()
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.dependencies is None:
            self.dependencies = []

class TaskManager:
    """任务管理器"""
    
    def __init__(self, max_workers: int = 4, db_session: Session = None):
        self.max_workers = max_workers
        self.db_session = db_session
        
        # 任务存储
        self.tasks: Dict[str, Task] = {}
        self.task_queue = PriorityQueue()
        self.running_tasks: Dict[str, threading.Thread] = {}
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 事件和锁
        self.shutdown_event = threading.Event()
        self.tasks_lock = threading.Lock()
        
        # 进度回调
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        
        # 启动任务调度器
        self.scheduler_thread = threading.Thread(target=self._task_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"任务管理器启动，最大工作线程数: {max_workers}")
    
    def create_task(self, name: str, task_type: str, function: Callable,
                   parameters: Dict[str, Any], priority: TaskPriority = TaskPriority.NORMAL,
                   created_by: str = None, timeout_seconds: int = None,
                   dependencies: List[str] = None) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            name=name,
            task_type=task_type,
            function=function,
            parameters=parameters,
            priority=priority,
            created_by=created_by,
            timeout_seconds=timeout_seconds,
            dependencies=dependencies or []
        )
        
        with self.tasks_lock:
            self.tasks[task_id] = task
            
            # 检查依赖是否满足
            if self._check_dependencies_completed(task):
                self.task_queue.put((priority.value * -1, time.time(), task_id))  # 负数实现高优先级
                task.status = TaskStatus.PENDING
            else:
                task.status = TaskStatus.PENDING  # 等待依赖完成
        
        # 持久化到数据库
        self._persist_task(task)
        
        logger.info(f"创建任务: {name} (ID: {task_id})")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        with self.tasks_lock:
            return self.tasks.get(task_id)
    
    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """获取任务进度"""
        task = self.get_task(task_id)
        return task.progress if task else None
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        task = self.get_task(task_id)
        return task.status if task else None
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self.tasks_lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            if task.status in [TaskStatus.PENDING]:
                task.status = TaskStatus.CANCELLED
                self._persist_task(task)
                logger.info(f"任务已取消: {task.name}")
                return True
            elif task.status == TaskStatus.RUNNING:
                # 标记为取消，由执行线程检查
                task.status = TaskStatus.CANCELLED
                self._persist_task(task)
                logger.info(f"运行中任务已标记取消: {task.name}")
                return True
            
            return False
    
    def retry_task(self, task_id: str) -> bool:
        """重试失败的任务"""
        with self.tasks_lock:
            task = self.tasks.get(task_id)
            if not task or task.status != TaskStatus.FAILED:
                return False
            
            if task.retry_count >= task.max_retries:
                logger.warning(f"任务重试次数已达上限: {task.name}")
                return False
            
            # 重置任务状态
            task.status = TaskStatus.PENDING
            task.result = None
            task.progress = TaskProgress()
            task.retry_count += 1
            
            # 重新加入队列
            self.task_queue.put((task.priority.value * -1, time.time(), task_id))
            
            self._persist_task(task)
            logger.info(f"任务重试: {task.name} (第{task.retry_count}次)")
            return True
    
    def add_progress_callback(self, task_id: str, callback: Callable[[TaskProgress], None]):
        """添加进度回调"""
        if task_id not in self.progress_callbacks:
            self.progress_callbacks[task_id] = []
        self.progress_callbacks[task_id].append(callback)
    
    def remove_progress_callback(self, task_id: str, callback: Callable = None):
        """移除进度回调"""
        if task_id in self.progress_callbacks:
            if callback:
                try:
                    self.progress_callbacks[task_id].remove(callback)
                except ValueError:
                    pass
            else:
                self.progress_callbacks[task_id].clear()
    
    def list_tasks(self, status: Optional[TaskStatus] = None, 
                  task_type: Optional[str] = None,
                  created_by: Optional[str] = None,
                  limit: int = 100) -> List[Task]:
        """列出任务"""
        with self.tasks_lock:
            tasks = list(self.tasks.values())
        
        # 过滤
        if status:
            tasks = [t for t in tasks if t.status == status]
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        if created_by:
            tasks = [t for t in tasks if t.created_by == created_by]
        
        # 按创建时间排序
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        with self.tasks_lock:
            tasks = list(self.tasks.values())
        
        stats = {
            'total_tasks': len(tasks),
            'by_status': {},
            'by_type': {},
            'running_tasks': len(self.running_tasks),
            'queue_size': self.task_queue.qsize(),
            'average_execution_time': 0.0,
            'success_rate': 0.0
        }
        
        # 按状态统计
        for status in TaskStatus:
            count = len([t for t in tasks if t.status == status])
            stats['by_status'][status.value] = count
        
        # 按类型统计
        type_counts = {}
        for task in tasks:
            type_counts[task.task_type] = type_counts.get(task.task_type, 0) + 1
        stats['by_type'] = type_counts
        
        # 执行时间和成功率
        completed_tasks = [t for t in tasks if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]]
        if completed_tasks:
            successful_tasks = [t for t in completed_tasks if t.status == TaskStatus.COMPLETED]
            stats['success_rate'] = len(successful_tasks) / len(completed_tasks) * 100
            
            # 平均执行时间
            execution_times = []
            for task in successful_tasks:
                if task.started_at and task.completed_at:
                    duration = (task.completed_at - task.started_at).total_seconds()
                    execution_times.append(duration)
            
            if execution_times:
                stats['average_execution_time'] = sum(execution_times) / len(execution_times)
        
        return stats
    
    def shutdown(self, wait_for_completion: bool = True, timeout: int = 30):
        """关闭任务管理器"""
        logger.info("正在关闭任务管理器...")
        
        self.shutdown_event.set()
        
        if wait_for_completion:
            # 等待运行中的任务完成
            start_time = time.time()
            while self.running_tasks and (time.time() - start_time) < timeout:
                time.sleep(1)
        
        # 关闭线程池
        self.executor.shutdown(wait=wait_for_completion)
        
        # 等待调度器线程结束
        if self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("任务管理器已关闭")
    
    def _task_scheduler(self):
        """任务调度器（后台线程）"""
        while not self.shutdown_event.is_set():
            try:
                # 检查是否有可用的工作线程
                if len(self.running_tasks) >= self.max_workers:
                    time.sleep(1)
                    continue
                
                # 从队列获取任务
                try:
                    priority, timestamp, task_id = self.task_queue.get(timeout=1)
                except:
                    continue
                
                with self.tasks_lock:
                    task = self.tasks.get(task_id)
                    if not task or task.status != TaskStatus.PENDING:
                        continue
                    
                    # 再次检查依赖
                    if not self._check_dependencies_completed(task):
                        # 重新入队等待
                        self.task_queue.put((priority, timestamp, task_id))
                        continue
                    
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.now()
                
                # 提交任务到线程池
                future = self.executor.submit(self._execute_task, task)
                self.running_tasks[task_id] = future
                
                logger.info(f"任务开始执行: {task.name}")
                
            except Exception as e:
                logger.error(f"任务调度器错误: {e}")
                time.sleep(1)
    
    def _execute_task(self, task: Task):
        """执行任务"""
        try:
            # 创建进度更新回调
            def update_progress(current=None, total=None, message=None, **details):
                task.progress.update(current, total, message, **details)
                self._notify_progress_callbacks(task.id, task.progress)
                
                # 检查是否被取消
                if task.status == TaskStatus.CANCELLED:
                    raise InterruptedError("任务已被取消")
            
            # 准备参数
            task_params = task.parameters.copy()
            task_params['progress_callback'] = update_progress
            
            # 执行任务
            start_time = time.time()
            
            # 设置超时
            if task.timeout_seconds:
                import signal
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"任务执行超时 ({task.timeout_seconds}秒)")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(task.timeout_seconds)
            
            try:
                # 调用任务函数
                if asyncio.iscoroutinefunction(task.function):
                    # 异步函数
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(task.function(**task_params))
                    loop.close()
                else:
                    # 同步函数
                    result = task.function(**task_params)
                
                execution_time = time.time() - start_time
                
                # 创建成功结果
                task.result = TaskResult(
                    success=True,
                    data=result,
                    execution_time=execution_time
                )
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.progress.update(current=task.progress.total_steps, message="任务完成")
                
                logger.info(f"任务执行成功: {task.name} (耗时: {execution_time:.2f}秒)")
                
            finally:
                if task.timeout_seconds:
                    signal.alarm(0)  # 取消超时
            
        except InterruptedError as e:
            # 任务被取消
            task.result = TaskResult(success=False, error=str(e))
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            logger.info(f"任务被取消: {task.name}")
            
        except Exception as e:
            # 任务执行失败
            error_msg = f"{type(e).__name__}: {str(e)}"
            task.result = TaskResult(
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time
            )
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            
            logger.error(f"任务执行失败: {task.name} - {error_msg}")
            logger.debug(traceback.format_exc())
        
        finally:
            # 从运行任务列表移除
            with self.tasks_lock:
                self.running_tasks.pop(task.id, None)
            
            # 持久化结果
            self._persist_task(task)
            
            # 检查依赖此任务的其他任务
            self._check_dependent_tasks(task.id)
            
            # 最终进度通知
            self._notify_progress_callbacks(task.id, task.progress)
    
    def _check_dependencies_completed(self, task: Task) -> bool:
        """检查任务依赖是否都已完成"""
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def _check_dependent_tasks(self, completed_task_id: str):
        """检查依赖已完成任务的其他任务"""
        with self.tasks_lock:
            for task in self.tasks.values():
                if (task.status == TaskStatus.PENDING and 
                    completed_task_id in task.dependencies and
                    self._check_dependencies_completed(task)):
                    
                    # 将任务加入队列
                    self.task_queue.put((task.priority.value * -1, time.time(), task.id))
    
    def _notify_progress_callbacks(self, task_id: str, progress: TaskProgress):
        """通知进度回调"""
        callbacks = self.progress_callbacks.get(task_id, [])
        for callback in callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"进度回调执行失败: {e}")
    
    def _persist_task(self, task: Task):
        """持久化任务到数据库"""
        if not self.db_session:
            return
        
        try:
            from models.knowledge import ImportTask
            
            # 查找已存在的记录
            db_task = self.db_session.query(ImportTask).filter(
                ImportTask.id == task.id
            ).first()
            
            task_data = {
                'task_name': task.name,
                'task_type': task.task_type,
                'status': task.status.value,
                'progress': task.progress.percentage,
                'message': task.progress.message,
                'parameters': json.dumps(task.parameters),
                'created_by': task.created_by,
                'started_at': task.started_at,
                'completed_at': task.completed_at,
                'updated_at': datetime.now()
            }
            
            if task.result:
                task_data.update({
                    'result_summary': json.dumps(asdict(task.result)),
                    'error_details': task.result.error
                })
            
            if db_task:
                # 更新现有记录
                for key, value in task_data.items():
                    setattr(db_task, key, value)
            else:
                # 创建新记录
                task_data['id'] = task.id
                task_data['created_at'] = task.created_at
                db_task = ImportTask(**task_data)
                self.db_session.add(db_task)
            
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"任务持久化失败: {e}")
            if self.db_session:
                self.db_session.rollback()

# 全局任务管理器实例
task_manager: Optional[TaskManager] = None

def get_task_manager() -> TaskManager:
    """获取全局任务管理器实例"""
    global task_manager
    if task_manager is None:
        task_manager = TaskManager()
    return task_manager

def initialize_task_manager(max_workers: int = 4, db_session: Session = None):
    """初始化任务管理器"""
    global task_manager
    if task_manager:
        task_manager.shutdown()
    task_manager = TaskManager(max_workers=max_workers, db_session=db_session)
    return task_manager

def shutdown_task_manager():
    """关闭任务管理器"""
    global task_manager
    if task_manager:
        task_manager.shutdown()
        task_manager = None 