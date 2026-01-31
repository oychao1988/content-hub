"""
发布池管理模块的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AddToPoolRequest(BaseModel):
    """添加到发布池请求模型"""
    content_id: int = Field(..., description="内容 ID")
    priority: int = Field(5, ge=1, le=10, description="优先级（1-10，数字越小优先级越高）")
    scheduled_at: Optional[datetime] = Field(None, description="计划发布时间")

    class Config:
        schema_extra = {
            "example": {
                "content_id": 1,
                "priority": 3,
                "scheduled_at": "2023-10-01T10:00:00"
            }
        }


class UpdatePoolEntryRequest(BaseModel):
    """更新发布池条目请求模型"""
    priority: Optional[int] = Field(None, ge=1, le=10, description="优先级（1-10，数字越小优先级越高）")
    scheduled_at: Optional[datetime] = Field(None, description="计划发布时间")
    status: Optional[str] = Field(None, max_length=50, description="状态")
    retry_count: Optional[int] = Field(None, ge=0, description="重试次数")
    max_retries: Optional[int] = Field(None, ge=0, description="最大重试次数")
    last_error: Optional[str] = Field(None, description="最后一次错误信息")

    class Config:
        schema_extra = {
            "example": {
                "priority": 2,
                "scheduled_at": "2023-10-01T11:00:00"
            }
        }


class PublishPoolRead(BaseModel):
    """发布池响应模型"""
    id: int
    content_id: int
    priority: int
    scheduled_at: Optional[datetime]
    status: str
    retry_count: int
    max_retries: int
    last_error: Optional[str]
    published_log_id: Optional[int]
    added_at: datetime  # 修复：从 created_at 改为 added_at
    updated_at: datetime
    published_at: Optional[datetime]

    class Config:
        orm_mode = True


class PublishPoolStatistics(BaseModel):
    """发布池统计响应模型"""
    total: int
    pending: int
    publishing: int
    published: int
    failed: int

    class Config:
        schema_extra = {
            "example": {
                "total": 10,
                "pending": 3,
                "publishing": 1,
                "published": 5,
                "failed": 1
            }
        }


class PoolEntryStatusUpdate(BaseModel):
    """发布池条目状态更新请求模型"""
    status: str = Field(..., max_length=50, description="状态")
