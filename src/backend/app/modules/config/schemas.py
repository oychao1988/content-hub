"""
系统配置模块的 Pydantic 模型
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ============= 写作风格相关 Schema =============

class WritingStyleBase(BaseModel):
    """写作风格基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="风格名称")
    code: str = Field(..., min_length=1, max_length=50, description="风格代码")
    description: Optional[str] = Field(None, description="风格描述")
    tone: Optional[str] = Field("专业", max_length=50, description="语气")
    persona: Optional[str] = Field(None, description="人设")
    min_words: Optional[int] = Field(800, ge=100, le=10000, description="最小字数")
    max_words: Optional[int] = Field(1500, ge=100, le=10000, description="最大字数")
    emoji_usage: Optional[str] = Field("适度", max_length=20, description="表情使用")
    forbidden_words: Optional[List[str]] = Field(default_factory=list, description="禁用词列表")
    is_system: Optional[bool] = Field(False, description="是否系统级风格")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "专业技术风格",
                "code": "tech_professional",
                "description": "适合技术博客的专业写作风格",
                "tone": "专业",
                "persona": "技术专家",
                "min_words": 800,
                "max_words": 1500,
                "emoji_usage": "适度",
                "forbidden_words": ["非常好的", "特别棒的"],
                "is_system": False
            }
        }
    )


class WritingStyleCreate(WritingStyleBase):
    """创建写作风格请求模型"""
    pass


class WritingStyleUpdate(BaseModel):
    """更新写作风格请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="风格名称")
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="风格代码")
    description: Optional[str] = Field(None, description="风格描述")
    tone: Optional[str] = Field(None, max_length=50, description="语气")
    persona: Optional[str] = Field(None, description="人设")
    min_words: Optional[int] = Field(None, ge=100, le=10000, description="最小字数")
    max_words: Optional[int] = Field(None, ge=100, le=10000, description="最大字数")
    emoji_usage: Optional[str] = Field(None, max_length=20, description="表情使用")
    forbidden_words: Optional[List[str]] = Field(None, description="禁用词列表")
    is_system: Optional[bool] = Field(None, description="是否系统级风格")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "专业技术风格（更新）",
                "description": "适合技术博客的专业写作风格，更注重实践"
            }
        }
    )


class WritingStyleResponse(BaseModel):
    """写作风格响应模型"""
    id: int
    name: str
    code: str
    description: Optional[str]
    tone: Optional[str]
    persona: Optional[str]
    min_words: Optional[int]
    max_words: Optional[int]
    emoji_usage: Optional[str]
    forbidden_words: Optional[List[str]]
    is_system: bool
    account_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= 内容主题相关 Schema =============

class ContentThemeBase(BaseModel):
    """内容主题基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="主题名称")
    code: str = Field(..., min_length=1, max_length=50, description="主题代码")
    description: Optional[str] = Field(None, description="主题描述")
    type: Optional[str] = Field(None, max_length=50, description="主题类型")
    is_system: Optional[bool] = Field(False, description="是否系统级主题")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "技术教程",
                "code": "tech_tutorial",
                "description": "技术教程类内容主题",
                "type": "技术",
                "is_system": False
            }
        }
    )


class ContentThemeCreate(ContentThemeBase):
    """创建内容主题请求模型"""
    pass


class ContentThemeUpdate(BaseModel):
    """更新内容主题请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="主题名称")
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="主题代码")
    description: Optional[str] = Field(None, description="主题描述")
    type: Optional[str] = Field(None, max_length=50, description="主题类型")
    is_system: Optional[bool] = Field(None, description="是否系统级主题")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "技术教程（更新）",
                "description": "技术教程类内容主题，包含实战案例"
            }
        }
    )


class ContentThemeResponse(BaseModel):
    """内容主题响应模型"""
    id: int
    name: str
    code: str
    description: Optional[str]
    type: Optional[str]
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)