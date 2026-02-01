#!/usr/bin/env python3
"""测试密码哈希和验证功能"""

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
    print("=== 测试密码哈希和验证功能 ===")

    from app.core.security import get_password_hash, verify_password, create_salt
    from app.models.user import User
    from app.modules.shared.services.user_service import create_user
    from app.modules.shared.schemas.user import UserCreate

    # 创建一个临时用户来测试
    test_username = "passwordtestuser"
    test_password = "testpassword123"
    user_data = UserCreate(
        username=test_username,
        email="passwordtest@example.com",
        password=test_password,
        role="admin"
    )

    # 1. 使用 user_service.create_user 创建用户
    print("\n1. 使用 user_service.create_user 创建用户:")
    created_user = create_user(db_session, user_data)
    print(f"用户 ID: {created_user.id}")
    print(f"用户名: {created_user.username}")
    print(f"密码哈希: {created_user.password_hash}")

    # 2. 验证密码
    print("\n2. 验证密码:")
    verify_result = verify_password(test_password, created_user.password_hash)
    print(f"密码验证结果: {verify_result}")
    if not verify_result:
        print("密码验证失败！")

    # 3. 尝试登录
    print("\n3. 尝试登录:")
    login_response = client.post("/api/v1/auth/login", data={
        "username": test_username,
        "password": test_password
    })
    print(f"登录状态码: {login_response.status_code}")
    if login_response.status_code == 200:
        print("登录成功")
        print(f"响应内容: {login_response.json()}")
    else:
        print("登录失败")
        print(f"响应内容: {login_response.json()}")

    # 4. 调试密码验证过程
    print("\n4. 调试密码验证过程:")
    from app.modules.shared.services.user_service import authenticate_user
    user = authenticate_user(db_session, test_username, test_password, use_email=False)
    print(f"通过用户名认证结果: {user is not None}")
    if user:
        print(f"找到用户: {user.username}")

    # 5. 直接调用 verify_password 函数
    print("\n5. 直接调用 verify_password 函数:")
    from app.core.security import verify_password
    print(f"密码哈希格式: {created_user.password_hash}")
    parts = created_user.password_hash.split('$', 2)
    print(f"密码哈希部分: {len(parts)}")
    for i, part in enumerate(parts):
        print(f"  部分 {i}: {part}")

    # 6. 重新计算哈希值进行对比
    print("\n6. 重新计算哈希值进行对比:")
    salt = parts[0] if len(parts) > 0 else ""
    rehashed = get_password_hash(test_password, salt)
    print(f"重新计算的哈希值: {rehashed}")
    print(f"原始哈希值:      {created_user.password_hash}")
    print(f"哈希值是否相等: {rehashed == created_user.password_hash}")

    # 清理
    db_session.delete(created_user)
    db_session.commit()

db_session.close()
Base.metadata.drop_all(bind=engine)