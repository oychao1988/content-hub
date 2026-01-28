"""认证模块 API 集成测试"""

import pytest
from fastapi.testclient import TestClient


class TestAuthRegister:
    """用户注册测试类"""

    def test_register_user_with_email(self, client: TestClient):
        """测试使用邮箱注册用户"""
        user_data = {
            "email": "newuser123@example.com",
            "username": "newuser123",
            "password": "password123"
        }

        response = client.post(
            "/api/v1/auth/register",
            json=user_data
        )

        import json
        print("Response status:", response.status_code)
        print("Response content:", response.content)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["email"] == "newuser123@example.com"
        assert data["data"]["username"] == "newuser123"
        assert data["data"]["is_active"] is True
        assert "id" in data["data"]

    def test_register_user_with_username_only(self, client: TestClient):
        """测试仅使用用户名注册用户"""
        user_data = {
            "username": "username_only",
            "email": "usernameonly@example.com",
            "password": "password123"
        }

        response = client.post(
            "/api/v1/auth/register",
            json=user_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "username_only"

    def test_register_duplicate_email(self, client: TestClient):
        """测试注册重复邮箱"""
        user_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "password123"
        }

        # 注册第一个用户
        client.post("/api/v1/auth/register", json=user_data)

        # 尝试注册相同邮箱
        user_data2 = {
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/register", json=user_data2)

        import json
        print("Response status:", response.status_code)
        print("Response content:", response.content)

        assert response.status_code == 400
        assert "邮箱已存在" in response.json()["error"]["message"]

    def test_register_duplicate_username(self, client: TestClient):
        """测试注册重复用户名"""
        user_data = {
            "email": "user1@example.com",
            "username": "samename",
            "password": "password123"
        }

        # 注册第一个用户
        client.post("/api/v1/auth/register", json=user_data)

        # 尝试注册相同用户名
        user_data2 = {
            "email": "user2@example.com",
            "username": "samename",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/register", json=user_data2)

        assert response.status_code == 400
        assert "用户名已存在" in response.json()["error"]["message"]

    def test_register_missing_email(self, client: TestClient):
        """测试注册时缺少邮箱"""
        user_data = {
            "username": "noemail",
            "password": "password123"
        }

        response = client.post(
            "/api/v1/auth/register",
            json=user_data
        )

        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        """测试注册时密码过短"""
        user_data = {
            "email": "shortpass@example.com",
            "username": "shortpass",
            "password": "12345"  # 少于6位
        }

        response = client.post(
            "/api/v1/auth/register",
            json=user_data
        )

        assert response.status_code == 422


class TestAuthLogin:
    """用户登录测试类"""

    def test_login_with_email(self, client: TestClient):
        """测试使用邮箱登录"""
        # 先注册用户
        user_data = {
            "email": "loginuser@example.com",
            "username": "loginuser",
            "password": "loginpass123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # 使用邮箱登录
        login_data = {
            "email": "loginuser@example.com",
            "password": "loginpass123"
        }

        response = client.post(
            "/api/v1/auth/login",
            json=login_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert "expires_in" in data["data"]

    def test_login_with_username(self, client: TestClient):
        """测试使用用户名登录"""
        # 先注册用户
        user_data = {
            "email": "username_login@example.com",
            "username": "username_login",
            "password": "userpass123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # 使用用户名登录
        login_data = {
            "username": "username_login",
            "password": "userpass123"
        }

        response = client.post(
            "/api/v1/auth/login",
            json=login_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]

    def test_login_with_form_data(self, client: TestClient):
        """测试使用表单数据登录"""
        # 先注册用户
        user_data = {
            "email": "formlogin@example.com",
            "username": "formlogin",
            "password": "formpass123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # 使用表单数据登录
        login_data = {
            "username": "formlogin",
            "password": "formpass123"
        }

        response = client.post(
            "/api/v1/auth/login",
            data=login_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]

    def test_login_with_email_in_username_field(self, client: TestClient):
        """测试在 username 字段使用邮箱登录"""
        # 先注册用户
        user_data = {
            "email": "emailasuser@example.com",
            "username": "emailasuser",
            "password": "emailpass123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # 在 username 字段使用邮箱
        login_data = {
            "username": "emailasuser@example.com",
            "password": "emailpass123"
        }

        response = client.post(
            "/api/v1/auth/login",
            json=login_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_login_wrong_password(self, client: TestClient):
        """测试使用错误密码登录"""
        # 先注册用户
        user_data = {
            "email": "wrongpass@example.com",
            "username": "wrongpass",
            "password": "correctpass123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # 使用错误密码登录
        login_data = {
            "email": "wrongpass@example.com",
            "password": "wrongpass123"
        }

        response = client.post(
            "/api/v1/auth/login",
            json=login_data
        )

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["error"]["message"]

    def test_login_nonexistent_user(self, client: TestClient):
        """测试使用不存在的用户登录"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "anypassword123"
        }

        response = client.post(
            "/api/v1/auth/login",
            json=login_data
        )

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["error"]["message"]

    def test_login_missing_password(self, client: TestClient):
        """测试登录时缺少密码"""
        login_data = {
            "email": "nopass@example.com"
        }

        response = client.post(
            "/api/v1/auth/login",
            json=login_data
        )

        assert response.status_code == 400
        assert "密码不能为空" in response.json()["error"]["message"]

    def test_login_missing_identifier(self, client: TestClient):
        """测试登录时缺少标识符"""
        login_data = {
            "password": "somepassword123"
        }

        response = client.post(
            "/api/v1/auth/login",
            json=login_data
        )

        assert response.status_code == 422


class TestAuthRefresh:
    """Token 刷新测试类"""

    def test_refresh_token(self, client: TestClient):
        """测试刷新访问令牌"""
        # 先注册并登录
        user_data = {
            "email": "refresh@example.com",
            "username": "refreshuser",
            "password": "refreshpass123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "refresh@example.com",
                "password": "refreshpass123"
            }
        )
        refresh_token = login_response.json()["data"]["refresh_token"]

        # 使用刷新令牌获取新的访问令牌
        refresh_data = {
            "refresh_token": refresh_token
        }

        response = client.post(
            "/api/v1/auth/refresh",
            json=refresh_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        # 新的刷新令牌应该与旧的不同
        assert data["data"]["refresh_token"] != refresh_token

    def test_refresh_invalid_token(self, client: TestClient):
        """测试使用无效的刷新令牌"""
        refresh_data = {
            "refresh_token": "invalid_refresh_token_12345"
        }

        response = client.post(
            "/api/v1/auth/refresh",
            json=refresh_data
        )

        assert response.status_code == 401
        assert "无效的刷新令牌" in response.json()["detail"]


class TestAuthMe:
    """获取当前用户信息测试类"""

    def test_get_current_user(self, client: TestClient):
        """测试获取当前登录用户信息"""
        # 先注册并登录
        user_data = {
            "email": "meuser@example.com",
            "username": "meuser",
            "password": "mepass123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "meuser@example.com",
                "password": "mepass123"
            }
        )
        access_token = login_response.json()["data"]["access_token"]

        # 获取当前用户信息
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "meuser@example.com"
        assert data["data"]["username"] == "meuser"

    def test_get_current_user_without_token(self, client: TestClient):
        """测试未提供令牌时获取当前用户"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """测试使用无效令牌获取当前用户"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 401


class TestAuthLogout:
    """用户登出测试类"""

    def test_logout(self, client: TestClient):
        """测试用户登出"""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 204
        assert response.content == b""


class TestAuthForgotPassword:
    """忘记密码测试类"""

    def test_forgot_password_existing_email(self, client: TestClient):
        """测试为存在的邮箱请求重置密码"""
        # 先注册用户
        user_data = {
            "email": "forgot@example.com",
            "username": "forgotuser",
            "password": "forgotpass123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # 请求重置密码
        forgot_data = {
            "email": "forgot@example.com"
        }

        response = client.post(
            "/api/v1/auth/forgot-password",
            json=forgot_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reset_token" in data["data"]

    def test_forgot_password_nonexistent_email(self, client: TestClient):
        """测试为不存在的邮箱请求重置密码"""
        # 不暴露用户是否存在，仍返回成功
        forgot_data = {
            "email": "nonexistent@example.com"
        }

        response = client.post(
            "/api/v1/auth/forgot-password",
            json=forgot_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 不存在的邮箱不返回 reset_token
        assert "reset_token" not in data["data"]


class TestAuthResetPassword:
    """重置密码测试类"""

    def test_reset_password_valid_token(self, client: TestClient):
        """测试使用有效令牌重置密码"""
        # 先注册用户
        user_data = {
            "email": "reset@example.com",
            "username": "resetuser",
            "password": "oldpass123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # 获取重置令牌
        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "reset@example.com"}
        )
        reset_token = forgot_response.json()["data"]["reset_token"]

        # 使用令牌重置密码
        reset_data = {
            "token": reset_token,
            "password": "newpass123"
        }

        response = client.post(
            "/api/v1/auth/reset-password",
            json=reset_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "密码已重置" in data["data"]["message"]

        # 验证新密码可以登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "reset@example.com",
                "password": "newpass123"
            }
        )
        assert login_response.status_code == 200

    def test_reset_password_invalid_token(self, client: TestClient):
        """测试使用无效令牌重置密码"""
        reset_data = {
            "token": "invalid_reset_token_12345",
            "password": "newpass123"
        }

        response = client.post(
            "/api/v1/auth/reset-password",
            json=reset_data
        )

        assert response.status_code == 400
        assert "无效或过期的重置令牌" in response.json()["detail"]


class TestAuthVerifyToken:
    """验证令牌测试类"""

    def test_verify_valid_reset_token(self, client: TestClient):
        """测试验证有效的重置令牌"""
        # 先注册用户
        user_data = {
            "email": "verify@example.com",
            "username": "verifyuser",
            "password": "verifypass123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # 获取重置令牌
        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "verify@example.com"}
        )
        reset_token = forgot_response.json()["data"]["reset_token"]

        # 验证令牌
        verify_data = {
            "token": reset_token
        }

        response = client.post(
            "/api/v1/auth/verify",
            json=verify_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["valid"] is True
        assert "user_id" in data["data"]

    def test_verify_invalid_reset_token(self, client: TestClient):
        """测试验证无效的重置令牌"""
        verify_data = {
            "token": "invalid_verify_token_12345"
        }

        response = client.post(
            "/api/v1/auth/verify",
            json=verify_data
        )

        assert response.status_code == 400
        assert "无效或过期的重置令牌" in response.json()["detail"]


class TestAuthWorkflow:
    """认证流程集成测试类"""

    def test_complete_auth_workflow(self, client: TestClient):
        """测试完整的认证流程"""
        # 1. 注册用户
        user_data = {
            "email": "workflow@example.com",
            "username": "workflowuser",
            "password": "workflowpass123"
        }
        register_response = client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        assert register_response.status_code == 200
        user_id = register_response.json()["data"]["id"]

        # 2. 登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "workflow@example.com",
                "password": "workflowpass123"
            }
        )
        assert login_response.status_code == 200
        tokens = login_response.json()["data"]
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 3. 获取当前用户信息
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["data"]["id"] == user_id

        # 4. 刷新令牌
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["data"]["access_token"]

        # 5. 使用新令牌获取用户信息
        me_response2 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert me_response2.status_code == 200

        # 6. 登出
        logout_response = client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 204

    def test_password_reset_workflow(self, client: TestClient):
        """测试密码重置完整流程"""
        # 1. 注册用户
        user_data = {
            "email": "resetflow@example.com",
            "username": "resetflow",
            "password": "oldpassword123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # 2. 请求重置密码
        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "resetflow@example.com"}
        )
        assert forgot_response.status_code == 200
        reset_token = forgot_response.json()["data"]["reset_token"]

        # 3. 验证令牌
        verify_response = client.post(
            "/api/v1/auth/verify",
            json={"token": reset_token}
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["data"]["valid"] is True

        # 4. 重置密码
        reset_response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token,
                "password": "newpassword123"
            }
        )
        assert reset_response.status_code == 200

        # 5. 使用新密码登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "resetflow@example.com",
                "password": "newpassword123"
            }
        )
        assert login_response.status_code == 200

        # 6. 验证旧密码无法登录
        old_login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "resetflow@example.com",
                "password": "oldpassword123"
            }
        )
        assert old_login_response.status_code == 401
