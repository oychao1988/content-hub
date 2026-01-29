"""
System module integration tests
"""
import pytest
from fastapi.testclient import TestClient

from app.factory import create_app


class TestSystemIntegration:
    """System 模块集成测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        app = create_app()
        return TestClient(app)

    def test_get_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/api/v1/system/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "status" in data["data"]
        assert "version" in data["data"]
        assert "uptime" in data["data"]
        assert "database" in data["data"]
        assert "services" in data["data"]

    def test_get_system_info_endpoint(self, client):
        """测试系统信息端点"""
        response = client.get("/api/v1/system/info")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "version" in data["data"]
        assert "python_version" in data["data"]
        assert "environment" in data["data"]
        assert "platform" in data["data"]
        assert "app_name" in data["data"]
        assert "debug_mode" in data["data"]

    def test_get_metrics_endpoint(self, client):
        """测试系统指标端点"""
        response = client.get("/api/v1/system/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "requests_total" in data["data"]
        assert "requests_per_minute" in data["data"]
        assert "active_users" in data["data"]
        assert "cache_stats" in data["data"]
        assert "uptime" in data["data"]

    def test_health_response_structure(self, client):
        """测试健康检查响应结构"""
        response = client.get("/api/v1/system/health")
        data = response.json()["data"]

        # 验证状态值
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

        # 验证数据库状态
        assert isinstance(data["database"], str)

        # 验证服务状态
        services = data["services"]
        assert "redis" in services
        assert "content_publisher" in services
        assert "content_creator" in services

    def test_system_info_response_structure(self, client):
        """测试系统信息响应结构"""
        response = client.get("/api/v1/system/info")
        data = response.json()["data"]

        # 验证环境值
        assert data["environment"] in ["development", "production"]

        # 验证数据类型
        assert isinstance(data["version"], str)
        assert isinstance(data["python_version"], str)
        assert isinstance(data["platform"], str)
        assert isinstance(data["app_name"], str)
        assert isinstance(data["debug_mode"], bool)

    def test_metrics_response_structure(self, client):
        """测试系统指标响应结构"""
        response = client.get("/api/v1/system/metrics")
        data = response.json()["data"]

        # 验证数据类型
        assert isinstance(data["requests_total"], int)
        assert isinstance(data["requests_per_minute"], (int, float))
        assert isinstance(data["active_users"], int)
        assert isinstance(data["cache_stats"], dict)
        assert isinstance(data["uptime"], float)

        # 验证缓存统计
        cache_stats = data["cache_stats"]
        assert "hits" in cache_stats
        assert "misses" in cache_stats
        assert "hit_rate" in cache_stats
