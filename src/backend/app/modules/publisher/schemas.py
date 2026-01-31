"""
发布管理模块的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PublishRequest(BaseModel):
    """发布请求模型"""
    content_id: int = Field(..., description="内容 ID")
    account_id: int = Field(..., description="账号 ID")
    publish_to_draft: bool = Field(True, description="是否发布到草稿箱")

    class Config:
        schema_extra = {
            "example": {
                "content_id": 1,
                "account_id": 1,
                "publish_to_draft": True
            }
        }


class BatchPublishRequest(BaseModel):
    """批量发布请求模型"""
    account_id: int = Field(..., description="账号 ID")
    content_ids: List[int] = Field(..., min_items=1, description="内容 ID 列表")
    publish_to_draft: bool = Field(True, description="是否发布到草稿箱")

    class Config:
        schema_extra = {
            "example": {
                "account_id": 1,
                "content_ids": [1, 2, 3],
                "publish_to_draft": True
            }
        }


class PublishLogRead(BaseModel):
    """发布日志响应模型"""
    id: int
    account_id: int
    content_id: int
    platform: str
    media_id: Optional[str]
    status: str
    error_message: Optional[str]
    theme: Optional[str]
    publish_to_draft: bool
    response_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


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


class PublishResult(BaseModel):
    """发布结果响应模型"""
    success: bool
    log_id: int
    media_id: Optional[str]
    error: Optional[str]
    message: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "log_id": 1,
                "media_id": "1234567890",
                "message": "发布成功"
            }
        }


class BatchPublishResult(BaseModel):
    """批量发布结果响应模型"""
    total: int
    success: int
    fail: int
    results: List[Dict[str, Any]]

    class Config:
        schema_extra = {
            "example": {
                "total": 3,
                "success": 2,
                "fail": 1,
                "results": [
                    {
                        "content_id": 1,
                        "success": True,
                        "media_id": "1234567890",
                        "published_at": "2023-10-01T10:00:00"
                    },
                    {
                        "content_id": 2,
                        "success": False,
                        "error": "发布失败"
                    }
                ]
            }
        }


class RetryPublishRequest(BaseModel):
    """重试发布请求模型"""
    pass
