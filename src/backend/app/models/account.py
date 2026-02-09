"""
账号相关数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.sql_db import Base


class Account(Base):
    """账号模型"""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True, comment="客户 ID")
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True, comment="平台 ID")

    # 用户关联（方案 A: 审计追踪）
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人 ID")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="最后修改人 ID")

    # 用户关联（方案 B: 账号所有者）
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="账号所有者 ID")

    name = Column(String(100), nullable=False, comment="账号名称")
    directory_name = Column(String(100), nullable=False, comment="目录名称")
    description = Column(Text, comment="账号描述")

    # 微信公众号配置
    wechat_app_id = Column(String(50), comment="微信公众号 AppID")
    wechat_app_secret = Column(String(255), comment="微信公众号 AppSecret（加密存储）")
    publisher_api_key = Column(String(255), comment="Publisher API 密钥")

    is_active = Column(Boolean, default=True, comment="是否激活")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    customer = relationship("Customer", back_populates="accounts")
    platform = relationship("Platform", back_populates="accounts")

    # 用户关系
    creator = relationship("User", foreign_keys=[created_by], backref="created_accounts")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_accounts")
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_accounts")

    configs = relationship("AccountConfig", back_populates="account", cascade="all, delete-orphan")
    writing_style = relationship("WritingStyle", back_populates="account", uselist=False, cascade="all, delete-orphan")
    content_sections = relationship("ContentSection", back_populates="account", cascade="all, delete-orphan")
    data_sources = relationship("DataSource", back_populates="account", cascade="all, delete-orphan")
    publish_config = relationship("PublishConfig", back_populates="account", uselist=False, cascade="all, delete-orphan")
    contents = relationship("Content", back_populates="account", cascade="all, delete-orphan")
    publish_logs = relationship("PublishLog", back_populates="account", cascade="all, delete-orphan")
    generation_tasks = relationship("ContentGenerationTask", back_populates="account", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_customer_platform', 'customer_id', 'platform_id'),
        Index('idx_directory_name', 'directory_name', unique=True),
    )

    def __repr__(self):
        return f"<Account(id={self.id}, name={self.name}, directory_name={self.directory_name})>"


class WritingStyle(Base):
    """写作风格配置"""

    __tablename__ = "writing_styles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="风格名称")
    code = Column(String(50), nullable=False, comment="风格代码")
    description = Column(Text, comment="风格描述")
    tone = Column(String(50), default="专业", comment="语气")
    persona = Column(Text, comment="人设")
    min_words = Column(Integer, default=800, comment="最小字数")
    max_words = Column(Integer, default=1500, comment="最大字数")
    emoji_usage = Column(String(20), default="适度", comment="表情使用：不使用/适度/频繁")
    forbidden_words = Column(JSON, default=list, comment="禁用词列表")
    is_system = Column(Boolean, default=False, comment="是否系统级风格")
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True, comment="账号 ID（系统级为 NULL）")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    account = relationship("Account", back_populates="writing_style")

    def __repr__(self):
        return f"<WritingStyle(id={self.id}, name={self.name}, code={self.code})>"


class ContentSection(Base):
    """内容板块配置"""

    __tablename__ = "content_sections"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, comment="板块名称")
    code = Column(String(50), nullable=False, comment="板块代码")
    description = Column(String(255), comment="板块描述")
    word_count = Column(Integer, default=1000, comment="字数要求")
    update_frequency = Column(String(20), default="每日", comment="更新频率")
    publish_time = Column(String(50), comment="发布时间")
    modules = Column(JSON, default=list, comment="模块列表")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    account = relationship("Account", back_populates="content_sections")

    def __repr__(self):
        return f"<ContentSection(id={self.id}, name={self.name}, code={self.code})>"


class DataSource(Base):
    """数据源配置"""

    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, comment="数据源名称")
    type = Column(String(50), default="tavily", comment="数据源类型：tavily/rss/api")
    url = Column(String(255), comment="数据源 URL")
    strategy = Column(Text, comment="搜索策略")
    keywords = Column(JSON, default=list, comment="关键词列表")
    scoring_criteria = Column(JSON, default=dict, comment="评分标准")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    account = relationship("Account", back_populates="data_sources")

    def __repr__(self):
        return f"<DataSource(id={self.id}, name={self.name}, type={self.type})>"


class PublishConfig(Base):
    """发布配置"""

    __tablename__ = "publish_configs"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, unique=True, index=True)
    theme_id = Column(Integer, ForeignKey("content_themes.id"), nullable=True, comment="主题 ID")

    # 审核配置
    review_mode = Column(String(20), default="auto", comment="审核模式：auto/manual")

    # 发布配置
    publish_mode = Column(String(20), default="draft", comment="发布模式：draft/live")
    auto_publish = Column(Boolean, default=False, comment="是否自动发布")

    # 定时发布配置
    publish_times = Column(JSON, default=list, comment="发布时间列表")
    section_theme_map = Column(JSON, default=dict, comment="板块主题映射")
    batch_settings = Column(JSON, default=dict, comment="批量发布设置")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    account = relationship("Account", back_populates="publish_config")
    theme = relationship("ContentTheme", back_populates="publish_configs")

    def __repr__(self):
        return f"<PublishConfig(id={self.id}, account_id={self.account_id})>"


# 通用配置表（用于存储 Markdown 配置）
class AccountConfig(Base):
    """通用账号配置表"""

    __tablename__ = "account_configs"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    config_type = Column(String(50), nullable=False, comment="配置类型")
    config_name = Column(String(100), comment="配置名称")
    config_data = Column(JSON, comment="配置数据（JSON 格式）")
    markdown_content = Column(Text, comment="Markdown 原文（备份）")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    account = relationship("Account", back_populates="configs")

    def __repr__(self):
        return f"<AccountConfig(id={self.id}, config_type={self.config_type}, account_id={self.account_id})>"
