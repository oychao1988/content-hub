"""
定时任务模块的 Pydantic 模型
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class TaskCreate(BaseModel):
    """创建任务请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="任务名称")
    description: Optional[str] = Field(None, max_length=255, description="任务描述")
    cron_expression: Optional[str] = Field(None, max_length=50, description="Cron 表达式")
    interval: Optional[int] = Field(None, ge=1, description="间隔时间")
    interval_unit: Optional[str] = Field(None, max_length=20, description="间隔单位：minutes/hours/days")
    is_active: bool = Field(True, description="是否启用")
    # 兼容前端字段名：前端使用 job_type，后端使用 task_type
    job_type: Optional[str] = Field(None, max_length=50, description="任务类型（兼容字段）")
    job_params: Optional[str] = Field(None, description="任务参数（兼容字段）")
    # 后端字段
    task_type: Optional[str] = Field(None, max_length=50, description="任务类型：content_generation/publishing")

    @model_validator(mode='after')
    def validate_task_type(self):
        """如果前端提供了 job_type，使用它作为 task_type"""
        if self.task_type is None and self.job_type is not None:
            # 使用 object.__setattr__ 绕过 Pydantic 的 frozen 限制
            object.__setattr__(self, 'task_type', self.job_type)
        if self.task_type is None:
            raise ValueError("字段 'task_type' 或 'job_type' 是必填项")
        return self

    class Config:
        schema_extra = {
            "example": {
                "name": "每日内容生成",
                "task_type": "content_generation",
                "description": "每天早上10点自动生成内容",
                "cron_expression": "0 10 * * *",
                "is_active": True
            }
        }


class TaskUpdate(BaseModel):
    """更新任务请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="任务名称")  # 修复：从 task_name 改为 name
    description: Optional[str] = Field(None, max_length=255, description="任务描述")
    cron_expression: Optional[str] = Field(None, max_length=50, description="Cron 表达式")
    interval: Optional[int] = Field(None, ge=1, description="间隔时间")  # 修复：从 interval_minutes 改为 interval
    interval_unit: Optional[str] = Field(None, max_length=20, description="间隔单位：minutes/hours/days")  # 新增
    is_active: Optional[bool] = Field(None, description="是否启用")  # 修复：从 is_enabled 改为 is_active

    class Config:
        schema_extra = {
            "example": {
                "name": "每日内容生成（更新）",
                "is_active": False
            }
        }


class TaskRead(BaseModel):
    """任务响应模型"""
    id: int
    name: str  # 修复：从 task_name 改为 name
    description: Optional[str]
    task_type: str
    cron_expression: Optional[str]
    interval: Optional[int]  # 修复：从 interval_minutes 改为 interval
    interval_unit: Optional[str]  # 新增：匹配数据库字段
    is_active: bool  # 修复：从 is_enabled 改为 is_active
    last_run_time: Optional[datetime]  # 修复：从 last_run_at 改为 last_run_time
    next_run_time: Optional[datetime]  # 修复：从 next_run_at 改为 next_run_time
    created_at: datetime
    updated_at: datetime

    # 计算字段（在服务层填充）
    run_count: int = 0  # 执行次数
    failure_count: int = 0  # 失败次数
    status: str = "idle"  # 状态：idle/running/paused

    class Config:
        orm_mode = True


class TaskExecution(BaseModel):
    """任务执行记录响应模型"""
    id: int
    task_id: int
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[int]
    error_message: Optional[str]
    result: Optional[Dict[str, Any]]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "task_id": 1,
                "status": "success",
                "start_time": "2023-10-01T10:00:00",
                "end_time": "2023-10-01T10:00:30",
                "duration": 30
            }
        }


class SchedulerStatus(BaseModel):
    """调度器状态响应模型"""
    running: bool
    jobs_count: int

    class Config:
        schema_extra = {
            "example": {
                "running": True,
                "jobs_count": 5
            }
        }
