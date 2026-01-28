"""
用户服务单元测试
"""
import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import create_salt, get_password_hash
from tests.config import TEST_USER


@pytest.mark.unit
def test_create_user(db_session: Session):
    """测试创建用户"""
    salt = create_salt()
    user_data = {
        "username": "new_user",
        "email": "new_user@example.com",
        "full_name": "New User",
        "password_hash": get_password_hash("password123", salt),
        "role": "operator",
        "is_active": True
    }

    # 创建用户
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 验证用户已创建
    assert user.id is not None
    assert user.username == "new_user"
    assert user.email == "new_user@example.com"
    assert user.role == "operator"

    print(f"✓ 用户创建测试通过 (ID: {user.id})")


@pytest.mark.unit
def test_query_user(db_session: Session, test_user: User):
    """测试查询用户"""
    # 通过 ID 查询
    user = db_session.query(User).filter(User.id == test_user.id).first()
    assert user is not None
    assert user.username == test_user.username

    # 通过用户名查询
    user = db_session.query(User).filter(User.username == test_user.username).first()
    assert user is not None
    assert user.email == test_user.email

    print("✓ 用户查询测试通过")


@pytest.mark.unit
def test_update_user(db_session: Session, test_user: User):
    """测试更新用户"""
    # 更新用户信息
    test_user.full_name = "Updated Name"
    db_session.commit()
    db_session.refresh(test_user)

    # 验证更新成功
    assert test_user.full_name == "Updated Name"

    print("✓ 用户更新测试通过")


@pytest.mark.unit
def test_delete_user(db_session: Session):
    """测试删除用户"""
    # 创建临时用户
    salt = create_salt()
    user = User(
        username="temp_user",
        email="temp@example.com",
        full_name="Temp User",
        password_hash=get_password_hash("password123", salt),
        role="operator",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    user_id = user.id

    # 删除用户
    db_session.delete(user)
    db_session.commit()

    # 验证删除成功
    deleted_user = db_session.query(User).filter(User.id == user_id).first()
    assert deleted_user is None

    print("✓ 用户删除测试通过")


@pytest.mark.unit
def test_user_role_validation(db_session: Session):
    """测试用户角色验证"""
    # 创建不同角色的用户
    salt = create_salt()

    admin = User(
        username="admin_user",
        email="admin@example.com",
        full_name="Admin User",
        password_hash=get_password_hash("password123", salt),
        role="admin",
        is_active=True
    )

    operator = User(
        username="operator_user",
        email="operator@example.com",
        full_name="Operator User",
        password_hash=get_password_hash("password123", salt),
        role="operator",
        is_active=True
    )

    customer = User(
        username="customer_user",
        email="customer@example.com",
        full_name="Customer User",
        password_hash=get_password_hash("password123", salt),
        role="customer",
        is_active=True
    )

    db_session.add_all([admin, operator, customer])
    db_session.commit()

    # 验证角色
    assert admin.role == "admin"
    assert operator.role == "operator"
    assert customer.role == "customer"

    # 查询管理员
    admins = db_session.query(User).filter(User.role == "admin").all()
    assert len(admins) >= 1

    print("✓ 用户角色验证测试通过")
