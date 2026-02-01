#!/usr/bin/env python3
"""修复后的简单认证流程测试脚本"""

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
    print("=== 修复后的简单认证测试 ===")

    # 1. 清理可能存在的用户
    from app.models.user import User

    # 查看当前数据库中的用户
    all_users = db_session.query(User).all()
    print(f"当前数据库中的用户数量: {len(all_users)}")
    for user in all_users:
        print(f"- {user.username} ({user.email})")

    # 尝试删除用户
    existing_user = db_session.query(User).filter(User.username == "adminuser").first()
    if existing_user:
        db_session.delete(existing_user)
        db_session.commit()
        print("\n已删除用户:", existing_user.username)

    existing_email = db_session.query(User).filter(User.email == "admin@example.com").first()
    if existing_email:
        db_session.delete(existing_email)
        db_session.commit()
        print("已删除邮箱:", existing_email.email)

    # 确认用户已删除
    remaining_users = db_session.query(User).all()
    print(f"\n删除后用户数量: {len(remaining_users)}")

    # 2. 重新注册用户
    user_data = {
        "username": "adminuser",
        "email": "admin@example.com",
        "password": "testpassword123",
        "role": "admin"
    }

    print("\n2. 注册新用户:")
    register_response = client.post("/api/v1/auth/register", json=user_data)
    print(f"状态码: {register_response.status_code}")
    print(f"响应内容: {register_response.json()}")

    if register_response.status_code == 200:
        print("\n3. 用户登录:")
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"],
        }

        login_response = client.post("/api/v1/auth/login", data=login_data)
        print(f"状态码: {login_response.status_code}")
        print(f"响应内容: {login_response.json()}")

        if login_response.status_code == 200:
            token = login_response.json()["data"]["access_token"]
            print(f"Token: {token}")

            print("\n4. 访问受保护的端点:")
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/v1/content/", headers=headers)
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.json()}")

db_session.close()
Base.metadata.drop_all(bind=engine)