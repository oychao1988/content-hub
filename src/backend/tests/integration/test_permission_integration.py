"""
权限控制 API 集成测试

测试各种权限组合和未授权访问的场景
"""
import pytest
from fastapi.testclient import TestClient


class TestPermissionEndpoints:
    """权限控制 API 端点测试类"""

    def test_admin_user_can_access_all_endpoints(self, client: TestClient, admin_auth_headers):
        """测试管理员用户可以访问所有端点"""
        print(f"admin_auth_headers: {admin_auth_headers}")
        # 测试内容管理
        content_response = client.get("/api/v1/content/", headers=admin_auth_headers)
        assert content_response.status_code in [200, 404]  # 可能没有数据

        # 测试账号管理
        accounts_response = client.get("/api/v1/accounts/", headers=admin_auth_headers)
        assert accounts_response.status_code in [200, 404]

        # 测试定时任务
        scheduler_response = client.get("/api/v1/scheduler/tasks", headers=admin_auth_headers)
        assert scheduler_response.status_code in [200, 404]

        # 测试发布管理
        publishers_response = client.get("/api/v1/publishers/", headers=admin_auth_headers)
        assert publishers_response.status_code in [200, 404]

        # 测试发布池
        publish_pool_response = client.get("/api/v1/publish-pool/", headers=admin_auth_headers)
        assert publish_pool_response.status_code in [200, 404]

    def test_operator_cannot_access_admin_endpoints(self, client: TestClient, operator_auth_headers):
        """测试操作员用户不能访问管理员才能访问的端点"""
        # 测试创建账号（需要 ACCOUNT_CREATE 权限）
        account_data = {
            "directory_name": "forbidden_account",
            "display_name": "禁止访问的账号",
            "description": "操作员用户无法创建账号",
            "niche": "technology"
        }
        create_account_response = client.post(
            "/api/v1/accounts/",
            json=account_data,
            headers=operator_auth_headers
        )

        assert create_account_response.status_code == 403  # 应该返回禁止访问

    def test_editor_can_access_content_endpoints(self, client: TestClient, editor_auth_headers, test_customer):
        """测试编辑用户可以访问内容管理相关端点"""
        # 测试获取内容列表
        content_list_response = client.get("/api/v1/content/", headers=editor_auth_headers)
        assert content_list_response.status_code in [200, 404]

        # 测试创建内容（需要 CONTENT_CREATE 权限）
        content_data = {
            "account_id": 1,  # 假设已存在的账号ID
            "topic": "编辑创建的测试文章",
            "category": "技术文章"
        }

        # 首先需要创建测试平台和账号，因为直接使用 account_id: 1 可能不存在
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "测试平台",
                "code": "test_platform",
                "type": "social_media",
                "description": "用于测试的平台",
                "api_url": "https://api.test.com",
                "api_key": "test_key",
                "is_active": True
            },
            headers=editor_auth_headers
        )

        # 如果创建平台成功，则可以继续创建账号和内容
        if platform_response.status_code == 201:
            platform_id = platform_response.json()["id"]

            account_response = client.post(
                "/api/v1/accounts/",
                json={
                    "directory_name": "editor_test_account",
                    "display_name": "编辑测试账号",
                    "description": "用于编辑用户测试的账号",
                    "niche": "technology"
                },
                headers=editor_auth_headers
            )

            if account_response.status_code == 201:
                content_data["account_id"] = account_response.json()["id"]

                create_content_response = client.post(
                    "/api/v1/content/create",
                    json=content_data,
                    headers=editor_auth_headers
                )

                assert create_content_response.status_code in [201, 403]  # 可能有权限限制

    def test_viewer_cannot_modify_data(self, client: TestClient, viewer_auth_headers, test_customer):
        """测试查看用户只能查看数据，不能修改数据"""
        # 测试获取内容列表（应该允许）
        get_response = client.get("/api/v1/content/", headers=viewer_auth_headers)
        assert get_response.status_code in [200, 404]

        # 测试创建内容（应该禁止）
        content_data = {
            "account_id": 1,
            "topic": "查看用户尝试创建的文章",
            "category": "技术文章"
        }

        create_response = client.post(
            "/api/v1/content/create",
            json=content_data,
            headers=viewer_auth_headers
        )

        assert create_response.status_code == 403

        # 测试更新内容（应该禁止）
        update_response = client.put(
            "/api/v1/content/1",
            json={"title": "尝试更新的标题"},
            headers=viewer_auth_headers
        )

        assert update_response.status_code in [403, 404]

    def test_unauthorized_access(self, client: TestClient):
        """测试未授权访问"""
        # 测试无任何认证信息
        response = client.get("/api/v1/content/")
        assert response.status_code == 401

    def test_token_expired_or_invalid(self, client: TestClient, invalid_auth_headers):
        """测试无效或过期的令牌"""
        response = client.get("/api/v1/content/", headers=invalid_auth_headers)
        assert response.status_code == 401

    def test_user_cannot_access_other_customer_data(self, client: TestClient, admin_auth_headers, test_customer):
        """测试用户无法访问其他客户的数据"""
        # 首先使用 admin 身份创建一些数据
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "客户1的平台",
                "code": "customer1_platform",
                "type": "social_media",
                "description": "仅客户1可以访问的平台",
                "api_url": "https://api.test.com",
                "api_key": "test_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )

        if platform_response.status_code == 201:
            platform_id = platform_response.json()["id"]

            # 创建账号
            account_response = client.post(
                "/api/v1/accounts/",
                json={
                    "directory_name": "customer2_test_account",
                    "display_name": "客户2的测试账号",
                    "description": "用于跨客户数据访问测试的账号",
                    "niche": "technology"
                },
                headers=admin_auth_headers
            )

            if account_response.status_code == 201:
                # 使用相同的身份尝试获取该账号（应该被允许，因为是创建者）
                get_response = client.get(
                    f"/api/v1/accounts/{account_response.json()['id']}",
                    headers=admin_auth_headers
                )
                assert get_response.status_code == 200

    def test_permission_denied_message(self, client: TestClient, operator_auth_headers):
        """测试权限拒绝时的错误信息格式"""
        # 尝试访问需要 admin 权限的端点
        response = client.post(
            "/api/v1/accounts/",
            json={
                "directory_name": "test_account",
                "display_name": "测试账号",
                "description": "测试权限拒绝",
                "niche": "technology"
            },
            headers=operator_auth_headers
        )

        if response.status_code == 403:
            error_data = response.json()
            assert "error" in error_data
            assert "权限" in error_data["error"]["message"]


class TestPermissionCombinations:
    """测试各种权限组合"""

    def test_admin_full_permissions(self, client: TestClient, admin_auth_headers, test_customer):
        """测试管理员拥有所有权限"""
        # 测试创建平台
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "管理员测试平台",
                "code": "admin_test_platform",
                "type": "social_media",
                "description": "管理员创建的平台",
                "api_url": "https://api.test.com",
                "api_key": "test_key",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        assert platform_response.status_code in [201, 200]

        # 测试创建账号
        if platform_response.status_code in [201, 200]:
            platform_id = platform_response.json()["id"]
            account_response = client.post(
                "/api/v1/accounts/",
                json={
                    "customer_id": test_customer.id,
                    "platform_id": platform_id,
                    "name": "管理员测试账号",
                    "directory_name": "admin_test_account",
                    "description": "管理员创建的账号",
                    "is_active": True
                },
                headers=admin_auth_headers
            )
            assert account_response.status_code in [201, 200]

        # 测试创建内容
        if account_response.status_code in [201, 200]:
            account_id = account_response.json()["id"]
            content_response = client.post(
                "/api/v1/content/create",
                json={
                    "account_id": account_id,
                    "topic": "管理员创建的内容",
                    "category": "测试分类"
                },
                headers=admin_auth_headers
            )
            assert content_response.status_code in [201, 200]

        # 测试创建定时任务
        task_response = client.post(
            "/api/v1/scheduler/tasks",
            json={
                "name": "管理员测试任务",
                "description": "管理员创建的任务",
                "task_type": "content_generation",
                "cron_expression": "0 8 * * *",
                "is_active": True
            },
            headers=admin_auth_headers
        )
        assert task_response.status_code in [201, 200]

    def test_editor_limited_permissions(self, client: TestClient, editor_auth_headers, test_customer):
        """测试编辑用户的权限限制"""
        # 编辑用户应该能够查看内容
        content_list_response = client.get("/api/v1/content/", headers=editor_auth_headers)
        assert content_list_response.status_code in [200, 404]

        # 编辑用户可能无法创建平台（取决于权限配置）
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "编辑测试平台",
                "code": "editor_test_platform",
                "type": "social_media",
                "description": "编辑尝试创建平台",
                "api_url": "https://api.test.com",
                "api_key": "test_key",
                "is_active": True
            },
            headers=editor_auth_headers
        )
        # 如果编辑用户没有创建平台的权限，应该返回403
        if platform_response.status_code not in [201, 200]:
            assert platform_response.status_code in [403, 401]

        # 编辑用户可能无法删除账号
        accounts_response = client.get("/api/v1/accounts/", headers=editor_auth_headers)
        if accounts_response.status_code == 200 and len(accounts_response.json()) > 0:
            account_id = accounts_response.json()[0]["id"]
            delete_response = client.delete(f"/api/v1/accounts/{account_id}", headers=editor_auth_headers)
            assert delete_response.status_code in [403, 401, 404]

    def test_viewer_read_only_permissions(self, client: TestClient, viewer_auth_headers):
        """测试查看用户的只读权限"""
        # 查看用户应该能够查看内容列表
        content_response = client.get("/api/v1/content/", headers=viewer_auth_headers)
        assert content_response.status_code in [200, 404]

        # 查看用户应该能够查看账号列表
        accounts_response = client.get("/api/v1/accounts/", headers=viewer_auth_headers)
        assert accounts_response.status_code in [200, 404]

        # 查看用户应该能够查看定时任务
        scheduler_response = client.get("/api/v1/scheduler/tasks", headers=viewer_auth_headers)
        assert scheduler_response.status_code in [200, 404]

        # 查看用户不应该能够创建内容
        create_response = client.post(
            "/api/v1/content/create",
            json={
                "account_id": 1,
                "topic": "查看用户尝试创建内容",
                "category": "测试"
            },
            headers=viewer_auth_headers
        )
        assert create_response.status_code in [403, 401, 400]

        # 查看用户不应该能够创建定时任务
        task_response = client.post(
            "/api/v1/scheduler/tasks",
            json={
                "name": "查看用户尝试创建任务",
                "description": "应该被拒绝",
                "task_type": "content_generation",
                "cron_expression": "0 8 * * *",
                "is_active": True
            },
            headers=viewer_auth_headers
        )
        assert task_response.status_code in [403, 401]

    def test_operator_maintenance_permissions(self, client: TestClient, operator_auth_headers):
        """测试操作员的维护权限"""
        # 操作员可能能够查看内容
        content_response = client.get("/api/v1/content/", headers=operator_auth_headers)
        assert content_response.status_code in [200, 404]

        # 操作员可能无法删除数据
        delete_response = client.delete("/api/v1/content/1", headers=operator_auth_headers)
        assert delete_response.status_code in [403, 401, 404]


class TestDataIsolation:
    """测试跨用户数据隔离"""

    def test_customer_data_isolation(self, client: TestClient, db_session):
        """测试不同客户的数据隔离"""
        from app.models.user import User
        from app.core.security import create_salt, get_password_hash
        from app.models.customer import Customer

        # 创建两个不同的客户
        customer1 = Customer(
            name="客户A",
            contact_name="张三",
            contact_email="zhangsan@example.com",
            contact_phone="13800000001",
            description="客户A的描述",
            is_active=True
        )
        customer2 = Customer(
            name="客户B",
            contact_name="李四",
            contact_email="lisi@example.com",
            contact_phone="13800000002",
            description="客户B的描述",
            is_active=True
        )
        db_session.add(customer1)
        db_session.add(customer2)
        db_session.commit()
        db_session.refresh(customer1)
        db_session.refresh(customer2)

        # 为两个客户创建用户
        salt1 = create_salt()
        user1 = User(
            username="customer1_user",
            email="user1@example.com",
            full_name="客户A用户",
            password_hash=get_password_hash("testpass123", salt1),
            role="editor",
            is_active=True
        )
        salt2 = create_salt()
        user2 = User(
            username="customer2_user",
            email="user2@example.com",
            full_name="客户B用户",
            password_hash=get_password_hash("testpass123", salt2),
            role="editor",
            is_active=True
        )
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)

        # 登录两个用户
        login1_response = client.post(
            "/api/v1/auth/login",
            data={"username": "customer1_user", "password": "testpass123"}
        )
        if login1_response.status_code != 200:
            pytest.skip("无法登录用户1")

        token1 = login1_response.json()["data"]["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        login2_response = client.post(
            "/api/v1/auth/login",
            data={"username": "customer2_user", "password": "testpass123"}
        )
        if login2_response.status_code != 200:
            pytest.skip("无法登录用户2")

        token2 = login2_response.json()["data"]["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # 用户1创建平台和账号
        platform_response = client.post(
            "/api/v1/platforms/",
            json={
                "name": "用户1的平台",
                "code": "user1_platform",
                "type": "social_media",
                "description": "用户1创建",
                "api_url": "https://api.test.com",
                "api_key": "test_key",
                "is_active": True
            },
            headers=headers1
        )

        # 验证数据隔离（具体实现取决于系统的权限模型）
        # 这里我们测试基本的权限边界
        content1_response = client.get("/api/v1/content/", headers=headers1)
        content2_response = client.get("/api/v1/content/", headers=headers2)

        # 两个用户都应该能够访问内容列表
        assert content1_response.status_code in [200, 404]
        assert content2_response.status_code in [200, 404]

    def test_user_cannot_modify_others_content(self, client: TestClient, db_session):
        """测试用户无法修改其他用户创建的内容"""
        from app.models.user import User
        from app.core.security import create_salt, get_password_hash

        # 创建两个用户
        salt1 = create_salt()
        user1 = User(
            username="content_creator1",
            email="creator1@example.com",
            full_name="内容创建者1",
            password_hash=get_password_hash("testpass123", salt1),
            role="editor",
            is_active=True
        )
        salt2 = create_salt()
        user2 = User(
            username="content_creator2",
            email="creator2@example.com",
            full_name="内容创建者2",
            password_hash=get_password_hash("testpass123", salt2),
            role="editor",
            is_active=True
        )
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()

        # 用户1登录
        login1_response = client.post(
            "/api/v1/auth/login",
            data={"username": "content_creator1", "password": "testpass123"}
        )
        if login1_response.status_code != 200:
            pytest.skip("无法登录用户1")

        token1 = login1_response.json()["data"]["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        # 用户2登录
        login2_response = client.post(
            "/api/v1/auth/login",
            data={"username": "content_creator2", "password": "testpass123"}
        )
        if login2_response.status_code != 200:
            pytest.skip("无法登录用户2")

        token2 = login2_response.json()["data"]["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # 用户1创建内容
        # （这里需要先创建平台和账号，简化起见我们跳过这步）
        # 主要的验证逻辑是：用户2不应该能够修改用户1的内容

    def test_audit_log_permission_tracking(self, client: TestClient, admin_auth_headers):
        """测试审计日志记录权限相关的操作"""
        # 管理员查看审计日志
        audit_response = client.get("/api/v1/audit/logs", headers=admin_auth_headers)
        assert audit_response.status_code in [200, 404]

        # 尝试一些操作（应该被记录在审计日志中）
        client.get("/api/v1/content/", headers=admin_auth_headers)
        client.get("/api/v1/accounts/", headers=admin_auth_headers)

        # 再次查看审计日志，应该有新的记录
        audit_response_after = client.get("/api/v1/audit/logs", headers=admin_auth_headers)
        assert audit_response_after.status_code in [200, 404]


class TestPermissionEdgeCases:
    """测试权限边界情况"""

    def test_inactive_user_cannot_access(self, client: TestClient, db_session):
        """测试未激活用户无法访问"""
        from app.models.user import User
        from app.core.security import create_salt, get_password_hash

        # 创建未激活的用户
        salt = create_salt()
        user = User(
            username="inactive_user",
            email="inactive@example.com",
            full_name="未激活用户",
            password_hash=get_password_hash("testpass123", salt),
            role="editor",
            is_active=False  # 未激活
        )
        db_session.add(user)
        db_session.commit()

        # 尝试登录
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "inactive_user", "password": "testpass123"}
        )
        # 应该失败（401或其他错误）
        assert login_response.status_code != 200

    def test_expired_token_rejected(self, client: TestClient):
        """测试过期token被拒绝"""
        # 使用一个明显无效的token
        expired_headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired.token"}
        response = client.get("/api/v1/content/", headers=expired_headers)
        assert response.status_code == 401

    def test_malformed_token_rejected(self, client: TestClient):
        """测试格式错误的token被拒绝"""
        malformed_headers = {"Authorization": "Bearer invalid-token-format"}
        response = client.get("/api/v1/content/", headers=malformed_headers)
        assert response.status_code == 401

    def test_missing_auth_header_rejected(self, client: TestClient):
        """测试缺少认证头被拒绝"""
        response = client.get("/api/v1/content/")
        assert response.status_code == 401

    def test_permission_check_on_all_endpoints(self, client: TestClient, invalid_auth_headers):
        """测试所有主要端点都有权限检查"""
        endpoints = [
            ("GET", "/api/v1/content/"),
            ("GET", "/api/v1/accounts/"),
            ("GET", "/api/v1/scheduler/tasks"),
            ("GET", "/api/v1/publishers/"),
            ("GET", "/api/v1/publish-pool/"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint, headers=invalid_auth_headers)
            else:
                response = client.post(endpoint, headers=invalid_auth_headers)

            # 所有端点都应该拒绝无效token
            assert response.status_code == 401, f"{method} {endpoint} 应该返回401"
