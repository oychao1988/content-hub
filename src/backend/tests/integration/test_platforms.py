"""平台管理 API 集成测试"""

import pytest
from fastapi.testclient import TestClient


class TestPlatformEndpoints:
    """平台管理 API 端点测试类"""

    def test_create_platform(self, client: TestClient, admin_auth_headers):
        """测试创建平台"""
        # 测试数据
        platform_data = {
            "name": "微信公众号",
            "code": "wechat_official",
            "type": "social_media",
            "description": "微信公众号平台",
            "api_url": "https://api.weixin.qq.com",
            "api_key": "test_api_key",
            "is_active": True
        }

        # 执行请求
        response = client.post(
            "/api/v1/platforms/",
            json=platform_data,
            headers=admin_auth_headers
        )

        # 断言结果
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "微信公众号"
        assert data["code"] == "wechat_official"
        assert data["type"] == "social_media"
        assert data["api_url"] == "https://api.weixin.qq.com"
        assert data["is_active"] is True

    def test_get_platform_list(self, client: TestClient, admin_auth_headers):
        """测试获取平台列表"""
        # 创建测试数据
        for i in range(3):
            client.post(
                "/api/v1/platforms/",
                json={
                    "name": f"平台{i+1}",
                    "code": f"platform{i+1}",
                    "type": "social_media",
                    "description": f"测试平台{i+1}",
                    "api_url": f"https://api.platform{i+1}.com",
                    "api_key": f"api_key{i+1}",
                    "is_active": True
                },
                headers=admin_auth_headers
            )

        # 执行请求
        response = client.get("/api/v1/platforms/", headers=admin_auth_headers)

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 3
        assert len(data["items"]) >= 3

    def test_get_platform_detail(self, client: TestClient, admin_auth_headers):
        """测试获取平台详情"""
        # 创建测试数据
        create_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "抖音平台",
                "code": "douyin",
                "type": "video",
                "description": "抖音短视频平台",
                "api_url": "https://api.douyin.com",
                "api_key": "douyin_api_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        platform_id = create_response.json()["id"]

        # 执行请求
        response = client.get(
            f"/api/v1/platforms/{platform_id}",
            headers=admin_auth_headers
        )

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == platform_id
        assert data["name"] == "抖音平台"

    def test_update_platform(self, client: TestClient, admin_auth_headers):
        """测试更新平台"""
        # 创建测试数据
        create_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "待更新平台",
                "code": "to_update",
                "type": "news",
                "description": "待更新的测试平台",
                "api_url": "https://api.to_update.com",
                "api_key": "to_update_api_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        platform_id = create_response.json()["id"]

        # 执行请求
        update_data = {
            "name": "已更新平台",
            "code": "updated",
            "type": "social_media",
            "description": "已更新的平台描述",
            "api_url": "https://api.updated.com",
            "api_key": "updated_api_key",
            "is_active": False
        }
        response = client.put(
            f"/api/v1/platforms/{platform_id}",
            json=update_data,
            headers=admin_auth_headers
        )

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == platform_id
        assert data["name"] == "已更新平台"
        assert data["code"] == "updated"
        assert data["is_active"] is False

    def test_delete_platform(self, client: TestClient, admin_auth_headers):
        """测试删除平台"""
        # 创建测试数据
        create_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "待删除平台",
                "code": "to_delete",
                "type": "test",
                "description": "待删除的测试平台",
                "api_url": "https://api.to_delete.com",
                "api_key": "to_delete_api_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        platform_id = create_response.json()["id"]

        # 执行请求
        response = client.delete(
            f"/api/v1/platforms/{platform_id}",
            headers=admin_auth_headers
        )

        # 断言结果
        assert response.status_code == 200
        assert "message" in response.json()

        # 验证平台已删除
        get_response = client.get(
            f"/api/v1/platforms/{platform_id}",
            headers=admin_auth_headers
        )
        assert get_response.status_code == 404

    def test_create_duplicate_platform(self, client: TestClient, admin_auth_headers):
        """测试创建重复名称或代码的平台"""
        # 创建第一个平台
        client.post(
            "/api/v1/platforms/",
            json={
                "name": "重复平台",
                "code": "duplicate",
                "type": "social_media",
                "description": "重复平台测试",
                "api_url": "https://api.duplicate.com",
                "api_key": "duplicate_api_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )

        # 尝试创建名称相同的平台
        response1 = client.post(
            "/api/v1/platforms/",
            json={
                "name": "重复平台",
                "code": "different_code",
                "type": "social_media",
                "description": "重复名称测试",
                "api_url": "https://api.different.com",
                "api_key": "different_api_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )

        # 尝试创建代码相同的平台
        response2 = client.post(
            "/api/v1/platforms/",
            json={
                "name": "不同平台",
                "code": "duplicate",
                "type": "social_media",
                "description": "重复代码测试",
                "api_url": "https://api.samecode.com",
                "api_key": "samecode_api_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )

        # 断言结果
        assert response1.status_code == 400
        assert response2.status_code == 400

    def test_search_platforms(self, client: TestClient, admin_auth_headers):
        """测试搜索平台"""
        # 创建测试数据
        client.post(
            "/api/v1/platforms/",
            json={
                "name": "今日头条",
                "code": "toutiao",
                "type": "news",
                "description": "今日头条新闻平台",
                "api_url": "https://api.toutiao.com",
                "api_key": "toutiao_api_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )

        # 执行搜索
        response = client.get(
            "/api/v1/platforms/?search=头条",
            headers=admin_auth_headers
        )

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("头条" in platform["name"] for platform in data["items"])

    def test_pagination(self, client: TestClient, admin_auth_headers):
        """测试分页功能"""
        # 创建多个平台
        for i in range(5):
            client.post(
                "/api/v1/platforms/",
                json={
                    "name": f"分页平台{i+1}",
                    "code": f"page{i+1}",
                    "type": "social_media",
                    "description": f"分页测试平台{i+1}",
                    "api_url": f"https://api.page{i+1}.com",
                    "api_key": f"page_api_key{i+1}",
                    "is_active": True
                },
                headers=admin_auth_headers
            )

        # 测试第一页
        response1 = client.get("/api/v1/platforms/?skip=0&limit=2", headers=admin_auth_headers)
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["items"]) == 2
        assert data1["total"] >= 5

        # 测试第二页
        response2 = client.get("/api/v1/platforms/?skip=2&limit=2", headers=admin_auth_headers)
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 2

        # 测试无效参数
        response_invalid = client.get("/api/v1/platforms/?skip=-1&limit=0", headers=admin_auth_headers)
        assert response_invalid.status_code == 422
