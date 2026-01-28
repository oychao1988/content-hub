"""
客户管理模块的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CustomerBase(BaseModel):
    """客户基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="客户名称")
    contact_name: Optional[str] = Field(None, max_length=100, description="联系人姓名")
    contact_email: Optional[str] = Field(None, max_length=100, description="联系人邮箱")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系人电话")
    description: Optional[str] = Field(None, description="客户描述")
    is_active: bool = Field(True, description="是否激活")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "示例客户",
                "contact_name": "张三",
                "contact_email": "zhangsan@example.com",
                "contact_phone": "13800138000",
                "description": "这是一个示例客户",
                "is_active": True
            }
        }
    }


class CustomerCreate(CustomerBase):
    """创建客户请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="客户名称")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "新客户",
                "contact_name": "李四",
                "contact_email": "lisi@example.com",
                "contact_phone": "13900139000",
                "description": "这是一个新客户",
                "is_active": True
            }
        }
    }


class CustomerUpdate(BaseModel):
    """更新客户请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="客户名称")
    contact_name: Optional[str] = Field(None, max_length=100, description="联系人姓名")
    contact_email: Optional[str] = Field(None, max_length=100, description="联系人邮箱")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系人电话")
    description: Optional[str] = Field(None, description="客户描述")
    is_active: Optional[bool] = Field(None, description="是否激活")

    model_config = {
        "json_schema_extra": {
            "example": {
                "contact_name": "王五",
                "contact_email": "wangwu@example.com",
                "is_active": False
            }
        }
    }


class CustomerResponse(CustomerBase):
    """客户响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerListResponse(BaseModel):
    """客户列表响应模型"""
    items: List[CustomerResponse]
    total: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [],
                "total": 0
            }
        }
    }
