"""
主题相关数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class ContentTheme(Base):
    """内容主题模型"""

    __tablename__ = "content_themes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, comment="主题名称")
    code = Column(String(50), nullable=False, unique=True, index=True, comment="主题代码")
    description = Column(Text, comment="主题描述")
    type = Column(String(50), comment="主题类型")
    is_system = Column(Boolean, default=False, comment="是否系统级主题")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    publish_configs = relationship("PublishConfig", back_populates="theme")

    def __repr__(self):
        return f"<ContentTheme(id={self.id}, name={self.name}, code={self.code})>"
