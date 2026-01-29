"""
E2E Test: Simple End-to-End Test

简化版的 E2E 测试，验证核心业务流程能否正常工作。
"""

import pytest
import random
from fastapi.testclient import TestClient


class TestSimpleE2E:
    """简化的 E2E 测试"""

    def test_platform_account_content_workflow(self, client: TestClient):
        """
        测试 平台 -> 账号 -> 内容 的完整工作流

        这是最核心的业务流程：
        1. 用户注册/登录
        2. 创建平台
        3. 创建账号
        4. 创建内容
        5. 查询内容
        """
        # ========== 步骤 1: 用户注册并登录 ==========
        unique_id = random.randint(10000, 99999)
        username = f"e2e_user_{unique_id}"
        email = f"e2e_{unique_id}@example.com"

        # 注册
        register_response = client.post("/api/v1/auth/register", json={
            "username": username,
            "email": email,
            "password": "testpass123"
        })
        assert register_response.status_code == 200, f"注册失败: {register_response.text}"

        # 登录
        login_response = client.post("/api/v1/auth/login", data={
            "username": username,
            "password": "testpass123"
        })
        assert login_response.status_code == 200, f"登录失败: {login_response.text}"
        token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # ========== 步骤 2: 创建平台 ==========
        platform_response = client.post("/api/v1/platforms/", json={
            "name": f"测试平台_{unique_id}",
            "code": f"test_platform_{unique_id}",
            "type": "social_media",
            "description": "E2E测试平台",
            "api_url": "https://api.test.com",
            "api_key": f"test_key_{unique_id}",
            "is_active": True
        }, headers=auth_headers)
        assert platform_response.status_code in [200, 201], f"平台创建失败: {platform_response.text}"
        platform_id = platform_response.json()["id"]

        # ========== 步骤 3: 创建客户和账号 ==========
        # 先创建客户（如果还没有）
        from app.models.customer import Customer
        from sqlalchemy.orm import sessionmaker
        from app.db.database import engine

        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        customer = Customer(
            name=f"E2E测试客户_{unique_id}",
            contact_name="测试联系人",
            contact_email=f"customer_{unique_id}@example.com",
            contact_phone="13800138000",
            description="E2E测试客户",
            is_active=True
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        customer_id = customer.id

        # 创建账号
        account_response = client.post("/api/v1/accounts/", json={
            "customer_id": customer_id,
            "platform_id": platform_id,
            "name": f"测试账号_{unique_id}",
            "directory_name": f"test_account_{unique_id}",
            "description": "E2E测试账号",
            "is_active": True
        }, headers=auth_headers)
        assert account_response.status_code in [200, 201], f"账号创建失败: {account_response.text}"
        account_id = account_response.json()["id"]

        # ========== 步骤 4: 创建内容 ==========
        content_response = client.post("/api/v1/content/", json={
            "account_id": account_id,
            "title": f"E2E测试文章_{unique_id}",
            "content": f"# E2E测试\n\n这是第{unique_id}篇E2E测试文章",
            "word_count": 500,
            "publish_status": "draft",
            "review_status": "pending"
        }, headers=auth_headers)
        assert content_response.status_code in [200, 201], f"内容创建失败: {content_response.text}"
        content_id = content_response.json()["id"]

        # ========== 步骤 5: 查询内容 ==========
        get_response = client.get(f"/api/v1/content/{content_id}", headers=auth_headers)
        assert get_response.status_code == 200
        content = get_response.json()
        assert content["id"] == content_id
        assert content["title"] == f"E2E测试文章_{unique_id}"

        # ========== 步骤 6: 更新内容 ==========
        update_response = client.put(f"/api/v1/content/{content_id}", json={
            "title": "更新后的标题",
            "word_count": 600
        }, headers=auth_headers)
        assert update_response.status_code == 200
        updated_content = update_response.json()
        assert updated_content["title"] == "更新后的标题"

        # ========== 步骤 7: 删除内容 ==========
        delete_response = client.delete(f"/api/v1/content/{content_id}", headers=auth_headers)
        assert delete_response.status_code == 200

        # 验证删除
        verify_response = client.get(f"/api/v1/content/{content_id}", headers=auth_headers)
        assert verify_response.status_code == 404

        # 清理
        db.delete(customer)
        db.commit()
        db.close()

    def test_list_operations(self, client: TestClient):
        """
        测试列表查询操作

        业务流程：
        1. 创建多个平台
        2. 查询平台列表
        3. 验证列表数据
        """
        # 注册并登录
        unique_id = random.randint(10000, 99999)
        register_response = client.post("/api/v1/auth/register", json={
            "username": f"list_user_{unique_id}",
            "email": f"list_{unique_id}@example.com",
            "password": "testpass123"
        })
        assert register_response.status_code == 200

        login_response = client.post("/api/v1/auth/login", data={
            "username": f"list_user_{unique_id}",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 创建多个平台
        platform_ids = []
        for i in range(3):
            response = client.post("/api/v1/platforms/", json={
                "name": f"列表测试平台{i}_{unique_id}",
                "code": f"list_platform_{i}_{unique_id}",
                "type": "social_media",
                "description": f"第{i}个测试平台",
                "api_url": "https://api.test.com",
                "api_key": f"key_{i}_{unique_id}",
                "is_active": True
            }, headers=auth_headers)
            assert response.status_code in [200, 201]
            platform_ids.append(response.json()["id"])

        # 查询平台列表
        list_response = client.get("/api/v1/platforms/", headers=auth_headers)
        assert list_response.status_code == 200
        platforms = list_response.json()

        # 验证列表格式
        assert isinstance(platforms, list) or "items" in platforms
        items = platforms if isinstance(platforms, list) else platforms.get("items", [])

        # 应该至少包含我们创建的3个平台
        assert len(items) >= 3

    def test_authentication_flow(self, client: TestClient):
        """
        测试认证流程

        业务流程：
        1. 注册用户
        2. 登录获取token
        3. 使用token访问受保护的资源
        4. 验证未授权访问被拒绝
        """
        unique_id = random.randint(10000, 99999)

        # 1. 注册
        register_response = client.post("/api/v1/auth/register", json={
            "username": f"auth_user_{unique_id}",
            "email": f"auth_{unique_id}@example.com",
            "password": "testpass123"
        })
        assert register_response.status_code == 200

        # 2. 登录
        login_response = client.post("/api/v1/auth/login", data={
            "username": f"auth_user_{unique_id}",
            "password": "testpass123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 3. 使用token访问受保护的资源
        me_response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["username"] == f"auth_user_{unique_id}"

        # 4. 验证未授权访问被拒绝
        unauthorized_response = client.get("/api/v1/platforms/")
        assert unauthorized_response.status_code == 401

    def test_error_handling(self, client: TestClient):
        """
        测试错误处理

        业务流程：
        1. 访问不存在的资源
        2. 提交无效数据
        3. 验证错误响应
        """
        # 注册并登录
        unique_id = random.randint(10000, 99999)
        client.post("/api/v1/auth/register", json={
            "username": f"error_user_{unique_id}",
            "email": f"error_{unique_id}@example.com",
            "password": "testpass123"
        })
        login_response = client.post("/api/v1/auth/login", data={
            "username": f"error_user_{unique_id}",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 1. 访问不存在的平台
        response = client.get("/api/v1/platforms/99999", headers=auth_headers)
        assert response.status_code == 404

        # 2. 访问不存在的内容
        response = client.get("/api/v1/content/99999", headers=auth_headers)
        assert response.status_code == 404

        # 3. 提交无效数据（空名称）
        response = client.post("/api/v1/platforms/", json={
            "name": "",
            "code": "",
            "type": "invalid",
            "is_active": True
        }, headers=auth_headers)
        assert response.status_code in [400, 422]
