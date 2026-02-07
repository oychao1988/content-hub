"""
内容审核任务执行器

负责审核内容，将审核状态设为 "approved"
"""
import time
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.services.scheduler_service import TaskExecutor, TaskExecutionResult
from app.models.content import Content
from app.utils.custom_logger import log


class ApproveExecutor(TaskExecutor):
    """
    内容审核任务执行器

    功能：
    1. 获取 content 内容
    2. 将 review_status 设为 "approved"
    3. 返回执行结果

    示例参数：
    {
        "content_id": 123
    }
    """

    @property
    def executor_type(self) -> str:
        """返回执行器类型标识"""
        return "approve"

    def validate_params(self, task_params: Dict[str, Any]) -> bool:
        """
        验证任务参数

        Args:
            task_params: 任务参数字典

        Returns:
            bool: 参数是否有效

        必需参数:
            - content_id: 内容ID（整数，大于0）
        """
        # 检查必需参数 content_id
        if "content_id" not in task_params:
            log.error("Missing required parameter: content_id")
            return False

        content_id = task_params.get("content_id")
        if not isinstance(content_id, int) or content_id <= 0:
            log.error(f"Invalid content_id: {content_id}")
            return False

        log.info(f"ApproveExecutor params validation passed: content_id={content_id}")
        return True

    async def execute(
        self,
        task_id: int,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        """
        执行内容审核任务

        Args:
            task_id: 任务ID
            task_params: 任务参数字典
            db: 数据库会话

        Returns:
            TaskExecutionResult: 任务执行结果

        执行流程:
            1. 提取任务参数
            2. 查询内容是否存在
            3. 将 review_status 设为 "approved"
            4. 返回执行结果
        """
        start_time = time.time()
        log.info(f"Executing approve task {task_id}")

        try:
            # 1. 提取任务参数
            content_id = task_params.get("content_id")

            log.info(f"Task params: content_id={content_id}")

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

            # 记录原始状态
            original_status = content.review_status

            # 3. 将 review_status 设为 "approved"
            log.info(
                f"Approving content {content_id}: "
                f"{original_status} -> approved"
            )

            content.review_status = "approved"
            db.commit()

            log.info(f"Content review status updated successfully")

            # 4. 返回执行结果
            duration = time.time() - start_time
            return TaskExecutionResult.success_result(
                message=f"Successfully approved content: {content.title}",
                data={
                    "content_id": content_id,
                    "content_title": content.title,
                    "original_status": original_status,
                    "new_status": "approved"
                },
                duration=duration,
                metadata={
                    "task_id": task_id,
                    "account_id": content.account_id,
                    "content_type": content.content_type,
                    "publish_status": content.publish_status
                }
            )

        except Exception as e:
            # 捕获所有未处理的异常
            error_msg = f"Unexpected error during approve: {str(e)}"
            log.error(error_msg)
            log.exception("Approve execution error")
            duration = time.time() - start_time
            return TaskExecutionResult.failure_result(
                message=error_msg,
                error=str(e),
                duration=duration
            )
