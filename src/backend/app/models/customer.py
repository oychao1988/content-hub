"""
客户相关数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.sql_db import Base


class Customer(Base):
    """客户模型"""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, comment="客户名称")
    contact_name = Column(String(100), comment="联系人姓名")
    contact_email = Column(String(100), comment="联系人邮箱")
    contact_phone = Column(String(20), comment="联系人电话")
    description = Column(Text, comment="客户描述")
    is_active = Column(Boolean, default=True, comment="是否激活")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    users = relationship("User", back_populates="customer")
    accounts = relationship("Account", back_populates="customer")

    def __repr__(self):
        return f"<Customer(id={self.id}, name={self.name})>"
