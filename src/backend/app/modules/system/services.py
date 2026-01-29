"""
System module service layer
"""
import os
import sys
import time
import platform
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.cache import redis_client, get_cache_stats
from app.utils.custom_logger import logger


# Track application start time
_app_start_time = time.time()


class SystemService:
    """系统管理服务"""

    @staticmethod
    def get_health_status(db: Session) -> Dict[str, Any]:
        """
        获取系统健康状态

        Args:
            db: 数据库会话

        Returns:
            包含健康状态信息的字典
        """
        # 检查数据库连接
        database_status = SystemService._check_database(db)

        # 检查外部服务
        services_status = {
            "redis": SystemService._check_redis(),
            "content_publisher": SystemService._check_content_publisher(),
            "content_creator": SystemService._check_content_creator()
        }

        # 确定整体健康状态
        if database_status == "connected":
            if all(status == "available" for status in services_status.values()):
                overall_status = "healthy"
            else:
                overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "version": settings.APP_VERSION,
            "uptime": time.time() - _app_start_time,
            "database": database_status,
            "services": services_status
        }

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """
        获取系统信息

        Returns:
            包含系统信息的字典
        """
        return {
            "version": settings.APP_VERSION,
            "python_version": sys.version.split()[0],
            "environment": "development" if settings.DEBUG else "production",
            "platform": platform.platform(),
            "app_name": settings.APP_NAME,
            "debug_mode": settings.DEBUG
        }

    @staticmethod
    def get_metrics(db: Session) -> Dict[str, Any]:
        """
        获取系统指标

        Args:
            db: 数据库会话

        Returns:
            包含系统指标的字典
        """
        # 获取缓存统计
        cache_stats = get_cache_stats()

        # 获取活跃用户数（最近5分钟有活动的用户）
        active_users = SystemService._get_active_users_count(db)

        # 请求统计（简化版本，实际应该从监控中间件获取）
        requests_total = cache_stats.get("hits", 0) + cache_stats.get("misses", 0)
        requests_per_minute = requests_total / max(1, (time.time() - _app_start_time) / 60)

        return {
            "requests_total": requests_total,
            "requests_per_minute": round(requests_per_minute, 2),
            "active_users": active_users,
            "cache_stats": cache_stats,
            "uptime": time.time() - _app_start_time
        }

    @staticmethod
    def _check_database(db: Session) -> str:
        """
        检查数据库连接状态

        Args:
            db: 数据库会话

        Returns:
            连接状态字符串
        """
        try:
            # 执行简单查询测试连接
            db.execute(text("SELECT 1"))
            return "connected"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return f"error: {str(e)}"

    @staticmethod
    def _check_redis() -> str:
        """
        检查 Redis 连接状态

        Returns:
            连接状态字符串
        """
        try:
            if redis_client and redis_client.ping():
                return "available"
            return "unavailable"
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return "unavailable"

    @staticmethod
    def _check_content_publisher() -> str:
        """
        检查 Content-Publisher 服务状态

        Returns:
            服务状态字符串
        """
        if not settings.PUBLISHER_API_URL:
            return "not_configured"

        # 简化检查，实际应该发送 HTTP 请求
        # 这里只检查是否配置了 URL
        return "available" if settings.PUBLISHER_API_URL else "not_configured"

    @staticmethod
    def _check_content_creator() -> str:
        """
        检查 Content-Creator CLI 状态

        Returns:
            服务状态字符串
        """
        if not settings.CREATOR_CLI_PATH:
            return "not_configured"

        # 检查 CLI 路径是否存在
        if os.path.exists(settings.CREATOR_CLI_PATH):
            return "available"
        return "not_found"

    @staticmethod
    def _get_active_users_count(db: Session) -> int:
        """
        获取活跃用户数

        Args:
            db: 数据库会话

        Returns:
            活跃用户数量
        """
        try:
            # 简化实现，返回用户总数
            # 实际应该基于最后活跃时间过滤
            from app.models.user import User
            total_users = db.query(User).count()
            return total_users
        except Exception as e:
            logger.error(f"Failed to get active users count: {e}")
            return 0


# 全局服务实例
system_service = SystemService()
