import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app.core.config import settings

# 使用 pbkdf2_sha256 以避免 bcrypt 依赖/长度限制
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def _create_token(
    subject: Union[str, Any],
    expires_delta: timedelta,
    token_type: str,
) -> str:
    expire = datetime.utcnow() + expires_delta
    to_encode: Dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "type": token_type,
        "jti": str(uuid.uuid4())  # 添加随机的 JWT ID
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    生成 Access Token
    """
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, delta, token_type="access")


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    生成 Refresh Token
    """
    delta = expires_delta or timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, delta, token_type="refresh")


def create_reset_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    生成 Reset Token（用于忘记密码）
    """
    delta = expires_delta or timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, delta, token_type="reset")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    """
    if "$" not in hashed_password:
        return False
    salt, hashed = hashed_password.split("$", 1)
    password_salt = f"{plain_password}{salt}"
    return pwd_context.verify(password_salt, hashed)


def get_password_hash(password: str, salt: str) -> str:
    """
    生成密码哈希，包含盐值
    """
    password_salt = f"{password}{salt}"
    hashed_password = pwd_context.hash(password_salt)
    return f"{salt}${hashed_password}"


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except (JWTError, ValidationError):
        return None


def decode_access_token(token: str) -> Optional[str]:
    """
    解码JWT访问令牌，返回 subject
    """
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    return payload.get("sub")


def decode_refresh_token(token: str) -> Optional[str]:
    """
    解码 refresh token，返回 subject
    """
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        return None
    return payload.get("sub")


def decode_reset_token(token: str) -> Optional[str]:
    """
    解码 reset token，返回 subject
    """
    payload = decode_token(token)
    if not payload or payload.get("type") != "reset":
        return None
    return payload.get("sub")


def create_salt(length: int = 16) -> str:
    """
    生成指定长度的盐值
    """
    return os.urandom(length).hex()
