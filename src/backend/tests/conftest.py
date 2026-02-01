"""Pytest configuration and fixtures for ContentHub tests."""

import pytest
import sys
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from app.db.sql_db import Base
from app.db.database import get_db as database_get_db
from app.db.sql_db import get_db as sql_db_get_db
import main
from app.models.user import User
from app.core.security import create_salt, get_password_hash

# 使用内存 SQLite 作为测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db() -> None:
    """创建并销毁测试数据库。"""
    # 导入所有模型以注册到 Base.metadata
    import app.models  # noqa: F401
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    yield
    # 销毁所有表
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db) -> Generator:
    """创建测试数据库会话。"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """创建 FastAPI 测试客户端。"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override both get_db functions (from database.py and sql_db.py)
    main.app.dependency_overrides[database_get_db] = override_get_db
    main.app.dependency_overrides[sql_db_get_db] = override_get_db

    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def test_user(db_session: sessionmaker, role: str = "operator"):
    """测试用户数据（返回 User 模型实例）。"""
    salt = create_salt()
    user_data = {
        "username": f"testuser_{role}",
        "email": f"test_{role}@example.com",
        "full_name": f"Test User ({role})",
        "password_hash": get_password_hash("testpassword123", salt),
        "role": role,
        "is_active": True
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user

    # 清理测试用户
    db_session.delete(user)
    db_session.commit()


@pytest.fixture(scope="function")
def test_user_data(role: str = "operator"):
    """测试用户数据（返回字典）。"""
    return {
        "username": f"testuser_{role}",
        "email": f"test_{role}@example.com",
        "password": "testpassword123",
    }


@pytest.fixture(scope="function")
def auth_headers(client, test_user_data):
    """获取认证头部。"""
    # 首先注册用户（如果需要）
    response = client.post("/api/v1/auth/register", json=test_user_data)
    if response.status_code == 200:
        # 然后登录获取 token
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"],
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        if login_response.status_code == 200:
            token = login_response.json()["data"]["access_token"]
            return {"Authorization": f"Bearer {token}"}

    return None


@pytest.fixture(scope="function")
def admin_auth_headers(client, db_session):
    """获取管理员用户认证头部。"""
    from app.models.user import User
    from app.core.security import create_salt, get_password_hash

    # 直接在数据库中创建用户（避免 API 注册的问题）
    existing_user = db_session.query(User).filter(User.username == "adminuser").first()
    if not existing_user:
        salt = create_salt()
        user_data = {
            "username": "adminuser",
            "email": "admin@example.com",
            "full_name": "Admin User",
            "password_hash": get_password_hash("testpassword123", salt),
            "role": "admin",
            "is_active": True
        }
        existing_user = User(**user_data)
        db_session.add(existing_user)
        db_session.commit()
        db_session.refresh(existing_user)

    print(f"=== 调试信息 ===")
    print(f"用户是否存在: {existing_user is not None}")
    if existing_user:
        print(f"用户名: {existing_user.username}")
        print(f"邮箱: {existing_user.email}")
        print(f"角色: {existing_user.role}")
        print(f"密码哈希: {existing_user.password_hash}")
        print(f"是否激活: {existing_user.is_active}")

    # 然后登录获取 token
    login_data = {
        "username": "adminuser",
        "password": "testpassword123",
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    print(f"登录状态码: {login_response.status_code}")
    print(f"登录响应: {login_response.json()}")

    if login_response.status_code == 200:
        token = login_response.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return None


@pytest.fixture(scope="function")
def operator_auth_headers(client, db_session):
    """获取操作员用户认证头部。"""
    from app.models.user import User
    from app.core.security import create_salt, get_password_hash

    # 直接在数据库中创建用户（避免 API 注册的问题）
    existing_user = db_session.query(User).filter(User.username == "operatoruser").first()
    if not existing_user:
        salt = create_salt()
        user_data = {
            "username": "operatoruser",
            "email": "operator@example.com",
            "full_name": "Operator User",
            "password_hash": get_password_hash("testpassword123", salt),
            "role": "operator",
            "is_active": True
        }
        existing_user = User(**user_data)
        db_session.add(existing_user)
        db_session.commit()
        db_session.refresh(existing_user)

    # 然后登录获取 token
    login_data = {
        "username": "operatoruser",
        "password": "testpassword123",
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    if login_response.status_code == 200:
        token = login_response.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return None


@pytest.fixture(scope="function")
def editor_auth_headers(client, db_session):
    """获取编辑用户认证头部。"""
    from app.models.user import User
    from app.core.security import create_salt, get_password_hash

    # 直接在数据库中创建用户（避免 API 注册的问题）
    existing_user = db_session.query(User).filter(User.username == "editoruser").first()
    if not existing_user:
        salt = create_salt()
        user_data = {
            "username": "editoruser",
            "email": "editor@example.com",
            "full_name": "Editor User",
            "password_hash": get_password_hash("testpassword123", salt),
            "role": "editor",
            "is_active": True
        }
        existing_user = User(**user_data)
        db_session.add(existing_user)
        db_session.commit()
        db_session.refresh(existing_user)

    # 然后登录获取 token
    login_data = {
        "username": "editoruser",
        "password": "testpassword123",
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    if login_response.status_code == 200:
        token = login_response.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return None


@pytest.fixture(scope="function")
def viewer_auth_headers(client, db_session):
    """获取查看用户认证头部。"""
    from app.models.user import User
    from app.core.security import create_salt, get_password_hash

    # 直接在数据库中创建用户（避免 API 注册的问题）
    existing_user = db_session.query(User).filter(User.username == "vieweruser").first()
    if not existing_user:
        salt = create_salt()
        user_data = {
            "username": "vieweruser",
            "email": "viewer@example.com",
            "full_name": "Viewer User",
            "password_hash": get_password_hash("testpassword123", salt),
            "role": "viewer",
            "is_active": True
        }
        existing_user = User(**user_data)
        db_session.add(existing_user)
        db_session.commit()
        db_session.refresh(existing_user)

    # 然后登录获取 token
    login_data = {
        "username": "vieweruser",
        "password": "testpassword123",
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    if login_response.status_code == 200:
        token = login_response.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return None


@pytest.fixture(scope="function")
def invalid_auth_headers():
    """获取无效的认证头部。"""
    return {"Authorization": "Bearer invalid_token"}


@pytest.fixture(scope="function")
def test_customer(db_session: sessionmaker):
    """测试客户数据（返回 Customer 模型实例）。"""
    from app.models.customer import Customer
    
    customer_data = {
        "name": "测试客户",
        "contact_name": "测试联系人",
        "contact_email": "test@example.com",
        "contact_phone": "13800138000",
        "description": "这是一个测试客户",
        "is_active": True
    }
    
    customer = Customer(**customer_data)
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    
    yield customer
    
    # 清理关联数据（先删除账号）
    from app.models.account import Account
    accounts = db_session.query(Account).filter(Account.customer_id == customer.id).all()
    for account in accounts:
        db_session.delete(account)
    
    # 然后删除客户
    db_session.delete(customer)
    db_session.commit()
