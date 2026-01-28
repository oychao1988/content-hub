"""
内容管理模块的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ContentCreateRequest(BaseModel):
    """创建内容请求模型"""
    account_id: int = Field(..., description="账号 ID")
    topic: str = Field(..., min_length=1, max_length=500, description="选题")
    category: str = Field(..., min_length=1, max_length=100, description="内容板块")

    class Config:
        schema_extra = {
            "example": {
                "account_id": 1,
                "topic": "Python 异步编程",
                "category": "技术文章"
            }
        }


class ContentUpdate(BaseModel):
    """更新内容请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="文章标题")
    category: Optional[str] = Field(None, max_length=100, description="内容板块")
    topic: Optional[str] = Field(None, max_length=500, description="选题")
    content: Optional[str] = Field(None, description="Markdown 内容")
    html_content: Optional[str] = Field(None, description="HTML 内容")
    cover_image: Optional[str] = Field(None, description="封面图片路径")
    images: Optional[List[str]] = Field(None, description="图片列表")
    status: Optional[str] = Field(None, max_length=50, description="状态")
    tags: Optional[List[str]] = Field(None, description="标签列表")

    class Config:
        schema_extra = {
            "example": {
                "title": "Python 异步编程详解",
                "content": "# Python 异步编程\n\n## 简介\n\n异步编程是..."
            }
        }


class ContentRead(BaseModel):
    """内容响应模型"""
    id: int
    account_id: int
    title: str
    category: Optional[str]
    topic: Optional[str]
    markdown_path: Optional[str]
    content: Optional[str]
    html_content: Optional[str]
    cover_image: Optional[str]
    images: Optional[List[str]]
    status: str
    review_mode: str
    review_status: str
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[int]
    review_comment: Optional[str]
    word_count: Optional[int]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    class Config:
        orm_mode = True


class ContentDetailRead(ContentRead):
    """内容详情响应模型（含审核信息）"""
    pass


class ContentListRead(BaseModel):
    """内容列表项响应模型"""
    id: int
    title: str
    category: Optional[str]
    status: str
    review_status: str
    word_count: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class SubmitReviewRequest(BaseModel):
    """提交审核请求模型"""
    pass


class ApproveRequest(BaseModel):
    """审核通过请求模型"""
    reviewer_id: Optional[int] = Field(None, description="审核人 ID")


class RejectRequest(BaseModel):
    """审核拒绝请求模型"""
    reason: str = Field(..., min_length=1, description="拒绝原因")
    reviewer_id: Optional[int] = Field(None, description="审核人 ID")


class ReviewStatistics(BaseModel):
    """审核统计响应模型"""
    total: int
    pending: int
    reviewing: int
    approved: int
    rejected: int

    class Config:
        schema_extra = {
            "example": {
                "total": 100,
                "pending": 20,
                "reviewing": 10,
                "approved": 60,
                "rejected": 10
            }
        }
