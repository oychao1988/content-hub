"""客户管理 API 集成测试"""

import pytest
from fastapi.testclient import TestClient


class TestCustomerEndpoints:
    """客户管理 API 端点测试类"""

    def test_create_customer(self, client: TestClient, admin_auth_headers):
        """测试创建客户"""
        # 测试数据
        customer_data = {
            "name": "API测试客户",
            "contact_name": "API测试联系人",
            "contact_email": "api@example.com",
            "contact_phone": "13800138999",
            "description": "这是通过API创建的测试客户",
            "is_active": True
        }

        # 执行请求
        response = client.post(
            "/api/v1/customers/",
            json=customer_data,
            headers=admin_auth_headers
        )

        # 断言结果
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API测试客户"
        assert data["contact_name"] == "API测试联系人"
        assert data["contact_email"] == "api@example.com"
        assert data["contact_phone"] == "13800138999"
        assert data["is_active"] is True

    def test_get_customer_list(self, client: TestClient, admin_auth_headers):
        """测试获取客户列表"""
        # 创建测试数据
        for i in range(3):
            client.post(
                "/api/v1/customers/",
                json={
                    "name": f"列表测试客户{i+1}",
                    "contact_name": f"测试联系人{i+1}",
                    "contact_email": f"list{i+1}@example.com",
                    "contact_phone": f"13800138{i+10}",
                    "is_active": True
                },
                headers=admin_auth_headers
            )

        # 执行请求
        response = client.get("/api/v1/customers/", headers=admin_auth_headers)

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 3
        assert len(data["items"]) >= 3

    def test_get_customer_detail(self, client: TestClient, admin_auth_headers):
        """测试获取客户详情"""
        # 创建测试数据
        create_response = client.post(
            "/api/v1/customers/",
            json={
                "name": "详情测试客户",
                "contact_name": "详情联系人",
                "contact_email": "detail@example.com",
                "contact_phone": "13800138777",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        customer_id = create_response.json()["id"]

        # 执行请求
        response = client.get(
            f"/api/v1/customers/{customer_id}",
            headers=admin_auth_headers
        )

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == customer_id
        assert data["name"] == "详情测试客户"

    def test_update_customer(self, client: TestClient, admin_auth_headers):
        """测试更新客户"""
        # 创建测试数据
        create_response = client.post(
            "/api/v1/customers/",
            json={
                "name": "待更新客户",
                "contact_name": "原联系人",
                "contact_email": "update@example.com",
                "contact_phone": "13800138666",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        customer_id = create_response.json()["id"]

        # 执行请求
        update_data = {
            "name": "已更新客户",
            "contact_name": "新联系人",
            "contact_email": "updated@example.com",
            "contact_phone": "13800138667",
            "is_active": False
        }
        response = client.put(
            f"/api/v1/customers/{customer_id}",
            json=update_data,
            headers=admin_auth_headers
        )

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == customer_id
        assert data["name"] == "已更新客户"
        assert data["contact_name"] == "新联系人"
        assert data["contact_email"] == "updated@example.com"
        assert data["contact_phone"] == "13800138667"
        assert data["is_active"] is False

    def test_delete_customer(self, client: TestClient, admin_auth_headers):
        """测试删除客户"""
        # 创建测试数据
        create_response = client.post(
            "/api/v1/customers/",
            json={
                "name": "待删除客户",
                "contact_name": "待删除联系人",
                "contact_email": "delete@example.com",
                "contact_phone": "13800138555",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        customer_id = create_response.json()["id"]

        # 执行请求
        response = client.delete(
            f"/api/v1/customers/{customer_id}",
            headers=admin_auth_headers
        )

        # 断言结果
        assert response.status_code == 200
        assert "message" in response.json()

        # 验证客户已删除
        get_response = client.get(
            f"/api/v1/customers/{customer_id}",
            headers=admin_auth_headers
        )
        assert get_response.status_code == 404

    def test_create_duplicate_customer(self, client: TestClient, admin_auth_headers):
        """测试创建重复名称的客户"""
        # 创建第一个客户
        client.post(
            "/api/v1/customers/",
            json={
                "name": "重复客户",
                "contact_name": "联系人",
                "contact_email": "duplicate@example.com",
                "contact_phone": "13800138444",
                "is_active": True
            },
            headers=admin_auth_headers
        )

        # 尝试创建重复名称的客户
        response = client.post(
            "/api/v1/customers/",
            json={
                "name": "重复客户",
                "contact_name": "重复联系人",
                "contact_email": "duplicate2@example.com",
                "contact_phone": "13800138445",
                "is_active": True
            },
            headers=admin_auth_headers
        )

        # 断言结果
        assert response.status_code == 400

    def test_search_customers(self, client: TestClient, admin_auth_headers):
        """测试搜索客户"""
        # 创建测试数据
        client.post(
            "/api/v1/customers/",
            json={
                "name": "阿里巴巴",
                "contact_name": "马云",
                "contact_email": "jack@alibaba.com",
                "contact_phone": "13800138111",
                "is_active": True
            },
            headers=admin_auth_headers
        )

        # 执行搜索
        response = client.get(
            "/api/v1/customers/?search=阿里",
            headers=admin_auth_headers
        )

        # 断言结果
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("阿里" in customer["name"] for customer in data["items"])

    def test_pagination(self, client: TestClient, admin_auth_headers):
        """测试分页功能"""
        # 创建多个客户
        for i in range(5):
            client.post(
                "/api/v1/customers/",
                json={
                    "name": f"分页客户{i+1}",
                    "contact_name": f"联系人{i+1}",
                    "contact_email": f"page{i+1}@example.com",
                    "contact_phone": f"13800138{i+20}",
                    "is_active": True
                },
                headers=admin_auth_headers
            )

        # 测试第一页
        response1 = client.get("/api/v1/customers/?skip=0&limit=2", headers=admin_auth_headers)
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["items"]) == 2
        assert data1["total"] >= 5

        # 测试第二页
        response2 = client.get("/api/v1/customers/?skip=2&limit=2", headers=admin_auth_headers)
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 2

        # 测试无效参数
        response_invalid = client.get("/api/v1/customers/?skip=-1&limit=0", headers=admin_auth_headers)
        assert response_invalid.status_code == 422
