"""
安全模块的临时替代方案
绕过 passlib 依赖
"""
import hashlib
import hmac
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import JWTError, jwt

from app.core.config import settings


def create_salt() -> str:
    """创建盐值"""
    return os.urandom(16).hex()


def get_password_hash(password: str, salt: str = None) -> str:
    """获取密码哈希
    
    使用 HMAC-SHA256 作为简单的替代方案
    """
    if salt is None:
        salt = create_salt()
    
    # 使用 HMAC-SHA256
    key = salt.encode('utf-8')
    message = password.encode('utf-8')
    
    # 生成哈希
    h = hmac.new(key, message, hashlib.sha256)
    return f"{salt}:{h.hexdigest()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        if ':' not in hashed_password:
            return False
            
        salt, stored_hash = hashed_password.split(':', 1)
        new_hash = get_password_hash(plain_password, salt)
        
        # 提取新哈希中的哈希部分
        _, new_hash_part = new_hash.split(':', 1)
        return hmac.compare_digest(new_hash_part, stored_hash)
    except Exception:
        return False


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode: Dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "jti": str(uuid.uuid4())
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建刷新令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode: Dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": str(uuid.uuid4())
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return {}


def is_token_expired(payload: Dict[str, Any]) -> bool:
    """检查令牌是否过期"""
    exp = payload.get("exp")
    if not exp:
        return True
    
    expire_timestamp = datetime.fromtimestamp(exp)
    return datetime.utcnow() > expire_timestamp


def get_token_subject(payload: Dict[str, Any]) -> Optional[str]:
    """获取令牌主题"""
    return payload.get("sub")


def get_token_type(payload: Dict[str, Any]) -> Optional[str]:
    """获取令牌类型"""
    return payload.get("type")