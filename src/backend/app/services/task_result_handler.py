"""
任务结果处理器
负责处理异步任务的结果，创建Content记录并添加到发布池
"""
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models import Content, ContentGenerationTask
from app.services.publish_pool_service import PublishPoolService
from app.utils.custom_logger import log


class TaskResultHandler:
    """任务结果处理器"""

    def __init__(self):
        self.publish_pool_service = PublishPoolService()

    def handle_success(
        self,
        db: Session,
        task: ContentGenerationTask,
        result: Dict
    ) -> Optional[Content]:
        """
        处理成功的任务

        Args:
            db: 数据库会话
            task: 任务对象
            result: 任务结果字典

        Returns:
            创建的 Content 对象，失败则返回 None
        """
        try:
            # 1. 更新任务状态
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.result = result

            # 2. 提取生成的内容
            content_text = result.get("content", "")
            html_content = result.get("htmlContent", "")
            images = result.get("images", [])
            quality_score = result.get("qualityScore", 0.0)

            if not content_text:
                raise ValueError("任务结果中缺少 content 字段")

            # 3. 创建 Content 记录
            content = Content(
                account_id=task.account_id,
                title=task.topic[:255],  # 使用选题作为标题
                content=content_text,
                summary=content_text[:200] if len(content_text) > 200 else content_text,
                topic=task.topic,
                category=task.category,
                images=images,
                word_count=len(content_text),
                generation_task_id=task.task_id,
                auto_publish=task.auto_approve,
                review_status="pending_review" if not task.auto_approve else "approved"
            )

            # 设置 HTML 内容（如果有）
            if html_content:
                content.html_content = html_content

            # 设置图片
            if images:
                content.images = images
                # 设置封面图（第一张图的 URL）
                if len(images) > 0 and isinstance(images[0], dict):
                    content.cover_image = images[0].get('url', '')
                elif len(images) > 0 and isinstance(images[0], str):
                    content.cover_image = images[0]

            db.add(content)
            db.flush()

            log.info(f"Created content {content.id} for task {task.task_id}")

            # 4. 更新任务关联
            task.content_id = content.id

            # 5. 自动审核流程
            if task.auto_approve:
                content.review_status = "approved"
                content.publish_status = "draft"

                # 添加到发布池
                try:
                    pool_entry = self.publish_pool_service.add_to_pool(
                        db=db,
                        content_id=content.id,
                        priority=task.priority,
                        scheduled_at=datetime.utcnow()
                    )
                    log.info(f"Content {content.id} auto-approved and added to pool (entry {pool_entry.id})")
                except Exception as e:
                    log.error(f"Failed to add content {content.id} to pool: {e}")
                    # 不影响主流程，继续提交

            db.commit()

            log.info(f"Task {task.task_id} completed successfully, content {content.id} created")

            return content

        except Exception as e:
            db.rollback()
            log.error(f"Failed to handle success for task {task.task_id}: {e}", exc_info=True)

            # 更新任务为失败状态
            task.status = "failed"
            task.completed_at = datetime.utcnow()
            task.error_message = f"Result handling failed: {str(e)}"
            db.commit()

            return None

    def handle_failure(
        self,
        db: Session,
        task: ContentGenerationTask,
        error_message: str
    ):
        """
        处理失败的任务

        Args:
            db: 数据库会话
            task: 任务对象
            error_message: 错误信息
        """
        try:
            task.status = "failed"
            task.completed_at = datetime.utcnow()
            task.error_message = error_message

            db.commit()

            log.info(f"Task {task.task_id} failed: {error_message}")

        except Exception as e:
            db.rollback()
            log.error(f"Failed to handle failure for task {task.task_id}: {e}", exc_info=True)

    def handle_timeout(
        self,
        db: Session,
        task: ContentGenerationTask
    ):
        """
        处理超时的任务

        Args:
            db: 数据库会话
            task: 任务对象
        """
        try:
            task.status = "timeout"
            task.completed_at = datetime.utcnow()
            task.error_message = "Task execution timeout"

            db.commit()

            log.warning(f"Task {task.task_id} timed out")

        except Exception as e:
            db.rollback()
            log.error(f"Failed to handle timeout for task {task.task_id}: {e}", exc_info=True)

    def handle_cancelled(
        self,
        db: Session,
        task: ContentGenerationTask
    ):
        """
        处理取消的任务

        Args:
            db: 数据库会话
            task: 任务对象
        """
        try:
            task.status = "cancelled"
            task.completed_at = datetime.utcnow()

            db.commit()

            log.info(f"Task {task.task_id} cancelled")

        except Exception as e:
            db.rollback()
            log.error(f"Failed to handle cancellation for task {task.task_id}: {e}", exc_info=True)

    def retry_task(
        self,
        db: Session,
        task: ContentGenerationTask
    ) -> bool:
        """
        重试失败的任务

        Args:
            db: 数据库会话
            task: 任务对象

        Returns:
            是否成功重试
        """
        try:
            # 检查重试次数
            if task.retry_count >= task.max_retries:
                log.warning(f"Task {task.task_id} reached max retries ({task.max_retries})")
                return False

            # 重置任务状态
            task.status = "pending"
            task.retry_count += 1
            task.submitted_at = None
            task.started_at = None
            task.completed_at = None
            task.error_message = None
            task.timeout_at = datetime.utcnow()

            db.commit()

            log.info(f"Task {task.task_id} retry {task.retry_count}/{task.max_retries}")

            return True

        except Exception as e:
            db.rollback()
            log.error(f"Failed to retry task {task.task_id}: {e}", exc_info=True)
            return False

    def handle_processing(
        self,
        db: Session,
        task: ContentGenerationTask
    ):
        """
        处理正在进行的任务（更新开始时间）

        Args:
            db: 数据库会话
            task: 任务对象
        """
        try:
            if not task.started_at:
                task.started_at = datetime.utcnow()
                db.commit()

        except Exception as e:
            db.rollback()
            log.error(f"Failed to update processing status for task {task.task_id}: {e}", exc_info=True)


# 全局服务实例
def get_task_result_handler() -> TaskResultHandler:
    """
    获取任务结果处理器实例（依赖注入）

    Returns:
        TaskResultHandler 实例
    """
    return TaskResultHandler()
