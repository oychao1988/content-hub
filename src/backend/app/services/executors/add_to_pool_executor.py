"""
加入发布池任务执行器

负责将内容加入发布池，支持自动审核
"""
import time
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.scheduler_service import TaskExecutor, TaskExecutionResult
from app.services.publish_pool_service import publish_pool_service
from app.models.content import Content
from app.utils.custom_logger import log


class AddToPoolExecutor(TaskExecutor):
    """
    加入发布池任务执行器

    功能：
    1. 获取 content 内容
    2. 如果 auto_approve=true，将 review_status 设为 "approved"
    3. 调用 publish_pool_service.add_to_pool() 加入发布池
    4. 返回包含 pool_id 的执行结果

    示例参数：
    {
        "content_id": 123,
        "priority": 5,
        "scheduled_at": "2024-01-01 12:00:00",
        "auto_approve": true
    }
    """

    @property
    def executor_type(self) -> str:
        """返回执行器类型标识"""
        return "add_to_pool"

    def validate_params(self, task_params: Dict[str, Any]) -> bool:
        """
        验证任务参数

        Args:
            task_params: 任务参数字典

        Returns:
            bool: 参数是否有效

        必需参数:
            - content_id: 内容ID（整数，大于0）

        可选参数:
            - priority: 优先级（1-10，默认5）
            - scheduled_at: 计划发布时间（ISO格式字符串）
            - auto_approve: 是否自动审核（布尔值，默认false）
        """
        # 检查必需参数 content_id
        if "content_id" not in task_params:
            log.error("Missing required parameter: content_id")
            return False

        content_id = task_params.get("content_id")
        if not isinstance(content_id, int) or content_id <= 0:
            log.error(f"Invalid content_id: {content_id}")
            return False

        # 验证可选参数 priority（如果提供）
        priority = task_params.get("priority")
        if priority is not None:
            if not isinstance(priority, int) or priority < 1 or priority > 10:
                log.error(f"Invalid priority: {priority} (must be 1-10)")
                return False

        # 验证可选参数 auto_approve（如果提供）
        auto_approve = task_params.get("auto_approve")
        if auto_approve is not None and not isinstance(auto_approve, bool):
            log.error(f"Invalid auto_approve: {auto_approve} (must be boolean)")
            return False

        log.info(
            f"AddToPoolExecutor params validation passed: "
            f"content_id={content_id}, priority={priority}, auto_approve={auto_approve}"
        )
        return True

    async def execute(
        self,
        task_id: int,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        """
        执行加入发布池任务

        Args:
            task_id: 任务ID
            task_params: 任务参数字典
            db: 数据库会话

        Returns:
            TaskExecutionResult: 任务执行结果

        执行流程:
            1. 提取任务参数
            2. 查询内容是否存在
            3. 如果 auto_approve=true，自动审核通过
            4. 调用 publish_pool_service.add_to_pool() 加入发布池
            5. 返回执行结果（包含 pool_id）
        """
        start_time = time.time()
        log.info(f"Executing add_to_pool task {task_id}")

        try:
            # 1. 提取任务参数
            content_id = task_params.get("content_id")
            priority = task_params.get("priority", 5)
            scheduled_at = task_params.get("scheduled_at")
            auto_approve = task_params.get("auto_approve", False)

            log.info(
                f"Task params: content_id={content_id}, priority={priority}, "
                f"scheduled_at={scheduled_at}, auto_approve={auto_approve}"
            )

            # 2. 查询内容是否存在
            content = db.query(Content).filter(Content.id == content_id).first()

            if not content:
                error_msg = f"Content not found (ID: {content_id})"
                log.error(error_msg)
                duration = time.time() - start_time
                return TaskExecutionResult.failure_result(
                    message=error_msg,
                    error="ContentNotFound",
                    duration=duration
                )

            log.info(f"Found content: id={content.id}, title={content.title}")

            # 3. 如果 auto_approve=true，自动审核通过
            if auto_approve:
                log.info(f"Auto-approving content {content_id}")
                original_status = content.review_status

                content.review_status = "approved"
                db.commit()

                log.info(
                    f"Content review status updated: {original_status} -> approved"
                )

            # 解析 scheduled_at（如果提供）
            scheduled_at_dt = None
            if scheduled_at:
                try:
                    if isinstance(scheduled_at, str):
                        scheduled_at_dt = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
                    elif isinstance(scheduled_at, datetime):
                        scheduled_at_dt = scheduled_at
                    log.info(f"Scheduled publish time: {scheduled_at_dt}")
                except Exception as e:
                    log.warning(f"Failed to parse scheduled_at '{scheduled_at}': {str(e)}, using current time")
                    scheduled_at_dt = None

            # 4. 加入发布池
            log.info(
                f"Adding content {content_id} to publish pool "
                f"(priority={priority}, scheduled_at={scheduled_at_dt or 'now'})"
            )

            try:
                pool_entry = publish_pool_service.add_to_pool(
                    db,
                    content_id,
                    priority,
                    scheduled_at_dt
                )
                log.info(f"Content added to pool: pool_id={pool_entry.id}")
            except Exception as e:
                error_msg = f"Failed to add content to publish pool: {str(e)}"
                log.error(error_msg)
                log.exception("Publish pool service error")
                duration = time.time() - start_time
                return TaskExecutionResult.failure_result(
                    message=error_msg,
                    error=str(e),
                    duration=duration
                )

            # 5. 返回执行结果
            duration = time.time() - start_time
            return TaskExecutionResult.success_result(
                message=f"Successfully added content to publish pool: {content.title}",
                data={
                    "pool_id": pool_entry.id,
                    "content_id": content_id,
                    "content_title": content.title,
                    "priority": priority,
                    "scheduled_at": scheduled_at_dt.isoformat() if scheduled_at_dt else None,
                    "auto_approved": auto_approve
                },
                duration=duration,
                metadata={
                    "task_id": task_id,
                    "account_id": content.account_id,
                    "review_status": content.review_status
                }
            )

        except Exception as e:
            # 捕获所有未处理的异常
            error_msg = f"Unexpected error during add_to_pool: {str(e)}"
            log.error(error_msg)
            log.exception("AddToPool execution error")
            duration = time.time() - start_time
            return TaskExecutionResult.failure_result(
                message=error_msg,
                error=str(e),
                duration=duration
            )
