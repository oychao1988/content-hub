#!/usr/bin/env python3
"""测试密码验证功能"""

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
    print("=== 测试密码验证功能 ===")

    from app.core.security import get_password_hash, verify_password, create_salt
    from app.models.user import User
    from app.modules.shared.services.user_service import create_user
    from app.modules.shared.schemas.user import UserCreate

    # 1. 直接测试密码哈希和验证
    print("\n1. 直接测试密码哈希和验证:")
    test_password = "testpassword123"
    salt = create_salt()
    hashed = get_password_hash(test_password, salt)
    print(f"密码: {test_password}")
    print(f"盐值: {salt}")
    print(f"哈希: {hashed}")

    verification_result = verify_password(test_password, hashed)
    print(f"验证结果: {verification_result}")

    # 2. 通过 API 创建用户并测试
    print("\n2. 通过 API 创建用户并测试:")
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": test_password,
        "role": "admin"
    }

    register_response = client.post("/api/v1/auth/register", json=user_data)
    print(f"注册状态码: {register_response.status_code}")

    if register_response.status_code == 200:
        # 获取创建的用户
        user = db_session.query(User).filter(User.username == user_data["username"]).first()
        if user:
            print(f"用户在数据库中的密码哈希: {user.password_hash}")

            # 直接使用验证函数
            verify_result = verify_password(test_password, user.password_hash)
            print(f"验证结果: {verify_result}")

            # 尝试登录
            login_response = client.post("/api/v1/auth/login", data={
                "username": user_data["username"],
                "password": test_password
            })
            print(f"登录状态码: {login_response.status_code}")

            if login_response.status_code == 200:
                print(f"登录成功，获取到 token")
                print(f"响应内容: {login_response.json()}")
            else:
                print(f"登录失败: {login_response.json()}")

    # 3. 测试测试夹具中的密码哈希
    print("\n3. 测试测试夹具中的密码哈希:")
    from tests.conftest import test_user

    # 直接调用 test_user 夹具（虽然不推荐，但用于测试）
    # 我们将模拟 test_user 夹具的行为
    test_salt = create_salt()
    fixture_hashed_password = get_password_hash("testpassword123", test_salt)
    print(f"夹具密码哈希: {fixture_hashed_password}")

    verify_fixture = verify_password("testpassword123", fixture_hashed_password)
    print(f"夹具密码验证结果: {verify_fixture}")

db_session.close()
Base.metadata.drop_all(bind=engine)