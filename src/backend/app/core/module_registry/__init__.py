"""
模块注册框架

提供通用的模型和任务注册机制，避免各模块重复代码
"""

from .models import (
    ModelRegistry,
    ModelType,
    ModelVersion,
    create_model_registry,
    get_model_registry_status,
    validate_model_data,
)
from .tasks import (
    TaskRegistry,
    TaskPriority,
    TaskQueue,
    TaskStatus,
    TaskInfo,
    create_task_registry,
    with_task_info,
    with_monitoring,
    with_dependencies,
)

__all__ = [
    # Models
    "ModelRegistry",
    "ModelType",
    "ModelVersion",
    "create_model_registry",
    "get_model_registry_status",
    "validate_model_data",
    # Tasks
    "TaskRegistry",
    "TaskPriority",
    "TaskQueue",
    "TaskStatus",
    "TaskInfo",
    "create_task_registry",
    "with_task_info",
    "with_monitoring",
    "with_dependencies",
]


