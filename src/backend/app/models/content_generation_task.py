"""
内容生成任务模型
用于异步内容生成系统的任务追踪和管理
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.sql_db import Base


class ContentGenerationTask(Base):
    """内容生成任务模型"""

    __tablename__ = "content_generation_tasks"

    id = Column(Integer, primary_key=True, index=True)

    # 任务标识
    task_id = Column(String(100), unique=True, nullable=False, index=True, comment="任务唯一标识")

    # 关联对象
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=True, comment="生成的内容 ID")
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True, comment="账号 ID")

    # 任务参数
    topic = Column(String(500), comment="选题")
    keywords = Column(String(500), comment="关键词（逗号分隔）")
    category = Column(String(100), comment="内容分类")
    requirements = Column(Text, comment="特殊要求")
    tone = Column(String(50), comment="语气风格")

    # 任务状态
    status = Column(String(50), default="pending", index=True, comment="任务状态：pending/processing/completed/failed/timeout")
    priority = Column(Integer, default=5, comment="优先级（1-10）")
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")

    # 时间戳
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), comment="提交时间")
    started_at = Column(DateTime(timezone=True), comment="开始执行时间")
    completed_at = Column(DateTime(timezone=True), comment="完成时间")
    timeout_at = Column(DateTime(timezone=True), comment="超时时间")

    # 结果
    result = Column(JSON, comment="生成结果（JSON 格式）")
    error_message = Column(Text, comment="错误信息")

    # 自动流程配置
    auto_approve = Column(Boolean, default=True, comment="是否自动审核通过")

    # Webhook 回调配置
    callback_url = Column(String(500), nullable=True, comment="Webhook 回调 URL")

    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    content = relationship("Content", back_populates="generation_tasks")
    account = relationship("Account", back_populates="generation_tasks")

    # 索引
    __table_args__ = (
        Index('idx_task_status', 'status'),
        Index('idx_task_account', 'account_id'),
        Index('idx_task_submitted', 'submitted_at'),
        Index('idx_task_content', 'content_id'),
    )

    def __repr__(self):
        return f"<ContentGenerationTask(id={self.id}, task_id={self.task_id}, status={self.status})>"
