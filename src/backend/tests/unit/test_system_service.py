"""
System service unit tests
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.modules.system.services import SystemService, system_service


class TestSystemService:
    """SystemService 单元测试"""

    def test_get_system_info(self):
        """测试获取系统信息"""
        info = system_service.get_system_info()

        assert "version" in info
        assert "python_version" in info
        assert "environment" in info
        assert "platform" in info
        assert "app_name" in info
        assert "debug_mode" in info
        assert isinstance(info["version"], str)
        assert isinstance(info["python_version"], str)
        assert info["environment"] in ["development", "production"]
        assert isinstance(info["platform"], str)

    def test_get_health_status_with_db(self, db_session: Session):
        """测试获取健康状态（含数据库）"""
        health = system_service.get_health_status(db_session)

        assert "status" in health
        assert "version" in health
        assert "uptime" in health
        assert "database" in health
        assert "services" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert isinstance(health["uptime"], float)
        assert health["uptime"] >= 0

    def test_get_metrics(self, db_session: Session):
        """测试获取系统指标"""
        metrics = system_service.get_metrics(db_session)

        assert "requests_total" in metrics
        assert "requests_per_minute" in metrics
        assert "active_users" in metrics
        assert "cache_stats" in metrics
        assert "uptime" in metrics
        assert isinstance(metrics["requests_total"], int)
        assert isinstance(metrics["requests_per_minute"], (int, float))
        assert isinstance(metrics["active_users"], int)
        assert isinstance(metrics["cache_stats"], dict)

    def test_check_database_connected(self, db_session: Session):
        """测试数据库连接检查"""
        status = SystemService._check_database(db_session)
        assert status == "connected"

    def test_check_redis(self):
        """测试 Redis 检查"""
        status = SystemService._check_redis()
        assert status in ["available", "unavailable"]

    def test_check_content_publisher(self):
        """测试 Content-Publisher 检查"""
        status = SystemService._check_content_publisher()
        assert status in ["available", "not_configured"]

    def test_check_content_creator(self):
        """测试 Content-Creator 检查"""
        status = SystemService._check_content_creator()
        assert status in ["available", "not_configured", "not_found"]

    def test_get_active_users_count(self, db_session: Session):
        """测试获取活跃用户数"""
        count = SystemService._get_active_users_count(db_session)
        assert isinstance(count, int)
        assert count >= 0
