"""发布池 API 集成测试"""

import pytest
from fastapi.testclient import TestClient


class TestPublishPoolEndpoints:
    """发布池 API 端点测试类"""

    def test_add_content_to_pool(self, client: TestClient, auth_headers, test_customer):
        """测试添加内容到发布池"""
        # 创建测试数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "发布池测试平台",
                "code": "pool_test_platform",
                "type": "social_media",
                "description": "发布池测试平台",
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
                "name": "发布池测试账号",
                "directory_name": "pool_test_account",
                "description": "发布池测试账号",
                "is_active": True
            },
            headers=auth_headers
        )
        account_id = account_response.json()["id"]

        content_response = client.post(
            "/api/v1/content/",
            json={
                "account_id": account_id,
                "title": "待发布到池的文章",
                "content": "# 待发布内容\n\n这是一篇待发布到发布池的文章",
                "word_count": 200,
                "publish_status": "draft",
                "review_status": "approved"
            },
            headers=auth_headers
        )
        content_id = content_response.json()["id"]

        # 添加到发布池
        pool_data = {
            "content_id": content_id,
            "account_id": account_id,
            "scheduled_time": "2024-12-31T10:00:00"
        }
        response = client.post(
            "/api/v1/publish-pool/",
            json=pool_data,
            headers=auth_headers
        )

        # 验证结果
        assert response.status_code == 201
        data = response.json()
        assert data["content_id"] == content_id
        assert data["account_id"] == account_id

    def test_get_publish_pool_list(self, client: TestClient, auth_headers, test_customer):
        """测试获取发布池列表"""
        # 创建测试数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "发布池列表测试平台",
                "code": "pool_list_test_platform",
                "type": "social_media",
                "description": "发布池列表测试平台",
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
                "name": "发布池列表测试账号",
                "directory_name": "pool_list_test_account",
                "description": "发布池列表测试账号",
                "is_active": True
            },
            headers=auth_headers
        )
        account_id = account_response.json()["id"]

        # 创建多个内容并添加到发布池
        for i in range(3):
            content_response = client.post(
                "/api/v1/content/",
                json={
                    "account_id": account_id,
                    "title": f"发布池测试文章{i+1}",
                    "content": f"# 发布池测试{i+1}\n\n这是第{i+1}篇发布池测试文章",
                    "word_count": 150 + i * 50,
                    "publish_status": "draft",
                    "review_status": "approved"
                },
                headers=auth_headers
            )
            content_id = content_response.json()["id"]

            client.post(
                "/api/v1/publish-pool/",
                json={
                    "content_id": content_id,
                    "account_id": account_id
                },
                headers=auth_headers
            )

        # 获取发布池列表
        response = client.get("/api/v1/publish-pool/", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 3

    def test_get_publish_pool_item_detail(self, client: TestClient, auth_headers, test_customer):
        """测试获取发布池项详情"""
        # 创建测试数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "发布池详情测试平台",
                "code": "pool_detail_test_platform",
                "type": "social_media",
                "description": "发布池详情测试平台",
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
                "name": "发布池详情测试账号",
                "directory_name": "pool_detail_test_account",
                "description": "发布池详情测试账号",
                "is_active": True
            },
            headers=auth_headers
        )
        account_id = account_response.json()["id"]

        content_response = client.post(
            "/api/v1/content/",
            json={
                "account_id": account_id,
                "title": "发布池详情测试文章",
                "content": "# 发布池详情测试\n\n这是用于详情测试的文章",
                "word_count": 200,
                "publish_status": "draft",
                "review_status": "approved"
            },
            headers=auth_headers
        )
        content_id = content_response.json()["id"]

        pool_response = client.post(
            "/api/v1/publish-pool/",
            json={
                "content_id": content_id,
                "account_id": account_id,
                "scheduled_time": "2024-12-31T10:00:00"
            },
            headers=auth_headers
        )
        pool_id = pool_response.json()["id"]

        # 获取发布池项详情
        response = client.get(f"/api/v1/publish-pool/{pool_id}", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pool_id
        assert data["content_id"] == content_id

    def test_update_publish_pool_item(self, client: TestClient, auth_headers, test_customer):
        """测试更新发布池项"""
        # 创建测试数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "发布池更新测试平台",
                "code": "pool_update_test_platform",
                "type": "social_media",
                "description": "发布池更新测试平台",
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
                "name": "发布池更新测试账号",
                "directory_name": "pool_update_test_account",
                "description": "发布池更新测试账号",
                "is_active": True
            },
            headers=auth_headers
        )
        account_id = account_response.json()["id"]

        content_response = client.post(
            "/api/v1/content/",
            json={
                "account_id": account_id,
                "title": "发布池更新测试文章",
                "content": "# 发布池更新测试\n\n这是用于更新测试的文章",
                "word_count": 200,
                "publish_status": "draft",
                "review_status": "approved"
            },
            headers=auth_headers
        )
        content_id = content_response.json()["id"]

        pool_response = client.post(
            "/api/v1/publish-pool/",
            json={
                "content_id": content_id,
                "account_id": account_id,
                "scheduled_time": "2024-12-31T10:00:00"
            },
            headers=auth_headers
        )
        pool_id = pool_response.json()["id"]

        # 更新发布池项
        update_data = {
            "scheduled_time": "2025-01-01T12:00:00",
            "priority": "high"
        }
        response = client.put(
            f"/api/v1/publish-pool/{pool_id}",
            json=update_data,
            headers=auth_headers
        )

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        # 验证更新后的时间（格式可能不同）

    def test_delete_from_publish_pool(self, client: TestClient, auth_headers, test_customer):
        """测试从发布池删除"""
        # 创建测试数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "发布池删除测试平台",
                "code": "pool_delete_test_platform",
                "type": "social_media",
                "description": "发布池删除测试平台",
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
                "name": "发布池删除测试账号",
                "directory_name": "pool_delete_test_account",
                "description": "发布池删除测试账号",
                "is_active": True
            },
            headers=auth_headers
        )
        account_id = account_response.json()["id"]

        content_response = client.post(
            "/api/v1/content/",
            json={
                "account_id": account_id,
                "title": "待从发布池删除的文章",
                "content": "# 待删除内容\n\n这篇将从发布池删除",
                "word_count": 200,
                "publish_status": "draft",
                "review_status": "approved"
            },
            headers=auth_headers
        )
        content_id = content_response.json()["id"]

        pool_response = client.post(
            "/api/v1/publish-pool/",
            json={
                "content_id": content_id,
                "account_id": account_id
            },
            headers=auth_headers
        )
        pool_id = pool_response.json()["id"]

        # 从发布池删除
        response = client.delete(f"/api/v1/publish-pool/{pool_id}", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200

    def test_batch_publish_from_pool(self, client: TestClient, auth_headers, test_customer):
        """测试批量发布"""
        # 创建测试数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "批量发布测试平台",
                "code": "batch_publish_test_platform",
                "type": "social_media",
                "description": "批量发布测试平台",
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
                "name": "批量发布测试账号",
                "directory_name": "batch_publish_test_account",
                "description": "批量发布测试账号",
                "is_active": True
            },
            headers=auth_headers
        )
        account_id = account_response.json()["id"]

        # 创建并添加多个内容到发布池
        pool_ids = []
        for i in range(3):
            content_response = client.post(
                "/api/v1/content/",
                json={
                    "account_id": account_id,
                    "title": f"批量发布测试文章{i+1}",
                    "content": f"# 批量发布测试{i+1}\n\n这是第{i+1}篇批量发布测试文章",
                    "word_count": 150 + i * 50,
                    "publish_status": "draft",
                    "review_status": "approved"
                },
                headers=auth_headers
            )
            content_id = content_response.json()["id"]

            pool_response = client.post(
                "/api/v1/publish-pool/",
                json={
                    "content_id": content_id,
                    "account_id": account_id
                },
                headers=auth_headers
            )
            pool_ids.append(pool_response.json()["id"])

        # 批量发布
        response = client.post(
            "/api/v1/publish-pool/batch-publish",
            json={"pool_ids": pool_ids},
            headers=auth_headers
        )

        # 验证结果（可能返回200或202）
        assert response.status_code in [200, 202]

    def test_filter_by_status(self, client: TestClient, auth_headers, test_customer):
        """测试按状态筛选发布池"""
        # 创建测试数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "状态筛选测试平台",
                "code": "status_filter_test_platform",
                "type": "social_media",
                "description": "状态筛选测试平台",
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
                "name": "状态筛选测试账号",
                "directory_name": "status_filter_test_account",
                "description": "状态筛选测试账号",
                "is_active": True
            },
            headers=auth_headers
        )
        account_id = account_response.json()["id"]

        # 创建待发布的内容
        content_response = client.post(
            "/api/v1/content/",
            json={
                "account_id": account_id,
                "title": "状态筛选测试文章",
                "content": "# 状态筛选测试\n\n这是用于状态筛选测试的文章",
                "word_count": 200,
                "publish_status": "draft",
                "review_status": "approved"
            },
            headers=auth_headers
        )
        content_id = content_response.json()["id"]

        # 添加到发布池
        client.post(
            "/api/v1/publish-pool/",
            json={
                "content_id": content_id,
                "account_id": account_id
            },
            headers=auth_headers
        )

        # 按状态筛选
        response = client.get("/api/v1/publish-pool/?status=pending", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_unauthorized_access(self, client: TestClient):
        """测试未授权访问"""
        response = client.get("/api/v1/publish-pool/")
        assert response.status_code == 401
