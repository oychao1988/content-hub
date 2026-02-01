"""仪表盘管理 API 集成测试"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.mark.integration
class TestDashboardEndpoints:
    """仪表盘管理 API 端点测试类"""

    def test_get_stats(self, client: TestClient, admin_auth_headers, db_session: Session):
        """测试获取仪表盘统计数据"""
        # 清空缓存
        from app.core.cache import memory_cache
        memory_cache.clear()

        # 执行请求
        response = client.get("/api/v1/dashboard/stats", headers=admin_auth_headers)

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert "account_count" in data
        assert "content_count" in data
        assert "pending_review_count" in data
        assert "published_count" in data
        assert "today_published_count" in data
        assert "week_published_count" in data
        # 验证数据类型
        assert isinstance(data["account_count"], int)
        assert isinstance(data["content_count"], int)
        assert isinstance(data["pending_review_count"], int)
        assert isinstance(data["published_count"], int)
        assert isinstance(data["today_published_count"], int)
        assert isinstance(data["week_published_count"], int)

    def test_get_activities(self, client: TestClient, admin_auth_headers):
        """测试获取最近活动记录"""
        # 执行请求
        response = client.get("/api/v1/dashboard/activities", headers=admin_auth_headers)

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        # 当前实现返回空列表
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    def test_get_content_trend(self, client: TestClient, admin_auth_headers, db_session: Session):
        """测试获取内容生成趋势"""
        # 清空缓存
        from app.core.cache import memory_cache
        memory_cache.clear()

        # 创建测试数据
        from app.models.account import Account
        from app.models.customer import Customer
        from app.models.platform import Platform
        from app.models.content import Content

        # 创建客户和平台
        customer = Customer(name="趋势测试客户", contact_name="测试", contact_email="trend@example.com", is_active=True)
        db_session.add(customer)
        db_session.commit()

        platform = Platform(name="趋势测试平台", code="trend_platform", type="test", is_active=True)
        db_session.add(platform)
        db_session.commit()

        account = Account(
            customer_id=customer.id,
            platform_id=platform.id,
            name="趋势测试账号",
            directory_name="trend_test_account",
            is_active=True
        )
        db_session.add(account)
        db_session.commit()

        # 创建一些测试内容
        from datetime import datetime, timedelta
        for i in range(5):
            content = Content(
                account_id=account.id,
                title=f"测试内容{i+1}",
                content=f"这是第{i+1}个测试内容",
                review_status="approved",
                publish_status="published"
            )
            # 设置不同的创建时间来测试趋势
            days_ago = i % 3
            content.created_at = datetime.utcnow() - timedelta(days=days_ago)
            db_session.add(content)
        db_session.commit()

        # 执行请求
        response = client.get("/api/v1/dashboard/content-trend?days=7", headers=admin_auth_headers)

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert data["period_days"] == 7
        assert "trend" in data
        assert isinstance(data["trend"], list)

    def test_get_publish_stats(self, client: TestClient, admin_auth_headers, db_session: Session):
        """测试获取发布统计"""
        # 清空缓存
        from app.core.cache import memory_cache
        memory_cache.clear()

        # 执行请求
        response = client.get("/api/v1/dashboard/publish-stats", headers=admin_auth_headers)

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert "total_publish" in data
        assert "success_publish" in data
        assert "failed_publish" in data
        assert "success_rate" in data
        assert "platform_stats" in data
        # 验证数据类型
        assert isinstance(data["total_publish"], int)
        assert isinstance(data["success_publish"], int)
        assert isinstance(data["failed_publish"], int)
        assert isinstance(data["success_rate"], float)
        assert isinstance(data["platform_stats"], list)

    def test_get_cache_stats(self, client: TestClient, admin_auth_headers):
        """测试获取缓存统计信息"""
        # 先执行一些操作来产生缓存
        client.get("/api/v1/dashboard/stats", headers=admin_auth_headers)

        # 执行请求
        response = client.get("/api/v1/dashboard/cache-stats", headers=admin_auth_headers)

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        # 验证返回缓存统计信息
        assert "hits" in data or "misses" in data or "size" in data or "hit_rate" in data

    def test_reset_cache_stats(self, client: TestClient, admin_auth_headers):
        """测试重置缓存统计"""
        # 执行请求
        response = client.post("/api/v1/dashboard/cache-stats/reset", headers=admin_auth_headers)

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "缓存统计已重置" == data["message"]

    def test_clear_cache(self, client: TestClient, admin_auth_headers):
        """测试清空所有缓存"""
        # 先创建一些缓存
        from app.core.cache import memory_cache
        memory_cache.set("test_key", "test_value", ttl=60)

        # 执行请求
        response = client.post("/api/v1/dashboard/cache/clear", headers=admin_auth_headers)

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "所有缓存已清空" == data["message"]

    def test_cleanup_cache(self, client: TestClient, admin_auth_headers):
        """测试清理过期缓存"""
        # 执行请求
        response = client.post("/api/v1/dashboard/cache/cleanup", headers=admin_auth_headers)

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "过期缓存已清理" == data["message"]
