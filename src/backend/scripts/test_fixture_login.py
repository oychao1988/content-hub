#!/usr/bin/env python3
"""测试测试夹具中的登录过程"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
import main

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

db_session = TestingSessionLocal()

def override_get_db():
    try:
        yield db_session
    finally:
        pass

main.app.dependency_overrides[get_db] = override_get_db

with TestClient(main.app) as client:
    print("=== 测试测试夹具中的登录过程 ===")

    # 测试 admin 用户登录
    print("\n1. 测试 admin 用户登录:")
    admin_user_data = {
        "username": "adminuser",
        "email": "admin@example.com",
        "password": "testpassword123",
        "role": "admin"
    }

    # 注册用户
    register_response = client.post("/api/v1/auth/register", json=admin_user_data)
    print(f"注册状态码: {register_response.status_code}")
    if register_response.status_code != 200:
        print(f"注册响应: {register_response.json()}")

    # 尝试登录
    login_data = {
        "username": admin_user_data["username"],
        "password": admin_user_data["password"],
    }

    login_response = client.post("/api/v1/auth/login", data=login_data)
    print(f"登录状态码: {login_response.status_code}")
    if login_response.status_code == 200:
        token = login_response.json()["data"]["access_token"]
        print(f"成功获取 token: {token[:50]}...")
    else:
        print(f"登录失败响应: {login_response.json()}")

    # 检查用户是否在数据库中
    from app.models.user import User
    from app.modules.shared.services.user_service import get_user_by_username

    user = get_user_by_username(db_session, admin_user_data["username"])
    if user:
        print(f"\n用户在数据库中找到:")
        print(f"用户名: {user.username}")
        print(f"邮箱: {user.email}")
        print(f"密码哈希: {user.password_hash}")

    # 测试 operator 用户登录
    print("\n2. 测试 operator 用户登录:")
    operator_user_data = {
        "username": "operatoruser",
        "email": "operator@example.com",
        "password": "testpassword123",
        "role": "operator"
    }

    # 注册用户
    register_response = client.post("/api/v1/auth/register", json=operator_user_data)
    print(f"注册状态码: {register_response.status_code}")
    if register_response.status_code != 200:
        print(f"注册响应: {register_response.json()}")

    # 尝试登录
    login_data = {
        "username": operator_user_data["username"],
        "password": operator_user_data["password"],
    }

    login_response = client.post("/api/v1/auth/login", data=login_data)
    print(f"登录状态码: {login_response.status_code}")
    if login_response.status_code == 200:
        token = login_response.json()["data"]["access_token"]
        print(f"成功获取 token: {token[:50]}...")
    else:
        print(f"登录失败响应: {login_response.json()}")

    # 测试使用 email 登录
    print("\n3. 测试使用 email 登录:")
    login_data_email = {
        "email": admin_user_data["email"],
        "password": admin_user_data["password"],
    }

    login_response_email = client.post("/api/v1/auth/login", data=login_data_email)
    print(f"邮箱登录状态码: {login_response_email.status_code}")
    if login_response_email.status_code == 200:
        token = login_response_email.json()["data"]["access_token"]
        print(f"成功获取 token: {token[:50]}...")
    else:
        print(f"邮箱登录失败响应: {login_response_email.json()}")

db_session.close()
Base.metadata.drop_all(bind=engine)