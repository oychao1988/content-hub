"""
平台相关数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.sql_db import Base


class Platform(Base):
    """平台模型"""

    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, comment="平台名称")
    code = Column(String(50), nullable=False, unique=True, index=True, comment="平台代码")
    type = Column(String(50), comment="平台类型")
    description = Column(Text, comment="平台描述")
    api_url = Column(String(255), comment="API 地址")
    api_key = Column(String(255), comment="API 密钥")
    is_active = Column(Boolean, default=True, comment="是否激活")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    accounts = relationship("Account", back_populates="platform")

    def __repr__(self):
        return f"<Platform(id={self.id}, name={self.name}, code={self.code})>"
