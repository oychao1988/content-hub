"""内容管理 API 集成测试"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime


class TestContentEndpoints:
    """内容管理 API 端点测试类"""

    def _create_test_account(self, db_session: Session, test_customer, platform_id: int, name: str):
        """辅助方法：直接在数据库中创建测试账号"""
        from app.models.account import Account

        account = Account(
            customer_id=test_customer.id,
            platform_id=platform_id,
            name=name,
            directory_name=f"test_account_{name}",
            description=f"测试账号 - {name}",
            is_active=True
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)
        return account

    def _create_test_content(self, db_session: Session, account_id: int, title: str, **kwargs):
        """辅助方法：直接在数据库中创建测试内容"""
        from app.models.content import Content

        content = Content(
            account_id=account_id,
            title=title,
            content_type=kwargs.get("content_type", "article"),
            content=kwargs.get("content", f"# {title}\n\n这是测试内容。"),
            publish_status=kwargs.get("publish_status", "draft"),
            review_status=kwargs.get("review_status", "pending"),
            word_count=kwargs.get("word_count", 100),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        return content

    def test_create_content(self, client: TestClient, admin_auth_headers, test_customer, db_session: Session):
        """测试创建内容"""
        # 首先创建平台
        platform_data = {
            "name": "微信公众号",
            "code": "wechat_content_test",
            "type": "social_media",
            "description": "用于内容测试的平台",
            "api_url": "https://api.weixin.qq.com",
            "api_key": "test_key",
            "is_active": True
        }
        platform_response = client.post("/api/v1/platforms/", json=platform_data, headers=admin_auth_headers)
        platform_id = platform_response.json()["id"]

        # 直接在数据库中创建账号
        account = self._create_test_account(db_session, test_customer, platform_id, "测试账号")
        account_id = account.id

        # 测试通过 API 创建内容
        content_data = {
            "account_id": account_id,
            "title": "测试文章标题",
            "content_type": "article",
            "content": "# 测试文章内容\n\n这是一篇测试文章的内容。",
        }

        response = client.post("/api/v1/content/", json=content_data, headers=admin_auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "测试文章标题"

    def test_get_content_list(self, client: TestClient, admin_auth_headers, test_customer, db_session: Session):
        """测试获取内容列表"""
        # 创建测试数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "测试平台",
                "code": "test_platform_list",
                "type": "social_media",
                "description": "测试平台",
                "api_url": "https://api.test.com",
                "api_key": "test_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        platform_id = platform_response.json()["id"]

        # 直接在数据库中创建账号
        account = self._create_test_account(db_session, test_customer, platform_id, "列表测试账号")
        account_id = account.id

        # 创建多个内容
        for i in range(3):
            self._create_test_content(db_session, account_id, f"测试文章{i+1}")

        # 获取内容列表
        response = client.get("/api/v1/content/", headers=admin_auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 3

    def test_get_content_detail(self, client: TestClient, admin_auth_headers, test_customer, db_session: Session):
        """测试获取内容详情"""
        # 创建测试数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "详情测试平台",
                "code": "detail_test_platform",
                "type": "social_media",
                "description": "详情测试平台",
                "api_url": "https://api.test.com",
                "api_key": "test_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        platform_id = platform_response.json()["id"]

        # 直接在数据库中创建账号和内容
        account = self._create_test_account(db_session, test_customer, platform_id, "详情测试账号")
        content = self._create_test_content(db_session, account.id, "详情测试文章")
        content_id = content.id

        # 获取内容详情
        response = client.get(f"/api/v1/content/{content_id}", headers=admin_auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == content_id
        assert data["title"] == "详情测试文章"

    def test_update_content(self, client: TestClient, admin_auth_headers, test_customer, db_session: Session):
        """测试更新内容"""
        # 创建测试数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "更新测试平台",
                "code": "update_test_platform",
                "type": "social_media",
                "description": "更新测试平台",
                "api_url": "https://api.test.com",
                "api_key": "test_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        platform_id = platform_response.json()["id"]

        # 直接在数据库中创建账号和内容
        account = self._create_test_account(db_session, test_customer, platform_id, "更新测试账号")
        content = self._create_test_content(db_session, account.id, "原标题")
        content_id = content.id

        # 更新内容
        update_data = {
            "title": "更新后的标题",
            "content": "# 更新后的内容\n\n这是更新后的内容"
        }
        response = client.put(f"/api/v1/content/{content_id}", json=update_data, headers=admin_auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的标题"

    def test_delete_content(self, client: TestClient, admin_auth_headers, test_customer, db_session: Session):
        """测试删除内容"""
        # 创建测试数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "删除测试平台",
                "code": "delete_test_platform",
                "type": "social_media",
                "description": "删除测试平台",
                "api_url": "https://api.test.com",
                "api_key": "test_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        platform_id = platform_response.json()["id"]

        # 直接在数据库中创建账号和内容
        account = self._create_test_account(db_session, test_customer, platform_id, "删除测试账号")
        content = self._create_test_content(db_session, account.id, "待删除的文章")
        content_id = content.id

        # 删除内容
        response = client.delete(f"/api/v1/content/{content_id}", headers=admin_auth_headers)

        # 验证结果
        assert response.status_code == 200

        # 验证内容已删除
        get_response = client.get(f"/api/v1/content/{content_id}", headers=admin_auth_headers)
        assert get_response.status_code == 404

    def test_search_content(self, client: TestClient, admin_auth_headers, test_customer, db_session: Session):
        """测试搜索内容"""
        # 创建测试数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "搜索测试平台",
                "code": "search_test_platform",
                "type": "social_media",
                "description": "搜索测试平台",
                "api_url": "https://api.test.com",
                "api_key": "test_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        platform_id = platform_response.json()["id"]

        # 直接在数据库中创建账号
        account = self._create_test_account(db_session, test_customer, platform_id, "搜索测试账号")

        # 创建不同主题的内容
        self._create_test_content(db_session, account.id, "Python编程教程", publish_status="published", review_status="approved")
        self._create_test_content(db_session, account.id, "Java编程指南", publish_status="draft", review_status="pending")

        # 搜索内容
        response = client.get("/api/v1/content/?search=Python", headers=admin_auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        # 搜索结果应该包含 "Python" 关键词（检查所有结果）
        python_found = any("Python" in item["title"] for item in data["items"])
        assert python_found, "搜索结果中应该包含 Python 相关内容"

    def test_content_pagination(self, client: TestClient, admin_auth_headers, test_customer, db_session: Session):
        """测试内容分页"""
        # 创建测试数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "分页测试平台",
                "code": "pagination_test_platform",
                "type": "social_media",
                "description": "分页测试平台",
                "api_url": "https://api.test.com",
                "api_key": "test_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        platform_id = platform_response.json()["id"]

        # 直接在数据库中创建账号
        account = self._create_test_account(db_session, test_customer, platform_id, "分页测试账号")

        # 创建15个内容项
        for i in range(15):
            self._create_test_content(db_session, account.id, f"分页测试文章{i+1}", word_count=100 + i * 10)

        # 测试第一页（每页10条）
        response = client.get("/api/v1/content/?page=1&page_size=10", headers=admin_auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 10
        assert data["total"] >= 15
        assert "page" in data
        assert data["page"] == 1
        assert "pageSize" in data
        assert data["pageSize"] == 10

    def test_unauthorized_access(self, client: TestClient):
        """测试未授权访问"""
        response = client.get("/api/v1/content/")
        assert response.status_code == 401
