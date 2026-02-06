"""
任务调度服务

提供任务执行器接口和任务调度功能
"""
from typing import Optional, Dict, Any, Type, List
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from functools import wraps

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.config import settings
from app.utils.custom_logger import log


class TaskStatus(str, Enum):
    """任务执行状态枚举"""
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class TaskExecutionResult:
    """
    任务执行结果数据类

    Attributes:
        success: 是否执行成功
        message: 执行结果消息（成功或失败原因）
        data: 执行返回的业务数据
        error: 错误信息（失败时）
        duration: 执行时长（秒）
        metadata: 额外的元数据信息
    """
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于存储到数据库）"""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "duration": self.duration,
            "metadata": self.metadata
        }

    @classmethod
    def success_result(
        cls,
        message: str = "Task executed successfully",
        data: Optional[Dict[str, Any]] = None,
        duration: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "TaskExecutionResult":
        """创建成功结果"""
        return cls(
            success=True,
            message=message,
            data=data,
            duration=duration,
            metadata=metadata or {}
        )

    @classmethod
    def failure_result(
        cls,
        message: str,
        error: Optional[str] = None,
        duration: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "TaskExecutionResult":
        """创建失败结果"""
        return cls(
            success=False,
            message=message,
            error=error,
            duration=duration,
            metadata=metadata or {}
        )


class TaskExecutor(ABC):
    """
    任务执行器基类（抽象接口）

    所有具体的任务执行器（如内容生成执行器、发布执行器）都必须继承此类
    并实现 execute 方法
    """

    @property
    @abstractmethod
    def executor_type(self) -> str:
        """
        返回执行器类型标识

        Returns:
            执行器类型字符串（如 'content_generation', 'publishing'）
        """
        pass

    @abstractmethod
    async def execute(
        self,
        task_id: int,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        """
        执行任务

        Args:
            task_id: 任务ID
            task_params: 任务参数字典
            db: 数据库会话

        Returns:
            TaskExecutionResult: 任务执行结果
        """
        pass

    def validate_params(self, task_params: Dict[str, Any]) -> bool:
        """
        验证任务参数（可选实现）

        Args:
            task_params: 任务参数字典

        Returns:
            bool: 参数是否有效
        """
        return True

    def get_executor_info(self) -> Dict[str, Any]:
        """
        获取执行器信息

        Returns:
            执行器元信息字典
        """
        return {
            "type": self.executor_type,
            "class": self.__class__.__name__,
            "module": self.__class__.__module__
        }


class SchedulerService:
    """
    任务调度服务

    负责：
    1. 管理任务执行器注册
    2. 调度和执行任务
    3. 记录任务执行历史
    """

    def __init__(self):
        """初始化调度服务"""
        self.scheduler = BackgroundScheduler(timezone=settings.SCHEDULER_TIMEZONE)
        self.executors: Dict[str, TaskExecutor] = {}
        log.info("调度服务初始化完成")

    def register_executor(self, executor: TaskExecutor) -> None:
        """
        注册任务执行器

        Args:
            executor: 任务执行器实例
        """
        executor_type = executor.executor_type
        if executor_type in self.executors:
            log.warning(f"执行器类型 '{executor_type}' 已存在，将被覆盖")

        self.executors[executor_type] = executor
        log.info(f"注册任务执行器: {executor.get_executor_info()}")

    def get_executor(self, executor_type: str) -> Optional[TaskExecutor]:
        """
        获取指定类型的执行器

        Args:
            executor_type: 执行器类型

        Returns:
            TaskExecutor实例或None
        """
        return self.executors.get(executor_type)

    async def execute_task(
        self,
        task_id: int,
        task_type: str,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        """
        执行任务

        Args:
            task_id: 任务ID
            task_type: 任务类型（对应执行器类型）
            task_params: 任务参数
            db: 数据库会话

        Returns:
            TaskExecutionResult: 任务执行结果
        """
        # 查找对应的执行器
        executor = self.get_executor(task_type)

        if executor is None:
            error_msg = f"未找到类型为 '{task_type}' 的任务执行器"
            log.error(f"任务 {task_id} 执行失败: {error_msg}")
            return TaskExecutionResult.failure_result(
                message=error_msg,
                error=f"ExecutorNotFound: {task_type}"
            )

        # 记录任务开始执行
        start_time = datetime.now()
        log.info(f"开始执行任务 {task_id} (类型: {task_type})")
        log.debug(f"任务参数: {task_params}")

        try:
            # 验证参数
            if not executor.validate_params(task_params):
                return TaskExecutionResult.failure_result(
                    message="任务参数验证失败",
                    error="InvalidParameters"
                )

            # 执行任务
            result = await executor.execute(task_id, task_params, db)

            # 计算执行时长
            duration = (datetime.now() - start_time).total_seconds()
            result.duration = duration

            # 记录执行结果
            if result.success:
                log.info(f"任务 {task_id} 执行成功，耗时 {duration:.2f}秒")
                log.debug(f"执行结果: {result.message}")
            else:
                log.error(f"任务 {task_id} 执行失败，耗时 {duration:.2f}秒")
                log.error(f"失败原因: {result.message}")
                if result.error:
                    log.error(f"错误详情: {result.error}")

            return result

        except Exception as e:
            # 计算执行时长
            duration = (datetime.now() - start_time).total_seconds()

            # 记录异常
            error_msg = f"任务执行过程中发生异常: {str(e)}"
            log.exception(f"任务 {task_id} 执行异常，耗时 {duration:.2f}秒")

            return TaskExecutionResult.failure_result(
                message=error_msg,
                error=str(e),
                duration=duration
            )

    def start(self) -> None:
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            log.info("调度器已启动")
        else:
            log.warning("调度器已在运行中")

    def shutdown(self, wait: bool = True) -> None:
        """
        关闭调度器

        Args:
            wait: 是否等待正在执行的任务完成
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            log.info(f"调度器已关闭 (wait={wait})")
        else:
            log.warning("调度器未运行")

    @property
    def is_running(self) -> bool:
        """检查调度器是否正在运行"""
        return self.scheduler.running

    def get_registered_executors(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有已注册的执行器信息

        Returns:
            执行器信息字典 {executor_type: executor_info}
        """
        return {
            executor_type: executor.get_executor_info()
            for executor_type, executor in self.executors.items()
        }

    def load_tasks_from_db(self, db: Session) -> int:
        """
        从数据库加载启用的定时任务并注册到调度器

        Args:
            db: 数据库会话

        Returns:
            int: 成功加载的任务数量
        """
        from app.models.scheduler import ScheduledTask

        try:
            # 查询所有启用的任务
            active_tasks = db.query(ScheduledTask).filter(
                ScheduledTask.is_active == True
            ).all()

            if not active_tasks:
                log.info("没有找到启用的定时任务")
                return 0

            loaded_count = 0
            failed_count = 0

            log.info(f"开始加载定时任务，共 {len(active_tasks)} 个任务")

            for task in active_tasks:
                try:
                    self.register_scheduled_task(db, task)
                    loaded_count += 1
                    log.info(f"✓ 加载任务成功: {task.name} (ID: {task.id}, 类型: {task.task_type})")
                except Exception as e:
                    failed_count += 1
                    log.error(f"✗ 加载任务失败: {task.name} (ID: {task.id}), 错误: {str(e)}")

            log.info(f"定时任务加载完成: 成功 {loaded_count} 个, 失败 {failed_count} 个")
            return loaded_count

        except Exception as e:
            log.error(f"从数据库加载任务时发生错误: {str(e)}")
            log.exception("Task loading error")
            return 0

    def register_scheduled_task(self, db: Session, task) -> bool:
        """
        注册单个定时任务到调度器

        Args:
            db: 数据库会话
            task: ScheduledTask 模型实例

        Returns:
            bool: 是否注册成功

        Raises:
            ValueError: 如果任务配置无效
        """
        from app.models.scheduler import ScheduledTask

        # 验证任务配置
        if not task.cron_expression and not task.interval:
            raise ValueError(
                f"任务 '{task.name}' 必须配置 cron_expression 或 interval"
            )

        if task.cron_expression and task.interval:
            log.warning(
                f"任务 '{task.name}' 同时配置了 cron_expression 和 interval，"
                f"将优先使用 cron_expression"
            )

        # 检查执行器是否存在
        executor = self.get_executor(task.task_type)
        if not executor:
            raise ValueError(
                f"未找到类型为 '{task.task_type}' 的执行器，"
                f"请先注册对应的执行器"
            )

        # 创建任务包装器
        task_wrapper = self._create_task_wrapper(task.id, task.task_type, task.name)

        # 根据调度配置创建触发器
        trigger = None
        if task.cron_expression:
            # 使用 Cron 表达式
            trigger = CronTrigger.from_crontab(task.cron_expression, timezone=settings.SCHEDULER_TIMEZONE)
            log.debug(f"使用 Cron 表达式: {task.cron_expression}")
        elif task.interval:
            # 使用间隔调度
            interval_seconds = self._convert_interval_to_seconds(task.interval, task.interval_unit)
            trigger = IntervalTrigger(seconds=interval_seconds, timezone=settings.SCHEDULER_TIMEZONE)
            log.debug(f"使用间隔调度: {interval_seconds} 秒")

        # 添加任务到调度器
        try:
            job = self.scheduler.add_job(
                task_wrapper,
                trigger=trigger,
                id=f"task_{task.id}",
                name=task.name,
                replace_existing=True,
                misfire_grace_time=300  # 错过执行时间的宽限时间（秒）
            )

            # 更新任务的下次运行时间
            if job.next_run_time:
                task.next_run_time = job.next_run_time
                db.commit()

            log.info(f"任务已注册到调度器: {task.name} (ID: {task.id}, 下次运行: {job.next_run_time})")
            return True

        except Exception as e:
            log.error(f"注册任务到调度器失败: {task.name}, 错误: {str(e)}")
            raise

    def unregister_task(self, task_id: int) -> bool:
        """
        从调度器移除任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否移除成功
        """
        job_id = f"task_{task_id}"
        try:
            self.scheduler.remove_job(job_id)
            log.info(f"任务已从调度器移除: task_id={task_id}, job_id={job_id}")
            return True
        except Exception as e:
            log.warning(f"移除任务失败: task_id={task_id}, 错误: {str(e)}")
            return False

    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """
        获取所有已注册的调度任务

        Returns:
            任务信息列表
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "job_id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger),
            })
        return jobs

    def _create_task_wrapper(self, task_id: int, task_type: str, task_name: str):
        """
        创建任务包装器函数

        任务包装器负责：
        1. 创建独立的数据库会话
        2. 调用执行器执行任务
        3. 更新任务执行记录
        4. 处理异常并记录日志

        Args:
            task_id: 任务ID
            task_type: 任务类型
            task_name: 任务名称

        Returns:
            可调用的任务包装函数
        """
        @wraps(self._execute_task_wrapper)
        def task_wrapper():
            """同步任务包装器（APScheduler 调用）"""
            from app.db.database import SessionLocal
            from app.models.scheduler import ScheduledTask, TaskExecution

            db = None
            execution_record = None

            try:
                # 1. 创建数据库会话
                db = SessionLocal()

                # 2. 查询任务信息
                task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
                if not task:
                    log.error(f"任务不存在: task_id={task_id}")
                    return

                # 3. 创建执行记录
                execution_record = TaskExecution(
                    task_id=task_id,
                    status="running",
                    start_time=datetime.now()
                )
                db.add(execution_record)
                db.commit()
                db.refresh(execution_record)

                log.info(
                    f"开始执行定时任务: {task_name} (ID: {task_id}, "
                    f"执行记录ID: {execution_record.id})"
                )

                # 4. 提取任务参数（从 task_params 或其他配置）
                task_params = self._extract_task_params(db, task)

                # 5. 调用异步执行器
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    result = loop.run_until_complete(
                        self.execute_task(task_id, task_type, task_params, db)
                    )
                finally:
                    loop.close()

                # 6. 更新执行记录
                execution_record.end_time = datetime.now()
                execution_record.duration = int(
                    (execution_record.end_time - execution_record.start_time).total_seconds()
                )

                if result.success:
                    execution_record.status = "success"
                    execution_record.result = result.to_dict()
                    # 更新任务的最后运行时间
                    task.last_run_time = execution_record.end_time

                    log.info(
                        f"任务执行成功: {task_name} (ID: {task_id}, "
                        f"耗时: {result.duration:.2f}秒)"
                    )
                else:
                    execution_record.status = "failed"
                    execution_record.error_message = result.message
                    execution_record.result = result.to_dict()

                    log.error(
                        f"任务执行失败: {task_name} (ID: {task_id}), "
                        f"原因: {result.message}"
                    )

                db.commit()

            except Exception as e:
                error_msg = f"任务包装器执行异常: {str(e)}"
                log.error(f"{error_msg}")
                log.exception("Task wrapper exception")

                # 更新执行记录为失败
                if execution_record and db:
                    try:
                        execution_record.end_time = datetime.now()
                        execution_record.duration = int(
                            (execution_record.end_time - execution_record.start_time).total_seconds()
                        )
                        execution_record.status = "failed"
                        execution_record.error_message = error_msg
                        db.commit()
                    except Exception as commit_error:
                        log.error(f"更新执行记录失败: {str(commit_error)}")

            finally:
                # 关闭数据库会话
                if db:
                    db.close()

        return task_wrapper

    def _extract_task_params(self, db: Session, task) -> Dict[str, Any]:
        """
        从任务配置中提取参数

        Args:
            db: 数据库会话
            task: ScheduledTask 实例

        Returns:
            任务参数字典
        """
        # 从 task.params 字段读取参数
        if task.params:
            if isinstance(task.params, dict):
                return task.params
            elif isinstance(task.params, str):
                import json
                try:
                    return json.loads(task.params)
                except json.JSONDecodeError:
                    log.warning(f"任务 {task.id} 的参数 JSON 解析失败")
                    return {}

        # 如果没有参数，返回空字典
        return {}

    def _convert_interval_to_seconds(self, interval: int, unit: str) -> int:
        """
        将间隔时间转换为秒数

        Args:
            interval: 间隔数值
            unit: 间隔单位 (minutes/hours/days)

        Returns:
            间隔秒数

        Raises:
            ValueError: 如果单位不支持
        """
        unit = unit.lower()

        multipliers = {
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400
        }

        if unit not in multipliers:
            raise ValueError(f"不支持的间隔单位: {unit}，支持的单位: {list(multipliers.keys())}")

        # 兼容单复数形式
        if unit.endswith("s"):
            unit_singular = unit[:-1]
        else:
            unit_singular = unit

        # 检查是否在 multipliers 中
        if unit in multipliers:
            return interval * multipliers[unit]
        elif unit_singular in multipliers:
            return interval * multipliers[unit_singular]
        else:
            raise ValueError(f"不支持的间隔单位: {unit}")

    def _execute_task_wrapper(self):
        """
        任务包装器的实际执行逻辑（占位符）

        实际的包装器由 _create_task_wrapper 动态创建
        """
        pass


# 全局调度器实例
scheduler_service = SchedulerService()
