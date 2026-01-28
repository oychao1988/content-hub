"""
安全模块单元测试
"""
import pytest
from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_salt,
    get_password_hash,
    verify_password,
    decode_access_token,
    decode_refresh_token,
)


@pytest.mark.unit
def test_create_salt():
    """测试盐值生成"""
    salt1 = create_salt()
    salt2 = create_salt()

    # 验证盐值不为空
    assert salt1
    assert salt2

    # 验证盐值是唯一的
    assert salt1 != salt2

    # 验证盐值长度合理（32字符 = 16字节的十六进制）
    assert len(salt1) == 32

    print(f"✓ 盐值生成测试通过 (salt1: {salt1[:8]}...)")


@pytest.mark.unit
def test_password_hashing():
    """测试密码哈希"""
    password = "test_password_123"
    salt = create_salt()

    # 生成密码哈希
    hashed = get_password_hash(password, salt)

    # 验证哈希格式（应该以盐值开头）
    assert hashed.startswith(salt)
    assert "$" in hashed

    # 验证哈希值不为空且与原密码不同
    assert hashed != password
    assert len(hashed) > len(salt)

    print("✓ 密码哈希测试通过")


@pytest.mark.unit
def test_password_verification():
    """测试密码验证"""
    password = "test_password_123"
    salt = create_salt()
    hashed = get_password_hash(password, salt)

    # 验证正确的密码
    assert verify_password(password, hashed) is True

    # 验证错误的密码
    assert verify_password("wrong_password", hashed) is False

    # 验证空密码
    assert verify_password("", hashed) is False

    print("✓ 密码验证测试通过")


@pytest.mark.unit
def test_access_token():
    """测试访问令牌生成和解码"""
    user_id = 123

    # 生成访问令牌
    token = create_access_token(user_id)
    assert token

    # 解码访问令牌
    decoded_user_id = decode_access_token(token)
    assert decoded_user_id == str(user_id)

    # 验证无效令牌
    invalid_token = "invalid.token.here"
    assert decode_access_token(invalid_token) is None

    print("✓ 访问令牌测试通过")


@pytest.mark.unit
def test_refresh_token():
    """测试刷新令牌生成和解码"""
    user_id = 456

    # 生成刷新令牌
    token = create_refresh_token(user_id)
    assert token

    # 解码刷新令牌
    decoded_user_id = decode_refresh_token(token)
    assert decoded_user_id == str(user_id)

    # 验证访问令牌不能用刷新令牌解码
    access_token = create_access_token(user_id)
    assert decode_refresh_token(access_token) is None

    print("✓ 刷新令牌测试通过")


@pytest.mark.unit
def test_token_uniqueness():
    """测试令牌唯一性"""
    user_id = 789

    # 生成多个令牌，使用不同的过期时间确保唯一性
    token1 = create_access_token(user_id, expires_delta=timedelta(minutes=1))
    token2 = create_access_token(user_id, expires_delta=timedelta(minutes=2))

    # 验证令牌不同（包含过期时间）
    assert token1 != token2

    print("✓ 令牌唯一性测试通过")
