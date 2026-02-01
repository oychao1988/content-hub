"""
用户管理 Pydantic 模型
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: Optional[EmailStr] = None
    role: Optional[str] = "viewer"


class UserCreate(UserBase):
    """创建用户模型"""
    password: str


class UserUpdate(BaseModel):
    """更新用户模型"""
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    pages: int
