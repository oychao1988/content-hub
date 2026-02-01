"""
用户相关数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.sql_db import Base


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True, comment="用户名")
    email = Column(String(100), nullable=False, unique=True, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    full_name = Column(String(100), comment="全名")
    role = Column(String(20), default="operator", nullable=False, comment="角色：admin/operator/customer")
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 客户关联（仅客户角色有值）
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, comment="客户 ID")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    customer = relationship("Customer", back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
