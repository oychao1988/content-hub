"""
ContentHub 配置文件
"""
import os
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
data_dir = os.path.join(base_dir, "data")
env_file = os.path.join(base_dir, ".env")


class Settings(BaseSettings):
    """ContentHub 配置"""

    # 应用基础配置
    APP_NAME: str = "ContentHub"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # 模块配置
    MODULES_ENABLED: str = "auth,accounts,content,scheduler,publisher,publish_pool,dashboard"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # API 配置
    API_V1_PREFIX: str = "/api/v1"
    API_STR: str = "/api/v1"

    # 数据库配置
    DATABASE_URL: Optional[str] = f"sqlite:///{os.path.join(data_dir, 'contenthub.db')}"

    # 安全配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 天
    RESET_TOKEN_EXPIRE_MINUTES: int = 30  # 30 分钟

    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3010", "http://localhost:3011", "http://localhost:5173"]

    # Content-Publisher 服务配置
    PUBLISHER_API_URL: str = "http://150.158.88.23:3010"
    PUBLISHER_API_KEY: str = ""

    # Content-Creator CLI 配置
    CREATOR_CLI_PATH: str = ""
    CREATOR_PROJECT_PATH: Optional[str] = None  # content-creator 项目路径
    CREATOR_WORK_DIR: str = os.path.join(data_dir, "creator-work")
    CREATOR_MODE: str = "async"  # sync | async - 内容生成模式

    # 默认写作风格配置
    DEFAULT_WRITING_STYLE_ID: int = 1  # 默认使用"专业技术风格"（ID 1）

    # Tavily API 配置（选题搜索）
    TAVILY_API_KEY: str = ""

    # 任务调度配置
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"

    # 文件存储配置
    STORAGE_ROOT: str = os.path.join(data_dir, "accounts")
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    IMAGE_UPLOAD_DIR: str = os.path.join(data_dir, "uploads", "images")  # 图片上传目录

    # 日志配置
    LOG_FILE: Optional[str] = "logs/contenthub.log"
    LOG_FORMAT: str = "detailed"  # simple | detailed
    LOG_ROTATION_SIZE: str = "10 MB"
    LOG_RETENTION_DAYS: int = 30
    LOG_ERROR_RETENTION_DAYS: int = 60
    LOG_COMPRESSION: bool = True
    LOG_ASYNC: bool = True
    LOG_SQL_QUERIES: bool = False
    LOG_HTTP_REQUESTS: bool = True
    LOG_PERFORMANCE: bool = False  # 性能日志
    LOG_THIRD_PARTY: bool = False  # 第三方库日志

    # 异步内容生成配置
    ASYNC_CONTENT_GENERATION_ENABLED: bool = True  # 是否启用异步内容生成
    ASYNC_MAX_CONCURRENT_TASKS: int = 5  # 最大并发任务数
    ASYNC_TASK_TIMEOUT: int = 1800  # 任务超时时间（秒）30分钟
    ASYNC_POLL_INTERVAL: int = 30  # 状态轮询间隔（秒）30秒
    ASYNC_AUTO_APPROVE: bool = True  # 是否自动审核通过
    ASYNC_WORKER_COUNT: int = 3  # Worker 进程数

    # Webhook 配置（可选）
    WEBHOOK_ENABLED: bool = False  # 是否启用 Webhook 通知
    WEBHOOK_URL: Optional[str] = None  # Webhook 回调 URL
    WEBHOOK_TIMEOUT: int = 10  # Webhook 请求超时（秒）
    WEBHOOK_SECRET_KEY: Optional[str] = None  # Webhook 签名密钥

    # Redis 配置（用于队列和缓存）
    REDIS_ENABLED: bool = False  # 是否启用 Redis
    REDIS_URL: str = "redis://localhost:6379/0"  # Redis 连接 URL

    model_config = SettingsConfigDict(
        env_file=env_file,
        validate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )


settings = Settings()
