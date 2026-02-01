#!/usr/bin/env python3
"""直接测试登录函数的脚本"""

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
    print("=== 直接测试登录函数 ===")

    from app.core.security import get_password_hash, verify_password, create_salt
    from app.models.user import User
    from app.modules.shared.services.user_service import create_user, authenticate_user
    from app.modules.shared.schemas.user import UserCreate

    # 创建一个测试用户
    test_username = "directtestuser"
    test_password = "testpassword123"
    user_data = UserCreate(
        username=test_username,
        email="directtest@example.com",
        password=test_password,
        role="admin"
    )

    created_user = create_user(db_session, user_data)
    print(f"创建用户: {created_user.username}")
    print(f"密码哈希: {created_user.password_hash}")

    # 测试 verify_password 函数
    verify_result = verify_password(test_password, created_user.password_hash)
    print(f"verify_password 结果: {verify_result}")

    # 测试 authenticate_user 函数
    user = authenticate_user(db_session, test_username, test_password, use_email=False)
    print(f"authenticate_user 结果: {user is not None}")

    # 测试通过 API 登录
    print("\n通过 API 登录:")
    response = client.post("/api/v1/auth/login", data={
        "username": test_username,
        "password": test_password
    })
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")

    if response.status_code != 200:
        print("\n=== 调试表单数据 ===")
        from urllib.parse import urlencode
        login_data = {
            "username": test_username,
            "password": test_password
        }
        print(f"表单数据: {urlencode(login_data)}")

    # 清理
    db_session.delete(created_user)
    db_session.commit()

db_session.close()
Base.metadata.drop_all(bind=engine)