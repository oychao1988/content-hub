#!/usr/bin/env python3
"""测试直接调用和API端点调用的差异"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
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
    print("=== 测试直接调用和API端点调用的差异 ===")

    # 1. 直接使用 user_service 创建用户
    from app.modules.shared.services.user_service import create_user
    from app.modules.shared.schemas.user import UserCreate

    print("\n1. 直接使用 user_service 创建用户:")
    try:
        user_data = UserCreate(
            username="adminuser",
            email="admin@example.com",
            password="testpassword123",
            role="admin"
        )
        new_user = create_user(db_session, user_data)
        print(f"成功创建用户: {new_user.username} ({new_user.email})")

        # 检查用户是否在数据库中
        all_users = db_session.query(text("SELECT * FROM users")).all()
        print(f"数据库中的用户数量: {len(all_users)}")
        if all_users:
            print(f"用户详细信息: {all_users[0]}")

    except Exception as e:
        print(f"创建失败: {e}")

    # 2. 尝试通过 API 端点注册用户
    print("\n2. 尝试通过 API 端点注册用户:")
    api_user_data = {
        "username": "adminuser_api",
        "email": "admin_api@example.com",
        "password": "testpassword123",
        "role": "admin"
    }

    register_response = client.post("/api/v1/auth/register", json=api_user_data)
    print(f"状态码: {register_response.status_code}")
    print(f"响应内容: {register_response.json()}")

    # 3. 检查数据库中的用户数量
    print("\n3. 数据库中的用户数量:")
    all_users = db_session.query(text("SELECT * FROM users")).all()
    print(f"数量: {len(all_users)}")
    for user in all_users:
        print(f"用户: {user}")

db_session.close()
Base.metadata.drop_all(bind=engine)