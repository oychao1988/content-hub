"""
发布任务执行器

负责批量检查发布池并发布到期内容
"""
import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.services.scheduler_service import TaskExecutor, TaskExecutionResult
from app.services.publish_pool_service import publish_pool_service
from app.modules.publisher.services import publisher_service
from app.models.publisher import PublishPool
from app.models.content import Content
from app.models.account import Account
from app.utils.custom_logger import log


class PublishingExecutor(TaskExecutor):
    """
    发布任务执行器

    功能：
    1. 查询发布池中所有待发布且已到期的内容
    2. 按优先级排序（priority 升序，scheduled_at 升序）
    3. 逐个发布内容：
       - 更新状态为 "publishing"
       - 调用发布服务发布内容
       - 成功后更新状态为 "published"
       - 失败时记录错误并更新重试计数
    4. 返回执行结果（包含成功和失败的统计）

    特点：
    - 这是一个批量处理器，不是单个任务处理器
    - 处理失败不应中断整个流程，继续处理其他内容
    - 使用现有的服务（PublishPoolService、PublisherService）
    """

    @property
    def executor_type(self) -> str:
        """返回执行器类型标识"""
        return "publishing"

    def validate_params(self, task_params: Dict[str, Any]) -> bool:
        """
        验证任务参数

        Args:
            task_params: 任务参数字典

        Returns:
            bool: 参数是否有效

        注意：
        PublishingExecutor 是批量处理器，不需要特定参数
        它会自动处理发布池中所有到期的内容
        """
        # PublishingExecutor 不需要特定参数
        # 它会自动查询发布池中的待发布内容
        log.info("PublishingExecutor params validation passed (no params required)")
        return True

    async def execute(
        self,
        task_id: int,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        """
        执行发布任务

        Args:
            task_id: 任务ID
            task_params: 任务参数字典（可选，当前不使用）
            db: 数据库会话

        Returns:
            TaskExecutionResult: 任务执行结果

        执行流程:
            1. 查询发布池中所有待发布且已到期的内容
            2. 按优先级排序
            3. 对每个条目执行发布流程
            4. 返回统计结果
        """
        start_time = time.time()
        log.info(f"Executing publishing task {task_id}")

        # 统计信息
        success_count = 0
        failed_count = 0
        skipped_count = 0
        results: List[Dict[str, Any]] = []

        try:
            # 1. 查询发布池中所有待发布且已到期的内容
            log.info("Fetching pending entries from publish pool...")
            pending_entries = publish_pool_service.get_pending_entries(db)

            if not pending_entries:
                log.info("No pending entries found in publish pool")
                duration = time.time() - start_time
                return TaskExecutionResult.success_result(
                    message="No pending entries to publish",
                    data={
                        "total_count": 0,
                        "success_count": 0,
                        "failed_count": 0,
                        "skipped_count": 0,
                        "results": []
                    },
                    duration=duration
                )

            log.info(f"Found {len(pending_entries)} pending entries in publish pool")

            # 2. 按优先级处理每个条目（已在 get_pending_entries 中排序）
            for idx, pool_entry in enumerate(pending_entries, 1):
                pool_id = pool_entry.id
                content_id = pool_entry.content_id

                log.info(f"Processing entry {idx}/{len(pending_entries)}: pool_id={pool_id}, content_id={content_id}")

                try:
                    # 获取内容和账号信息
                    content = db.query(Content).filter(Content.id == content_id).first()
                    if not content:
                        error_msg = f"Content not found (ID: {content_id})"
                        log.error(error_msg)
                        self._handle_publish_failure(db, pool_id, error_msg)
                        failed_count += 1
                        results.append({
                            "pool_id": pool_id,
                            "content_id": content_id,
                            "status": "failed",
                            "error": error_msg
                        })
                        continue

                    account = db.query(Account).filter(Account.id == content.account_id).first()
                    if not account:
                        error_msg = f"Account not found (ID: {content.account_id})"
                        log.error(error_msg)
                        self._handle_publish_failure(db, pool_id, error_msg)
                        failed_count += 1
                        results.append({
                            "pool_id": pool_id,
                            "content_id": content_id,
                            "status": "failed",
                            "error": error_msg
                        })
                        continue

                    # 3a. 更新状态为 "publishing"
                    log.info(f"Starting publish for content_id={content_id}")
                    publish_pool_service.start_publishing(db, pool_id)

                    # 3b. 调用发布服务发布内容
                    publish_request = {
                        "content_id": content_id,
                        "account_id": account.id,
                        "publish_to_draft": True  # 默认发布到草稿箱
                    }

                    publish_result = publisher_service.manual_publish(db, publish_request)

                    # 3c. 检查发布结果
                    if publish_result.get("success"):
                        # 发布成功
                        log.info(f"Successfully published content_id={content_id}, log_id={publish_result.get('log_id')}")
                        publish_pool_service.complete_publishing(
                            db,
                            pool_id,
                            publish_result.get("log_id")
                        )
                        success_count += 1
                        results.append({
                            "pool_id": pool_id,
                            "content_id": content_id,
                            "status": "published",
                            "log_id": publish_result.get("log_id"),
                            "media_id": publish_result.get("media_id")
                        })
                    else:
                        # 发布失败
                        error_msg = publish_result.get("error", "Unknown error")
                        log.error(f"Failed to publish content_id={content_id}: {error_msg}")
                        self._handle_publish_failure(db, pool_id, error_msg)
                        failed_count += 1
                        results.append({
                            "pool_id": pool_id,
                            "content_id": content_id,
                            "status": "failed",
                            "error": error_msg
                        })

                except Exception as e:
                    # 捕获单个内容的发布异常，继续处理其他内容
                    error_msg = f"Error processing content_id={content_id}: {str(e)}"
                    log.error(error_msg)
                    log.exception("Exception during publishing")

                    try:
                        self._handle_publish_failure(db, pool_id, error_msg)
                    except Exception as inner_e:
                        log.error(f"Failed to handle publish failure: {str(inner_e)}")

                    failed_count += 1
                    results.append({
                        "pool_id": pool_id,
                        "content_id": content_id,
                        "status": "error",
                        "error": error_msg
                    })

            # 4. 返回执行结果
            total_count = len(pending_entries)
            duration = time.time() - start_time

            log.info(
                f"Publishing task completed: "
                f"total={total_count}, success={success_count}, failed={failed_count}, "
                f"duration={duration:.2f}s"
            )

            return TaskExecutionResult.success_result(
                message=f"Publishing completed: {success_count} succeeded, {failed_count} failed",
                data={
                    "total_count": total_count,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "skipped_count": skipped_count,
                    "results": results
                },
                duration=duration,
                metadata={
                    "task_id": task_id,
                    "average_time_per_item": duration / total_count if total_count > 0 else 0
                }
            )

        except Exception as e:
            # 捕获整个流程的异常
            error_msg = f"Unexpected error during publishing execution: {str(e)}"
            log.error(error_msg)
            log.exception("Publishing execution error")
            duration = time.time() - start_time

            return TaskExecutionResult.failure_result(
                message=error_msg,
                error=str(e),
                duration=duration,
                metadata={
                    "task_id": task_id,
                    "partial_results": {
                        "success_count": success_count,
                        "failed_count": failed_count,
                        "results": results
                    }
                }
            )

    def _handle_publish_failure(self, db: Session, pool_id: int, error_message: str) -> None:
        """
        处理发布失败

        Args:
            db: 数据库会话
            pool_id: 发布池条目ID
            error_message: 错误信息
        """
        try:
            # 更新状态为 failed 并增加重试计数
            pool_entry = publish_pool_service.fail_publishing(db, pool_id, error_message)

            if pool_entry:
                # 检查是否需要重试
                if pool_entry.retry_count < pool_entry.max_retries:
                    log.info(
                        f"Scheduling retry for pool_id={pool_id} "
                        f"(attempt {pool_entry.retry_count}/{pool_entry.max_retries})"
                    )
                    # 重置为 pending 以便下次调度时重试
                    publish_pool_service.retry_publishing(db, pool_id)
                else:
                    log.warning(
                        f"Pool entry {pool_id} has reached max retries ({pool_entry.max_retries})"
                    )
        except Exception as e:
            log.error(f"Failed to handle publish failure for pool_id={pool_id}: {str(e)}")
            raise
