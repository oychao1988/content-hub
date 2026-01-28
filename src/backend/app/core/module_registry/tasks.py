"""
通用任务注册器

提供Celery任务的注册、队列管理和监控功能
"""

import time
import traceback
from typing import Dict, List, Any, Optional, Callable
from logging import getLogger
from datetime import datetime
from enum import Enum
from functools import wraps

logger = getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    URGENT = 9


class TaskQueue(Enum):
    """任务队列枚举（基础队列，各模块可继承扩展）"""
    DEFAULT = "celery"


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class TaskInfo:
    """任务信息"""

    def __init__(
        self,
        name: str,
        func: Callable,
        queue: str = "celery",
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: int = 60,
        time_limit: int = 3600,
        soft_time_limit: int = 3300,
        description: str = None,
        tags: List[str] = None
    ):
        self.name = name
        self.func = func
        self.queue = queue
        self.priority = priority
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.time_limit = time_limit
        self.soft_time_limit = soft_time_limit
        self.description = description
        self.tags = tags or []
        self.registered_at = datetime.utcnow()


class TaskRegistry:
    """Celery任务注册管理器"""

    def __init__(self, module_name: str):
        """
        初始化任务注册器
        
        Args:
            module_name: 模块名称（如 "market_evaluation", "product_selection"）
        """
        self.module_name = module_name
        self.tasks = {}
        self.task_metrics = {}
        self.queue_configs = {}
        self.retry_policies = {}
        self.task_dependencies = {}
        self.monitoring_enabled = True

    def register_task(self, task_info: TaskInfo):
        """注册任务"""
        if task_info.name in self.tasks:
            logger.warning(f"[{self.module_name}] Task {task_info.name} already registered, overwriting")

        self.tasks[task_info.name] = task_info

        # 初始化任务指标
        self.task_metrics[task_info.name] = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'retry_executions': 0,
            'average_execution_time': 0,
            'last_executed': None,
            'last_success': None,
            'last_failure': None
        }

        logger.info(f"[{self.module_name}] Registered task: {task_info.name} -> {task_info.queue}")

    def configure_queue(self, queue_name: str, config: Dict[str, Any]):
        """配置队列"""
        self.queue_configs[queue_name] = config
        logger.info(f"[{self.module_name}] Configured queue: {queue_name}")

    def set_retry_policy(self, task_name: str, policy: Dict[str, Any]):
        """设置重试策略"""
        self.retry_policies[task_name] = policy
        logger.info(f"[{self.module_name}] Set retry policy for task: {task_name}")

    def add_task_dependency(self, task_name: str, dependencies: List[str]):
        """添加任务依赖"""
        self.task_dependencies[task_name] = dependencies
        logger.info(f"[{self.module_name}] Added dependencies for task {task_name}: {dependencies}")

    def get_task_info(self, task_name: str) -> Optional[TaskInfo]:
        """获取任务信息"""
        return self.tasks.get(task_name)

    def get_tasks_by_queue(self, queue_name: str) -> List[TaskInfo]:
        """获取指定队列的任务"""
        return [task for task in self.tasks.values() if task.queue == queue_name]

    def get_tasks_by_priority(self, priority: TaskPriority) -> List[TaskInfo]:
        """获取指定优先级的任务"""
        return [task for task in self.tasks.values() if task.priority == priority]

    def update_task_metrics(
        self,
        task_name: str,
        status: TaskStatus,
        execution_time: float = None,
        error: str = None
    ):
        """更新任务指标"""
        if not self.monitoring_enabled:
            return

        if task_name not in self.task_metrics:
            return

        metrics = self.task_metrics[task_name]
        metrics['total_executions'] += 1
        metrics['last_executed'] = datetime.utcnow()

        if status == TaskStatus.SUCCESS:
            metrics['successful_executions'] += 1
            metrics['last_success'] = datetime.utcnow()

            if execution_time is not None:
                # 更新平均执行时间
                if metrics['average_execution_time'] == 0:
                    metrics['average_execution_time'] = execution_time
                else:
                    metrics['average_execution_time'] = (
                        metrics['average_execution_time'] * 0.9 + execution_time * 0.1
                    )

        elif status == TaskStatus.FAILURE:
            metrics['failed_executions'] += 1
            metrics['last_failure'] = datetime.utcnow()

        elif status == TaskStatus.RETRY:
            metrics['retry_executions'] += 1

        logger.debug(f"[{self.module_name}] Updated metrics for task {task_name}: {status.value}")

    def get_task_metrics(self, task_name: str = None) -> Dict[str, Any]:
        """获取任务指标"""
        if task_name:
            return self.task_metrics.get(task_name, {})
        return self.task_metrics

    def get_registry_status(self) -> Dict[str, Any]:
        """获取注册器状态"""
        queue_stats = {}
        for queue_name in self.queue_configs:
            queue_stats[queue_name] = len(self.get_tasks_by_queue(queue_name))
        
        return {
            'module_name': self.module_name,
            'total_tasks': len(self.tasks),
            'tasks_by_queue': queue_stats,
            'tasks_by_priority': {
                priority.name: len(self.get_tasks_by_priority(priority))
                for priority in TaskPriority
            },
            'monitoring_enabled': self.monitoring_enabled,
            'configured_queues': len(self.queue_configs),
            'retry_policies': len(self.retry_policies),
            'task_dependencies': len(self.task_dependencies)
        }

    def validate_dependencies(self, task_name: str) -> bool:
        """验证任务依赖"""
        if task_name not in self.task_dependencies:
            return True

        dependencies = self.task_dependencies[task_name]
        for dep in dependencies:
            if dep not in self.tasks:
                logger.error(f"[{self.module_name}] Task {task_name} depends on unregistered task: {dep}")
                return False

        return True

    def get_task_chain(self, task_name: str) -> List[str]:
        """获取任务链"""
        chain = []
        visited = set()

        def build_chain(name):
            if name in visited:
                return  # 避免循环依赖

            visited.add(name)
            dependencies = self.task_dependencies.get(name, [])

            for dep in dependencies:
                build_chain(dep)

            if name not in chain:
                chain.append(name)

        build_chain(task_name)
        return chain


def create_task_registry(
    module_name: str,
    queue_configs: Dict[str, Dict[str, Any]] = None,
    retry_policies: Dict[str, Dict[str, Any]] = None
) -> TaskRegistry:
    """
    创建并配置任务注册器
    
    Args:
        module_name: 模块名称
        queue_configs: 队列配置字典 {queue_name: {routing_key, priority, ...}}
        retry_policies: 重试策略字典 {task_name: {max_retries, countdown, ...}}
        
    Returns:
        配置好的TaskRegistry实例
        
    Example:
        registry = create_task_registry(
            module_name="product_selection",
            queue_configs={
                "product_selection_data": {
                    "routing_key": "product_selection_data",
                    "priority": 7,
                    "max_length": 500,
                    "message_ttl": 3600
                }
            },
            retry_policies={
                "process_scoring": {
                    "max_retries": 3,
                    "countdown": 60,
                    "backoff": True
                }
            }
        )
    """
    registry = TaskRegistry(module_name)
    
    # 配置队列
    if queue_configs:
        for queue_name, config in queue_configs.items():
            registry.configure_queue(queue_name, config)
    
    # 设置重试策略
    if retry_policies:
        for task_name, policy in retry_policies.items():
            registry.set_retry_policy(task_name, policy)
    
    return registry


def with_task_info(
    registry: TaskRegistry,
    queue: str = "celery",
    priority: TaskPriority = TaskPriority.NORMAL,
    max_retries: int = 3,
    retry_delay: int = 60,
    time_limit: int = 3600,
    soft_time_limit: int = 3300,
    description: str = None,
    tags: List[str] = None
):
    """任务信息装饰器"""
    def decorator(func):
        task_info = TaskInfo(
            name=func.__name__,
            func=func,
            queue=queue,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            time_limit=time_limit,
            soft_time_limit=soft_time_limit,
            description=description,
            tags=tags
        )
        registry.register_task(task_info)
        return func
    return decorator


def with_monitoring(registry: TaskRegistry):
    """任务监控装饰器工厂"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            task_name = func.__name__
            start_time = time.time()

            try:
                # 记录任务开始
                registry.update_task_metrics(task_name, TaskStatus.STARTED)

                # 执行任务
                result = func(*args, **kwargs)

                # 记录任务成功
                execution_time = time.time() - start_time
                registry.update_task_metrics(
                    task_name, TaskStatus.SUCCESS, execution_time
                )

                return result

            except Exception as e:
                # 记录任务失败
                registry.update_task_metrics(
                    task_name, TaskStatus.FAILURE, error=str(e)
                )
                raise

        return wrapper
    return decorator


def with_dependencies(registry: TaskRegistry, *dependencies):
    """任务依赖装饰器工厂"""
    def decorator(func):
        registry.add_task_dependency(func.__name__, list(dependencies))
        return func
    return decorator


