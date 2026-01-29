"""内容管理 API 集成测试"""

import pytest
from fastapi.testclient import TestClient


class TestContentEndpoints:
    """内容管理 API 端点测试类"""

    def test_create_content(self, client: TestClient, auth_headers, test_customer):
        """测试创建内容"""
        # 首先创建平台和账号
        platform_data = {
            "name": "微信公众号",
            "code": "wechat_content_test",
            "type": "social_media",
            "description": "用于内容测试的平台",
            "api_url": "https://api.weixin.qq.com",
            "api_key": "test_key",
            "is_active": True
        }
        platform_response = client.post("/api/v1/platforms/", json=platform_data, headers=auth_headers)
        platform_id = platform_response.json()["id"]

        account_data = {
            "customer_id": test_customer.id,
            "platform_id": platform_id,
            "name": "测试账号",
            "directory_name": "test_account_content",
            "description": "用于内容测试的账号",
            "is_active": True
        }
        account_response = client.post("/api/v1/accounts/", json=account_data, headers=auth_headers)
        account_id = account_response.json()["id"]

        # 测试创建内容
        content_data = {
            "account_id": account_id,
            "title": "测试文章标题",
            "content": "# 测试文章内容\n\n这是一篇测试文章的内容。",
            "word_count": 100,
            "publish_status": "draft",
            "review_status": "pending"
        }

        response = client.post("/api/v1/content/", json=content_data, headers=auth_headers)

        # 验证结果
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "测试文章标题"
        assert data["publish_status"] == "draft"
        assert data["review_status"] == "pending"

    def test_get_content_list(self, client: TestClient, auth_headers, test_customer):
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
            headers=auth_headers
        )
        platform_id = platform_response.json()["id"]

        account_response = client.post(
            "/api/v1/accounts/",
            json={
                "customer_id": test_customer.id,
                "platform_id": platform_id,
                "name": "测试账号",
                "directory_name": "test_account_list",
                "description": "测试账号",
                "is_active": True
            },
            headers=auth_headers
        )
        account_id = account_response.json()["id"]

        # 创建多个内容
        for i in range(3):
            client.post(
                "/api/v1/content/",
                json={
                    "account_id": account_id,
                    "title": f"测试文章{i+1}",
                    "content": f"# 内容{i+1}\n\n这是第{i+1}篇测试文章",
                    "word_count": 100 + i * 50,
                    "publish_status": "draft",
                    "review_status": "pending"
                },
                headers=auth_headers
            )

        # 获取内容列表
        response = client.get("/api/v1/content/", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 3

    def test_get_content_detail(self, client: TestClient, auth_headers, test_customer):
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
            headers=auth_headers
        )
        platform_id = platform_response.json()["id"]

        account_response = client.post(
            "/api/v1/accounts/",
            json={
                "customer_id": test_customer.id,
                "platform_id": platform_id,
                "name": "详情测试账号",
                "directory_name": "detail_test_account",
                "description": "详情测试账号",
                "is_active": True
            },
            headers=auth_headers
        )
        account_id = account_response.json()["id"]

        content_response = client.post(
            "/api/v1/content/",
            json={
                "account_id": account_id,
                "title": "详情测试文章",
                "content": "# 详情测试内容\n\n这是用于详情测试的文章",
                "word_count": 200,
                "publish_status": "draft",
                "review_status": "pending"
            },
            headers=auth_headers
        )
        content_id = content_response.json()["id"]

        # 获取内容详情
        response = client.get(f"/api/v1/content/{content_id}", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == content_id
        assert data["title"] == "详情测试文章"

    def test_update_content(self, client: TestClient, auth_headers, test_customer):
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
            headers=auth_headers
        )
        platform_id = platform_response.json()["id"]

        account_response = client.post(
            "/api/v1/accounts/",
            json={
                "customer_id": test_customer.id,
                "platform_id": platform_id,
                "name": "更新测试账号",
                "directory_name": "update_test_account",
                "description": "更新测试账号",
                "is_active": True
            },
            headers=auth_headers
        )
        account_id = account_response.json()["id"]

        content_response = client.post(
            "/api/v1/content/",
            json={
                "account_id": account_id,
                "title": "原标题",
                "content": "# 原内容\n\n这是原始内容",
                "word_count": 100,
                "publish_status": "draft",
                "review_status": "pending"
            },
            headers=auth_headers
        )
        content_id = content_response.json()["id"]

        # 更新内容
        update_data = {
            "title": "更新后的标题",
            "content": "# 更新后的内容\n\n这是更新后的内容",
            "word_count": 200
        }
        response = client.put(f"/api/v1/content/{content_id}", json=update_data, headers=auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的标题"
        assert data["word_count"] == 200

    def test_delete_content(self, client: TestClient, auth_headers, test_customer):
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
            headers=auth_headers
        )
        platform_id = platform_response.json()["id"]

        account_response = client.post(
            "/api/v1/accounts/",
            json={
                "customer_id": test_customer.id,
                "platform_id": platform_id,
                "name": "删除测试账号",
                "directory_name": "delete_test_account",
                "description": "删除测试账号",
                "is_active": True
            },
            headers=auth_headers
        )
        account_id = account_response.json()["id"]

        content_response = client.post(
            "/api/v1/content/",
            json={
                "account_id": account_id,
                "title": "待删除的文章",
                "content": "# 待删除内容\n\n这篇将被删除",
                "word_count": 100,
                "publish_status": "draft",
                "review_status": "pending"
            },
            headers=auth_headers
        )
        content_id = content_response.json()["id"]

        # 删除内容
        response = client.delete(f"/api/v1/content/{content_id}", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200

        # 验证内容已删除
        get_response = client.get(f"/api/v1/content/{content_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_search_content(self, client: TestClient, auth_headers, test_customer):
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
            headers=auth_headers
        )
        platform_id = platform_response.json()["id"]

        account_response = client.post(
            "/api/v1/accounts/",
            json={
                "customer_id": test_customer.id,
                "platform_id": platform_id,
                "name": "搜索测试账号",
                "directory_name": "search_test_account",
                "description": "搜索测试账号",
                "is_active": True
            },
            headers=auth_headers
        )
        account_id = account_response.json()["id"]

        # 创建不同状态的内容
        client.post(
            "/api/v1/content/",
            json={
                "account_id": account_id,
                "title": "Python编程教程",
                "content": "# Python教程\n\n学习Python编程",
                "word_count": 300,
                "publish_status": "published",
                "review_status": "approved"
            },
            headers=auth_headers
        )

        client.post(
            "/api/v1/content/",
            json={
                "account_id": account_id,
                "title": "Java编程指南",
                "content": "# Java指南\n\n学习Java编程",
                "word_count": 250,
                "publish_status": "draft",
                "review_status": "pending"
            },
            headers=auth_headers
        )

        # 搜索内容
        response = client.get("/api/v1/content/?search=Python", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        # 搜索结果应该包含 "Python" 关键词
        if data["total"] > 0:
            assert "Python" in data["items"][0]["title"] or "Python" in data["items"][0]["content"]

    def test_content_pagination(self, client: TestClient, auth_headers, test_customer):
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
            headers=auth_headers
        )
        platform_id = platform_response.json()["id"]

        account_response = client.post(
            "/api/v1/accounts/",
            json={
                "customer_id": test_customer.id,
                "platform_id": platform_id,
                "name": "分页测试账号",
                "directory_name": "pagination_test_account",
                "description": "分页测试账号",
                "is_active": True
            },
            headers=auth_headers
        )
        account_id = account_response.json()["id"]

        # 创建15个内容项
        for i in range(15):
            client.post(
                "/api/v1/content/",
                json={
                    "account_id": account_id,
                    "title": f"分页测试文章{i+1}",
                    "content": f"# 分页测试内容{i+1}\n\n这是第{i+1}篇用于分页测试的文章",
                    "word_count": 100 + i * 10,
                    "publish_status": "draft",
                    "review_status": "pending"
                },
                headers=auth_headers
            )

        # 测试第一页（每页10条）
        response = client.get("/api/v1/content/?page=1&page_size=10", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 10
        assert data["total"] >= 15
        assert "page" in data
        assert data["page"] == 1
        assert "page_size" in data
        assert data["page_size"] == 10

    def test_unauthorized_access(self, client: TestClient, test_customer):
        """测试未授权访问"""
        response = client.get("/api/v1/content/")
        assert response.status_code == 401
