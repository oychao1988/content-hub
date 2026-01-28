"""
发布相关数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class PublishLog(Base):
    """发布日志模型"""

    __tablename__ = "publish_logs"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False, unique=True, index=True)

    # 发布信息
    platform = Column(String(50), default="wechat", comment="发布平台")
    media_id = Column(String(255), comment="媒体 ID（微信公众号返回）")

    # 发布结果
    status = Column(String(20), default="pending", comment="状态：pending/success/failed")
    error_message = Column(Text, comment="错误信息")

    # 重试配置
    retry_count = Column(Integer, default=0, comment="重试次数")
    result = Column(Text, comment="发布结果详情")

    # 时间戳
    publish_time = Column(DateTime(timezone=True), comment="发布时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    account = relationship("Account", back_populates="publish_logs")
    content = relationship("Content", back_populates="publish_log")
    pool_entry = relationship("PublishPool", back_populates="published_log")

    def __repr__(self):
        return f"<PublishLog(id={self.id}, content_id={self.content_id}, status={self.status})>"


class PublishPool(Base):
    """发布池模型"""

    __tablename__ = "publish_pool"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False, unique=True, index=True)

    # 优先级和调度
    priority = Column(Integer, default=5, comment="优先级（1-10，数字越小优先级越高）")
    scheduled_at = Column(DateTime(timezone=True), comment="计划发布时间")

    # 发布状态
    status = Column(String(20), default="pending", comment="状态：pending/publishing/published/failed")
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    last_error = Column(Text, comment="最后一次错误信息")
    published_at = Column(DateTime(timezone=True), comment="实际发布时间")
    published_log_id = Column(Integer, ForeignKey("publish_logs.id"), comment="关联的发布日志ID")

    # 时间戳
    added_at = Column(DateTime(timezone=True), server_default=func.now(), comment="加入发布池时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    content = relationship("Content", back_populates="pool_entry")
    published_log = relationship("PublishLog", back_populates="pool_entry")

    # 索引
    __table_args__ = (
        Index('idx_priority_scheduled', 'priority', 'scheduled_at'),
    )

    def __repr__(self):
        return f"<PublishPool(id={self.id}, content_id={self.content_id}, priority={self.priority}, status={self.status})>"
