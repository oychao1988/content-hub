"""
CLI 配置管理

从环境变量和 .env 文件加载配置。
"""

from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv


class CLIConfig:
    """CLI 配置管理"""

    def __init__(self):
        self._load_env()

    def _load_env(self):
        """加载环境变量

        按优先级加载配置文件：
        1. ./contenthub.env              # 当前目录
        2. ~/.contenthub.env             # 用户主目录
        3. /etc/contenthub/env           # 系统配置目录
        4. src/backend/.env              # 开发环境
        """
        env_files = [
            Path("./contenthub.env"),
            Path.home() / ".contenthub.env",
            Path("/etc/contenthub/env"),
            Path("src/backend/.env"),
        ]

        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file, override=True)
                break

    @property
    def database_url(self) -> str:
        """数据库连接字符串"""
        return os.getenv("CLI_DB_PATH") or os.getenv(
            "DATABASE_URL",
            "sqlite:///./data/contenthub.db"
        )

    @property
    def creator_cli_path(self) -> Optional[str]:
        """content-creator CLI 路径"""
        return os.getenv("CREATOR_CLI_PATH")

    @property
    def publisher_api_url(self) -> str:
        """发布服务 URL"""
        return os.getenv("PUBLISHER_API_URL", "http://localhost:3010")

    @property
    def publisher_api_key(self) -> Optional[str]:
        """发布服务 API 密钥"""
        return os.getenv("PUBLISHER_API_KEY")

    @property
    def tavily_api_key(self) -> Optional[str]:
        """Tavily API 密钥"""
        return os.getenv("TAVILY_API_KEY")

    @property
    def log_level(self) -> str:
        """日志级别"""
        return os.getenv("LOG_LEVEL", "INFO")

    @property
    def output_format(self) -> str:
        """输出格式"""
        return os.getenv("CLI_FORMAT", "table")


# 全局配置实例
config = CLIConfig()
