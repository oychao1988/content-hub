#!/usr/bin/env python3
"""测试会话管理问题的脚本"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.sql_db import Base, get_db, get_engine, get_session_local
import main
from app.core.config import settings

# 覆盖配置，使用内存数据库
settings.DATABASE_URL = "sqlite:///:memory:"

# 重置数据库引擎和会话工厂
import app.db.sql_db
app.db.sql_db._engine = None
app.db.sql_db._session_local = None

# 创建测试数据库引擎和会话
engine = get_engine()
TestingSessionLocal = get_session_local()

# 使用正确的初始化函数创建表
from app.db.sql_db import init_db
init_db()

db_session = TestingSessionLocal()

def override_get_db():
    try:
        yield db_session
    finally:
        pass

main.app.dependency_overrides[get_db] = override_get_db

with TestClient(main.app) as client:
    print("=== 测试会话管理问题 ===")

    from app.core.security import get_password_hash, verify_password, create_salt
    from app.models.user import User
    from app.modules.shared.services.user_service import get_user_by_username

    # 1. 直接在 db_session 中创建用户
    print("\n1. 在 db_session 中创建用户:")
    test_username = "sessiontestuser"
    salt = create_salt()
    user = User(
        username=test_username,
        email="sessiontest@example.com",
        full_name="Session Test User",
        password_hash=get_password_hash("testpassword123", salt),
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    print(f"用户创建成功: {user.username}")

    # 2. 验证用户存在于 db_session 中
    print("\n2. 在 db_session 中查找用户:")
    found_user = get_user_by_username(db_session, test_username)
    print(f"找到用户: {found_user is not None}")
    if found_user:
        print(f"用户名: {found_user.username}")

    # 3. 通过 API 查找用户
    print("\n3. 通过 API 查找用户:")

    # 创建一个测试端点来查找用户
    from fastapi import APIRouter, Depends
    from sqlalchemy.orm import Session

    temp_router = APIRouter()

    @temp_router.get("/test-get-user/{username}")
    def test_get_user(username: str, db: Session = Depends(get_db)):
        print(f"API 端点中的 db: {id(db)}")
        user = db.query(User).filter(User.username == username).first()
        print(f"API 中找到用户: {user}")
        return {"found": user is not None, "user": user.username if user else None}

    # 临时添加路由
    main.app.include_router(temp_router, prefix="/api/v1")

    response = client.get(f"/api/v1/test-get-user/{test_username}")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

    # 4. 尝试登录
    print("\n4. 尝试登录:")
    login_response = client.post("/api/v1/auth/login", data={
        "username": test_username,
        "password": "testpassword123"
    })
    print(f"状态码: {login_response.status_code}")
    print(f"响应: {login_response.json()}")

db_session.close()
Base.metadata.drop_all(bind=engine)