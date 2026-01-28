"""
定时任务模块的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TaskCreate(BaseModel):
    """创建任务请求模型"""
    account_id: int = Field(..., description="账号 ID")
    task_name: str = Field(..., min_length=1, max_length=200, description="任务名称")
    task_type: str = Field(..., max_length=50, description="任务类型：content_generation/publishing")
    description: Optional[str] = Field(None, description="任务描述")
    cron_expression: Optional[str] = Field(None, max_length=100, description="Cron 表达式")
    interval_minutes: Optional[int] = Field(None, ge=1, description="间隔分钟数")
    run_at_time: Optional[str] = Field(None, max_length=50, description="运行时间（HH:MM 格式）")
    task_config: Optional[Dict[str, Any]] = Field(None, description="任务配置（JSON 格式）")
    is_enabled: bool = Field(True, description="是否启用")

    class Config:
        schema_extra = {
            "example": {
                "account_id": 1,
                "task_name": "每日内容生成",
                "task_type": "content_generation",
                "description": "每天早上10点自动生成内容",
                "cron_expression": "0 10 * * *",
                "task_config": {
                    "category": "技术文章",
                    "topic": "Python 教程"
                },
                "is_enabled": True
            }
        }


class TaskUpdate(BaseModel):
    """更新任务请求模型"""
    task_name: Optional[str] = Field(None, min_length=1, max_length=200, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    cron_expression: Optional[str] = Field(None, max_length=100, description="Cron 表达式")
    interval_minutes: Optional[int] = Field(None, ge=1, description="间隔分钟数")
    run_at_time: Optional[str] = Field(None, max_length=50, description="运行时间（HH:MM 格式）")
    task_config: Optional[Dict[str, Any]] = Field(None, description="任务配置（JSON 格式）")
    is_enabled: Optional[bool] = Field(None, description="是否启用")

    class Config:
        schema_extra = {
            "example": {
                "task_name": "每日内容生成（更新）",
                "is_enabled": False
            }
        }


class TaskRead(BaseModel):
    """任务响应模型"""
    id: int
    account_id: int
    task_name: str
    task_type: str
    description: Optional[str]
    cron_expression: Optional[str]
    interval_minutes: Optional[int]
    run_at_time: Optional[str]
    task_config: Optional[Dict[str, Any]]
    is_enabled: bool
    status: str
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    run_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TaskExecution(BaseModel):
    """任务执行记录响应模型"""
    id: int
    task_name: str
    task_type: str
    last_run_at: Optional[datetime]
    run_count: int
    failure_count: int
    status: str

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "task_name": "每日内容生成",
                "task_type": "content_generation",
                "last_run_at": "2023-10-01T10:00:00",
                "run_count": 30,
                "failure_count": 2,
                "status": "completed"
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
