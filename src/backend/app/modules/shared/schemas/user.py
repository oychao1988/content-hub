from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.core.permissions import get_user_permissions, get_role_permissions


class UserBase(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=64)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=128)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)

    @model_validator(mode="after")
    def validate_email(self):
        if self.email is None:
            raise ValueError("email is required")
        return self


class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)

    @model_validator(mode="after")
    def at_least_one_identifier(self):
        if not self.email and not self.username:
            raise ValueError("email or username is required")
        return self


class UserRead(UserBase):
    id: int
    role: str = "operator"  # 用户角色：admin/operator/customer
    permissions: List[str] = []  # 用户权限列表（基于角色自动计算）
    is_active: bool
    created_at: datetime

    @model_validator(mode="before")
    def compute_permissions(cls, values):
        """自动计算用户的权限列表"""
        if isinstance(values, dict):
            role = values.get("role", "operator")
            values["permissions"] = [perm.value for perm in get_role_permissions(role)]
        else:
            # 从 ORM 对象读取
            role = getattr(values, "role", "operator")
            permissions = get_role_permissions(role)
            setattr(values, "permissions", [perm.value for perm in permissions])
        return values

    class Config:
        from_attributes = True
