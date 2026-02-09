"""
Webhook 处理器
负责处理来自 content-creator 的 Webhook 回调
"""
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.models import Content, ContentGenerationTask
from app.services.publish_pool_service import PublishPoolService
from app.services.task_result_handler import TaskResultHandler
from app.utils.custom_logger import log


class WebhookHandler:
    """
    Webhook 回调处理器

    处理来自 content-creator 的异步任务完成通知，包括：
    - 任务成功完成
    - 任务失败
    - 任务进度更新（可选）

    支持幂等性检查，确保同一任务的重复回调不会造成数据不一致。
    """

    # 已完成的任务状态（这些状态的任务不需要再处理）
    COMPLETED_STATUSES = ["completed", "failed", "timeout", "cancelled"]

    def __init__(self):
        """初始化 Webhook 处理器"""
        self.task_result_handler = TaskResultHandler()
        self.publish_pool_service = PublishPoolService()

    @staticmethod
    def _check_idempotency(task: ContentGenerationTask) -> Dict:
        """
        检查任务状态，确保幂等性

        Args:
            task: 任务对象

        Returns:
            检查结果字典，包含:
            - should_process: 是否应该处理该任务
            - reason: 原因说明
        """
        if task.status in WebhookHandler.COMPLETED_STATUSES:
            return {
                "should_process": False,
                "reason": f"Task already in final state: {task.status}"
            }

        return {
            "should_process": True,
            "reason": "Task is in processable state"
        }

    async def handle_task_completed(
        self,
        db: Session,
        task: ContentGenerationTask,
        result: Dict
    ) -> Dict:
        """
        处理任务完成事件

        Args:
            db: 数据库会话
            task: 任务记录
            result: 生成结果字典，包含:
                - content: 生成的内容（Markdown）
                - htmlContent: HTML 格式内容（可选）
                - images: 图片列表（可选）
                - qualityScore: 质量评分（可选）
                - wordCount: 字数统计（可选）

        Returns:
            处理结果字典，包含:
            - success: 是否处理成功
            - content_id: 创建的内容 ID（如果有）
            - message: 处理结果说明
            - skipped: 是否跳过处理（幂等性）
        """
        try:
            # 1. 幂等性检查
            idempotency_check = self._check_idempotency(task)

            if not idempotency_check["should_process"]:
                log.info(
                    f"Skipping webhook callback for task {task.task_id}: "
                    f"{idempotency_check['reason']}"
                )
                return {
                    "success": True,
                    "content_id": task.content_id,
                    "message": idempotency_check["reason"],
                    "skipped": True
                }

            log.info(f"Processing task completed webhook: {task.task_id}")

            # 2. 验证结果数据
            if not result.get("content"):
                error_msg = "Missing required field 'content' in result"
                log.error(f"Task {task.task_id}: {error_msg}")
                await self.handle_task_failed(
                    db=db,
                    task=task,
                    error={
                        "message": error_msg,
                        "code": "INVALID_RESULT",
                        "type": "ValidationError"
                    }
                )
                return {
                    "success": False,
                    "content_id": None,
                    "message": error_msg,
                    "skipped": False
                }

            # 3. 调用 TaskResultHandler 处理成功结果
            #    这会创建 Content 记录、处理自动审核和发布池
            content = self.task_result_handler.handle_success(
                db=db,
                task=task,
                result=result
            )

            if not content:
                # handle_success 内部已经处理了错误和回滚
                return {
                    "success": False,
                    "content_id": None,
                    "message": "Failed to create content record",
                    "skipped": False
                }

            # 4. 记录详细信息
            log.info(
                f"Webhook: Task {task.task_id} completed successfully. "
                f"Content ID: {content.id}, "
                f"Review Status: {content.review_status}, "
                f"Auto-approved: {task.auto_approve}"
            )

            # 5. 返回处理结果
            return {
                "success": True,
                "content_id": content.id,
                "message": "Task completed and content created",
                "skipped": False,
                "details": {
                    "review_status": content.review_status,
                    "publish_status": content.publish_status,
                    "auto_approved": task.auto_approve,
                    "word_count": content.word_count
                }
            }

        except Exception as e:
            # 捕获所有异常，确保 Webhook 端点不会崩溃
            log.error(
                f"Unexpected error handling task completed webhook {task.task_id}: {e}",
                exc_info=True
            )

            # 尝试更新任务状态为失败
            try:
                task.status = "failed"
                task.completed_at = datetime.utcnow()
                task.error_message = f"Webhook handling error: {str(e)}"
                db.commit()
            except Exception as commit_error:
                log.error(f"Failed to update task status after webhook error: {commit_error}")
                db.rollback()

            return {
                "success": False,
                "content_id": None,
                "message": f"Internal error: {str(e)}",
                "skipped": False
            }

    async def handle_task_failed(
        self,
        db: Session,
        task: ContentGenerationTask,
        error: Dict
    ) -> Dict:
        """
        处理任务失败事件

        Args:
            db: 数据库会话
            task: 任务记录
            error: 错误信息字典，包含:
                - message: 错误消息
                - code: 错误代码（可选）
                - type: 错误类型（可选）

        Returns:
            处理结果字典，包含:
            - success: 是否处理成功
            - retry_scheduled: 是否安排了重试
            - message: 处理结果说明
            - skipped: 是否跳过处理（幂等性）
        """
        try:
            # 1. 幂等性检查
            idempotency_check = self._check_idempotency(task)

            if not idempotency_check["should_process"]:
                log.info(
                    f"Skipping webhook callback for task {task.task_id}: "
                    f"{idempotency_check['reason']}"
                )
                return {
                    "success": True,
                    "retry_scheduled": False,
                    "message": idempotency_check["reason"],
                    "skipped": True
                }

            log.warning(
                f"Processing task failed webhook: {task.task_id}, "
                f"error: {error.get('message', 'Unknown error')}"
            )

            # 2. 解析错误信息
            error_message = error.get("message", "Unknown error")
            error_code = error.get("code", "UNKNOWN")
            error_type = error.get("type", "GeneralError")

            full_error_message = f"[{error_code}] {error_type}: {error_message}"

            # 3. 调用 TaskResultHandler 处理失败结果
            self.task_result_handler.handle_failure(
                db=db,
                task=task,
                error_message=full_error_message
            )

            # 4. 检查是否可以重试
            retry_scheduled = False

            if task.retry_count < task.max_retries:
                log.info(
                    f"Task {task.task_id} failed, scheduling retry "
                    f"({task.retry_count + 1}/{task.max_retries})"
                )

                # 调用重试逻辑
                retry_scheduled = self.task_result_handler.retry_task(db=db, task=task)

                if retry_scheduled:
                    log.info(f"Task {task.task_id} has been scheduled for retry")
                else:
                    log.warning(f"Failed to schedule retry for task {task.task_id}")
            else:
                log.warning(
                    f"Task {task.task_id} reached max retries ({task.max_retries}), "
                    f"not retrying"
                )

            # 5. 返回处理结果
            return {
                "success": True,
                "retry_scheduled": retry_scheduled,
                "message": full_error_message,
                "skipped": False,
                "details": {
                    "error_code": error_code,
                    "error_type": error_type,
                    "retry_count": task.retry_count,
                    "max_retries": task.max_retries
                }
            }

        except Exception as e:
            # 捕获所有异常，确保 Webhook 端点不会崩溃
            log.error(
                f"Unexpected error handling task failed webhook {task.task_id}: {e}",
                exc_info=True
            )

            # 尝试记录错误
            try:
                task.status = "failed"
                task.completed_at = datetime.utcnow()
                task.error_message = f"Webhook handling error: {str(e)}"
                db.commit()
            except Exception as commit_error:
                log.error(f"Failed to update task status after webhook error: {commit_error}")
                db.rollback()

            return {
                "success": False,
                "retry_scheduled": False,
                "message": f"Internal error: {str(e)}",
                "skipped": False
            }

    async def handle_task_progress(
        self,
        db: Session,
        task: ContentGenerationTask,
        progress: Dict
    ) -> Dict:
        """
        处理任务进度更新事件（可选）

        Args:
            db: 数据库会话
            task: 任务记录
            progress: 进度信息字典，包含:
                - percentage: 完成百分比（0-100）
                - message: 进度消息（可选）
                - stage: 当前阶段（可选）

        Returns:
            处理结果字典，包含:
            - success: 是否处理成功
            - message: 处理结果说明
        """
        try:
            # 1. 检查任务状态（进度更新只能在处理中状态）
            if task.status not in ["submitted", "processing"]:
                log.warning(
                    f"Received progress update for task {task.task_id} "
                    f"in invalid state: {task.status}"
                )
                return {
                    "success": False,
                    "message": f"Cannot update progress for task in state: {task.status}"
                }

            # 2. 提取进度信息
            percentage = progress.get("percentage", 0)
            message = progress.get("message", "")
            stage = progress.get("stage", "")

            # 3. 更新任务状态（如果是第一次收到进度，标记为 processing）
            if task.status == "submitted":
                task.status = "processing"
                if not task.started_at:
                    task.started_at = datetime.utcnow()

            # 4. 记录进度信息（存储在 result 字段的 progress 子对象中）
            if not task.result:
                task.result = {}

            task.result["progress"] = {
                "percentage": percentage,
                "message": message,
                "stage": stage,
                "updated_at": datetime.utcnow().isoformat()
            }

            db.commit()

            # 5. 记录日志
            log.info(
                f"Task {task.task_id} progress: {percentage}%"
                f"{f' - {stage}' if stage else ''}"
                f"{f' - {message}' if message else ''}"
            )

            return {
                "success": True,
                "message": "Progress updated",
                "details": {
                    "percentage": percentage,
                    "stage": stage,
                    "message": message
                }
            }

        except Exception as e:
            log.error(
                f"Error handling task progress webhook {task.task_id}: {e}",
                exc_info=True
            )
            db.rollback()

            return {
                "success": False,
                "message": f"Internal error: {str(e)}"
            }


# 全局服务实例
def get_webhook_handler() -> WebhookHandler:
    """
    获取 Webhook 处理器实例（依赖注入）

    Returns:
        WebhookHandler 实例
    """
    return WebhookHandler()
