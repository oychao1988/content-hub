"""
测试错误处理机制
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.exceptions import (
    BusinessException,
    ResourceNotFoundException,
    ResourceAlreadyExistsException,
    PermissionDeniedException,
    CreatorTimeoutException,
    PublisherException
)
from app.factory import create_app


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app()
    return TestClient(app)


def test_http_exception_handler(client):
    """测试 HTTP 异常处理器"""
    response = client.get("/non-existent-endpoint")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "requestId" in data


def test_validation_exception_handler(client):
    """测试验证异常处理器"""
    response = client.post(
        "/api/v1/auth/login",
        json={"invalid_field": "test"}  # 缺少必要字段
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]
    assert "requestId" in data


def test_business_exception_handler(client):
    """测试业务异常处理器"""
    from app.factory import create_app

    app = create_app()

    @app.get("/test/business-error")
    def test_business_error():
        raise BusinessException(
            message="测试业务错误",
            details={"field": "value"}
        )

    with TestClient(app) as test_client:
        response = test_client.get("/test/business-error")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "BUSINESS_ERROR"
        assert data["error"]["message"] == "测试业务错误"
        assert data["error"]["details"] == {"field": "value"}
        assert "requestId" in data


def test_resource_not_found_exception(client):
    """测试资源未找到异常"""
    from app.factory import create_app

    app = create_app()

    @app.get("/test/resource-not-found")
    def test_resource_not_found():
        raise ResourceNotFoundException(
            resource_name="测试资源",
            resource_id="123"
        )

    with TestClient(app) as test_client:
        response = test_client.get("/test/resource-not-found")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "测试资源" in data["error"]["message"]
        assert "123" in data["error"]["message"]


def test_permission_denied_exception(client):
    """测试权限拒绝异常"""
    from app.factory import create_app

    app = create_app()

    @app.get("/test/permission-denied")
    def test_permission_denied():
        raise PermissionDeniedException(
            message="您没有权限执行此操作"
        )

    with TestClient(app) as test_client:
        response = test_client.get("/test/permission-denied")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["error"]["code"] == "PERMISSION_DENIED"


def test_creator_timeout_exception(client):
    """测试 Creator 超时异常"""
    from app.factory import create_app

    app = create_app()

    @app.get("/test/creator-timeout")
    def test_creator_timeout():
        raise CreatorTimeoutException(timeout=120)

    with TestClient(app) as test_client:
        response = test_client.get("/test/creator-timeout")

        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        data = response.json()
        assert data["error"]["code"] == "CREATOR_TIMEOUT"
        assert "120" in data["error"]["message"]


def test_publisher_exception(client):
    """测试 Publisher 异常"""
    from app.factory import create_app

    app = create_app()

    @app.get("/test/publisher-error")
    def test_publisher_error():
        raise PublisherException(
            message="Publisher API 调用失败",
            details={"status_code": 500}
        )

    with TestClient(app) as test_client:
        response = test_client.get("/test/publisher-error")

        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        data = response.json()
        assert data["error"]["code"] == "PUBLISHER_API_ERROR"


def test_error_details_sanitization(client):
    """测试错误详情脱敏"""
    from app.factory import create_app

    app = create_app()

    @app.get("/test/sensitive-error")
    def test_sensitive_error():
        raise BusinessException(
            message="测试敏感信息",
            details={
                "password": "secret123",
                "api_key": "key_abc",
                "normal_field": "public_value"
            }
        )

    with TestClient(app) as test_client:
        response = test_client.get("/test/sensitive-error")

        data = response.json()
        assert data["error"]["details"]["password"] == "***REDACTED***"
        assert data["error"]["details"]["api_key"] == "***REDACTED***"
        assert data["error"]["details"]["normal_field"] == "public_value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
