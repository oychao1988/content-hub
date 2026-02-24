"""
异步内容生成服务
负责提交异步生成任务、查询任务状态、管理任务生命周期（使用 HTTP API）
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    CreatorException,
    InvalidStateException,
    ResourceNotFoundException
)
from app.db.database import SessionLocal
from app.models import ContentGenerationTask, Account
from app.utils.custom_logger import log
from app.services.creator_api_client import get_creator_api_client


class AsyncContentGenerationService:
    """异步内容生成服务（使用 HTTP API）"""

    # 默认超时时间（30分钟）
    DEFAULT_TIMEOUT_MINUTES = 30

    def __init__(self, db: Optional[Session] = None):
        """
        初始化服务

        Args:
            db: 数据库会话（可选，如果未提供则创建新会话）
        """
        self.db = db or SessionLocal()
        self.api_client = get_creator_api_client()

    def submit_task(
        self,
        account_id: int,
        topic: str,
        keywords: Optional[str] = None,
        category: Optional[str] = None,
        requirements: Optional[str] = None,
        tone: Optional[str] = None,
        priority: int = 5,
        auto_approve: bool = True
    ) -> str:
        """
        提交异步生成任务

        Args:
            account_id: 账号ID
            topic: 选题
            keywords: 关键词（逗号分隔）
            category: 内容板块
            requirements: 创作要求
            tone: 语气风格
            priority: 优先级（1-10）
            auto_approve: 是否自动审核通过

        Returns:
            task_id: 任务ID

        Raises:
            ResourceNotFoundException: 账号不存在
            CreatorException: API调用失败
        """
        # 验证账号存在
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ResourceNotFoundException("账号", resource_id=str(account_id))

        # 生成任务ID
        task_id = f"task-{uuid.uuid4().hex[:12]}"

        # 创建任务记录
        task = ContentGenerationTask(
            task_id=task_id,
            account_id=account_id,
            topic=topic,
            keywords=keywords,
            category=category,
            requirements=requirements,
            tone=tone,
            status="pending",
            priority=priority,
            auto_approve=auto_approve,
            timeout_at=datetime.utcnow() + timedelta(minutes=self.DEFAULT_TIMEOUT_MINUTES)
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        log.info(f"Created async generation task: {task_id} for account {account_id}")

        # 提交任务到 content-creator HTTP API（异步模式）
        try:
            self._submit_to_creator(task)
        except Exception as e:
            # 如果提交失败，更新任务状态
            task.status = "failed"
            task.error_message = f"Failed to submit to creator: {str(e)}"
            self.db.commit()
            raise

        return task_id

    def _submit_to_creator(self, task: ContentGenerationTask):
        """
        将任务提交到 content-creator HTTP API

        Args:
            task: 任务对象

        Raises:
            CreatorException: API调用失败
        """
        # 检查 API 配置
        if not settings.CREATOR_API_BASE_URL:
            raise CreatorException("CREATOR_API_BASE_URL 未配置")

        # 处理关键词（从逗号分隔的字符串转换为列表）
        keywords_list = None
        if task.keywords:
            keywords_list = [k.strip() for k in task.keywords.split(",") if k.strip()]

        # 处理 Webhook 回调 URL
        callback_url = None
        if settings.WEBHOOK_ENABLED:
            # 构造回调 URL
            base_url = getattr(settings, 'WEBHOOK_CALLBACK_BASE_URL', None)
            if not base_url:
                # 如果没有配置 WEBHOOK_CALLBACK_BASE_URL，使用默认构造
                base_url = f"http://{settings.HOST}:{settings.PORT}"

            callback_url = f"{base_url}/api/v1/content/callback/{task.task_id}"

            # 更新任务记录
            task.callback_url = callback_url
            self.db.commit()

            log.info(f"Webhook callback enabled for task {task.task_id}: {callback_url}")
        else:
            log.info(f"Webhook callback disabled for task {task.task_id}")

        log.info(f"Submitting task to creator API: {task.task_id}")

        try:
            # 调用 HTTP API 创建异步任务
            result = self.api_client.create_task_async(
                topic=task.topic,
                task_id=task.task_id,
                requirements=task.requirements,
                tone=task.tone,
                keywords=keywords_list,
                callback_url=callback_url,
                priority=task.priority,
            )

            # 更新任务状态为已提交
            task.status = "submitted"
            task.submitted_at = datetime.utcnow()
            self.db.commit()

            log.info(f"Task {task.task_id} submitted successfully to API")

        except CreatorException as e:
            log.error(f"Failed to submit task {task.task_id}: {str(e)}")
            raise

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        查询任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字典，如果任务不存在则返回 None
        """
        task = self.db.query(ContentGenerationTask).filter_by(task_id=task_id).first()

        if not task:
            return None

        return {
            "task_id": task.task_id,
            "status": task.status,
            "account_id": task.account_id,
            "topic": task.topic,
            "priority": task.priority,
            "auto_approve": task.auto_approve,
            "callback_url": task.callback_url,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "submitted_at": task.submitted_at.isoformat() if task.submitted_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "timeout_at": task.timeout_at.isoformat() if task.timeout_at else None,
            "error": task.error_message,
            "content_id": task.content_id
        }

    def check_task_status_from_api(self, task_id: str) -> Dict[str, Any]:
        """
        从 content-creator API 查询任务最新状态

        Args:
            task_id: 任务ID

        Returns:
            API 返回的任务状态字典

        Raises:
            CreatorException: API调用失败
        """
        try:
            return self.api_client.get_task_status(task_id)
        except CreatorException as e:
            log.error(f"Failed to check task status from API: {str(e)}")
            raise

    def get_task_result_from_api(self, task_id: str) -> Dict[str, Any]:
        """
        从 content-creator API 获取任务结果

        Args:
            task_id: 任务ID

        Returns:
            API 返回的任务结果字典

        Raises:
            CreatorException: API调用失败或任务未完成
        """
        try:
            return self.api_client.get_task_result(task_id)
        except CreatorException as e:
            log.error(f"Failed to get task result from API: {str(e)}")
            raise

    def list_tasks(
        self,
        account_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ContentGenerationTask]:
        """
        列出任务

        Args:
            account_id: 账号ID（可选）
            status: 任务状态（可选）
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            任务列表
        """
        query = self.db.query(ContentGenerationTask)

        if account_id:
            query = query.filter_by(account_id=account_id)
        if status:
            query = query.filter_by(status=status)

        return query.order_by(
            ContentGenerationTask.created_at.desc()
        ).offset(offset).limit(limit).all()

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消

        Raises:
            InvalidStateException: 任务状态不允许取消
        """
        task = self.db.query(ContentGenerationTask).filter_by(task_id=task_id).first()

        if not task:
            return False

        # 只有 pending 或 submitted 状态的任务可以取消
        if task.status not in ["pending", "submitted"]:
            raise InvalidStateException(
                message=f"任务状态为 {task.status}，无法取消",
                current_state=task.status,
                required_state="pending or submitted"
            )

        try:
            # 调用 API 取消任务
            self.api_client.cancel_task(task_id)

            # 更新任务状态
            task.status = "cancelled"
            task.completed_at = datetime.utcnow()
            self.db.commit()

            log.info(f"Task {task_id} cancelled via API")

        except CreatorException as e:
            log.warning(f"Failed to cancel task via API: {str(e)}, marking as cancelled locally")
            # 即使 API 调用失败，也标记本地任务为取消状态
            task.status = "cancelled"
            task.completed_at = datetime.utcnow()
            self.db.commit()

        return True

    def retry_task(self, task_id: str) -> str:
        """
        重试失败的任务

        Args:
            task_id: 任务ID

        Returns:
            新任务ID

        Raises:
            CreatorException: 重试失败
        """
        task = self.db.query(ContentGenerationTask).filter_by(task_id=task_id).first()

        if not task:
            raise ResourceNotFoundException("任务", resource_id=task_id)

        if task.status != "failed":
            raise InvalidStateException(
                message=f"只有失败的任务可以重试，当前状态: {task.status}",
                current_state=task.status,
                required_state="failed"
            )

        try:
            # 调用 API 重试任务
            result = self.api_client.retry_task(task_id)

            # 创建新的任务记录
            new_task_id = f"task-{uuid.uuid4().hex[:12]}"
            new_task = ContentGenerationTask(
                task_id=new_task_id,
                account_id=task.account_id,
                topic=task.topic,
                keywords=task.keywords,
                category=task.category,
                requirements=task.requirements,
                tone=task.tone,
                status="submitted",
                priority=task.priority,
                auto_approve=task.auto_approve,
                retry_count=task.retry_count + 1,
                timeout_at=datetime.utcnow() + timedelta(minutes=self.DEFAULT_TIMEOUT_MINUTES)
            )

            self.db.add(new_task)
            self.db.commit()

            log.info(f"Task {task_id} retried as {new_task_id}")

            return new_task_id

        except CreatorException as e:
            log.error(f"Failed to retry task {task_id}: {str(e)}")
            raise

    def get_task_by_id(self, task_id: str) -> Optional[ContentGenerationTask]:
        """
        根据任务ID获取任务对象

        Args:
            task_id: 任务ID

        Returns:
            任务对象，不存在则返回 None
        """
        return self.db.query(ContentGenerationTask).filter_by(task_id=task_id).first()

    def update_task_status(
        self,
        task_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息（可选）

        Returns:
            是否成功更新
        """
        task = self.db.query(ContentGenerationTask).filter_by(task_id=task_id).first()

        if not task:
            return False

        task.status = status

        if status == "processing" and not task.started_at:
            task.started_at = datetime.utcnow()
        elif status in ["completed", "failed", "timeout", "cancelled"]:
            task.completed_at = datetime.utcnow()

        if error_message:
            task.error_message = error_message

        self.db.commit()

        return True

    def get_pending_tasks(self, limit: int = 100) -> List[ContentGenerationTask]:
        """
        获取待处理的任务

        Args:
            limit: 返回数量限制

        Returns:
            待处理任务列表
        """
        return self.db.query(ContentGenerationTask).filter(
            ContentGenerationTask.status == "pending"
        ).order_by(
            ContentGenerationTask.priority.desc(),
            ContentGenerationTask.created_at.asc()
        ).limit(limit).all()

    def get_running_tasks(self) -> List[ContentGenerationTask]:
        """
        获取正在运行的任务

        Returns:
            运行中任务列表
        """
        return self.db.query(ContentGenerationTask).filter(
            ContentGenerationTask.status.in_(["submitted", "processing"])
        ).all()

    def cleanup_old_tasks(self, days: int = 7) -> int:
        """
        清理旧任务记录

        Args:
            days: 保留天数

        Returns:
            清理的任务数量
        """
        from datetime import timezone

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        deleted = self.db.query(ContentGenerationTask).filter(
            ContentGenerationTask.status.in_(["completed", "failed", "cancelled", "timeout"]),
            ContentGenerationTask.completed_at < cutoff_date
        ).delete()

        self.db.commit()

        log.info(f"Cleaned up {deleted} old tasks (older than {days} days)")

        return deleted

    def close(self):
        """关闭数据库会话"""
        if self.db:
            self.db.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# 全局服务实例
def get_async_content_service() -> AsyncContentGenerationService:
    """
    获取异步内容生成服务实例（依赖注入）

    Returns:
        AsyncContentGenerationService 实例
    """
    return AsyncContentGenerationService()
