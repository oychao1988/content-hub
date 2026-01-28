from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


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
    roles: List[str] = ["user"]
    is_active: bool
    created_at: datetime

    @model_validator(mode="before")
    def split_roles(cls, values):
        if isinstance(values, dict):
            roles = values.get("roles")
        else:
            roles = getattr(values, "roles", None)
        if isinstance(roles, str):
            normalized = [r for r in roles.split(",") if r]
            if isinstance(values, dict):
                values["roles"] = normalized
            else:
                setattr(values, "roles", normalized)
        return values

    class Config:
        from_attributes = True
