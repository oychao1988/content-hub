"""
内容相关数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Content(Base):
    """内容模型"""

    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)

    # 内容基本信息
    title = Column(String(255), nullable=False, comment="文章标题")
    content = Column(Text, nullable=False, comment="文章内容（Markdown）")
    image_url = Column(String(255), comment="图片 URL")
    image_path = Column(String(255), comment="本地图片路径")
    section_code = Column(String(50), comment="板块代码")
    category = Column(String(100), comment="内容分类")
    topic = Column(String(500), comment="选题")
    word_count = Column(Integer, default=0, comment="字数")
    cover_image = Column(String(255), comment="封面图片")
    images = Column(JSON, default=[], comment="图片列表")

    # 审核相关字段
    review_mode = Column(String(20), default="auto", comment="审核模式：auto/manual")
    review_status = Column(String(20), default="pending", comment="审核状态：pending/approved/rejected")
    review_comment = Column(Text, comment="审核意见")

    # 发布相关字段
    publish_status = Column(String(20), default="draft", comment="发布状态：draft/publishing/published/failed")
    priority = Column(Integer, default=5, comment="优先级（1-10）")
    scheduled_at = Column(DateTime(timezone=True), comment="计划发布时间")
    published_at = Column(DateTime(timezone=True), comment="实际发布时间")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    account = relationship("Account", back_populates="contents")
    publish_log = relationship("PublishLog", back_populates="content", uselist=False)
    pool_entry = relationship("PublishPool", back_populates="content", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Content(id={self.id}, title={self.title}, publish_status={self.publish_status})>"


class TopicHistory(Base):
    """选题历史记录"""

    __tablename__ = "topic_history"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)

    # 选题信息
    topic = Column(String(500), nullable=False, comment="选题")
    section_code = Column(String(50), comment="板块代码")
    source_url = Column(String(500), comment="来源 URL")
    source_name = Column(String(200), comment="来源名称")

    # 评分信息
    priority_score = Column(Integer, comment="优先级评分")
    freshness_score = Column(Integer, comment="时效性评分")
    relevance_score = Column(Integer, comment="相关性评分")

    # 状态
    status = Column(String(50), default="pending", comment="状态：pending/in_progress/completed/skipped")

    # 关联内容
    content_id = Column(Integer, ForeignKey("contents.id"), comment="关联的内容 ID")

    # 备注
    notes = Column(Text, comment="备注")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<TopicHistory(id={self.id}, topic={self.topic}, status={self.status})>"
