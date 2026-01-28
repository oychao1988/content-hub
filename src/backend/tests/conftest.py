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

from app.db.database import Base, get_db
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

    main.app.dependency_overrides[get_db] = override_get_db

    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def test_user(db_session: sessionmaker):
    """测试用户数据（返回 User 模型实例）。"""
    salt = create_salt()
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password_hash": get_password_hash("testpassword123", salt),
        "role": "operator",
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
def test_user_data():
    """测试用户数据（返回字典）。"""
    return {
        "username": "testuser",
        "email": "test@example.com",
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
            token = login_response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}

    return None


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
