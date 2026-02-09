"""
异步内容生成服务
负责提交异步生成任务、查询任务状态、管理任务生命周期
"""
import subprocess
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    CreatorCLINotFoundException,
    CreatorException,
    InvalidStateException,
    ResourceNotFoundException
)
from app.db.database import SessionLocal
from app.models import ContentGenerationTask, Account
from app.utils.custom_logger import log


class AsyncContentGenerationService:
    """异步内容生成服务"""

    # 默认超时时间（30分钟）
    DEFAULT_TIMEOUT_MINUTES = 30

    def __init__(self, db: Optional[Session] = None):
        """
        初始化服务

        Args:
            db: 数据库会话（可选，如果未提供则创建新会话）
        """
        self.db = db or SessionLocal()

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
            CreatorException: CLI调用失败
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

        # 提交任务到 content-creator CLI（异步模式）
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
        将任务提交到 content-creator CLI

        Args:
            task: 任务对象

        Raises:
            CreatorCLINotFoundException: CLI不存在
            CreatorException: CLI调用失败
        """
        if not settings.CREATOR_CLI_PATH:
            raise CreatorCLINotFoundException("CREATOR_CLI_PATH 未配置")

        # 构建命令参数
        command = [
            settings.CREATOR_CLI_PATH,
            "create",
            "--type", "content-creator",
            "--mode", "async",  # 异步模式
            "--topic", task.topic,
            "--task-id", task.task_id
        ]

        # 可选参数
        if task.requirements:
            command.extend(["--requirements", task.requirements])
        if task.tone:
            command.extend(["--tone", task.tone])
        if task.keywords:
            command.extend(["--keywords", task.keywords])

        # 处理 Webhook 回调 URL
        if settings.WEBHOOK_ENABLED:
            # 构造回调 URL
            base_url = getattr(settings, 'WEBHOOK_CALLBACK_BASE_URL', None)
            if not base_url:
                # 如果没有配置 WEBHOOK_CALLBACK_BASE_URL，使用默认构造
                # 注意：这里使用 HOST 和 PORT，但建议在生产环境配置 WEBHOOK_CALLBACK_BASE_URL
                base_url = f"http://{settings.HOST}:{settings.PORT}"

            callback_url = f"{base_url}/api/v1/content/callback/{task.task_id}"

            # 更新任务记录
            task.callback_url = callback_url
            self.db.commit()

            # 添加到 CLI 命令
            command.extend(["--callback-url", callback_url])

            log.info(f"Webhook callback enabled for task {task.task_id}: {callback_url}")
        else:
            log.info(f"Webhook callback disabled for task {task.task_id}")

        log.info(f"Submitting task to creator: {task.task_id}")
        log.debug(f"Command arguments: {' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=30  # 提交超时30秒
            )

            # 更新任务状态为已提交
            task.status = "submitted"
            task.submitted_at = datetime.utcnow()
            self.db.commit()

            log.info(f"Task {task.task_id} submitted successfully")

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or str(e)
            log.error(f"Failed to submit task {task.task_id}: {error_msg}")
            raise CreatorException(
                message=f"提交任务到 CLI 失败: {error_msg}",
                details={"return_code": e.returncode}
            )
        except subprocess.TimeoutExpired:
            log.error(f"Timeout submitting task {task.task_id}")
            raise CreatorException(
                message="提交任务超时",
                details={"timeout": 30}
            )

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

        # 更新任务状态
        task.status = "cancelled"
        task.completed_at = datetime.utcnow()
        self.db.commit()

        log.info(f"Task {task_id} cancelled")

        return True

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
