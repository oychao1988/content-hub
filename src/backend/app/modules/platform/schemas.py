"""
平台管理模块的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PlatformBase(BaseModel):
    """平台基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="平台名称")
    code: str = Field(..., min_length=1, max_length=50, description="平台代码")
    type: Optional[str] = Field(None, max_length=50, description="平台类型")
    description: Optional[str] = Field(None, description="平台描述")
    api_url: Optional[str] = Field(None, max_length=255, description="API 地址")
    api_key: Optional[str] = Field(None, max_length=255, description="API 密钥")
    is_active: bool = Field(True, description="是否激活")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "微信公众号",
                "code": "wechat_mp",
                "type": "social",
                "description": "微信公众号平台",
                "api_url": "https://api.weixin.qq.com",
                "api_key": "your-api-key",
                "is_active": True
            }
        }
    }


class PlatformCreate(PlatformBase):
    """创建平台请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="平台名称")
    code: str = Field(..., min_length=1, max_length=50, description="平台代码")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "新浪微博",
                "code": "weibo",
                "type": "social",
                "description": "新浪微博平台",
                "api_url": "https://api.weibo.com",
                "api_key": "your-api-key",
                "is_active": True
            }
        }
    }


class PlatformUpdate(BaseModel):
    """更新平台请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="平台名称")
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="平台代码")
    type: Optional[str] = Field(None, max_length=50, description="平台类型")
    description: Optional[str] = Field(None, description="平台描述")
    api_url: Optional[str] = Field(None, max_length=255, description="API 地址")
    api_key: Optional[str] = Field(None, max_length=255, description="API 密钥")
    is_active: Optional[bool] = Field(None, description="是否激活")

    model_config = {
        "json_schema_extra": {
            "example": {
                "description": "更新后的平台描述",
                "is_active": False
            }
        }
    }


class PlatformResponse(PlatformBase):
    """平台响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlatformListResponse(BaseModel):
    """平台列表响应模型"""
    items: List[PlatformResponse]
    total: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [],
                "total": 0
            }
        }
    }
