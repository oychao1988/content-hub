#!/usr/bin/env python3
"""调试认证夹具的测试脚本"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
import main

# 使用内存 SQLite 作为测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建测试数据库
Base.metadata.create_all(bind=engine)

# 创建测试会话
db_session = TestingSessionLocal()

def override_get_db():
    try:
        yield db_session
    finally:
        pass

main.app.dependency_overrides[get_db] = override_get_db

with TestClient(main.app) as client:
    print("=== 调试 admin_auth_headers 夹具 ===")

    # 1. 尝试注册用户
    user_data = {
        "username": "adminuser",
        "email": "admin@example.com",
        "password": "testpassword123",
        "role": "admin"
    }

    print("\n1. 注册用户:")
    register_response = client.post("/api/v1/auth/register", json=user_data)
    print(f"状态码: {register_response.status_code}")
    print(f"响应内容: {register_response.json()}")

    # 2. 尝试登录
    print("\n2. 用户登录:")
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"],
    }

    login_response = client.post("/api/v1/auth/login", data=login_data)
    print(f"状态码: {login_response.status_code}")
    print(f"响应内容: {login_response.json()}")

    # 3. 提取 token
    if login_response.status_code == 200:
        print("\n3. 成功获取 token")
        token = login_response.json()["data"]["access_token"]
        print(f"Access Token: {token[:50]}...")

        # 4. 测试使用 token 访问受保护的端点
        print("\n4. 测试访问内容管理端点:")
        headers = {"Authorization": f"Bearer {token}"}
        content_response = client.get("/api/v1/content/", headers=headers)
        print(f"状态码: {content_response.status_code}")
        print(f"响应内容: {content_response.json()}")
    else:
        print("\n3. 登录失败")

# 清理
db_session.close()
Base.metadata.drop_all(bind=engine)