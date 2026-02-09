"""
发布池扫描执行器
负责自动扫描发布池并批量发布内容
"""
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.scheduler_service import TaskExecutor, TaskExecutionResult
from app.services.publish_pool_service import publish_pool_service
from app.services.executors.publishing_executor import PublishingExecutor
from app.models.publisher import PublishPool
from app.utils.custom_logger import log


class PublishPoolScannerExecutor(TaskExecutor):
    """
    发布池扫描执行器

    功能：
    1. 扫描发布池中待发布的内容
    2. 按优先级和计划时间排序
    3. 批量触发发布任务
    """

    @property
    def executor_type(self) -> str:
        """执行器类型"""
        return "publish_pool_scanner"

    async def execute(
        self,
        task_id: int,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        """
        执行发布池扫描和批量发布

        Args:
            task_id: 任务ID
            task_params: 任务参数，可包含：
                - max_batch_size: 单次最大发布数量（默认10）
                - check_future_tasks: 是否检查未来任务（默认false）
            db: 数据库会话

        Returns:
            TaskExecutionResult: 执行结果
        """
        # 获取参数
        max_batch_size = task_params.get("max_batch_size", 10)
        check_future_tasks = task_params.get("check_future_tasks", False)

        log.info(
            f"开始扫描发布池: task_id={task_id}, "
            f"max_batch_size={max_batch_size}, check_future_tasks={check_future_tasks}"
        )

        try:
            # 1. 查询待发布的任务
            pending_tasks = self._get_pending_tasks(
                db,
                max_batch_size=max_batch_size,
                check_future_tasks=check_future_tasks
            )

            if not pending_tasks:
                log.info("发布池中没有待发布的任务")
                return TaskExecutionResult.success_result(
                    message="发布池扫描完成，没有待发布任务",
                    data={
                        "scanned": True,
                        "pending_count": 0,
                        "published_count": 0,
                        "failed_count": 0
                    }
                )

            log.info(f"找到 {len(pending_tasks)} 个待发布任务")

            # 2. 批量发布
            publishing_executor = PublishingExecutor()
            published_count = 0
            failed_count = 0
            results = []

            for pool_entry in pending_tasks:
                try:
                    # 检查重试次数
                    if pool_entry.retry_count >= pool_entry.max_retries:
                        log.warning(
                            f"任务 {pool_entry.id} 已达到最大重试次数 "
                            f"({pool_entry.retry_count}/{pool_entry.max_retries})，跳过"
                        )
                        failed_count += 1
                        results.append({
                            "pool_id": pool_entry.id,
                            "content_id": pool_entry.content_id,
                            "success": False,
                            "error": "超过最大重试次数"
                        })
                        continue

                    # 调用发布执行器
                    log.info(f"正在发布: pool_id={pool_entry.id}, content_id={pool_entry.content_id}")

                    # 构造发布参数
                    publish_params = {
                        "content_id": pool_entry.content_id,
                        "pool_id": pool_entry.id
                    }

                    # 执行发布
                    result = await publishing_executor.execute(
                        task_id,
                        publish_params,
                        db
                    )

                    if result.success:
                        published_count += 1
                        results.append({
                            "pool_id": pool_entry.id,
                            "content_id": pool_entry.content_id,
                            "success": True,
                            "message": result.message
                        })
                    else:
                        failed_count += 1
                        # 更新重试次数
                        pool_entry.retry_count += 1
                        pool_entry.last_error = result.message
                        db.commit()

                        results.append({
                            "pool_id": pool_entry.id,
                            "content_id": pool_entry.content_id,
                            "success": False,
                            "error": result.message
                        })

                except Exception as e:
                    failed_count += 1
                    error_msg = f"发布任务执行异常: {str(e)}"
                    log.error(f"{error_msg}", exc_info=True)

                    # 更新任务状态
                    try:
                        pool_entry.retry_count += 1
                        pool_entry.last_error = error_msg
                        db.commit()
                    except Exception as commit_error:
                        log.error(f"更新任务状态失败: {str(commit_error)}")

                    results.append({
                        "pool_id": pool_entry.id,
                        "content_id": pool_entry.content_id,
                        "success": False,
                        "error": str(e)
                    })

            # 3. 返回执行结果
            total_count = len(pending_tasks)
            message = (
                f"发布池扫描完成: 扫描 {total_count} 个任务, "
                f"成功 {published_count} 个, 失败 {failed_count} 个"
            )

            return TaskExecutionResult.success_result(
                message=message,
                data={
                    "scanned": True,
                    "pending_count": total_count,
                    "published_count": published_count,
                    "failed_count": failed_count,
                    "results": results
                }
            )

        except Exception as e:
            error_msg = f"发布池扫描执行失败: {str(e)}"
            log.error(error_msg, exc_info=True)
            return TaskExecutionResult.failure_result(
                message=error_msg,
                error=str(e)
            )

    def _get_pending_tasks(
        self,
        db: Session,
        max_batch_size: int = 10,
        check_future_tasks: bool = False
    ) -> list:
        """
        获取待发布的任务

        Args:
            db: 数据库会话
            max_batch_size: 最大批处理数量
            check_future_tasks: 是否检查未来任务（未到发布时间的任务）

        Returns:
            待发布的 PublishPool 列表
        """
        from app.models.publisher import PublishPool

        # 基础查询：待发布状态
        query = db.query(PublishPool).filter(
            PublishPool.status == "pending"
        )

        # 如果不检查未来任务，只查询已到发布时间的任务
        if not check_future_tasks:
            query = query.filter(
                (PublishPool.scheduled_at == None) |
                (PublishPool.scheduled_at <= datetime.now())
            )

        # 按优先级降序、添加时间升序排序
        query = query.order_by(
            PublishPool.priority.desc(),
            PublishPool.scheduled_at.asc(),
            PublishPool.added_at.asc()
        )

        # 限制数量
        query = query.limit(max_batch_size)

        return query.all()
