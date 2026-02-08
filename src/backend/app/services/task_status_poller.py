"""
任务状态轮询器
负责定期查询进行中任务的状态并更新数据库
"""
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal
from app.models import ContentGenerationTask
from app.services.task_result_handler import TaskResultHandler
from app.utils.custom_logger import log


class TaskStatusPoller:
    """任务状态轮询器"""

    def __init__(self, poll_interval: int = 30):
        """
        初始化轮询器

        Args:
            poll_interval: 轮询间隔（秒）
        """
        self.poll_interval = poll_interval
        self.result_handler = TaskResultHandler()

    def poll_running_tasks(self) -> Dict[str, int]:
        """
        轮询所有进行中的任务

        Returns:
            统计信息字典
        """
        db = SessionLocal()
        try:
            # 查询进行中的任务
            running_tasks = db.query(ContentGenerationTask).filter(
                ContentGenerationTask.status.in_(["submitted", "processing"])
            ).all()

            stats = {
                "total": len(running_tasks),
                "completed": 0,
                "failed": 0,
                "timeout": 0,
                "still_running": 0,
                "error": 0
            }

            log.info(f"Polling {len(running_tasks)} running tasks")

            for task in running_tasks:
                try:
                    # 检查任务状态
                    status_info = self.check_task_status(task.task_id)

                    if not status_info:
                        log.warning(f"Failed to get status for task {task.task_id}")
                        stats["error"] += 1
                        continue

                    new_status = status_info.get("status")

                    # 处理不同状态
                    if new_status == "completed":
                        result = self.get_task_result(task.task_id)
                        if result:
                            self.result_handler.handle_success(db, task, result)
                            stats["completed"] += 1
                        else:
                            log.error(f"Failed to get result for completed task {task.task_id}")
                            stats["error"] += 1

                    elif new_status == "failed":
                        error_msg = status_info.get("error", "Unknown error")
                        self.result_handler.handle_failure(db, task, error_msg)
                        stats["failed"] += 1

                    elif new_status in ["submitted", "processing"]:
                        # 检查超时
                        if task.timeout_at and datetime.utcnow() > task.timeout_at:
                            self.result_handler.handle_timeout(db, task)
                            stats["timeout"] += 1
                        else:
                            # 更新开始时间（如果需要）
                            self.result_handler.handle_processing(db, task)
                            stats["still_running"] += 1

                    else:
                        log.warning(f"Unknown status for task {task.task_id}: {new_status}")
                        stats["error"] += 1

                except Exception as e:
                    log.error(f"Error processing task {task.task_id}: {e}", exc_info=True)
                    stats["error"] += 1

            log.info(f"Poll completed: {stats}")

            return stats

        finally:
            db.close()

    def check_task_status(self, task_id: str) -> Optional[Dict]:
        """
        查询任务状态（调用 content-creator CLI）

        Args:
            task_id: 任务ID

        Returns:
            状态信息字典，失败则返回 None
        """
        if not settings.CREATOR_CLI_PATH:
            log.error("CREATOR_CLI_PATH not configured")
            return None

        try:
            cmd = [
                settings.CREATOR_CLI_PATH,
                "status",
                "--task-id", task_id,
                "--json"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    log.error(f"Failed to parse status JSON for {task_id}: {e}")
                    log.error(f"Response: {result.stdout[:500]}")
                    return None
            else:
                log.error(f"CLI status command failed for {task_id}: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            log.error(f"Timeout checking status for {task_id}")
            return None
        except Exception as e:
            log.error(f"Error checking task status: {e}", exc_info=True)
            return None

    def get_task_result(self, task_id: str) -> Optional[Dict]:
        """
        获取任务结果

        Args:
            task_id: 任务ID

        Returns:
            结果字典，失败则返回 None
        """
        if not settings.CREATOR_CLI_PATH:
            log.error("CREATOR_CLI_PATH not configured")
            return None

        try:
            cmd = [
                settings.CREATOR_CLI_PATH,
                "result",
                "--task-id", task_id,
                "--json"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 获取结果可能需要更长时间
            )

            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    log.error(f"Failed to parse result JSON for {task_id}: {e}")
                    log.error(f"Response: {result.stdout[:500]}")
                    return None
            else:
                log.error(f"CLI result command failed for {task_id}: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            log.error(f"Timeout getting result for {task_id}")
            return None
        except Exception as e:
            log.error(f"Error getting task result: {e}", exc_info=True)
            return None

    def poll_single_task(self, task_id: str) -> Optional[str]:
        """
        轮询单个任务

        Args:
            task_id: 任务ID

        Returns:
            当前状态，失败则返回 None
        """
        status_info = self.check_task_status(task_id)

        if not status_info:
            return None

        return status_info.get("status")

    def get_timeout_tasks(self) -> List[ContentGenerationTask]:
        """
        获取超时的任务

        Returns:
            超时任务列表
        """
        db = SessionLocal()
        try:
            now = datetime.utcnow()

            timeout_tasks = db.query(ContentGenerationTask).filter(
                ContentGenerationTask.status.in_(["submitted", "processing"]),
                ContentGenerationTask.timeout_at < now
            ).all()

            return timeout_tasks

        finally:
            db.close()

    def handle_timeout_tasks(self) -> int:
        """
        处理所有超时任务

        Returns:
            处理的任务数量
        """
        timeout_tasks = self.get_timeout_tasks()

        if not timeout_tasks:
            return 0

        db = SessionLocal()
        try:
            count = 0
            for task in timeout_tasks:
                self.result_handler.handle_timeout(db, task)
                count += 1

            log.info(f"Handled {count} timeout tasks")
            return count

        finally:
            db.close()


# 全局服务实例
def get_task_status_poller() -> TaskStatusPoller:
    """
    获取任务状态轮询器实例（依赖注入）

    Returns:
        TaskStatusPoller 实例
    """
    return TaskStatusPoller()
